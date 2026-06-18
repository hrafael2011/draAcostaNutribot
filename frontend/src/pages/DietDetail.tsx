import { useCallback, useEffect, useState } from "react"
import { Link, useParams } from "react-router-dom"
import { downloadDietPdf, getDiet, getDietPdfBlob } from "../services/api"
import type { Diet } from "../types"
import DietPreviewPanel from "../components/diet/DietPreviewPanel"
import GenerationOverlay from "../components/ui/GenerationOverlay"
import { useDietGeneration } from "../hooks/useDietGeneration"
import { useToast } from "../context/ToastContext"

export default function DietDetail() {
  const { dietId } = useParams()
  const id = Number(dietId)
  const [diet, setDiet] = useState<Diet | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [editing, setEditing] = useState(false)
  const [pdfLoading, setPdfLoading] = useState(false)
  const [patientEmail, setPatientEmail] = useState<string | null>(null)
  const [emailLoading, setEmailLoading] = useState(false)
  const { editMeals } = useDietGeneration()
  const { addToast } = useToast()

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

  useEffect(() => {
    refresh().catch((e) => setError(e instanceof Error ? e.message : "Error"))
  }, [refresh])

  const handleToggleEdit = () => {
    if (!editing && diet?.status === "generated") {
      addToast("La dieta volverá a estado pendiente de aprobación después de editar", "info")
    }
    setEditing(!editing)
  }

  const handleDownloadPdf = async () => {
    if (!diet) return
    setPdfLoading(true)
    try {
      await downloadDietPdf(diet.id)
    } catch (err: unknown) {
      addToast(err instanceof Error ? err.message : "Error al descargar PDF", "error")
    } finally {
      setPdfLoading(false)
    }
  }

  const handleSharePdf = async () => {
    if (!diet) return
    setPdfLoading(true)
    try {
      const blob = await getDietPdfBlob(diet.id)
      const file = new File([blob], `dieta-${diet.id}.pdf`, { type: "application/pdf" })
      if (navigator.share && navigator.canShare({ files: [file] })) {
        await navigator.share({
          files: [file],
          title: `Dieta - ${diet.title || "Plan Nutricional"}`,
        })
      } else {
        // Fallback: download if Web Share API doesn't support files
        const url = URL.createObjectURL(blob)
        const a = document.createElement("a")
        a.href = url
        a.download = `dieta-${diet.id}.pdf`
        a.click()
        URL.revokeObjectURL(url)
      }
    } catch (err: unknown) {
      if (err instanceof DOMException && err.name === "AbortError") {
        return
      }
      addToast(err instanceof Error ? err.message : "Error al compartir PDF", "error")
    } finally {
      setPdfLoading(false)
    }
  }

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

  const handleMealSave = (dayIndex: number, slotKey: string, text: string) => {
    if (!diet) return
    editMeals.mutate(
      { dietId: diet.id, meals: [{ day_index: dayIndex, slot_key: slotKey, meal_text: text }] },
      {
        onSuccess: (updatedDiet) => {
          setDiet(updatedDiet)
          addToast("Comida actualizada. Dieta en revisión", "success")
        },
        onError: (err) => {
          addToast(err instanceof Error ? err.message : "Error al guardar", "error")
        },
      }
    )
  }

  if (!Number.isFinite(id)) {
    return <p>Invalid diet</p>
  }

  if (error && !diet) {
    return (
      <div>
        <p>
          <Link to="/diets">← Diets</Link>
        </p>
        <p style={{ color: "#b00020" }}>{error}</p>
      </div>
    )
  }

  if (!diet) {
    return <p>Loading…</p>
  }

  return (
    <div className="max-w-[900px] mx-auto space-y-6">
      {/* Breadcrumb */}
      <div>
        <Link to="/diets" className="text-sm text-slate-500 hover:text-slate-700 transition-colors">
          ← Dietas
        </Link>
        <span className="text-xs text-slate-300 mx-2">/</span>
        <span className="text-sm text-slate-700 font-medium">
          {diet.title || "Plan Nutricional"}
        </span>
      </div>

      {/* Status + Date */}
      <div className="flex items-center gap-3">
        <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${
          diet.status === "pending_approval"
            ? "bg-amber-50 text-amber-700 ring-amber-600/20"
            : "bg-emerald-50 text-emerald-700 ring-emerald-600/20"
        }`}>
          {diet.status === "pending_approval" ? "Pendiente de aprobación" : "Aprobada"}
        </span>
        <span className="text-sm text-slate-400">
          {diet.updated_at
            ? new Date(diet.updated_at).toLocaleDateString("es-VE", {
                day: "numeric", month: "long", year: "numeric",
              })
            : ""}
        </span>
      </div>

      {/* Error / Message */}
      {error && (
        <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>
      )}
      {/* Diet Preview */}
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
    </div>
  )
}
