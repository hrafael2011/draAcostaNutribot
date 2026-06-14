#!/usr/bin/env python
"""Create an admin account for accessing the admin panel.

Connects to the database via the DATABASE_URL environment variable (or the
value defined in .env at the project root).  If an account with the given
email already exists it is promoted to role="admin" and its password is
reset — the script never creates duplicates.

Usage (run from the backend/ directory):
    python scripts/create_admin.py --email admin@example.com --password mypassword

Optional flags:
    --name   "Full Name"   Display name stored in full_name  (default: "Admin")
    --phone  "+1234567890" Phone number                      (default: none)
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Make sure the backend package root is on sys.path so that `app.*` imports
# work regardless of the working directory the script is called from.
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Allow DATABASE_URL to be supplied as a plain env-var override before the
# settings object is instantiated (useful in CI / Railway deploy hooks).
_db_url_override = os.environ.get("DATABASE_URL")
if _db_url_override:
    # Normalise legacy postgres:// scheme so asyncpg is happy.
    from app.core.config import normalize_async_database_url  # noqa: E402

    os.environ["DATABASE_URL"] = normalize_async_database_url(_db_url_override)

from sqlalchemy import select  # noqa: E402
from sqlalchemy.exc import OperationalError, SQLAlchemyError  # noqa: E402

from app.core.database import AsyncSessionLocal  # noqa: E402
from app.core.security import get_password_hash  # noqa: E402
from app.models import Doctor, utcnow  # noqa: E402


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create (or reset) an admin account for the admin panel.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--email",
        required=True,
        metavar="EMAIL",
        help="Email address used to log in (e.g. admin@example.com).",
    )
    parser.add_argument(
        "--password",
        required=True,
        metavar="PASSWORD",
        help="Plain-text password — will be hashed with bcrypt before storage.",
    )
    parser.add_argument(
        "--name",
        default="Admin",
        metavar="NAME",
        help='Display name stored in full_name (default: "Admin").',
    )
    parser.add_argument(
        "--phone",
        default=None,
        metavar="PHONE",
        help="Optional phone number.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

async def create_or_update_admin(
    email: str,
    password: str,
    full_name: str,
    phone: str | None,
) -> None:
    """Insert a new admin Doctor row, or update an existing one."""

    email = email.lower().strip()

    if not email or "@" not in email:
        print(f"ERROR: '{email}' does not look like a valid email address.", file=sys.stderr)
        sys.exit(1)

    if len(password) < 8:
        print("ERROR: Password must be at least 8 characters.", file=sys.stderr)
        sys.exit(1)

    hashed = get_password_hash(password)

    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Doctor).where(Doctor.email == email)
            )
            existing = result.scalar_one_or_none()

            if existing is None:
                admin = Doctor(
                    full_name=full_name.strip(),
                    email=email,
                    phone=phone,
                    hashed_password=hashed,
                    role="admin",
                    is_active=True,
                    must_change_password=False,
                )
                session.add(admin)
                action = "created"
            else:
                existing.full_name = full_name.strip()
                existing.phone = phone
                existing.hashed_password = hashed
                existing.role = "admin"
                existing.is_active = True
                existing.must_change_password = False
                existing.updated_at = utcnow()
                action = "updated"

            await session.commit()

    except OperationalError as exc:
        print(
            f"\nERROR: Could not connect to the database.\n"
            f"  Make sure DATABASE_URL is set correctly and the database is reachable.\n"
            f"  Detail: {exc.orig}",
            file=sys.stderr,
        )
        sys.exit(1)
    except SQLAlchemyError as exc:
        print(f"\nERROR: Database error — {exc}", file=sys.stderr)
        sys.exit(1)

    # Success output
    print()
    print(f"  Admin account {action} successfully.")
    print(f"  ----------------------------------------")
    print(f"  Email    : {email}")
    print(f"  Name     : {full_name.strip()}")
    print(f"  Role     : admin")
    print(f"  Active   : yes")
    print()
    print("  You can now log in at the admin panel with these credentials.")
    print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()
    asyncio.run(
        create_or_update_admin(
            email=args.email,
            password=args.password,
            full_name=args.name,
            phone=args.phone,
        )
    )


if __name__ == "__main__":
    main()
