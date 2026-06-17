#!/usr/bin/env python
"""
Uso: railway run python scripts/super_admin_crear.py
Crea un super_admin desde cero (email y password configurables).
"""
import asyncio, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault("ENV", "production")

from app.core.database import AsyncSessionLocal
from app.models import Doctor
from app.core.security import get_password_hash
from sqlalchemy import select

async def main():
    email = os.getenv("EMAIL", "inghendrickrafael@gmail.com")
    password = os.getenv("PASSWORD", "cedano@1")

    async with AsyncSessionLocal() as db:
        existe = (await db.execute(select(Doctor).where(Doctor.email == email))).scalar_one_or_none()
        if existe:
            print(f"❌ El email {email} ya pertenece a {existe.full_name} (rol: {existe.role})")
            print("Usa scripts/super_admin_editar.py para cambiarle el rol.")
            return

        admin = Doctor(
            full_name=os.getenv("NOMBRE", "Super Admin"),
            email=email,
            hashed_password=get_password_hash(password),
            role="super_admin",
            must_change_password=False,
            is_active=True,
        )
        db.add(admin)
        await db.commit()
        print(f"✅ Super admin creado: {email} / {password}")

asyncio.run(main())
