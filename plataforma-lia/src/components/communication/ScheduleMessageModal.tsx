"use client"

import { useState } from "react"
import { useMutation } from "@tanstack/react-query"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Calendar, Loader2 } from "lucide-react"

export interface ScheduleMessageModalProps {
  open: boolean
  onClose: () => void
  candidateId: string
  candidateName: string
  /** Optional vacancy context */
  vacancyId?: string
}

interface SchedulePayload {
  candidate_id: string
  candidate_name: string
  vacancy_id?: string
  channel: "email" | "whatsapp"
  message: string
  subject?: string
  send_at: string
}

interface ScheduleResponse {
  scheduled_message_id: string
  send_at: string
  status: string
  channel: string
  candidate_id: string
}

async function postScheduleMessage(payload: SchedulePayload): Promise<ScheduleResponse> {
  const res = await fetch("/api/backend-proxy/messages/schedule", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err?.detail?.message ?? err?.message ?? "Erro ao agendar mensagem")
  }
  return res.json()
}

/** Formats a local datetime-local value to ISO-8601 UTC string. */
function toUtcIso(localDatetimeValue: string): string {
  // datetime-local gives "YYYY-MM-DDTHH:MM" in local time
  const dt = new Date(localDatetimeValue)
  return dt.toISOString()
}

/** Min value for datetime-local input: now + 5 minutes, truncated to seconds. */
function minDatetimeLocal(): string {
  const dt = new Date(Date.now() + 5 * 60 * 1000)
  return dt.toISOString().slice(0, 16)
}

export function ScheduleMessageModal({
  open,
  onClose,
  candidateId,
  candidateName,
  vacancyId,
}: ScheduleMessageModalProps) {
  const [channel, setChannel] = useState<"email" | "whatsapp">("email")
  const [sendAt, setSendAt] = useState("")
  const [message, setMessage] = useState("")
  const [subject, setSubject] = useState("")
  const [successId, setSuccessId] = useState<string | null>(null)

  const { mutate: schedule, isPending, error } = useMutation({
    mutationFn: () =>
      postScheduleMessage({
        candidate_id: candidateId,
        candidate_name: candidateName,
        vacancy_id: vacancyId,
        channel,
        message,
        subject: channel === "email" ? subject || undefined : undefined,
        send_at: toUtcIso(sendAt),
      }),
    onSuccess: (data) => {
      setSuccessId(data.scheduled_message_id)
    },
  })

  const handleClose = () => {
    // Reset state on close
    setChannel("email")
    setSendAt("")
    setMessage("")
    setSubject("")
    setSuccessId(null)
    onClose()
  }

  const canSubmit = !isPending && sendAt !== "" && message.trim() !== ""

  return (
    <Dialog open={open} onOpenChange={(o) => !o && handleClose()}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Agendar Mensagem</DialogTitle>
        </DialogHeader>

        {successId ? (
          <div className="py-6 text-center space-y-3">
            <p className="text-sm font-medium text-green-700 dark:text-green-400">
              Mensagem agendada com sucesso!
            </p>
            <p className="text-xs text-muted-foreground">
              ID: {successId}
            </p>
            <Button variant="outline" onClick={handleClose} className="mt-2">
              Fechar
            </Button>
          </div>
        ) : (
          <>
            <div className="space-y-4 py-2">
              {/* Recipient */}
              <div>
                <Label className="text-xs text-muted-foreground">Para</Label>
                <p className="text-sm font-medium mt-0.5">{candidateName}</p>
              </div>

              {/* Channel */}
              <div className="space-y-1">
                <Label htmlFor="sched-channel">Canal</Label>
                <Select
                  value={channel}
                  onValueChange={(v) => setChannel(v as "email" | "whatsapp")}
                >
                  <SelectTrigger id="sched-channel">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="email">E-mail</SelectItem>
                    <SelectItem value="whatsapp">WhatsApp</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Subject (email only) */}
              {channel === "email" && (
                <div className="space-y-1">
                  <Label htmlFor="sched-subject">Assunto (opcional)</Label>
                  <Input
                    id="sched-subject"
                    value={subject}
                    onChange={(e) => setSubject(e.target.value)}
                    placeholder="Assunto do e-mail"
                  />
                </div>
              )}

              {/* Send at */}
              <div className="space-y-1">
                <Label htmlFor="sched-send-at">Enviar em</Label>
                <Input
                  id="sched-send-at"
                  type="datetime-local"
                  value={sendAt}
                  min={minDatetimeLocal()}
                  onChange={(e) => setSendAt(e.target.value)}
                />
              </div>

              {/* Message */}
              <div className="space-y-1">
                <Label htmlFor="sched-message">Mensagem</Label>
                <textarea
                  id="sched-message"
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm min-h-[90px] resize-none focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Digite a mensagem que será enviada ao candidato..."
                />
              </div>

              {/* Error */}
              {error && (
                <p className="text-xs text-destructive" role="alert">
                  {error.message}
                </p>
              )}
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={handleClose} disabled={isPending}>
                Cancelar
              </Button>
              <Button onClick={() => schedule()} disabled={!canSubmit}>
                {isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Agendando...
                  </>
                ) : (
                  <>
                    <Calendar className="h-4 w-4 mr-2" />
                    Agendar
                  </>
                )}
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}

// ── Global store-driven wrapper (GAP-07-007) ──────────────────────────────────
// Self-contained: reads open/candidateId/candidateName from useScheduleMessageStore.
// Mount once in a layout or page-level modals host; no prop drilling required.
import { useScheduleMessageStore } from "@/stores/schedule-message-store"

export function ScheduleMessageModalGlobal() {
  const { open, candidateId, candidateName, vacancyId, closeScheduleModal } =
    useScheduleMessageStore()

  if (!candidateId) return null

  return (
    <ScheduleMessageModal
      open={open}
      onClose={closeScheduleModal}
      candidateId={candidateId}
      candidateName={candidateName ?? ""}
      vacancyId={vacancyId ?? undefined}
    />
  )
}
