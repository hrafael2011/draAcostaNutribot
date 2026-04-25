#!/usr/bin/env python
"""Create or reset the internal admin account.

Usage from backend container/project root:
    python scripts/bootstrap_admin.py --email admin@example.com --name "Admin" --password "TempPass123!"
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
import sys

from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.database import AsyncSessionLocal  # noqa: E402
from app.core.security import get_password_hash  # noqa: E402
from app.models import Doctor, utcnow  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bootstrap/reset admin account")
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--phone", default=None)
    parser.add_argument(
        "--no-force-change",
        action="store_true",
        help="Do not force password change on next login.",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    email = args.email.lower().strip()
    must_change_password = not args.no_force_change

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Doctor).where(Doctor.email == email))
        admin = result.scalar_one_or_none()
        if admin is None:
            admin = Doctor(
                full_name=args.name.strip(),
                email=email,
                phone=args.phone,
                hashed_password=get_password_hash(args.password),
                role="admin",
                must_change_password=must_change_password,
                is_active=True,
            )
            session.add(admin)
            action = "created"
        else:
            admin.full_name = args.name.strip()
            admin.phone = args.phone
            admin.hashed_password = get_password_hash(args.password)
            admin.role = "admin"
            admin.must_change_password = must_change_password
            admin.is_active = True
            admin.updated_at = utcnow()
            action = "updated"

        await session.commit()
        print(f"Admin {action}: {email}")
        print(f"must_change_password={must_change_password}")


if __name__ == "__main__":
    asyncio.run(main())
