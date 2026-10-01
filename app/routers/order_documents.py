from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.core.rate_limit import rate_limit
from app.database import get_db
from app.dependencies import get_current_user_optional, require_role
from app.models.enums import UserRole
from app.models.order import Order
from app.models.order_document import DOCUMENT_TYPES, OrderDocument
from app.models.user import User
from app.routers.orders import _require_order_access
from app.schemas.document import DocumentLinkOut, OrderDocumentOut
from app.services import documents
from app.services.audit import log_audit

# Customer side: list a document's metadata and get a short-lived signed link. The file itself is
# only reachable through that link, never from a public static path.
router = APIRouter(tags=["order-documents"], dependencies=[Depends(rate_limit("order_documents", 60, 60))])


def _order_for_customer(db: Session, order_id: int, user: Optional[User], order_token: Optional[str]) -> Order:
    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    _require_order_access(order, user, order_token)
    return order


@router.get("/orders/{order_id}/documents", response_model=list[OrderDocumentOut])
def list_order_documents(
    order_id: int,
    order_token: Optional[str] = Header(default=None, alias="X-Order-Token"),
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> list[OrderDocument]:
    _order_for_customer(db, order_id, user, order_token)
    stmt = select(OrderDocument).where(OrderDocument.order_id == order_id, OrderDocument.status == "issued").order_by(OrderDocument.id)
    return list(db.execute(stmt).scalars())


@router.post("/orders/{order_id}/documents/{document_id}/link", response_model=DocumentLinkOut)
def document_link(
    order_id: int,
    document_id: int,
    order_token: Optional[str] = Header(default=None, alias="X-Order-Token"),
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> DocumentLinkOut:
    _order_for_customer(db, order_id, user, order_token)
    doc = db.get(OrderDocument, document_id)
    if doc is None or doc.order_id != order_id or doc.status != "issued":
        raise HTTPException(status_code=404, detail="Document not found")
    token = documents.make_link_token(doc.id)
    return DocumentLinkOut(
        url=f"{settings.BACKEND_URL.rstrip('/')}/api/v1/documents/download?token={token}",
        expires_in_seconds=documents.LINK_MINUTES * 60,
    )


@router.get("/documents/download")
def download_document(token: str, db: Session = Depends(get_db)) -> FileResponse:
    document_id = documents.read_link_token(token)
    doc = db.get(OrderDocument, document_id) if document_id is not None else None
    if doc is None or doc.status != "issued":
        raise HTTPException(status_code=404, detail="Link expired or invalid")
    path = documents.path_of(doc.storage_name)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Document not found")
    return FileResponse(
        path, media_type=doc.content_type, filename=doc.filename,
        headers={"Cache-Control": "private, no-store", "X-Robots-Tag": "noindex, nofollow"},
    )


admin_router = APIRouter(prefix="/admin/orders", tags=["admin-order-documents"])


@admin_router.get("/{order_id}/documents", response_model=list[OrderDocumentOut])
def admin_list_documents(
    order_id: int, user: User = Depends(require_role(UserRole.SALES_MANAGER)), db: Session = Depends(get_db)
) -> list[OrderDocument]:
    stmt = select(OrderDocument).where(OrderDocument.order_id == order_id).order_by(OrderDocument.id)
    return list(db.execute(stmt).scalars())


@admin_router.post("/{order_id}/documents", response_model=OrderDocumentOut, status_code=status.HTTP_201_CREATED)
async def admin_add_document(
    order_id: int,
    file: UploadFile = File(...),
    doc_type: str = Form(...),
    external_id: Optional[str] = Form(default=None),
    user: User = Depends(require_role(UserRole.SALES_MANAGER)),
    db: Session = Depends(get_db),
) -> OrderDocument:
    if db.get(Order, order_id) is None:
        raise HTTPException(status_code=404, detail="Order not found")
    if doc_type not in DOCUMENT_TYPES:
        raise HTTPException(status_code=400, detail=f"doc_type must be one of {', '.join(DOCUMENT_TYPES)}")
    if file.content_type not in documents.ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF, JPEG and PNG documents are accepted")
    data = await file.read()
    if len(data) > documents.MAX_BYTES:
        raise HTTPException(status_code=400, detail="Document too large (max 10MB)")
    if not documents.matches_signature(file.content_type, data):
        raise HTTPException(status_code=400, detail="File content does not match its type")
    doc = OrderDocument(
        order_id=order_id, doc_type=doc_type, external_id=(external_id or None),
        filename=(file.filename or "document")[:255].replace("/", "_").replace("\\", "_"),
        storage_name=documents.save(file.content_type, data), content_type=file.content_type, size_bytes=len(data),
    )
    db.add(doc)
    db.flush()
    log_audit(db, user, "order_document_add", "order", order_id, new={"document_id": doc.id, "doc_type": doc_type})
    db.commit()
    db.refresh(doc)
    return doc


@admin_router.post("/{order_id}/documents/{document_id}/void", response_model=OrderDocumentOut)
def admin_void_document(
    order_id: int, document_id: int, user: User = Depends(require_role(UserRole.SALES_MANAGER)), db: Session = Depends(get_db)
) -> OrderDocument:
    doc = db.get(OrderDocument, document_id)
    if doc is None or doc.order_id != order_id:
        raise HTTPException(status_code=404, detail="Document not found")
    doc.status = "void"
    log_audit(db, user, "order_document_void", "order", order_id, new={"document_id": doc.id})
    db.commit()
    db.refresh(doc)
    return doc
