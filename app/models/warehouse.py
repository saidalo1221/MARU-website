from sqlalchemy import BigInteger, Boolean, Column, DateTime, Float, Integer, String, Text, func

from app.database import Base


class Warehouse(Base):
    """PRD ТЗ№3 §27/§68: multiple warehouses, with manual priority ("на
    первом этапе допускается ручная настройка приоритета" — automatic
    selection by distance/cost is explicitly deferred beyond MVP). Lower
    `priority` is preferred by app/services/order_service.py's warehouse
    selection when reserving stock."""

    __tablename__ = "warehouses"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    country = Column(String(100), nullable=False)
    address = Column(Text, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    priority = Column(Integer, nullable=False, default=100)
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
