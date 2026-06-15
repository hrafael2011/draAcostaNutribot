# Compartir PDF + Feedback Visual + Reglas Clínicas Amigables

**Date:** 2026-06-15
**Status:** Approved

## Contexto

Tres mejoras en la experiencia post-generación de dieta:

1. **Solo se puede descargar el PDF** — En móvil no hay opción de compartir directo a WhatsApp, correo, etc. como hacen las aplicaciones nativas.
2. **Botones de duración sin feedback visual** — Al elegir 7, 14, 21 días no se marca en verde qué opción está seleccionada.
3. **Reglas clínicas en lenguaje técnico** — Se muestran códigos como `diabetes_carb_distribution_low_gi` que la doctora no entiende a simple vista.

## Decisiones de Diseño

### 1. Compartir PDF con Web Share API

**Enfoque:** Usar `navigator.share()` en dispositivos que lo soporten (móviles Android/iOS). En desktop, mantener solo el botón de descarga.

**Flujo:**
1. Usuario toca "Compartir PDF" → se muestra overlay de carga "Preparando documento..."
2. Se descarga el PDF como Blob (reutilizando `downloadDietPdf` de `api.ts`)
3. Se convierte el Blob a `File` con nombre `dieta-{id}.pdf`
4. Se llama `navigator.share({files: [file]})` → se abre el menú nativo del SO (WhatsApp, Telegram, Gmail, etc.)
5. Si `navigator.share` no está disponible (desktop), se muestra el botón "Descargar PDF" como fallback

**Detección de soporte:**
```ts
const canShare = typeof navigator !== "undefined" && navigator.share && navigator.canShare;
const canShareFiles = canShare && navigator.canShare({ files: [new File([], "test.pdf", { type: "application/pdf" })] });
```

- **Móvil con soporte** → Se muestran ambos botones: "Descargar PDF" + "Compartir PDF" (este último con borde verde, estilo outline)
- **Desktop sin soporte** → Solo "Descargar PDF" (comportamiento actual)

**Archivos a modificar:**
- `frontend/src/components/diet/DietActions.tsx` — Añadir botón "Compartir" condicional + lógica de share
- `frontend/src/services/api.ts` — Modificar `downloadDietPdf` para devolver el Blob (opcional, o crear `getDietPdfBlob`)
- `frontend/src/pages/DietDetail.tsx` — Pasar handler de share a DietActions

### 2. Duración con feedback verde esmeralda

**Enfoque:** Añadir prop `value` a `DurationPresetButtons` para saber cuál está seleccionado y aplicar el mismo estilo que ya usa `DurationPresets.tsx` (la versión wizard).

**Estilo seleccionado** (idéntico al wizard):
```
border-emerald-500 bg-emerald-50 text-emerald-700 shadow-sm
```

**Estilo no seleccionado:**
```
border-gray-200 bg-white text-gray-600 hover:bg-gray-50
```

**Cambios:**
- `frontend/src/components/DurationPresetButtons.tsx` — Añadir prop `value?: number` y aplicar clases condicionales Tailwind
- `frontend/src/pages/Diets.tsx` — Pasar el valor actual como prop `value`

### 3. Reglas clínicas legibles

**Enfoque:** Crear un mapeo en el frontend de código → etiqueta. Aplicarlo en `DietPreviewPanel.tsx` al renderizar `clinical_rules_applied`.

**Mapeo:**
```ts
const CLINICAL_RULE_LABELS: Record<string, string> = {
  diabetes_carb_distribution_low_gi: "🩸 Diabetes: Distribución de carbohidratos, priorizando bajo índice glucémico",
  hypertension_sodium_moderation: "❤️ Hipertensión: Moderación de sodio, patrón tipo DASH",
  renal_protein_ceiling_applied: "🫘 Condición renal: Tope conservador de proteína",
  dyslipidemia_reduced_fat_fraction: "🩺 Dislipidemia: Límite de grasas saturadas y trans",
};
```

Si un código no está en el mapeo, se muestra el código original como fallback.

**Cambios:**
- `frontend/src/components/diet/DietPreviewPanel.tsx` — Reemplazar renderizado de códigos crudos por etiquetas del mapeo

## Archivos a Modificar

| Archivo | Cambio |
|---------|--------|
| `frontend/src/components/diet/DietActions.tsx` | Nuevo botón "Compartir PDF" (condicional) + lógica `navigator.share` |
| `frontend/src/services/api.ts` | Nueva función `getDietPdfBlob(id)` que devuelve Blob (o refactor de `downloadDietPdf`) |
| `frontend/src/pages/DietDetail.tsx` | Handler `handleSharePdf` para pasar a DietActions |
| `frontend/src/components/DurationPresetButtons.tsx` | Añadir prop `value`, aplicar clases Tailwind condicionales |
| `frontend/src/pages/Diets.tsx` | Pasar `value` a DurationPresetButtons |
| `frontend/src/components/diet/DietPreviewPanel.tsx` | Mapeo de códigos clínicos a etiquetas amigables |

## Sin Cambios en Backend

Los 3 cambios son 100% frontend. No se requiere modificar endpoints, esquemas ni base de datos.

## Verificación

1. **Compartir PDF**: Abrir DietDetail en móvil → botón "Compartir PDF" visible → tocar → se abre menú nativo con WhatsApp, Telegram, Gmail, etc.
2. **Compartir PDF en desktop**: Abrir DietDetail en desktop → solo "Descargar PDF" visible (sin botón compartir).
3. **Duración**: Abrir página de dietas → seleccionar 14 días → botón se pone verde con borde emerald-500.
4. **Reglas clínicas**: Abrir dieta de paciente con diabetes + hipertensión → se muestran etiquetas amigables con íconos, no códigos crudos.
5. **Build**: `cd frontend && npx tsc --noEmit && npm run build` sin errores.
