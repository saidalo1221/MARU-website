from sqlalchemy import BigInteger, Boolean, Column, DateTime, Float, ForeignKey, String, func

from app.database import Base


class Address(Base):
    __tablename__ = "addresses"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    label = Column(String(50), nullable=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(30), nullable=False)
    country = Column(String(100), nullable=False)
    region = Column(String(100), nullable=True)  # state/province; selects region tax rules
    city = Column(String(100), nullable=False)
    address_line = Column(String(255), nullable=False)
    postal_code = Column(String(20), nullable=False)
    is_default = Column(Boolean, nullable=False, default=False)
    # Set when the address was picked via the map (customer-facing MapPicker
    # component); text fields above are still the source of truth for
    # shipping-rate country matching, so they're kept in sync via reverse
    # geocoding rather than replaced.
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
