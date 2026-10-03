"""Create a staff account (default role: super_admin) in the database the backend uses.

    python scripts/create_admin.py you@example.com                 # asks for the password
    python scripts/create_admin.py you@example.com --role marketing_manager

Roles: super_admin, product_manager, sales_manager, warehouse_manager, accountant, marketing_manager.
An existing e-mail is never changed; the script stops instead.
"""
import argparse
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.database import SessionLocal  # noqa: E402
import app.models  # noqa: E402,F401  (registers every table)
from app.models.enums import UserRole  # noqa: E402
from app.models.user import User  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("email")
    ap.add_argument("--role", default="super_admin", choices=[r.value for r in UserRole if r != UserRole.CUSTOMER])
    args = ap.parse_args()

    password = getpass.getpass("Password (at least 10 characters): ")
    if len(password) < 10 or password != getpass.getpass("Repeat password: "):
        sys.exit("Password too short or the two entries differ. Nothing was created.")

    db = SessionLocal()
    try:
        email = args.email.strip().lower()
        if db.execute(select(User).where(User.email == email)).scalar_one_or_none() is not None:
            sys.exit("That e-mail already has an account. Nothing was changed.")
        db.add(User(email=email, password_hash=hash_password(password), role=UserRole(args.role), is_active=True, email_verified=True))
        db.commit()
        print("Created %s as %s." % (email, args.role))
    finally:
        db.close()


if __name__ == "__main__":
    main()
