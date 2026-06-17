# Railway — Comandos útiles

## Super Admin

### Crear super_admin desde cero
```bash
railway run python scripts/super_admin_crear.py
```
Con datos personalizados:
```bash
EMAIL=admin@midominio.com PASSWORD=Clave123 NOMBRE="Admin Pro" railway run python scripts/super_admin_crear.py
```

### Elevar usuario existente a super_admin
```bash
EMAIL=admin@nutribot.com railway run python scripts/super_admin_editar.py
```

## Base de datos

### Correr migraciones
```bash
railway run alembic upgrade head
```
Para staging:
```bash
railway run --environment staging alembic upgrade head
```
