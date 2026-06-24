import { useLiaModalTracking } from '@/lib/use-lia-modal-tracking'
import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { AlertCircle, CheckCircle2, Clock, FileText, RefreshCw } from "lucide-react"

interface FieldValue {
  field_id: string
  field_name?: string
  value?: string
  file_url?: string
  file_name?: string
  verified?: boolean
  verified_at?: string
}

interface DataRequestDetails {
  id: string
  status: string
  is_blocking: boolean
  trigger_stage?: string
  fields_requested: FieldValue[]
  fields_completed: FieldValue[]
  completion_percentage: number
  expires_at?: string
  created_at: string
  completed_at?: string
  sent_via_email: boolean
  sent_via_whatsapp: boolean
  reminder_count: number
}

interface DataRequestDetailsModalProps {
  requestId: string | null
  open: boolean
  onClose: () => void
}

const STATUS_CONFIG = {
  pending: { label: "Pendente", variant: "secondary" as const, icon: Clock },
  partial: { label: "Parcial", variant: "outline" as const, icon: RefreshCw },
  partially_filled: { label: "Parcial", variant: "outline" as const, icon: RefreshCw },
  completed: { label: "Completo", variant: "default" as const, icon: CheckCircle2 },
  expired: { label: "Expirado", variant: "destructive" as const, icon: AlertCircle },
  cancelled: { label: "Cancelado", variant: "destructive" as const, icon: AlertCircle },
}

function FieldRow({ field, isCompleted }: { field: FieldValue; isCompleted: boolean }) {
  const label = field.field_name || field.field_id

  return (
    <div className="flex items-start justify-between py-2 border-b border-border/50 last:border-0">
      <div className="flex items-center gap-2 min-w-0 flex-1">
        {isCompleted ? (
          <CheckCircle2 className="h-3.5 w-3.5 text-green-500 shrink-0" />
        ) : (
          <Clock className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
        )}
        <span className="text-sm text-muted-foreground truncate">{label}</span>
      </div>
      {isCompleted && (
        <div className="ml-3 text-right shrink-0 max-w-[55%]">
          {field.file_url ? (
            <a
              href={field.file_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-xs text-blue-600 hover:underline"
            >
              <FileText className="h-3 w-3" />
              {field.file_name || "Ver arquivo"}
            </a>
          ) : (
            <span className="text-sm font-medium truncate block max-w-[200px]">
              {field.value ?? "—"}
            </span>
          )}
        </div>
      )}
    </div>
  )
}

export function DataRequestDetailsModal({
  requestId,
  open,
  onClose,
}: DataRequestDetailsModalProps) {
  // P0-2 (2026-06-18): LIA screen awareness
  useLiaModalTracking('data-request-details', open)

  const [details, setDetails] = useState<DataRequestDetails | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function fetchDetails(id: string) {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`/api/backend-proxy/data-requests/${id}`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setDetails(data)
    } catch (e) {
      setError("Não foi possível carregar os detalhes.")
    } finally {
      setLoading(false)
    }
  }

  // Fetch when opening
  const handleOpenChange = (isOpen: boolean) => {
    if (isOpen && requestId && !loading) {
      setDetails(null)
      fetchDetails(requestId)
    }
    if (!isOpen) onClose()
  }

  const statusCfg = details
    ? STATUS_CONFIG[details.status as keyof typeof STATUS_CONFIG] ?? STATUS_CONFIG.pending
    : null
  const StatusIcon = statusCfg?.icon ?? Clock

  const completedIds = new Set((details?.fields_completed ?? []).map((f) => f.field_id))
  const pendingFields = (details?.fields_requested ?? []).filter((f) => !completedIds.has(f.field_id))

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileText className="h-4 w-4" />
            Coleta de Dados
          </DialogTitle>
        </DialogHeader>

        {loading && (
          <div className="py-8 flex items-center justify-center gap-2 text-muted-foreground text-sm">
            <RefreshCw className="h-4 w-4 animate-spin" />
            Carregando...
          </div>
        )}

        {error && (
          <div className="py-6 text-center text-sm text-destructive">{error}</div>
        )}

        {details && !loading && (
          <div className="space-y-4">
            {/* Header row */}
            <div className="flex items-center justify-between">
              <Badge variant={statusCfg?.variant ?? "secondary"} className="flex items-center gap-1">
                <StatusIcon className="h-3 w-3" />
                {statusCfg?.label ?? details.status}
              </Badge>
              <div className="text-xs text-muted-foreground">
                {details.completion_percentage}% completo
              </div>
            </div>

            {/* Progress bar */}
            <div className="h-1.5 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-green-500 rounded-full transition-all"
                style={{ width: `${details.completion_percentage}%` }}
              />
            </div>

            {/* Blocking warning */}
            {details.is_blocking && (details.status === "pending" || details.status === "partially_filled") && (
              <div className="flex items-start gap-2 rounded-md bg-amber-50 border border-amber-200 p-2.5 text-xs text-amber-800">
                <AlertCircle className="h-3.5 w-3.5 shrink-0 mt-0.5" />
                <span>Este preenchimento é obrigatório para avançar para a próxima etapa.</span>
              </div>
            )}

            {/* Completed fields */}
            {details.fields_completed.length > 0 && (
              <div>
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">
                  Campos Preenchidos ({details.fields_completed.length})
                </p>
                <div className="rounded-md border border-border/60 px-3">
                  {details.fields_completed.map((f) => (
                    <FieldRow key={f.field_id} field={f} isCompleted />
                  ))}
                </div>
              </div>
            )}

            {/* Pending fields */}
            {pendingFields.length > 0 && (
              <div>
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">
                  Aguardando ({pendingFields.length})
                </p>
                <div className="rounded-md border border-border/60 px-3">
                  {pendingFields.map((f) => (
                    <FieldRow key={f.field_id} field={f} isCompleted={false} />
                  ))}
                </div>
              </div>
            )}

            {/* Meta */}
            <div className="text-xs text-muted-foreground grid grid-cols-2 gap-x-4 gap-y-1 pt-1">
              {details.trigger_stage && (
                <>
                  <span>Etapa:</span>
                  <span className="font-medium">{details.trigger_stage}</span>
                </>
              )}
              {details.expires_at && (
                <>
                  <span>Expira em:</span>
                  <span className="font-medium">
                    {new Date(details.expires_at).toLocaleDateString("pt-BR")}
                  </span>
                </>
              )}
              <span>Enviado por:</span>
              <span className="font-medium">
                {[details.sent_via_email && "e-mail", details.sent_via_whatsapp && "WhatsApp"]
                  .filter(Boolean)
                  .join(", ") || "—"}
              </span>
            </div>

            <div className="flex justify-end">
              <Button variant="outline" size="sm" onClick={onClose}>
                Fechar
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
