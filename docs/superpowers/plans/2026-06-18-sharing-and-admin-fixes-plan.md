# Sharing & Admin Fixes — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add diet email sharing, differentiate web/mobile share buttons, fix admin user creation UX, and resolve Vercel public form access.

**Architecture:** New backend endpoint `POST /diets/{id}/email` generates PDF and sends via Gmail API (existing `send_email_sync` extended with attachment support). Frontend `DietActions` detects platform to show web (email + download) or mobile (email + share) buttons. `AdminUsers` conditionally hides role dropdown for non-super-admin users. Vercel Deployment Protection disabled via dashboard.

**Tech Stack:** Python/FastAPI (backend), React/TypeScript (frontend), Gmail API (email), ReportLab (PDF)

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `backend/app/services/email_service.py` | Modify | Add `send_email_with_attachment()` |
| `backend/app/api/diets.py` | Modify | Add `POST /{diet_id}/email` endpoint |
| `frontend/src/services/api.ts` | Modify | Add `sendDietByEmail()` |
| `frontend/src/components/diet/DietActions.tsx` | Modify | Platform detection, new button layout |
| `frontend/src/components/diet/DietPreviewPanel.tsx` | Modify | Pass new props through |
| `frontend/src/pages/DietDetail.tsx` | Modify | Fetch patient, email handler, toasts |
| `frontend/src/pages/AdminUsers.tsx` | Modify | Conditional modal for admin vs super_admin |

---

### Task 1: Backend — Add `send_email_with_attachment` to email_service.py

**Files:**
- Modify: `backend/app/services/email_service.py`

- [ ] **Step 1: Add `send_email_with_attachment` function**

Add this function after the existing `send_email_sync` function (after line 58):

```python
def send_email_with_attachment(
    to_email: str,
    subject: str,
    html_body: str,
    attachment_bytes: bytes,
    attachment_filename: str,
    attachment_mimetype: str = "application/pdf",
) -> bool:
    """Send email with a file attachment via Gmail API."""
    import mimetypes
    from email.mime.application import MIMEApplication
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    try:
        access_token = _get_access_token()

        msg = MIMEMultipart()
        msg["To"] = to_email
        msg["From"] = settings.GMAIL_FROM_EMAIL or "Dra. Acosta"
        msg["Subject"] = subject

        # Attach HTML body
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        # Attach file
        part = MIMEApplication(attachment_bytes, _subtype="pdf")
        part.add_header(
            "Content-Disposition",
            "attachment",
            filename=attachment_filename,
        )
        msg.attach(part)

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

        url = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        body = {"raw": raw}

        with httpx.Client(timeout=30) as client:
            r = client.post(url, headers=headers, json=body)
            r.raise_for_status()
            return True
    except Exception as e:
        logger.exception("Gmail API attachment error: %s", e)
        return False
```

- [ ] **Step 2: Verify the import at the top of email_service.py has `base64`**

The file already imports `base64` at line 1. No change needed.

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/email_service.py
git commit -m "feat: add send_email_with_attachment for diet PDF delivery

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 2: Backend — Add `POST /{diet_id}/email` endpoint

**Files:**
- Modify: `backend/app/api/diets.py`

- [ ] **Step 1: Add the import for email service**

Add this import at the top of `diets.py` (after the existing imports, around line 28):

```python
from app.services.email_service import send_email_with_attachment
```

- [ ] **Step 2: Add the endpoint**

Add this endpoint after the `get_diet_pdf` route (after line 343):

```python
@router.post("/{diet_id}/email")
async def email_diet_pdf(
    diet_id: int,
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor),
):
    """Send the diet PDF to the patient's registered email."""
    diet = await db.get(Diet, diet_id)
    if diet is None or diet.doctor_id != doctor.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diet not found",
        )

    patient = await db.get(Patient, diet.patient_id)
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PATIENT_NOT_FOUND",
        )
    if not patient.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PATIENT_NO_EMAIL",
        )

    # Fetch profile and latest metrics for PDF generation
    profile = None
    metrics = None
    if patient.doctor_id == doctor.id:
        pr = await db.execute(
            select(PatientProfile).where(PatientProfile.patient_id == patient.id)
        )
        profile = pr.scalar_one_or_none()
        mr = await db.execute(
            select(PatientMetrics)
            .where(PatientMetrics.patient_id == patient.id)
            .order_by(PatientMetrics.recorded_at.desc())
            .limit(1)
        )
        metrics = mr.scalar_one_or_none()

    # Generate PDF
    pdf_bytes = build_diet_export_pdf_bytes(
        diet,
        patient=patient,
        profile=profile,
        metrics=metrics,
        doctor=doctor,
    )

    # Build email
    patient_name = (patient.first_name or "Paciente").strip()
    subject = f"Tu Plan Nutricional - Dra. Acosta"
    html_body = f"""<html><body style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:20px">
<h2 style="color:#1e3a5f">Hola {patient_name},</h2>
<p>La <strong>Dra. Acosta</strong> te comparte tu plan nutricional personalizado.</p>
<p>Adjunto encontrarás el PDF con tu dieta y recomendaciones.</p>
<p style="color:#666;font-size:13px;margin-top:30px;border-top:1px solid #eee;padding-top:15px">
Este correo fue enviado por el consultorio de la Dra. Acosta.<br/>
Si tienes dudas, responde a este correo o contacta por WhatsApp.
</p></body></html>"""

    success = send_email_with_attachment(
        to_email=patient.email,
        subject=subject,
        html_body=html_body,
        attachment_bytes=pdf_bytes,
        attachment_filename=f"Plan_Nutricional_{patient_name}.pdf",
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="EMAIL_SEND_FAILED",
        )

    return {"ok": True, "sent_to": patient.email}
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/diets.py
git commit -m "feat: add POST /diets/{id}/email endpoint for diet PDF delivery

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 3: Frontend — Add `sendDietByEmail` to api.ts

**Files:**
- Modify: `frontend/src/services/api.ts`

- [ ] **Step 1: Add `sendDietByEmail` function**

Add this function after the `downloadDietPdf` function (after line 456):

```typescript
export async function sendDietByEmail(dietId: number): Promise<{ ok: boolean; sent_to: string }> {
  const res = await authFetch(`/diets/${dietId}/email`, {
    method: "POST",
  })
  if (!res.ok) {
    const detail = await readApiError(res)
    if (detail === "PATIENT_NO_EMAIL") {
      throw new Error("PATIENT_NO_EMAIL")
    }
    throw new Error(detail || "Error al enviar por correo")
  }
  return res.json() as Promise<{ ok: boolean; sent_to: string }>
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/services/api.ts
git commit -m "feat: add sendDietByEmail API function for diet email delivery

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 4: Frontend — Update DietActions with platform detection and new buttons

**Files:**
- Modify: `frontend/src/components/diet/DietActions.tsx`

- [ ] **Step 1: Add new props and platform detection**

Replace the `Props` type (lines 6-17) with:

```typescript
type Props = {
  dietId: number
  status: string
  onApprove: () => void
  onDiscard: () => void
  onQuickAdjust: (key: string, label: string) => void
  onDownloadPdf: () => void
  onSharePdf?: () => void
  onSendEmail?: () => void
  onToggleEdit?: () => void
  editing?: boolean
  loading: boolean
  emailLoading?: boolean
  patientEmail?: string | null
}
```

- [ ] **Step 2: Destructure new props**

Replace the destructuring in the component function (lines 19-30) with:

```typescript
export default function DietActions({
  dietId,
  status,
  onApprove,
  onDiscard,
  onQuickAdjust,
  onDownloadPdf,
  onSharePdf,
  onSendEmail,
  onToggleEdit,
  editing,
  loading,
  emailLoading = false,
  patientEmail,
}: Props) {
```

- [ ] **Step 3: Add platform detection and email handler**

Add after `const [showQuickAdjust, setShowQuickAdjust] = useState(false)` (after line 31):

```typescript
  const isMobile = /Android|iPhone|iPad|iPod|webOS/i.test(navigator.userAgent)

  const handleSendEmail = () => {
    if (!patientEmail) {
      return  // parent handles the toast
    }
    onSendEmail?.()
  }
```

- [ ] **Step 4: Replace the "generated" status buttons section (lines 61-86)**

Replace lines 61-86 with:

```typescript
  if (status === "generated") {
    const noEmail = !patientEmail
    return (
      <div className="space-y-2">
        <Button
          onClick={handleSendEmail}
          disabled={emailLoading || noEmail}
          className="w-full"
          title={noEmail ? "El paciente no tiene correo registrado" : undefined}
        >
          {emailLoading ? "⏳ Enviando..." : "📧 Enviar por correo"}
        </Button>
        {noEmail && (
          <p className="text-xs text-amber-600 text-center">
            ⚠️ El paciente no tiene correo registrado
          </p>
        )}
        {isMobile ? (
          onSharePdf && (
            <Button
              variant="secondary"
              onClick={onSharePdf}
              className="w-full border-emerald-500 text-emerald-700 hover:bg-emerald-50"
            >
              <span className="flex items-center justify-center gap-1.5">
                <Share size={14} />
                Compartir
              </span>
            </Button>
          )
        ) : (
          <Button onClick={onDownloadPdf} className="w-full">
            📄 Descargar PDF
          </Button>
        )}
        <Button variant="ghost" onClick={onToggleEdit} className="w-full text-sm">
          <span className="flex items-center justify-center gap-1.5">
            <PencilSimple size={14} />
            {editing ? "Dejar de editar" : "Editar comidas"}
          </span>
        </Button>
      </div>
    )
  }
```

- [ ] **Step 5: Add `Share` icon import check**

The `Share` icon is already imported at line 1:
```typescript
import { PencilSimple, Share } from "@phosphor-icons/react"
```
No change needed.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/diet/DietActions.tsx
git commit -m "feat: add platform detection and email button to DietActions

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 5: Frontend — Update DietPreviewPanel to pass new props

**Files:**
- Modify: `frontend/src/components/diet/DietPreviewPanel.tsx`

- [ ] **Step 1: Add new props to the Props type**

Replace the Props type (lines 18-27) with:

```typescript
type Props = {
  diet: Diet
  editable?: boolean
  onMealSave?: (dayIndex: number, slotKey: string, text: string) => void
  onToggleEdit?: () => void
  onApprove?: () => void
  onDiscard?: () => void
  onDownloadPdf?: () => void
  onSharePdf?: () => void
  onSendEmail?: () => void
  emailLoading?: boolean
  patientEmail?: string | null
}
```

- [ ] **Step 2: Destructure new props and pass to DietActions**

Replace the function signature destructuring (line 29) with:

```typescript
export default function DietPreviewPanel({ diet, editable, onMealSave, onToggleEdit, onApprove, onDiscard, onDownloadPdf, onSharePdf, onSendEmail, emailLoading, patientEmail }: Props) {
```

- [ ] **Step 3: Pass new props to DietActions**

Replace the `<DietActions` block (lines 80-97) with:

```typescript
      <DietActions
        dietId={diet.id}
        status={diet.status}
        onApprove={onApprove || (() => approve.mutate(diet.id))}
        onDiscard={onDiscard || (() => discard.mutate(diet.id))}
        onQuickAdjust={(key, label) => quickAdjust.mutate({ dietId: diet.id, adjustment: label })}
        onDownloadPdf={() => {
          if (onDownloadPdf) {
            onDownloadPdf()
          } else {
            import("../../services/api").then(({ downloadDietPdf }) => downloadDietPdf(diet.id))
          }
        }}
        onSharePdf={onSharePdf}
        onSendEmail={onSendEmail}
        emailLoading={emailLoading}
        patientEmail={patientEmail}
        onToggleEdit={onToggleEdit}
        editing={editable}
        loading={loading}
      />
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/diet/DietPreviewPanel.tsx
git commit -m "feat: pass email props through DietPreviewPanel to DietActions

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 6: Frontend — Update DietDetail to fetch patient and handle email

**Files:**
- Modify: `frontend/src/pages/DietDetail.tsx`

- [ ] **Step 1: Add patient state and email handler**

After the `const [pdfLoading, setPdfLoading] = useState(false)` line (line 16), add:

```typescript
  const [patientEmail, setPatientEmail] = useState<string | null>(null)
  const [emailLoading, setEmailLoading] = useState(false)
```

- [ ] **Step 2: Add patient fetch to the `refresh` callback**

Replace the `refresh` callback (lines 20-25) with:

```typescript
  const refresh = useCallback(async () => {
    if (!Number.isFinite(id)) return
    setError(null)
    const d = await getDiet(id)
    setDiet(d)
    if (d.patient_id) {
      try {
        const { getPatient } = await import("../services/api")
        const p = await getPatient(d.patient_id)
        setPatientEmail(p.email || null)
      } catch {
        setPatientEmail(null)
      }
    }
  }, [id])
```

- [ ] **Step 3: Add `handleSendEmail` function**

Add after the `handleSharePdf` function (after line 78):

```typescript
  const handleSendEmail = async () => {
    if (!diet) return
    if (!patientEmail) {
      addToast(
        "El paciente no tiene correo registrado. Use la opción de Descargar o Compartir.",
        "info",
      )
      return
    }
    setEmailLoading(true)
    try {
      const { sendDietByEmail } = await import("../services/api")
      const result = await sendDietByEmail(diet.id)
      addToast(`Dieta enviada a ${result.sent_to}`, "success")
    } catch (err: unknown) {
      if (err instanceof Error && err.message === "PATIENT_NO_EMAIL") {
        addToast(
          "El paciente no tiene correo registrado. Use la opción de Descargar o Compartir.",
          "info",
        )
      } else {
        addToast(
          err instanceof Error ? err.message : "Error al enviar por correo",
          "error",
        )
      }
    } finally {
      setEmailLoading(false)
    }
  }
```

- [ ] **Step 4: Pass new props to DietPreviewPanel**

Replace the `<DietPreviewPanel` block (lines 151-176) with:

```typescript
      <DietPreviewPanel
        diet={diet}
        editable={editing}
        onMealSave={handleMealSave}
        onToggleEdit={handleToggleEdit}
        onApprove={() => {
          import("../services/api").then(({ approveDiet }) =>
            approveDiet(diet.id).then((d) => {
              setDiet(d)
              setEditing(false)
              addToast("Dieta aprobada", "success")
            })
          )
        }}
        onDiscard={() => {
          import("../services/api").then(({ discardDiet }) =>
            discardDiet(diet.id).then((d) => {
              setDiet(d)
              setEditing(false)
              addToast("Dieta descartada", "success")
            })
          )
        }}
        onDownloadPdf={handleDownloadPdf}
        onSharePdf={handleSharePdf}
        onSendEmail={handleSendEmail}
        emailLoading={emailLoading}
        patientEmail={patientEmail}
      />
```

- [ ] **Step 5: Update the generation overlay to also cover email loading**

Replace the `open` prop on `GenerationOverlay` (line 178) with:

```typescript
        open={pdfLoading || emailLoading}
```

And update the label to be dynamic:

```typescript
        label={emailLoading ? "Enviando por correo..." : "Descargando PDF..."}
        doneLabel={emailLoading ? "¡Correo enviado!" : "¡PDF descargado!"}
```

The full GenerationOverlay replacement (lines 177-188):

```typescript
      <GenerationOverlay
        open={pdfLoading || emailLoading}
        patientName=""
        label={emailLoading ? "Enviando por correo..." : "Descargando PDF..."}
        doneLabel={emailLoading ? "¡Correo enviado!" : "¡PDF descargado!"}
        steps={[
          { pct: 30, msg: "Preparando documento..." },
          { pct: 60, msg: "Renderizando plan nutricional..." },
          { pct: 90, msg: emailLoading ? "Enviando correo..." : "Finalizando..." },
        ]}
        onComplete={() => {}}
      />
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/DietDetail.tsx
git commit -m "feat: add patient email fetch and email sending to DietDetail

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 7: Frontend — Update AdminUsers modal for admin vs super_admin

**Files:**
- Modify: `frontend/src/pages/AdminUsers.tsx`

- [ ] **Step 1: Replace the role dropdown section in the create modal (lines 250-258)**

Replace these lines:

```typescript
              <div className="mb-3">
                <label className="mb-1 block text-sm font-medium text-gray-700">Rol</label>
                <select value={createRole} onChange={(e) => setCreateRole(e.target.value as Role)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm
                    focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500">
                  <option value="doctor">Doctor</option>
                  {isSuperAdmin && <option value="admin">Admin</option>}
                </select>
              </div>
```

With:

```typescript
              {isSuperAdmin ? (
                <div className="mb-3">
                  <label className="mb-1 block text-sm font-medium text-gray-700">Rol</label>
                  <select value={createRole} onChange={(e) => setCreateRole(e.target.value as Role)}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm
                      focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500">
                    <option value="doctor">Doctor</option>
                    <option value="admin">Admin</option>
                  </select>
                </div>
              ) : (
                <div className="mb-3 rounded-lg bg-emerald-50 border border-emerald-200 px-4 py-3 flex items-center gap-3">
                  <span className="text-lg">👨‍⚕️</span>
                  <div>
                    <p className="text-sm font-medium text-emerald-800">Rol: Doctor</p>
                    <p className="text-xs text-emerald-600">Los administradores crean doctores</p>
                  </div>
                </div>
              )}
```

- [ ] **Step 2: Replace the modal title (line 232)**

Replace:

```typescript
              <h2 className="text-lg font-bold text-gray-800">Crear Usuario</h2>
```

With:

```typescript
              <h2 className="text-lg font-bold text-gray-800">
                {isSuperAdmin ? "Crear Usuario" : "Crear Doctor"}
              </h2>
```

- [ ] **Step 3: Replace the submit button text (line 269)**

Replace:

```typescript
                  {creating ? "Creando..." : "Crear Usuario"}
```

With:

```typescript
                  {creating ? "Creando..." : isSuperAdmin ? "Crear Usuario" : "Crear Doctor"}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/AdminUsers.tsx
git commit -m "feat: hide role dropdown for admin users, show 'Crear Doctor' modal

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 8: Vercel — Disable Deployment Protection

**No code changes.** This is a Vercel dashboard configuration step.

- [ ] **Step 1: Open Vercel Dashboard**

Navigate to: https://vercel.com → Select project `dra-acosta-nutribot`

- [ ] **Step 2: Disable Vercel Authentication**

1. Go to **Settings** → **Deployment Protection**
2. Set **Vercel Authentication** to **Disabled**
3. Click **Save**

- [ ] **Step 3: Verify public access**

Open an incognito/private browser window and navigate to an existing intake link:
```
https://<your-domain>/intake/<any-valid-token>
```
The form should load without a Vercel login prompt. If the token is invalid you'll see "Enlace no disponible" — that's the app's own validation, which is correct.

- [ ] **Step 4: No commit needed (configuration change only)**

---

## Verification Checklist

After all tasks are complete, verify:

- [ ] **Diet email — happy path:** Open a diet for a patient with email. Click "Enviar por correo". Patient receives PDF.
- [ ] **Diet email — no email:** Open a diet for a patient without email. Verify the amber warning "El paciente no tiene correo registrado" appears below the button. Clicking shows a toast.
- [ ] **Web buttons:** On desktop, diet detail shows "📧 Enviar por correo" + "📄 Descargar PDF".
- [ ] **Mobile buttons:** On mobile (or Chrome DevTools mobile emulation), diet detail shows "📧 Enviar por correo" + "📤 Compartir".
- [ ] **Admin modal:** Login as admin (not super_admin). Click "Nuevo Usuario". Modal title is "Crear Doctor". No role dropdown — shows "Rol: Doctor" badge.
- [ ] **Super admin modal:** Login as super_admin. Click "Nuevo Usuario". Modal title is "Crear Usuario". Role dropdown visible with Doctor and Admin options.
- [ ] **Public intake:** Open an intake link in incognito window. Form loads without Vercel login prompt.
- [ ] **Link expiration:** Submit an intake form. Re-open the same link — shows "Link already used" / "Enlace no disponible".
