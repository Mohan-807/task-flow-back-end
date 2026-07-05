"""One-off bootstrap script: create the first admin user.

Run with:
    uv run python scripts/create_admin.py
"""

import getpass
import sys
from pathlib import Path

# Run as a script (not `python -m`), so the project root needs to be on
# sys.path for `app.*` imports to resolve.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.security import hash_password
from app.core.utils import generate_initials
from app.db.session import SessionLocal
from app.models.user import User


def main() -> None:
    db = SessionLocal()

    try:
        name = input("Admin name: ").strip()
        email = input("Admin email: ").strip()
        password = getpass.getpass("Admin password: ")
        confirm = getpass.getpass("Confirm password: ")

        if password != confirm:
            print("Passwords do not match. Aborting.")
            return

        if len(password) < 6:
            print("Password must be at least 6 characters. Aborting.")
            return

        if db.query(User).filter(User.email == email).first():
            print(f"A user with email '{email}' already exists. Aborting.")
            return

        user = User(
            name=name,
            email=email,
            hashed_password=hash_password(password),
            role="admin",
            status="active",
            color="#6366f1",
            initials=generate_initials(name),
        )
        db.add(user)
        db.commit()

        print(f"Created admin user '{email}' (id={user.id}).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
