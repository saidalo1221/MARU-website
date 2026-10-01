from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String, func

from app.database import Base

DOCUMENT_TYPES = (
    "invoice", "proforma_invoice", "order_confirmation", "packing_list",
    "fiscal_receipt", "shipping_document", "return_document", "other",
)
GENERATED_TYPES = ("invoice", "proforma_invoice", "order_confirmation", "packing_list")


class OrderDocument(Base):
    """A document that belongs to an order - invoice, fiscal receipt, shipping or return document
    (PRD ТЗ№4 §81-83). The file lives in private storage (never under /static); customers get it
    through a short-lived signed link after the normal order-access check."""

    __tablename__ = "order_documents"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_id = Column(BigInteger, ForeignKey("orders.id"), nullable=False, index=True)
    doc_type = Column(String(30), nullable=False)
    status = Column(String(20), nullable=False, default="issued")  # issued | void
    external_id = Column(String(120), nullable=True)  # the ERP's document id, when it came from there
    filename = Column(String(255), nullable=False)  # name shown to the customer
    storage_name = Column(String(80), nullable=False)  # name on disk (random)
    content_type = Column(String(100), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
