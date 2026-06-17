"use client"

import { 
  AlertCircle, Upload, X, Eye,
  FileText,
  Image as ImageIcon,
  Phone,
  Mail,
  Calendar,
  CreditCard,
  Hash,
  Type,
  MapPin,
  Building,
  User
} from "lucide-react"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Progress } from "@/components/ui/progress"
import { CheckCircle2 } from "lucide-react"

interface FieldConfig {
  name: string
  label: string
  field_type: string
  required: boolean
  placeholder?: string
  description?: string
  options?: string[]
  validation_rules?: {
    pattern?: string
    min_length?: number
    max_length?: number
    pattern_error?: string
  }
  max_file_size_mb?: number
  allowed_file_types?: string[]
}

interface FieldCompleted {
  name: string
  value?: string
  file_url?: string
  file_name?: string
  submitted_at: string
}

const FIELD_TYPE_ICONS: Record<string, React.ReactNode> = {
  text: <Type className="w-4 h-4" />,
  cpf: <CreditCard className="w-4 h-4" />,
  cnpj: <Building className="w-4 h-4" />,
  email: <Mail className="w-4 h-4" />,
  phone: <Phone className="w-4 h-4" />,
  date: <Calendar className="w-4 h-4" />,
  number: <Hash className="w-4 h-4" />,
  currency: <CreditCard className="w-4 h-4" />,
  file: <FileText className="w-4 h-4" />,
  photo: <ImageIcon className="w-4 h-4" />,
  address: <MapPin className="w-4 h-4" />,
  select: <Type className="w-4 h-4" />,
  textarea: <Type className="w-4 h-4" />,
}

interface PortalFieldRendererProps {
  field: FieldConfig
  value: string
  error?: string
  upload?: { file: File; preview?: string }
  uploadProgress?: number
  completedFile?: FieldCompleted
  onChange: (fieldName: string, value: string, fieldType: string) => void
  onFileChange: (fieldName: string, file: File | null) => void
}

export function PortalFieldRenderer({
  field,
  value,
  error,
  upload,
  uploadProgress,
  completedFile,
  onChange,
  onFileChange,
}: PortalFieldRendererProps) {
  const icon = FIELD_TYPE_ICONS[field.field_type] || <Type className="w-4 h-4" />

  if (field.field_type === "file" || field.field_type === "photo") {
    return (
      <div className="space-y-2">
        <Label className="flex items-center gap-2 text-sm font-medium text-lia-text-primary dark:text-lia-text-tertiary">
          {icon}
          {field.label}
          {field.required && <span className="text-status-error">*</span>}
        </Label>
        {field.description && (
          <p className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">{field.description}</p>
        )}
        <div className="relative">
          {upload?.preview ? (
            <div className="relative rounded-xl overflow-hidden border border-lia-border-subtle">
              <img src={upload.preview} alt="Preview" className="w-full h-48 object-cover" />
              <button
                type="button"
                onClick={() => onFileChange(field.name, null)}
                className="absolute top-2 right-2 p-1 bg-status-error text-white rounded-full hover:bg-status-error"
                aria-label="Remover arquivo"
              >
                <X className="w-4 h-4" />
              </button>
              <div className="absolute bottom-0 left-0 right-0 bg-lia-overlay text-white text-xs p-2 truncate">
                {upload.file.name}
              </div>
            </div>
          ) : upload?.file ? (
            <div className="flex items-center gap-3 p-4 border border-lia-border-subtle rounded-xl">
              <FileText className="w-8 h-8 text-lia-text-tertiary dark:text-lia-text-secondary" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-lia-text-primary dark:text-lia-text-tertiary truncate">{upload.file.name}</p>
                <p className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">{(upload.file.size / 1024 / 1024).toFixed(2)} MB</p>
              </div>
              <button type="button" onClick={() => onFileChange(field.name, null)} className="p-1 text-lia-text-tertiary dark:text-lia-text-secondary hover:text-status-error" aria-label="Remover arquivo">
                <X className="w-5 h-5" />
              </button>
            </div>
          ) : completedFile ? (
            <div className="flex items-center gap-3 p-4 border border-status-success/30 bg-status-success/10 rounded-xl">
              <CheckCircle2 className="w-6 h-6 text-status-success" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-lia-text-primary dark:text-lia-text-tertiary truncate">{completedFile.file_name || "Arquivo enviado"}</p>
                <p className="text-xs text-status-success">Arquivo já enviado</p>
              </div>
              <button
                type="button"
                onClick={() => { const input = document.getElementById(`file-${field.name}`) as HTMLInputElement; input?.click() }}
                className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary hover:text-lia-text-primary dark:hover:text-lia-text-muted underline"
              >
                Substituir
              </button>
            </div>
          ) : (
            <label
              htmlFor={`file-${field.name}`}
              className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-lia-border-default rounded-xl cursor-pointer hover:border-lia-border-medium dark:hover:border-lia-border-medium hover:bg-lia-bg-secondary dark:hover:bg-lia-bg-inverse transition-colors motion-reduce:transition-none"
            >
              <Upload className="w-8 h-8 text-lia-text-tertiary dark:text-lia-text-secondary mb-2" />
              <span className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">
                {field.field_type === "photo" ? "Toque para tirar foto ou selecionar" : "Toque para selecionar arquivo"}
              </span>
              <span className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary mt-1">Máx: {field.max_file_size_mb || 10}MB</span>
            </label>
          )}
          <input
            id={`file-${field.name}`}
            type="file"
            accept={field.field_type === "photo" ? "image/*" : field.allowed_file_types?.join(",") || "image/*,application/pdf"}
            capture={field.field_type === "photo" ? "environment" : undefined}
            className="hidden"
            onChange={(e) => onFileChange(field.name, e.target.files?.[0] || null)}
          />
        </div>
        {uploadProgress !== undefined && uploadProgress < 100 && (
          <div className="mt-2">
            <Progress value={uploadProgress} className="h-1" />
            <p className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary mt-1">Enviando... {uploadProgress}%</p>
          </div>
        )}
        {error && (
          <p className="text-xs text-status-error flex items-center gap-1">
            <AlertCircle className="w-3 h-3" />
            {error}
          </p>
        )}
      </div>
    )
  }

  if (field.field_type === "select" && field.options) {
    return (
      <div className="space-y-2">
        <Label className="flex items-center gap-2 text-sm font-medium text-lia-text-primary dark:text-lia-text-tertiary">
          {icon}
          {field.label}
          {field.required && <span className="text-status-error">*</span>}
        </Label>
        {field.description && <p className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">{field.description}</p>}
        <select
          value={value}
          onChange={(e) => onChange(field.name, e.target.value, field.field_type)}
          className="flex h-10 w-full rounded-xl border border-lia-border-default bg-lia-bg-primary dark:bg-lia-btn-primary-hover dark:text-lia-text-muted dark:border-lia-border-medium px-3 py-2 text-sm focus:outline-none focus:border-lia-border-medium focus:ring-2 focus:ring-lia-border-subtle"
        >
          <option value="">Selecione...</option>
          {field.options.map((opt) => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
        {error && (
          <p className="text-xs text-status-error flex items-center gap-1">
            <AlertCircle className="w-3 h-3" />{error}
          </p>
        )}
      </div>
    )
  }

  if (field.field_type === "textarea") {
    return (
      <div className="space-y-2">
        <Label className="flex items-center gap-2 text-sm font-medium text-lia-text-primary dark:text-lia-text-tertiary">
          {icon}
          {field.label}
          {field.required && <span className="text-status-error">*</span>}
        </Label>
        {field.description && <p className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">{field.description}</p>}
        <textarea
          value={value}
          onChange={(e) => onChange(field.name, e.target.value, field.field_type)}
          placeholder={field.placeholder}
          rows={4}
          className="flex w-full rounded-xl border border-lia-border-default bg-lia-bg-primary dark:bg-lia-btn-primary-hover dark:text-lia-text-disabled dark:border-lia-border-medium px-3 py-2 text-sm focus:outline-none focus:border-lia-border-medium focus:ring-2 focus:ring-lia-border-subtle resize-none"
        />
        {error && (
          <p className="text-xs text-status-error flex items-center gap-1">
            <AlertCircle className="w-3 h-3" />{error}
          </p>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <Label className="flex items-center gap-2 text-sm font-medium text-lia-text-primary dark:text-lia-text-tertiary">
        {icon}
        {field.label}
        {field.required && <span className="text-status-error">*</span>}
      </Label>
      {field.description && <p className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">{field.description}</p>}
      <Input
        type={field.field_type === "date" ? "date" : "text"}
        value={value}
        onChange={(e) => onChange(field.name, e.target.value, field.field_type)}
        placeholder={field.placeholder}
        inputMode={["cpf", "cnpj", "phone", "number", "currency"].includes(field.field_type) ? "numeric" : "text"}
        className={error ? "border-status-error/30 focus:border-status-error/30" : ""}
      />
      {error && (
        <p className="text-xs text-status-error flex items-center gap-1">
          <AlertCircle className="w-3 h-3" />{error}
        </p>
      )}
    </div>
  )
}
