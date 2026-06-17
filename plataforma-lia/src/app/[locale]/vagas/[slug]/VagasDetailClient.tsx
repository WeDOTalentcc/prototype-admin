"use client"

import React, { useEffect, useState, useRef } from "react"
import NextImage from "next/image"
import { Button } from "@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Checkbox } from "@/components/ui/checkbox"
import { cardStyles, textStyles } from "@/lib/design-tokens"
import { cn } from "@/lib/utils"
import {
  MapPin,
  Briefcase,
  GraduationCap,
  CheckCircle2,
  Building2,
  Globe,
  Code2,
  Languages,
  Users,
  Heart,
  Loader2,
  AlertCircle,
  MessageCircle,
  Bot,
  Shield,
  ExternalLink,
  FileText,
  MessageSquare,
  UserCheck,
  Send,
  ArrowRight,
  Upload,
  Monitor,
  X,
  CheckCircle
} from "lucide-react"

interface TechnicalRequirement {
  technology: string
  level: string
  category: string
  required: boolean
}

interface Language {
  language: string
  level: string
  required: boolean
}

interface Competency {
  competency: string
  weight: string
}

interface PublicVacancy {
  title: string
  description: string | null
  requirements: string[]
  benefits: string[]
  location: string | null
  work_model: string | null
  employment_type: string | null
  seniority_level: string | null
  department: string | null
  company_name: string | null
  company_description: string | null
  company_website: string | null
  company_logo: string | null
  is_confidential: boolean
  is_affirmative: boolean
  technical_requirements: TechnicalRequirement[]
  languages: Language[]
  behavioral_competencies: Competency[]
}

const WORK_MODEL_LABELS: Record<string, string> = {
  'remoto': 'Remoto',
  'hibrido': 'Híbrido',
  'híbrido': 'Híbrido',
  'presencial': 'Presencial'
}

const LEVEL_LABELS: Record<string, string> = {
  'Básico': 'Básico',
  'Intermediário': 'Intermediário',
  'Avançado': 'Avançado',
  'Fluente': 'Fluente'
}

const SECTION_TITLE_CLASS = cn(textStyles.subtitleMuted, "uppercase tracking-wider")

const processSteps = [
  {
    icon: FileText,
    title: "Candidatura",
    description: "Envie seu CV online ou via WhatsApp",
    highlight: false
  },
  {
    icon: Bot,
    title: "Triagem com IA",
    description: "Nossa IA analisa seu perfil e faz perguntas",
    highlight: true
  },
  {
    icon: MessageSquare,
    title: "Feedback Inicial",
    description: "Você recebe retorno sobre sua candidatura",
    highlight: false
  },
  {
    icon: UserCheck,
    title: "Avaliação",
    description: "Recrutador analisa os candidatos selecionados",
    highlight: false
  },
  {
    icon: Send,
    title: "Feedback Final",
    description: "Retorno sobre próximas etapas",
    highlight: false
  }
]

interface ApplicationForm {
  name: string
  email: string
  phone: string
  lgpdConsent: boolean
  cvFile: File | null
}

interface ApplicationResult {
  status: string
  message: string
  candidate_id?: string
  adherence_score?: number
  next_step?: string
}

interface Props {
  slug: string
}

export default function VagasDetailClient({ slug }: Props) {
  const [vacancy, setVacancy] = useState<PublicVacancy | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [applicationResult, setApplicationResult] = useState<ApplicationResult | null>(null)
  const [formErrors, setFormErrors] = useState<Record<string, string>>({})
  const [form, setForm] = useState<ApplicationForm>({
    name: "",
    email: "",
    phone: "",
    lgpdConsent: false,
    cvFile: null
  })
  const fileInputRef = useRef<HTMLInputElement>(null)
  const formRef = useRef<HTMLElement>(null)
  const formHeadingRef = useRef<HTMLHeadingElement>(null)

  useEffect(() => {
    const fetchVacancy = async () => {
      if (!slug) return

      try {
        setLoading(true)
        const response = await fetch(`/api/backend-proxy/public-vacancies/p/${slug}`)

        if (!response.ok) {
          if (response.status === 404) {
            setError("Vaga não encontrada ou não está mais disponível.")
          } else {
            setError("Erro ao carregar a vaga. Tente novamente mais tarde.")
          }
          return
        }

        const data = await response.json()
        setVacancy(data)
      } catch (err) {
        setError("Erro ao carregar a vaga. Verifique sua conexão.")
      } finally {
        setLoading(false)
      }
    }

    fetchVacancy()
  }, [slug])

  if (loading) {
    return (
      <div
        className="min-h-screen bg-lia-bg-primary dark:bg-lia-bg-primary flex items-center justify-center"
        role="status"
        aria-live="polite"
        aria-label="Carregando vaga..."
      >
        <div className="text-center">
          <Loader2 className="w-10 h-10 animate-spin motion-reduce:animate-none text-lia-text-tertiary dark:text-lia-text-secondary mx-auto" aria-hidden="true" />
          <p className="text-lia-text-secondary dark:text-lia-text-tertiary mt-4 text-sm">Carregando vaga...</p>
        </div>
      </div>
    )
  }

  if (error || !vacancy) {
    return (
      <div className="min-h-screen bg-lia-bg-primary dark:bg-lia-bg-primary flex items-center justify-center p-6">
        <div className="max-w-md w-full text-center">
          <div className="w-16 h-16 rounded-full bg-lia-bg-tertiary dark:bg-lia-bg-elevated flex items-center justify-center mx-auto mb-6">
            <AlertCircle className="w-8 h-8 text-lia-text-tertiary dark:text-lia-text-secondary" aria-hidden="true" />
          </div>
          <h2 className="text-xl font-semibold text-lia-text-primary dark:text-lia-text-primary mb-2">
            Vaga Indisponível
          </h2>
          <p className="text-lia-text-secondary dark:text-lia-text-tertiary mb-6" aria-live="polite" aria-atomic="true">
            {error || "Esta vaga não está mais disponível."}
          </p>
          <Button variant="outline" onClick={() => window.history.back()}>
            Voltar
          </Button>
        </div>
      </div>
    )
  }

  const handleApplyWhatsApp = () => {
    const message = encodeURIComponent(
      `Olá! Tenho interesse na vaga de ${vacancy.title} - Ref: ${slug}`
    )
    const whatsappNumber = process.env.NEXT_PUBLIC_WHATSAPP_NUMBER || ''
    if (!whatsappNumber) return
    window.open(`https://wa.me/${whatsappNumber}?text=${message}`, '_blank')
  }

  const handleOpenForm = () => {
    setShowForm(true)
    setApplicationResult(null)
    setFormErrors({})
    setTimeout(() => {
      formRef.current?.scrollIntoView({ behavior: "smooth", block: "start" })
      formHeadingRef.current?.focus()
    }, 150)
  }

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {}
    if (!form.name.trim()) errors.name = "Nome é obrigatório"
    if (!form.email.trim()) errors.email = "Email é obrigatório"
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) errors.email = "Email inválido"
    if (!form.phone.trim()) errors.phone = "Telefone é obrigatório"
    if (!form.cvFile) errors.cvFile = "Currículo é obrigatório"
    else {
      const allowedTypes = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
      ]
      if (!allowedTypes.includes(form.cvFile.type)) {
        errors.cvFile = "Formato inválido. Envie PDF ou DOC/DOCX"
      }
      if (form.cvFile.size > 10 * 1024 * 1024) {
        errors.cvFile = "Arquivo muito grande. Máximo 10MB"
      }
    }
    if (!form.lgpdConsent) errors.lgpdConsent = "Consentimento LGPD é obrigatório"
    setFormErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleSubmitApplication = async () => {
    if (!validateForm()) return
    setSubmitting(true)
    try {
      const formData = new FormData()
      formData.append("name", form.name.trim())
      formData.append("email", form.email.trim())
      formData.append("phone", form.phone.trim())
      formData.append("lgpd_consent", "true")
      if (form.cvFile) formData.append("cv_file", form.cvFile)

      const response = await fetch(`/api/backend-proxy/public-vacancies/p/${slug}/apply`, {
        method: "POST",
        body: formData
      })

      const data = await response.json()

      if (!response.ok) {
        setApplicationResult({
          status: "error",
          message: data.error || data.detail || "Erro ao processar candidatura. Tente novamente."
        })
        return
      }

      setApplicationResult(data)
    } catch (err) {
      setApplicationResult({
        status: "error",
        message: "Erro de conexão. Verifique sua internet e tente novamente."
      })
    } finally {
      setSubmitting(false)
    }
  }

  const showCompanyInfo = !vacancy.is_confidential && (
    vacancy.company_name ||
    vacancy.company_description ||
    vacancy.company_logo ||
    vacancy.company_website
  )

  return (
    <div className="min-h-screen bg-lia-bg-primary dark:bg-lia-bg-primary">
      <main className="max-w-3xl mx-auto px-4 py-6 sm:py-8 sm:px-6 lg:px-8" aria-label="Detalhes da vaga">

        {/* Logo + nome da empresa — top-left, visível antes do título */}
        {showCompanyInfo && (
          <div className="flex items-center gap-3 mb-5">
            {vacancy.company_logo ? (
              <NextImage
                src={vacancy.company_logo}
                alt={vacancy.company_name ? `Logo ${vacancy.company_name}` : "Logo da empresa"}
                width={56}
                height={56}
                className="w-14 h-14 rounded-xl object-contain border border-lia-border-subtle dark:border-lia-border-strong bg-white"
              />
            ) : (
              <div
                className="w-14 h-14 rounded-xl bg-lia-bg-tertiary dark:bg-lia-bg-elevated flex items-center justify-center"
                aria-hidden="true"
              >
                <Building2 className="w-7 h-7 text-lia-text-tertiary dark:text-lia-text-secondary" aria-hidden="true" />
              </div>
            )}
            <div>
              {vacancy.company_name && (
                <p className={cn(textStyles.h4, "text-lg font-medium")}>
                  {vacancy.company_name}
                </p>
              )}
              {vacancy.company_website && (
                <a
                  href={vacancy.company_website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={cn(textStyles.linkSubtle, "flex items-center gap-1")}
                >
                  Visitar website
                  <ExternalLink className="w-3 h-3" aria-hidden="true" />
                  <span className="sr-only">(abre em nova janela)</span>
                </a>
              )}
            </div>
          </div>
        )}

        <header className="mb-5">
          <div className="flex flex-wrap gap-2 mb-4">
            {vacancy.is_affirmative && (
              <Chip variant="info" density="compact">
                <Heart className="w-3 h-3 mr-1" aria-hidden="true" />
                Vaga Afirmativa
              </Chip>
            )}
            {vacancy.department && (
              <Chip variant="neutral" muted density="compact">
                {vacancy.department}
              </Chip>
            )}
          </div>

          <h1 className={cn(textStyles.h1, "text-[22px] sm:text-[28px] tracking-tight mb-4")}>
            {vacancy.title}
          </h1>

          <div className={cn(textStyles.description, "flex flex-wrap gap-x-4 gap-y-2")}>
            {vacancy.location && (
              <div className="flex items-center gap-2">
                <MapPin className="w-4 h-4 text-lia-text-tertiary dark:text-lia-text-secondary" aria-hidden="true" />
                <span>{vacancy.location}</span>
              </div>
            )}
            {vacancy.work_model && (
              <div className="flex items-center gap-2">
                <Globe className="w-4 h-4 text-lia-text-tertiary dark:text-lia-text-secondary" aria-hidden="true" />
                <span>{WORK_MODEL_LABELS[vacancy.work_model.toLowerCase()] || vacancy.work_model}</span>
              </div>
            )}
            {vacancy.employment_type && (
              <div className="flex items-center gap-2">
                <Briefcase className="w-4 h-4 text-lia-text-tertiary dark:text-lia-text-secondary" aria-hidden="true" />
                <span>{vacancy.employment_type}</span>
              </div>
            )}
            {vacancy.seniority_level && (
              <div className="flex items-center gap-2">
                <GraduationCap className="w-4 h-4 text-lia-text-tertiary dark:text-lia-text-secondary" aria-hidden="true" />
                <span>{vacancy.seniority_level}</span>
              </div>
            )}
          </div>
        </header>

        {showCompanyInfo && vacancy.company_description && (
          <section
            className="mb-5 pb-5 border-b border-lia-border-subtle dark:border-lia-border-subtle"
            aria-labelledby="section-empresa"
          >
            <h3 id="section-empresa" className={cn(SECTION_TITLE_CLASS, "mb-3")}>
              Sobre a Empresa
            </h3>
            <p className={cn(textStyles.body, "leading-relaxed")}>
              {vacancy.company_description}
            </p>
          </section>
        )}

        {vacancy.description && (
          <section
            className="mb-5 pb-5 border-b border-lia-border-subtle dark:border-lia-border-subtle"
            aria-labelledby="section-vaga"
          >
            <h3 id="section-vaga" className={cn(SECTION_TITLE_CLASS, "mb-3")}>
              Sobre a Vaga
            </h3>
            <p className={cn(textStyles.body, "whitespace-pre-wrap leading-relaxed")}>
              {vacancy.description}
            </p>
          </section>
        )}

        {vacancy.requirements && vacancy.requirements.length > 0 && (
          <section
            className="mb-5 pb-5 border-b border-lia-border-subtle dark:border-lia-border-subtle"
            aria-labelledby="section-requisitos"
          >
            <h3 id="section-requisitos" className={cn(SECTION_TITLE_CLASS, "mb-4")}>
              Requisitos
            </h3>
            <ul className="space-y-3">
              {vacancy.requirements.map((req, idx) => (
                <li key={`req-${idx}`} className="flex items-start gap-3 text-lia-text-primary dark:text-lia-text-primary">
                  <CheckCircle2 className="w-4 h-4 text-lia-text-muted dark:text-lia-text-secondary mt-0.5 flex-shrink-0" aria-hidden="true" />
                  <span>{req}</span>
                </li>
              ))}
            </ul>
          </section>
        )}

        {vacancy.technical_requirements && vacancy.technical_requirements.length > 0 && (
          <section
            className="mb-5 pb-5 border-b border-lia-border-subtle dark:border-lia-border-subtle"
            aria-labelledby="section-stack"
          >
            <h3 id="section-stack" className={cn(SECTION_TITLE_CLASS, "mb-4 flex items-center gap-1.5")}>
              <Code2 className="w-3.5 h-3.5" aria-hidden="true" />
              Stack Técnico
            </h3>
            <div className="flex flex-wrap gap-2">
              {vacancy.technical_requirements.map((tech, idx) => (
                <Chip
                  key={`tech-${idx}`}
                  variant="neutral"
                  muted={!tech.required}
                  density="compact"
                >
                  {tech.technology}
                  {tech.level && (
                    <span className="ml-1 opacity-70">· {tech.level}</span>
                  )}
                </Chip>
              ))}
            </div>
          </section>
        )}

        {vacancy.languages && vacancy.languages.length > 0 && (
          <section
            className="mb-5 pb-5 border-b border-lia-border-subtle dark:border-lia-border-subtle"
            aria-labelledby="section-idiomas"
          >
            <h3 id="section-idiomas" className={cn(SECTION_TITLE_CLASS, "mb-4 flex items-center gap-1.5")}>
              <Languages className="w-3.5 h-3.5" aria-hidden="true" />
              Idiomas
            </h3>
            <div className="flex flex-wrap gap-2">
              {vacancy.languages.map((lang, idx) => (
                <Chip
                  key={`lang-${idx}`}
                  variant="neutral"
                  muted={!lang.required}
                  density="compact"
                >
                  {lang.language}
                  {lang.level && (
                    <span className="ml-1 opacity-70">· {LEVEL_LABELS[lang.level] || lang.level}</span>
                  )}
                </Chip>
              ))}
            </div>
          </section>
        )}

        {vacancy.behavioral_competencies && vacancy.behavioral_competencies.length > 0 && (
          <section
            className="mb-5 pb-5 border-b border-lia-border-subtle dark:border-lia-border-subtle"
            aria-labelledby="section-competencias"
          >
            <h3 id="section-competencias" className={cn(SECTION_TITLE_CLASS, "mb-4 flex items-center gap-1.5")}>
              <Users className="w-3.5 h-3.5" aria-hidden="true" />
              Competências
            </h3>
            <div className="flex flex-wrap gap-2">
              {vacancy.behavioral_competencies.map((comp, idx) => (
                <Chip key={`comp-${idx}`} variant="neutral" muted density="compact">
                  {comp.competency}
                </Chip>
              ))}
            </div>
          </section>
        )}

        {vacancy.benefits && vacancy.benefits.length > 0 && (
          <section
            className="mb-5 pb-5 border-b border-lia-border-subtle dark:border-lia-border-subtle"
            aria-labelledby="section-beneficios"
          >
            <h3 id="section-beneficios" className={cn(SECTION_TITLE_CLASS, "mb-4")}>
              Benefícios
            </h3>
            <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2 list-none">
              {vacancy.benefits.map((benefit, idx) => (
                <li
                  key={`benefit-${idx}`}
                  className="flex items-center gap-3 text-lia-text-primary dark:text-lia-text-primary py-2"
                >
                  <CheckCircle2 className="w-4 h-4 text-lia-text-muted dark:text-lia-text-secondary flex-shrink-0" aria-hidden="true" />
                  <span className="text-sm">{benefit}</span>
                </li>
              ))}
            </ul>
          </section>
        )}

        <section
          className="mb-5 pb-5 border-b border-lia-border-subtle dark:border-lia-border-subtle"
          aria-labelledby="section-processo"
        >
          <h3 id="section-processo" className={cn(SECTION_TITLE_CLASS, "mb-6")}>
            Como funciona o processo
          </h3>

          <div className="relative">
            <div
              className="absolute left-4 top-8 bottom-8 w-px bg-lia-bg-tertiary dark:bg-lia-bg-inverse hidden sm:block"
              aria-hidden="true"
            />

            <ol className="space-y-3 list-none">
              {processSteps.map((step, idx) => (
                <li key={`step-${idx}`} className="flex items-start gap-4 relative">
                  <div
                    className={cn(
                      "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 z-10",
                      step.highlight
                        ? "bg-lia-btn-primary-bg text-white dark:bg-lia-bg-inverse"
                        : "bg-lia-bg-tertiary dark:bg-lia-bg-inverse text-lia-text-secondary dark:text-lia-text-tertiary"
                    )}
                    aria-hidden="true"
                  >
                    <step.icon className="w-3.5 h-3.5" aria-hidden="true" />
                  </div>
                  <div className="pt-1.5">
                    <h4 className="font-medium text-lia-text-primary dark:text-lia-text-primary">
                      {step.title}
                    </h4>
                    <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary mt-0.5">
                      {step.description}
                    </p>
                  </div>
                  {idx < processSteps.length - 1 && (
                    <ArrowRight className="w-4 h-4 text-lia-text-muted dark:text-lia-text-primary absolute left-2 -bottom-3 hidden sm:block" aria-hidden="true" />
                  )}
                </li>
              ))}
            </ol>
          </div>

          <div className={cn(cardStyles.default, "mt-6 p-4")}>
            <div className="flex items-start gap-3">
              <Bot className="w-5 h-5 text-lia-text-tertiary dark:text-lia-text-secondary mt-0.5 flex-shrink-0" aria-hidden="true" />
              <p className={cn(textStyles.body, "leading-relaxed")}>
                <strong className="font-semibold text-lia-text-primary dark:text-lia-text-primary">Triagem inteligente com IA.</strong>{" "}
                Nossa assistente de IA conduz uma conversa amigável para conhecer você melhor,
                garantindo uma avaliação justa e feedback em todas as etapas.
              </p>
            </div>
          </div>
        </section>

        <section className="mb-8" aria-labelledby="section-cta">
          <div className={cn(cardStyles.flat, "p-4 sm:p-6 text-center")}>
            <h3 id="section-cta" className={cn(textStyles.h2, "mb-2")}>
              Interessado na vaga?
            </h3>
            <p className={cn(textStyles.description, "mb-6 max-w-md mx-auto leading-relaxed")}>
              Candidate-se online ou via WhatsApp em menos de 10 minutos.
              Basta enviar seu currículo e responder algumas perguntas.
            </p>

            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Button size="lg" onClick={handleOpenForm}>
                <Monitor className="w-5 h-5 mr-2" aria-hidden="true" />
                Candidatar-se Online
              </Button>
              <Button size="lg" variant="outline" onClick={handleApplyWhatsApp}>
                <MessageCircle className="w-5 h-5 mr-2" aria-hidden="true" />
                Candidatar-se via WhatsApp
                <span className="sr-only">(abre em nova janela)</span>
              </Button>
            </div>
          </div>
        </section>

        {showForm && (
          <section
            className="mb-8"
            ref={formRef}
            aria-live="polite"
            aria-atomic="false"
          >
            {applicationResult && applicationResult.status !== "error" ? (
              <div className={cn(cardStyles.default, "p-6 sm:p-8 text-center")}>
                <div className="w-16 h-16 rounded-full bg-status-success/10 flex items-center justify-center mx-auto mb-4">
                  <CheckCircle className="w-8 h-8 text-status-success" aria-hidden="true" />
                </div>
                <h3 className={cn(textStyles.h2, "mb-2")}>
                  {applicationResult.status === "applied" ? "Candidatura Enviada!" :
                  applicationResult.status === "queued" ? "Dados Registrados!" :
                  applicationResult.status === "already_applied" ? "Candidatura Existente" : "Obrigado pela Candidatura"}
                </h3>
                <p className={cn(textStyles.description, "max-w-md mx-auto leading-relaxed")}>
                  {applicationResult.message}
                </p>
              </div>
            ) : (
              <div className={cn(cardStyles.default, "p-6 sm:p-8")}>
                <div className="flex items-center justify-between mb-6">
                  <h3 ref={formHeadingRef} tabIndex={-1} className={textStyles.h2}>
                    Candidatura Online
                  </h3>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setShowForm(false)}
                    aria-label="Fechar formulário"
                  >
                    <X className="w-5 h-5" aria-hidden="true" />
                  </Button>
                </div>

                {applicationResult?.status === "error" && (
                  <div className="mb-4 p-3 bg-status-error/10 border border-status-error/30 rounded-md" role="alert">
                    <p className={cn(textStyles.body, "text-status-error dark:text-status-error")}>{applicationResult.message}</p>
                  </div>
                )}

                <div className="space-y-4">
                  <div className="space-y-1.5">
                    <Label htmlFor="vagas-name">Nome completo *</Label>
                    <Input
                      id="vagas-name"
                      type="text"
                      maxLength={120}
                      value={form.name}
                      onChange={(e) => setForm(prev => ({ ...prev, name: e.target.value }))}
                      placeholder="Seu nome completo"
                      aria-invalid={!!formErrors.name}
                      aria-describedby={formErrors.name ? "vagas-name-error" : undefined}
                      className={formErrors.name ? "border-status-error/60 focus:ring-status-error/20" : undefined}
                    />
                    {formErrors.name && (
                      <p id="vagas-name-error" className={cn(textStyles.caption, "text-status-error dark:text-status-error")}>{formErrors.name}</p>
                    )}
                  </div>

                  <div className="space-y-1.5">
                    <Label htmlFor="vagas-email">Email *</Label>
                    <Input
                      id="vagas-email"
                      type="email"
                      maxLength={254}
                      value={form.email}
                      onChange={(e) => setForm(prev => ({ ...prev, email: e.target.value }))}
                      placeholder="seu@email.com"
                      aria-invalid={!!formErrors.email}
                      aria-describedby={formErrors.email ? "vagas-email-error" : undefined}
                      className={formErrors.email ? "border-status-error/60 focus:ring-status-error/20" : undefined}
                    />
                    {formErrors.email && (
                      <p id="vagas-email-error" className={cn(textStyles.caption, "text-status-error dark:text-status-error")}>{formErrors.email}</p>
                    )}
                  </div>

                  <div className="space-y-1.5">
                    <Label htmlFor="vagas-phone">Telefone / WhatsApp *</Label>
                    <Input
                      id="vagas-phone"
                      type="tel"
                      maxLength={20}
                      value={form.phone}
                      onChange={(e) => setForm(prev => ({ ...prev, phone: e.target.value }))}
                      placeholder="+55 (11) 99999-9999"
                      aria-invalid={!!formErrors.phone}
                      aria-describedby={formErrors.phone ? "vagas-phone-error" : undefined}
                      className={formErrors.phone ? "border-status-error/60 focus:ring-status-error/20" : undefined}
                    />
                    {formErrors.phone && (
                      <p id="vagas-phone-error" className={cn(textStyles.caption, "text-status-error dark:text-status-error")}>{formErrors.phone}</p>
                    )}
                  </div>

                  <div className="space-y-1.5">
                    <Label htmlFor="vagas-cv">Currículo (PDF ou DOC) *</Label>
                    <input
                      id="vagas-cv"
                      ref={fileInputRef}
                      type="file"
                      accept=".pdf,.doc,.docx,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                      onChange={(e) => {
                        const file = e.target.files?.[0] || null
                        setForm(prev => ({ ...prev, cvFile: file }))
                      }}
                      className="hidden"
                    />
                    <div
                      role="button"
                      tabIndex={0}
                      onClick={() => fileInputRef.current?.click()}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") {
                          e.preventDefault()
                          fileInputRef.current?.click()
                        }
                      }}
                      aria-invalid={!!formErrors.cvFile}
                      aria-describedby={formErrors.cvFile ? "vagas-cv-error" : undefined}
                      className={cn(
                        "w-full px-3 py-4 border border-dashed rounded-md text-center cursor-pointer transition-colors motion-reduce:transition-none",
                        "bg-lia-bg-primary dark:bg-lia-bg-elevated hover:border-lia-border-medium hover:bg-lia-bg-secondary dark:hover:bg-lia-bg-secondary",
                        "focus:outline-none focus-visible:ring-2 focus-visible:ring-lia-btn-primary-bg/20",
                        formErrors.cvFile
                          ? "border-status-error/60"
                          : form.cvFile
                          ? "border-lia-border-default bg-lia-bg-secondary dark:bg-lia-bg-secondary"
                          : "border-lia-border-default",
                      )}
                    >
                      {form.cvFile ? (
                        <div className={cn(textStyles.body, "flex items-center justify-center gap-2")}>
                          <FileText className="w-4 h-4" aria-hidden="true" />
                          <span>{form.cvFile.name}</span>
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation()
                              setForm(prev => ({ ...prev, cvFile: null }))
                              if (fileInputRef.current) fileInputRef.current.value = ""
                            }}
                            aria-label="Remover currículo"
                            className="text-lia-text-tertiary dark:text-lia-text-secondary hover:text-lia-text-primary dark:hover:text-lia-text-primary ml-1"
                          >
                            <X className="w-4 h-4" aria-hidden="true" />
                          </button>
                        </div>
                      ) : (
                        <div className="flex flex-col items-center gap-1">
                          <Upload className="w-5 h-5 text-lia-text-tertiary dark:text-lia-text-secondary" aria-hidden="true" />
                          <span className={textStyles.body}>
                            Clique para enviar seu currículo
                          </span>
                          <span className={textStyles.caption}>PDF ou DOC, até 10MB</span>
                        </div>
                      )}
                    </div>
                    {formErrors.cvFile && (
                      <p id="vagas-cv-error" className={cn(textStyles.caption, "text-status-error dark:text-status-error")}>{formErrors.cvFile}</p>
                    )}
                  </div>

                  <div className="pt-2">
                    <label htmlFor="vagas-lgpd" className="flex items-start gap-3 cursor-pointer">
                      <Checkbox
                        id="vagas-lgpd"
                        checked={form.lgpdConsent}
                        onCheckedChange={(checked) => setForm(prev => ({ ...prev, lgpdConsent: checked === true }))}
                        aria-invalid={!!formErrors.lgpdConsent}
                        aria-describedby={formErrors.lgpdConsent ? "vagas-lgpd-error" : undefined}
                        className="mt-0.5"
                      />
                      <span className={cn(
                        textStyles.caption,
                        "leading-relaxed",
                        formErrors.lgpdConsent && "text-status-error dark:text-status-error",
                      )}>
                        Autorizo a coleta e tratamento dos meus dados pessoais para fins deste processo seletivo,
                        conforme a Lei Geral de Proteção de Dados (LGPD). Entendo que posso solicitar a exclusão
                        dos meus dados a qualquer momento. *
                      </span>
                    </label>
                    {formErrors.lgpdConsent && (
                      <p id="vagas-lgpd-error" className={cn(textStyles.caption, "text-status-error dark:text-status-error mt-1")}>{formErrors.lgpdConsent}</p>
                    )}
                  </div>

                  <div className="pt-4">
                    <Button
                      size="lg"
                      className="w-full"
                      onClick={handleSubmitApplication}
                      disabled={submitting}
                    >
                      {submitting ? (
                        <>
                          <Loader2 className="w-5 h-5 mr-2 animate-spin motion-reduce:animate-none" aria-hidden="true" />
                          Enviando candidatura...
                        </>
                      ) : (
                        <>
                          <Send className="w-5 h-5 mr-2" aria-hidden="true" />
                          Enviar Candidatura
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              </div>
            )}
          </section>
        )}

        <section className="text-center" aria-labelledby="section-privacidade">
          <div className={cn(cardStyles.default, "p-6")}>
            <div className="flex items-center justify-center gap-2 mb-3">
              <Shield className="w-4 h-4 text-lia-text-tertiary dark:text-lia-text-secondary" aria-hidden="true" />
              <h4 id="section-privacidade" className={textStyles.subtitle}>
                Privacidade e Proteção de Dados
              </h4>
            </div>
            <p className={cn(textStyles.description, "leading-relaxed max-w-lg mx-auto mb-2")}>
              Este processo seletivo utiliza inteligência artificial (IA) para auxiliar na triagem.
              Seus dados são tratados conforme a LGPD. Ao se candidatar, você autoriza a coleta
              e análise dos seus dados para fins deste processo.
            </p>
            <p className={textStyles.caption}>
              <a href="/privacidade" className="hover:text-lia-text-primary dark:hover:text-lia-text-primary underline">
                Política de Privacidade
              </a>
              {" · "}
              <a href="mailto:dpo@wedotalent.com" className="hover:text-lia-text-primary dark:hover:text-lia-text-primary">
                dpo@wedotalent.com
              </a>
            </p>
          </div>
        </section>

        <footer className="text-center mt-8 pt-5 border-t border-lia-border-subtle dark:border-lia-border-subtle">
          <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary">
            Powered by{" "}
            <span className="font-medium text-lia-text-secondary dark:text-lia-text-tertiary">WeDOTalent</span>
          </p>
        </footer>
      </main>
    </div>
  )
}
