import React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Edit, Save, Clock, Shield, Loader2, AlertCircle, CheckCircle } from "lucide-react"
import { textStyles, actionButtonStyles } from '@/lib/design-tokens'

interface ScheduleTabProps {
  successMessage: string | null
  error: string | null
  sendingHours: { start: number; end: number }
  setSendingHours: (v: { start: number; end: number } | ((prev: { start: number; end: number }) => { start: number; end: number })) => void
  respectHolidays: boolean
  setRespectHolidays: (v: boolean) => void
  respectWeekends: boolean
  setRespectWeekends: (v: boolean) => void
  maxMessagesPerDay: number
  setMaxMessagesPerDay: (v: number) => void
  isEditingSchedule: boolean
  setIsEditingSchedule: (v: boolean) => void
  savingSettings: boolean
  saveCommunicationSettings: () => Promise<void>
}

export function ScheduleTab({
  successMessage, error,
  sendingHours, setSendingHours,
  respectHolidays, setRespectHolidays,
  respectWeekends, setRespectWeekends,
  maxMessagesPerDay, setMaxMessagesPerDay,
  isEditingSchedule, setIsEditingSchedule,
  savingSettings, saveCommunicationSettings
}: ScheduleTabProps) {
  return (
    <div className="space-y-4">
      {successMessage && (
        <div className="px-2 py-1.5 rounded-md flex items-center gap-2 bg-status-success/15 border border-status-success/30 text-status-success dark:bg-status-success dark:border-status-success/30 dark:text-status-success">
          <CheckCircle className="w-3.5 h-3.5 text-status-success dark:text-status-success" />
          <span className="text-xs">{successMessage}</span>
        </div>
      )}
      {error && (
        <div className="bg-status-error/10 border border-status-error/30 text-status-error px-2 py-1.5 rounded-md flex items-center gap-2">
          <AlertCircle className="w-3.5 h-3.5" />
          <span className="text-xs">{error}</span>
        </div>
      )}
      <Card className="border-0 rounded-md backdrop-blur-sm">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className={`${textStyles.h4} flex items-center gap-2`}>
              <Clock className="w-3.5 h-3.5 lia-text-600 dark:text-lia-text-tertiary" />
              Horários de Envio (Conformidade LGPD)
            </CardTitle>
            {!isEditingSchedule ? (
              <button onClick={() => setIsEditingSchedule(true)} className={actionButtonStyles.smOutline}>
                <Edit className={actionButtonStyles.icon} />
                Editar
              </button>
            ) : (
              <div className="flex items-center gap-2">
                <button onClick={() => setIsEditingSchedule(false)} className={actionButtonStyles.smSecondary}>
                  Cancelar
                </button>
                <button
                  onClick={async () => { await saveCommunicationSettings(); setIsEditingSchedule(false) }}
                  disabled={savingSettings}
                  className={actionButtonStyles.smPrimary}
                >
                  {savingSettings ? <Loader2 className={actionButtonStyles.icon} /> : <Save className={actionButtonStyles.icon} />}
                  Salvar Alterações
                </button>
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="bg-status-warning/10 dark:bg-status-warning/20 rounded-md p-3 border border-status-warning/30 dark:border-status-warning/30">
            <div className="flex items-start gap-2">
              <Shield className="w-4 h-4 text-status-warning flex-shrink-0 mt-0.5" />
              <div>
                <p className={`${textStyles.subtitle} text-status-warning dark:text-status-warning`}>Conformidade LGPD</p>
                <p className="text-xs text-status-warning dark:text-status-warning mt-0.5">
                  De acordo com as boas práticas de LGPD, mensagens só podem ser enviadas entre 8h e 20h em dias úteis.
                  A LIA respeita automaticamente estes horários.
                </p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-micro font-medium lia-text-600 dark:text-lia-text-tertiary mb-1.5">
                Horário de Início
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="range" min={6} max={12}
                  value={sendingHours.start}
                  onChange={(e) => setSendingHours(prev => ({ ...prev, start: parseInt(e.target.value) }))}
                  disabled={!isEditingSchedule}
                  className="flex-1 disabled:opacity-50 accent-gray-700"
                />
                <div className="w-14 text-center">
                  <span className="text-xs font-semibold lia-text-950 dark:lia-text-50">{sendingHours.start}:00</span>
                </div>
              </div>
            </div>
            <div>
              <label className="block text-micro font-medium lia-text-600 dark:text-lia-text-tertiary mb-1.5">
                Horário de Fim
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="range" min={18} max={22}
                  value={sendingHours.end}
                  onChange={(e) => setSendingHours(prev => ({ ...prev, end: parseInt(e.target.value) }))}
                  disabled={!isEditingSchedule}
                  className="flex-1 disabled:opacity-50 accent-gray-700"
                />
                <div className="w-14 text-center">
                  <span className="text-xs font-semibold lia-text-950 dark:lia-text-50">{sendingHours.end}:00</span>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-gray-50 dark:bg-lia-bg-secondary/50 rounded-md p-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-micro font-medium lia-text-600">Janela de Envio</span>
              <Badge variant="outline" className="text-micro rounded-full border-lia-border-default lia-text-700 dark:border-lia-border-default dark:text-lia-text-secondary">
                {sendingHours.end - sendingHours.start} horas/dia
              </Badge>
            </div>
            <div className="relative h-6 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="absolute h-full rounded-full bg-gray-800"
                style={{left: `${((sendingHours.start - 6) / 18) * 100}%`, width: `${((sendingHours.end - sendingHours.start) / 18) * 100}%`}}
              />
              <div className="absolute inset-0 flex items-center justify-between px-2">
                <span className="text-micro lia-text-600">6:00</span>
                <span className="text-micro lia-text-600">24:00</span>
              </div>
            </div>
          </div>

          <div className="space-y-2">
            <h4 className="text-micro font-semibold lia-text-600 uppercase tracking-wider">
              Configurações Adicionais
            </h4>
            <div className="space-y-1.5">
              <label className={`flex items-center justify-between gap-3 p-2.5 bg-gray-50 dark:bg-lia-bg-secondary/50 rounded-md ${isEditingSchedule ? 'cursor-pointer' : 'cursor-default opacity-70'}`}>
                <span className="text-xs lia-text-800 dark:text-lia-text-primary">Respeitar feriados nacionais</span>
                <input type="checkbox" checked={respectHolidays} onChange={(e) => setRespectHolidays(e.target.checked)} disabled={!isEditingSchedule} className="rounded-md accent-gray-700" />
              </label>
              <label className={`flex items-center justify-between gap-3 p-2.5 bg-gray-50 dark:bg-lia-bg-secondary/50 rounded-md ${isEditingSchedule ? 'cursor-pointer' : 'cursor-default opacity-70'}`}>
                <span className="text-xs lia-text-800 dark:text-lia-text-primary">Não enviar nos finais de semana</span>
                <input type="checkbox" checked={respectWeekends} onChange={(e) => setRespectWeekends(e.target.checked)} disabled={!isEditingSchedule} className="rounded-md accent-gray-700" />
              </label>
              <label className={`flex items-center justify-between gap-3 p-2.5 bg-gray-50 dark:bg-lia-bg-secondary/50 rounded-md ${isEditingSchedule ? 'cursor-pointer' : 'cursor-default opacity-70'}`}>
                <span className="text-xs lia-text-800 dark:text-lia-text-primary" aria-live="polite" aria-atomic="true">Limite máximo de {maxMessagesPerDay} mensagens/dia por candidato</span>
                <input type="checkbox" checked={maxMessagesPerDay > 0} onChange={(e) => setMaxMessagesPerDay(e.target.checked ? 3 : 0)} disabled={!isEditingSchedule} className="rounded-md accent-gray-700" />
              </label>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
