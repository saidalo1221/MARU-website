from sqlalchemy import BigInteger, Boolean, Column, DateTime, DECIMAL, ForeignKey, Integer, String, UniqueConstraint, func

from app.database import Base

# kind values of LoyaltyTransaction
EARN = "earn"                      # + points for a paid order
EARN_REVERSE = "earn_reverse"      # - the same points when the order is refunded / cancelled after payment
REDEEM = "redeem"                  # - points spent as a discount at checkout
REDEEM_RESTORE = "redeem_restore"  # + points given back when the order never completed
ADJUST = "adjust"                  # +/- a manual correction by staff
EXPIRE = "expire"                  # - points that sat unspent past the expiry period


class LoyaltySettings(Base):
    """The single row (id = 1) that defines the loyalty programme (PRD ТЗ№1 §11, §62): how fast points are earned,
    what a point is worth, and how much of an order points may pay for. Edited in the admin panel."""

    __tablename__ = "loyalty_settings"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = Column(BigInteger, primary_key=True)
    enabled = Column(Boolean, nullable=False, default=True)
    earn_per_usd = Column(DECIMAL(8, 2), nullable=False, default=1)         # points per 1 USD of goods paid
    point_value_usd = Column(DECIMAL(8, 4), nullable=False, default=0.01)   # what one point is worth when spent
    max_redeem_percent = Column(Integer, nullable=False, default=50)        # points may pay for at most this % of the goods
    # Which customer types take part: comma-separated CustomerType values (retail, wholesale, distributor, export, special).
    eligible_customer_types = Column(String(120), nullable=False, default="retail", server_default="retail")
    # Earned points expire after this many days when unspent (oldest points are spent first); 0 = never.
    expiry_days = Column(Integer, nullable=False, default=0, server_default="0")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class LoyaltyTransaction(Base):
    """One movement of a customer's points; the balance is the sum of `points`. For the order-driven kinds the
    pair (order_id, kind) is unique, so replaying a status change can never pay out or take back twice."""

    __tablename__ = "loyalty_transactions"
    __table_args__ = (
        UniqueConstraint("order_id", "kind", name="uq_loyalty_order_kind"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    kind = Column(String(20), nullable=False)
    points = Column(Integer, nullable=False)  # signed
    order_id = Column(BigInteger, ForeignKey("orders.id"), nullable=True)
    note = Column(String(300), nullable=True)
    created_by_user_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class LoyaltyTier(Base):
    """A level of the programme (PRD ТЗ№1 §62): customers whose lifetime earned points reach `min_points_earned`
    earn points `earn_multiplier` times as fast (1.50 = 50% faster). Defined by the business in the admin panel."""

    __tablename__ = "loyalty_tiers"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(60), nullable=False)
    min_points_earned = Column(Integer, nullable=False, default=0)
    earn_multiplier = Column(DECIMAL(4, 2), nullable=False, default=1)
