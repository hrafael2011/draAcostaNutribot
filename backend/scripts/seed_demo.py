#!/usr/bin/env python3
"""Carga datos demo en la BD. Ejecutar desde la carpeta backend: python scripts/seed_demo.py"""
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


async def main() -> None:
    from app.demo_seed import (
        DEMO_DOCTOR_EMAIL,
        DEMO_DOCTOR_PASSWORD,
        run_demo_seed,
    )

    info = await run_demo_seed()
    print("Demo seed OK.")
    print(f"  Doctor ID: {info['doctor_id']}")
    print(f"  Login:     {DEMO_DOCTOR_EMAIL}")
    print(f"  Password:  {DEMO_DOCTOR_PASSWORD}")
    for p in info["patients"]:
        print(f"  Paciente #{p['id']}: {p['name']}")


if __name__ == "__main__":
    asyncio.run(main())
