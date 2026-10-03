from sqlalchemy import BigInteger, Column, DateTime, String, UniqueConstraint, func

from app.database import Base


class ExternalId(Base):
    """Maps one of our records to its id in an outside system (ERP, CRM, marketplace, carrier) -
    PRD ТЗ№4 §3-5. One row per (system, entity, internal id); the external id itself is unique per
    (system, entity), so an inbound event can be matched back to the right record."""

    __tablename__ = "external_ids"
    __table_args__ = (
        UniqueConstraint("system", "entity", "internal_id", name="uq_external_ids_internal"),
        UniqueConstraint("system", "entity", "external_id", name="uq_external_ids_external"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    system = Column(String(40), nullable=False)  # "erp_1c", "crm_bitrix24", "uzum", ...
    entity = Column(String(40), nullable=False)  # "order", "customer", "product", "sku", "shipment"
    internal_id = Column(BigInteger, nullable=False)
    external_id = Column(String(120), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
