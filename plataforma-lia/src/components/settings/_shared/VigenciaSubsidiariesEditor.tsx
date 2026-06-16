"use client"

/**
 * VigenciaSubsidiariesEditor — editor canonico de vigencia + filiais (CNPJ).
 *
 * Compartilhado por verbas variaveis e (futuro) beneficios. subsidiaries =
 * [{ name, cnpj }]. Vazio = aplica a todas as entidades da empresa. Labels de
 * vigencia configuraveis (fromLabel/untilLabel) por contexto.
 */
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { X, Plus } from "lucide-react"

export interface Subsidiary {
  name: string
  cnpj?: string | null
}

export interface VigenciaValue {
  valid_from?: string | null
  valid_until?: string | null
  subsidiaries?: Subsidiary[]
}

export interface VigenciaSubsidiariesEditorProps {
  value: VigenciaValue
  onChange: (patch: Partial<VigenciaValue>) => void
  fromLabel?: string
  untilLabel?: string
}

const labelCls = "text-xs mb-1 block text-lia-text-secondary"

export function VigenciaSubsidiariesEditor({
  value,
  onChange,
  fromLabel = "Início da vigência",
  untilLabel = "Fim da vigência",
}: VigenciaSubsidiariesEditorProps) {
  const subs = value.subsidiaries || []

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-3">
        <div>
          <Label className={labelCls}>{fromLabel}</Label>
          <Input
            type="date"
            value={value.valid_from || ""}
            onChange={(e) => onChange({ valid_from: e.target.value || null })}
            className="mt-1 rounded-md text-sm"
          />
        </div>
        <div>
          <Label className={labelCls}>{untilLabel}</Label>
          <Input
            type="date"
            value={value.valid_until || ""}
            onChange={(e) => onChange({ valid_until: e.target.value || null })}
            className="mt-1 rounded-md text-sm"
          />
        </div>
      </div>

      <div>
        <Label className={labelCls}>Filiais aplicáveis (CNPJ)</Label>
        <p className="text-xs text-lia-text-tertiary mb-2">
          Deixe em branco para aplicar a todas as entidades da empresa
        </p>
        <div className="space-y-2">
          {subs.map((sub, idx) => (
            <div key={idx} className="flex gap-2 items-center">
              <Input
                value={sub.name}
                onChange={(e) => {
                  const next = [...subs]
                  next[idx] = { ...next[idx], name: e.target.value }
                  onChange({ subsidiaries: next })
                }}
                placeholder="Nome da filial"
                className="flex-1 rounded-md text-sm"
              />
              <Input
                value={sub.cnpj || ""}
                onChange={(e) => {
                  const next = [...subs]
                  next[idx] = { ...next[idx], cnpj: e.target.value || null }
                  onChange({ subsidiaries: next })
                }}
                placeholder="CNPJ"
                maxLength={18}
                className="w-40 rounded-md text-sm"
              />
              <button
                type="button"
                onClick={() => onChange({ subsidiaries: subs.filter((_, i) => i !== idx) })}
                className="text-lia-text-tertiary hover:text-status-error transition-colors"
                aria-label="Remover filial"
              >
                <X size={16} />
              </button>
            </div>
          ))}
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => onChange({ subsidiaries: [...subs, { name: "", cnpj: null }] })}
          >
            <Plus size={14} className="mr-1" /> Adicionar filial
          </Button>
        </div>
      </div>
    </div>
  )
}
