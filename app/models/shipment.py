from sqlalchemy import BigInteger, Column, DateTime, Enum as SAEnum, ForeignKey, String, Text, func
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.enums import ShipmentStatus


class Shipment(Base):
    """One parcel handed to a carrier for an order (PRD ТЗ№2 §25, ТЗ№3 §32,
    ТЗ№4 §29-33). An order may have several shipments (split deliveries). No
    carrier API is integrated yet: `carrier` is free text and events are
    entered by an admin; a carrier adapter can later write the same
    ShipmentEvent rows."""

    __tablename__ = "shipments"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_id = Column(BigInteger, ForeignKey("orders.id"), nullable=False, index=True)

    carrier = Column(String(100), nullable=False)
    tracking_number = Column(String(100), nullable=True)
    tracking_url = Column(String(500), nullable=True)

    status = Column(SAEnum(ShipmentStatus, native_enum=False, length=20), nullable=False, default=ShipmentStatus.SHIPPED)
    shipped_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)

    created_by_user_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    order = relationship("Order", back_populates="shipments")
    events = relationship(
        "ShipmentEvent",
        back_populates="shipment",
        cascade="all, delete-orphan",
        order_by="ShipmentEvent.occurred_at, ShipmentEvent.id",
    )


class ShipmentEvent(Base):
    """Timeline entry shown to the customer ("Departed Tashkent hub")."""

    __tablename__ = "shipment_events"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    shipment_id = Column(BigInteger, ForeignKey("shipments.id"), nullable=False, index=True)

    status = Column(SAEnum(ShipmentStatus, native_enum=False, length=20), nullable=False)
    location = Column(String(255), nullable=True)
    note = Column(Text, nullable=True)
    occurred_at = Column(DateTime, server_default=func.now(), nullable=False)

    created_by_user_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    shipment = relationship("Shipment", back_populates="events")
