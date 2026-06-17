#!/usr/bin/env python
"""
Crea un usuario super_admin en la base de datos.
Uso en Railway: railway run python scripts/create_super_admin.py
"""
import asyncio
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Must be set before importing app modules
os.environ.setdefault("ENV", "production")

from app.core.database import AsyncSessionLocal
from app.models import Doctor
from app.core.security import get_password_hash
from sqlalchemy import select


async def main():
    email = os.getenv("SUPER_ADMIN_EMAIL", "super@clinica.com")
    password = os.getenv("SUPER_ADMIN_PASSWORD", "")
    name = os.getenv("SUPER_ADMIN_NAME", "Super Admin")

    if not password:
        import secrets
        password = secrets.token_urlsafe(12)[:12]
        auto_generated = True
    else:
        auto_generated = False

    async with AsyncSessionLocal() as db:
        # Check if any super_admin exists
        r = await db.execute(select(Doctor).where(Doctor.role == "super_admin"))
        existing = r.scalar_one_or_none()

        if existing:
            print(f"✅ Super admin ya existe:")
            print(f"   Email: {existing.email}")
            print(f"   Nombre: {existing.full_name}")
            return

        # Check if email is already used by another role
        r = await db.execute(select(Doctor).where(Doctor.email == email))
        conflict = r.scalar_one_or_none()
        if conflict:
            print(f"⚠️  El email '{email}' ya está en uso por un usuario con rol '{conflict.role}'.")
            print(f"   Puedes elevarlo a super_admin con:")
            print(f"   railway run python -c \"")
            print(f"import asyncio")
            print(f"from app.core.database import AsyncSessionLocal")
            print(f"from app.models import Doctor")
            print(f"from sqlalchemy import select")
            print(f"async def f():")
            print(f"    async with AsyncSessionLocal() as db:")
            print(f"        r = await db.execute(select(Doctor).where(Doctor.id == {conflict.id}))")
            print(f"        d = r.scalar_one()")
            print(f"        d.role = 'super_admin'")
            print(f"        await db.commit()")
            print(f"        print(f'{{d.email}} ahora es super_admin')")
            print(f"asyncio.run(f())")
            print(f"   \"")
            return

        admin = Doctor(
            full_name=name,
            email=email,
            hashed_password=get_password_hash(password),
            role="super_admin",
            must_change_password=False,
            is_active=True,
        )
        db.add(admin)
        await db.commit()

        print(f"✅ Super admin creado exitosamente")
        print(f"")
        print(f"   Portal:   https://<tu-dominio>/admin")
        print(f"   Email:    {email}")
        print(f"   Password: {password}")
        if auto_generated:
            print(f"")
            print(f"   ⚠️  Contraseña generada automáticamente. Cópiala ahora.")
            print(f"   Para personalizarla, usa:")
            print(f"   SUPER_ADMIN_EMAIL=admin@tudominio.com SUPER_ADMIN_PASSWORD=MiPass123 railway run python scripts/create_super_admin.py")


if __name__ == "__main__":
    asyncio.run(main())
