import React from"react"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Edit, Save, PenTool, Loader2, AlertCircle, CheckCircle } from"lucide-react"
import { textStyles, actionButtonStyles } from '@/lib/design-tokens'

interface SignatureTabProps {
  successMessage: string | null
  error: string | null
  signature: string
  setSignature: (v: string) => void
  isEditingSignature: boolean
  setIsEditingSignature: (v: boolean) => void
  savingSettings: boolean
  saveCommunicationSettings: () => Promise<void>
}

export function SignatureTab({
  successMessage, error,
  signature, setSignature,
  isEditingSignature, setIsEditingSignature,
  savingSettings, saveCommunicationSettings
}: SignatureTabProps) {
  return (
    <div className="space-y-4">
      {successMessage && (
        <div className="px-2 py-1.5 rounded-xl flex items-center gap-2 bg-status-success/15 border border-status-success/30 text-status-success dark:bg-status-success dark:border-status-success/30 dark:text-status-success">
          <CheckCircle className="w-3.5 h-3.5 text-status-success dark:text-status-success" />
          <span className="text-xs">{successMessage}</span>
        </div>
      )}
      {error && (
        <div className="bg-status-error/10 border border-status-error/30 text-status-error px-2 py-1.5 rounded-xl flex items-center gap-2">
          <AlertCircle className="w-3.5 h-3.5" />
          <span className="text-xs">{error}</span>
        </div>
      )}
      <Card className="border-0 rounded-md backdrop-blur-sm">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className={`${textStyles.h4} flex items-center gap-2`}>
              <PenTool className="w-3.5 h-3.5 text-lia-text-secondary" />
              Assinatura Padrão de Email
            </CardTitle>
            {!isEditingSignature ? (
              <button onClick={() => setIsEditingSignature(true)} className={actionButtonStyles.smOutline}>
                <Edit className={actionButtonStyles.icon} />
                Editar
              </button>
            ) : (
              <div className="flex items-center gap-2">
                <button onClick={() => setIsEditingSignature(false)} className={actionButtonStyles.smSecondary}>
                  Cancelar
                </button>
                <button
                  onClick={async () => { await saveCommunicationSettings(); setIsEditingSignature(false) }}
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
        <CardContent className="space-y-3">
          <div>
            <label className="block text-micro font-medium text-lia-text-secondary mb-1">
              Template de Assinatura
            </label>
            <textarea
              value={signature}
              onChange={(e) => setSignature(e.target.value)}
              rows={5}
              disabled={!isEditingSignature}
              className="w-full px-2 py-1.5 text-xs border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary text-lia-text-primary focus:ring-2 focus:outline-none font-mono disabled:bg-lia-bg-secondary disabled:text-lia-text-secondary"
            />
          </div>
          <div>
            <label className="block text-micro font-medium text-lia-text-secondary mb-1">
              Variáveis Disponíveis
            </label>
            <div className="flex flex-wrap gap-1">
              {['recrutador_nome', 'cargo', 'empresa_nome', 'email', 'telefone', 'website', 'linkedin'].map((v) => (
                <Chip key={v} variant="neutral" className="text-micro font-mono cursor-pointer hover:bg-lia-bg-tertiary rounded-full border-lia-border-default text-lia-text-primary dark:border-lia-border-default">
                  {`{{${v}}}`}
                </Chip>
              ))}
            </div>
          </div>
          <div className="bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 rounded-xl p-3">
            <label className="block text-micro font-medium text-lia-text-secondary mb-1.5">
              Prévia
            </label>
            <div className="text-xs text-lia-text-primary whitespace-pre-wrap">
              {signature
                .replace('{{recrutador_nome}}', 'Ana Silva')
                .replace('{{cargo}}', 'Recrutadora Sênior')
                .replace('{{empresa_nome}}', 'WedoTalent')
                .replace('{{email}}', 'ana.silva@wedotalent.com')
                .replace('{{telefone}}', '+55 11 99999-0000')
                .replace('{{website}}', 'www.wedotalent.com')}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
