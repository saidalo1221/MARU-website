from datetime import datetime
from secrets import token_urlsafe
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models.enums import UserRole
from app.models.user import User
from app.models.webhook_endpoint import EVENTS, WebhookEndpoint
from app.services.audit import log_audit
from app.services.outbound_webhooks import UnsafeURLError, check_url, emit

router = APIRouter(prefix="/admin/webhooks", tags=["admin-webhooks"])
_ROLE = UserRole.SUPER_ADMIN


def _normalize_events(value: list[str]) -> str:
    cleaned = sorted({v.strip() for v in value if v.strip()})
    if not cleaned or cleaned == ["*"] or "*" in cleaned:
        return "*"
    unknown = [v for v in cleaned if v not in EVENTS]
    if unknown:
        raise ValueError(f"Unknown event(s): {', '.join(unknown)}. Choose from {', '.join(EVENTS)}")
    return ",".join(cleaned)


class EndpointIn(BaseModel):
    url: str = Field(min_length=8, max_length=500)
    description: Optional[str] = Field(default=None, max_length=200)
    events: list[str] = Field(default_factory=lambda: ["*"])
    is_active: bool = True

    @field_validator("events")
    @classmethod
    def _events(cls, v):
        _normalize_events(v)
        return v


class EndpointUpdate(BaseModel):
    url: Optional[str] = Field(default=None, min_length=8, max_length=500)
    description: Optional[str] = Field(default=None, max_length=200)
    events: Optional[list[str]] = None
    is_active: Optional[bool] = None

    @field_validator("events")
    @classmethod
    def _events(cls, v):
        if v is not None:
            _normalize_events(v)
        return v


class EndpointOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    description: Optional[str]
    events: list[str]
    is_active: bool
    secret_hint: str
    last_delivery_at: Optional[datetime]
    last_status_code: Optional[int]
    last_error: Optional[str]


class EndpointCreated(EndpointOut):
    secret: str  # shown once, here and on rotation


def _out(e: WebhookEndpoint, with_secret: bool = False):
    base = dict(
        id=e.id, url=e.url, description=e.description, events=(["*"] if e.events == "*" else e.events.split(",")),
        is_active=e.is_active, secret_hint="…" + e.secret[-4:], last_delivery_at=e.last_delivery_at,
        last_status_code=e.last_status_code, last_error=e.last_error,
    )
    return EndpointCreated(**base, secret=e.secret) if with_secret else EndpointOut(**base)


def _check(url: str) -> None:
    try:
        check_url(url)
    except UnsafeURLError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/events", response_model=list[str])
def list_events(user: User = Depends(require_role(_ROLE))) -> list[str]:
    return list(EVENTS)


@router.get("/", response_model=list[EndpointOut])
def list_endpoints(user: User = Depends(require_role(_ROLE)), db: Session = Depends(get_db)):
    return [_out(e) for e in db.execute(select(WebhookEndpoint).order_by(WebhookEndpoint.id)).scalars()]


@router.post("/", response_model=EndpointCreated, status_code=status.HTTP_201_CREATED)
def create_endpoint(payload: EndpointIn, user: User = Depends(require_role(_ROLE)), db: Session = Depends(get_db)):
    _check(payload.url)
    endpoint = WebhookEndpoint(
        url=payload.url, description=payload.description, secret=token_urlsafe(32), is_active=payload.is_active,
        events=_normalize_events(payload.events),
    )
    db.add(endpoint)
    db.flush()
    log_audit(db, user, "webhook_endpoint_create", "webhook_endpoint", endpoint.id, new={"url": endpoint.url, "events": endpoint.events})
    db.commit()
    db.refresh(endpoint)
    return _out(endpoint, with_secret=True)


@router.patch("/{endpoint_id}", response_model=EndpointOut)
def update_endpoint(endpoint_id: int, payload: EndpointUpdate, user: User = Depends(require_role(_ROLE)), db: Session = Depends(get_db)):
    endpoint = db.get(WebhookEndpoint, endpoint_id)
    if endpoint is None:
        raise HTTPException(status_code=404, detail="Webhook not found")
    changes = payload.model_dump(exclude_unset=True)
    if "url" in changes:
        _check(changes["url"])
    if "events" in changes:
        changes["events"] = _normalize_events(changes["events"])
    log_audit(db, user, "webhook_endpoint_update", "webhook_endpoint", endpoint.id, new=changes)
    for field, value in changes.items():
        setattr(endpoint, field, value)
    db.commit()
    db.refresh(endpoint)
    return _out(endpoint)


@router.post("/{endpoint_id}/rotate-secret", response_model=EndpointCreated)
def rotate_secret(endpoint_id: int, user: User = Depends(require_role(_ROLE)), db: Session = Depends(get_db)):
    endpoint = db.get(WebhookEndpoint, endpoint_id)
    if endpoint is None:
        raise HTTPException(status_code=404, detail="Webhook not found")
    endpoint.secret = token_urlsafe(32)
    log_audit(db, user, "webhook_endpoint_rotate", "webhook_endpoint", endpoint.id)
    db.commit()
    db.refresh(endpoint)
    return _out(endpoint, with_secret=True)


@router.post("/{endpoint_id}/test", status_code=status.HTTP_202_ACCEPTED)
def send_test(endpoint_id: int, user: User = Depends(require_role(_ROLE)), db: Session = Depends(get_db)) -> dict:
    """Queues a `ping` event to this endpoint only, so the receiver can be wired up before real events flow."""
    endpoint = db.get(WebhookEndpoint, endpoint_id)
    if endpoint is None:
        raise HTTPException(status_code=404, detail="Webhook not found")
    from app.services.jobs import enqueue, run_pending
    from app.config import settings
    import json
    import uuid
    from datetime import timezone

    event_id = uuid.uuid4().hex
    body = json.dumps({"id": event_id, "event": "ping", "created_at": datetime.now(timezone.utc).isoformat(), "data": {"message": "Test event from MARU"}})
    enqueue(db, "webhook.deliver", {"endpoint_id": endpoint.id, "event": "ping", "event_id": event_id, "body": body}, dedupe_key=f"wh:{endpoint.id}:{event_id}")
    if not settings.JOBS_ASYNC:
        run_pending(db, "inline", limit=1)
    db.refresh(endpoint)
    return {"status": "queued", "last_status_code": endpoint.last_status_code, "last_error": endpoint.last_error}


@router.delete("/{endpoint_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_endpoint(endpoint_id: int, user: User = Depends(require_role(_ROLE)), db: Session = Depends(get_db)) -> None:
    endpoint = db.get(WebhookEndpoint, endpoint_id)
    if endpoint is None:
        raise HTTPException(status_code=404, detail="Webhook not found")
    log_audit(db, user, "webhook_endpoint_delete", "webhook_endpoint", endpoint.id, old={"url": endpoint.url})
    db.delete(endpoint)
    db.commit()
