# Sharing & Admin Fixes — Design Spec

**Date:** 2026-06-18
**Status:** Approved
**Branch:** dev

## Overview

Four fixes to improve the diet sharing UX, admin user creation clarity, form link accessibility, and patient email validation.

---

## Fix 1: Diet Sharing — Web vs Mobile Differentiation

### Current State
`DietDetail.tsx` → `DietActions.tsx` shows two buttons for approved diets:
- "📄 Descargar PDF" — always visible
- "📤 Compartir PDF" — uses `navigator.share()` on mobile, falls back to download on desktop

There is no "send by email" functionality for diets.

### Desired Behavior
- **Web (desktop):** "📧 Enviar por correo" + "📄 Descargar PDF"
- **Mobile:** "📧 Enviar por correo" + "📤 Compartir" (native share via `navigator.share()`)
- Both platforms get the email option; the second button adapts to the platform

### Implementation

#### Backend: New endpoint
**`POST /api/diets/{diet_id}/email`**

- Auth required (doctor)
- Validates diet belongs to doctor
- Fetches patient → checks `patient.email`
- If `!patient.email` → returns `400` with detail `"PATIENT_NO_EMAIL"`
- Generates PDF blob via `build_diet_export_pdf_bytes()`
- Calls `send_email_sync()` with PDF as attachment
- Returns `{ ok: true }` on success
- Returns `{ ok: false, detail: "..." }` on email send failure

#### Frontend: Platform detection + new buttons

**`DietActions.tsx`** changes:
- Add `patientEmail?: string | null` prop
- Add `onSendEmail?: () => void` callback
- Detect platform: `const isMobile = /Android|iPhone|iPad|iPod|webOS/i.test(navigator.userAgent)`
- Remove single "Compartir PDF" button
- Add conditional rendering:
  - **Web:** "📧 Enviar por correo" (primary, emerald) + "📄 Descargar PDF" (secondary, white)
  - **Mobile:** "📧 Enviar por correo" (primary, emerald) + "📤 Compartir" (secondary, outlined emerald)
- "Enviar por correo" button disabled if `!patientEmail` (with tooltip/visual cue)

**`DietDetail.tsx`** changes:
- Fetch patient data if not already available (diet has `patient_id`)
- Pass `patientEmail` and `onSendEmail` to `DietActions`
- `handleSendEmail`: calls `POST /diets/{diet_id}/email`, shows loading overlay, handles errors
- If error is `PATIENT_NO_EMAIL` → show toast: "El paciente no tiene correo registrado. Use la opción de Descargar o Compartir."

**`DietPreviewPanel.tsx`** changes:
- Pass through `patientEmail` and `onSendEmail` props to `DietActions`

### Files Changed
| File | Change |
|------|--------|
| `backend/app/api/diets.py` | Add `POST /{diet_id}/email` endpoint |
| `frontend/src/services/api.ts` | Add `sendDietByEmail(dietId)` function |
| `frontend/src/components/diet/DietActions.tsx` | Platform detection, new button layout |
| `frontend/src/components/diet/DietPreviewPanel.tsx` | Pass new props |
| `frontend/src/pages/DietDetail.tsx` | Email handler, patient email lookup |

---

## Fix 2: Patient Without Email — Warning Message

### Current State
No email sending exists. When implemented (Fix 1), clicking "Enviar por correo" without a patient email would fail silently or error out.

### Desired Behavior
If patient has no email registered:
- "Enviar por correo" button shows disabled or triggers a warning
- On click, show toast: "El paciente no tiene correo registrado. Use la opción de Descargar o Compartir."

### Implementation (included in Fix 1)
- Backend returns `400 PATIENT_NO_EMAIL` → frontend catches and shows toast
- OR frontend pre-validates: if `!patientEmail`, button click shows toast immediately without API call
- **Chosen approach:** Pre-validate in frontend (avoids unnecessary API call). Show toast via `useToast()`.

---

## Fix 3: Vercel Deployment Protection — Public Form Access

### Current State
`/intake/:token` is a public route (outside `RequireAuth` in `App.tsx`). However, when external users (patients) open the link, Vercel prompts them to authenticate.

### Root Cause
Vercel Deployment Protection ("Vercel Authentication") is enabled on the project. This protects ALL routes behind a Vercel login — only project members can access.

### Fix
**Disable Vercel Authentication** in the Vercel project dashboard:

1. Go to [Vercel Dashboard](https://vercel.com) → `dra-acosta-nutribot` project
2. Navigate to **Settings** → **Deployment Protection**
3. Set **Vercel Authentication** to **Disabled**
4. Deploy to apply

No code changes required. The frontend already correctly routes `/intake/:token` as a public route without `RequireAuth`.

---

## Fix 4: Admin Creating Doctor — No Role Dropdown

### Current State
`AdminUsers.tsx` modal always shows a role `<select>`:
- "Doctor" option always visible
- "Admin" option only for `isSuperAdmin`

Regular admins see a dropdown with only "Doctor" — redundant.

### Desired Behavior
- **Admin (role="admin"):** No dropdown at all. Title: "👨‍⚕️ Crear Doctor". Role auto-set to `"doctor"`. Replace dropdown with an informational badge: "Rol: Doctor".
- **Super Admin (role="super_admin"):** Dropdown visible with "Doctor" and "Admin" options. Title: "👥 Crear Usuario".

### Implementation

**`AdminUsers.tsx`** changes:
- Conditional rendering based on `isSuperAdmin`:
  - `!isSuperAdmin`: modal title = "Crear Doctor", hide `<select>`, show `<Badge variant="info">Rol: Doctor</Badge>`, `createRole` always `"doctor"`
  - `isSuperAdmin`: modal title = "Crear Usuario", show `<select>` with both options (current behavior)
- The `onCreate` already sends `createRole` — for admin it stays `"doctor"`

### Files Changed
| File | Change |
|------|--------|
| `frontend/src/pages/AdminUsers.tsx` | Conditional modal title and dropdown visibility |

---

## Non-Change: Link Expiration

Originally discussed but confirmed **current behavior is correct**:
- Intake links have `max_uses=1` by default
- Link expires after form submission (status → "completed")
- If patient exits without submitting, link remains active so they can retry
- Doctor can manually revoke links at any time

No changes needed.

---

## Edge Cases & Error Handling

### Fix 1 & 2 — Email Sending
- **Gmail API down:** Backend catches exception, returns `500` with detail. Frontend shows error toast.
- **PDF generation fails:** Caught in endpoint, returns `500`.
- **Patient has no email:** Frontend pre-validates, shows specific toast, no API call.
- **Concurrent requests:** Button disabled while loading (`pdfLoading` state).
- **Mobile without Share API:** `navigator.share` fallback already exists (download).

### Fix 3 — Vercel
- After disabling, verify `/intake/<token>` is accessible from incognito window.
- Existing rewrites in `vercel.json` remain correct (SPA fallback).

### Fix 4 — Admin Role
- Backend `admin.py` already validates that admin users can only create doctor accounts
- Even if an admin somehow sends `role=admin`, backend rejects it
- Super admin can still create both roles (existing behavior preserved)

---

## Testing Checklist

- [ ] Web: Diet detail shows "Enviar por correo" + "Descargar PDF"
- [ ] Mobile: Diet detail shows "Enviar por correo" + "Compartir"
- [ ] Email sent successfully to patient with valid email
- [ ] Warning toast when patient has no email
- [ ] Public intake form accessible without Vercel login (incognito)
- [ ] Admin modal: title "Crear Doctor", no dropdown, role badge visible
- [ ] Super admin modal: title "Crear Usuario", dropdown with Doctor/Admin visible
- [ ] Link expires after form submission (existing behavior preserved)
- [ ] Doctor can still revoke links manually
