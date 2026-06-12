# Limpiar DietDetail + Simplificar estrategias + Recalcular nutrición

**Fecha:** 2026-06-12

---

## 1. DietDetail — Lenguaje amigable

- Mostrar nombre real del paciente, no `Patient #7`
- Badge de estado: "Aprobada" / "Pendiente de aprobación"
- Fecha legible: "12 de junio, 2026"
- `Summary` → `Resumen`
- Quitar botones sueltos: `Download .txt`, `Download .json`, `Download PDF` (ya están en DietActions)
- Quitar sección `Versions`
- Quitar `Structured plan (JSON)`
- Quitar formulario `Regenerate (new version)`

## 2. Quitar "Regenerar"

- Eliminar botón "Regenerar (nueva versión)" de `DietActions.tsx`

## 3. Ocultar estrategias avanzadas

- Feature flag `NEXT_FEATURES.advancedStrategies = false`
- Oculta: selector de modo, estilos de dieta, preferencias de macros, targets manuales
- En wizard y formulario inline

## 4. Recalcular nutrición al editar comidas

- Después de `update_diet_meals()`, re-ejecutar `_generate_plan_with_nutrition_engine`
- Actualizar `daily_calories`, `macro_grams`, `nutrition_engine` en el plan
- Agregar nota: "Valores nutricionales recalculados según perfil del paciente"

---

## Verificación

- [ ] DietDetail muestra nombre del paciente, badge legible, fecha legible, sin JSON
- [ ] No aparecen botones Download .txt/.json sueltos
- [ ] No aparece sección Versions ni Structured plan
- [ ] No aparece botón Regenerar
- [ ] Wizard solo muestra modo Auto (Guided/Manual ocultos)
- [ ] Al editar una comida, los macros se recalculan
