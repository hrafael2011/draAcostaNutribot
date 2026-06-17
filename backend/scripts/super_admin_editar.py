#!/usr/bin/env python
"""
Uso: railway run python scripts/super_admin_editar.py
Cambia el rol de un usuario existente a super_admin.
Configurable via EMAIL=xxx.
"""
import asyncio, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault("ENV", "production")

from app.core.database import AsyncSessionLocal
from app.models import Doctor
from sqlalchemy import select

async def main():
    email = os.getenv("EMAIL", "admin@nutribot.com")

    async with AsyncSessionLocal() as db:
        doc = (await db.execute(select(Doctor).where(Doctor.email == email))).scalar_one_or_none()
        if not doc:
            print(f"❌ No existe un usuario con email {email}")
            return

        rol_viejo = doc.role
        doc.role = "super_admin"
        await db.commit()
        print(f"✅ {doc.full_name} ({email}) ahora es super_admin")
        print(f"   Rol anterior: {rol_viejo}")

asyncio.run(main())
