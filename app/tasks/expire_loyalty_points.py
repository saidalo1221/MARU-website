"""Removes loyalty points that stayed unspent past the expiry period set in Admin > Loyalty (0 = they never expire).
Customers who look at their balance or spend points are brought up to date on the spot; this daily run catches the
rest so the numbers in reports are right.

    python -m app.tasks.expire_loyalty_points
"""

from sqlalchemy import select

from app.database import SessionLocal
from app.models.loyalty import LoyaltyTransaction
from app.services import loyalty


def run(db) -> int:
    """Returns how many points were expired in total."""
    if not loyalty.get_settings(db).expiry_days:
        return 0
    total = 0
    for user_id in db.execute(select(LoyaltyTransaction.user_id).distinct()).scalars().all():
        total += loyalty.expire_due(db, user_id)
    db.commit()
    return total


if __name__ == "__main__":
    session = SessionLocal()
    try:
        print(f"loyalty points expired: {run(session)}")
    finally:
        session.close()
