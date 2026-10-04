from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.rate_limit import rate_limit
from app.database import get_db
from app.services import webhooks

router = APIRouter(prefix="/integrations", tags=["integration-webhooks"])

MAX_BODY = 1_000_000


@router.post("/{provider}/webhook", status_code=202, dependencies=[Depends(rate_limit("integration_webhook", 300, 60))])
async def receive_webhook(provider: str, request: Request, db: Session = Depends(get_db)) -> dict:
    secret = webhooks.provider_secret(provider)
    if secret is None:
        raise HTTPException(status_code=404, detail="Unknown provider")
    body = await request.body()
    if len(body) > MAX_BODY:
        raise HTTPException(status_code=413, detail="Payload too large")
    h = request.headers
    if not webhooks.verify(secret, h.get("x-maru-timestamp", ""), h.get("x-maru-signature", ""), body):
        raise HTTPException(status_code=401, detail="Invalid signature")
    event_id = h.get("x-maru-event-id", "").strip()
    if not event_id or len(event_id) > 120:
        raise HTTPException(status_code=400, detail="X-Maru-Event-Id header is required")
    created = webhooks.accept(db, provider, event_id, body)
    return {"status": "accepted" if created else "duplicate"}
