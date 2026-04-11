"use client"

import React, { useEffect, useState, useRef } from "react"
import NextImage from "next/image"
import { useParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
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

const processSteps = [
 {
 icon: FileText,
 title: "Candidatura",
 description: "Envie seu CV online ou via WhatsApp",
 highlight: false
 },
 {
 icon: Bot,
 title: "Triagem com LIA",
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

export default function PublicVacancyPage() {
 const params = useParams()
 const slug = params?.slug as string
 
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
 const formRef = useRef<HTMLDivElement>(null)

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
 <div className="min-h-screen bg-lia-bg-primary dark:bg-lia-bg-primary flex items-center justify-center" role="status" aria-live="polite" aria-label="Carregando...">
 <div className="text-center" role="status" aria-live="polite" aria-label="Carregando...">
 <Loader2 className="w-10 h-10 animate-spin motion-reduce:animate-none text-lia-text-tertiary dark:text-lia-text-secondary mx-auto" />
 <p className="text-lia-text-secondary dark:text-lia-text-tertiary mt-4 text-sm" aria-live="polite" aria-atomic="true">Carregando vaga...</p>
 </div>
 </div>
 )
 }

 if (error || !vacancy) {
 return (
 <div className="min-h-screen bg-lia-bg-primary dark:bg-lia-bg-primary flex items-center justify-center p-6">
 <div className="max-w-md w-full text-center">
 <div className="w-16 h-16 rounded-full bg-lia-bg-tertiary dark:bg-lia-bg-elevated flex items-center justify-center mx-auto mb-6">
 <AlertCircle className="w-8 h-8 text-lia-text-tertiary dark:text-lia-text-secondary" />
 </div>
 <h2 className="text-xl font-semibold text-lia-text-primary dark:text-lia-text-primary mb-2">
 Vaga Indisponível
 </h2>
 <p className="text-lia-text-secondary dark:text-lia-text-tertiary mb-6" aria-live="polite" aria-atomic="true">
 {error || "Esta vaga não está mais disponível."}
 </p>
 <Button 
 variant="outline"
 className="border-lia-border-subtle dark:border-lia-border-medium text-lia-text-primary dark:text-lia-text-disabled hover:bg-lia-bg-secondary dark:hover:bg-lia-bg-inverse"
 onClick={() => window.history.back()}
 >
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
 if (!whatsappNumber) {
 console.warn('NEXT_PUBLIC_WHATSAPP_NUMBER not configured')
 return
 }
 window.open(`https://wa.me/${whatsappNumber}?text=${message}`, '_blank')
 }

 const handleOpenForm = () => {
 setShowForm(true)
 setApplicationResult(null)
 setFormErrors({})
 setTimeout(() => {
 formRef.current?.scrollIntoView({ behavior: "smooth", block: "start" })
 }, 100)
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

 const workModelLabels: Record<string, string> = {
 'remoto': 'Remoto',
 'hibrido': 'Híbrido',
 'híbrido': 'Híbrido',
 'presencial': 'Presencial'
 }

 const levelLabels: Record<string, string> = {
 'Básico': 'Básico',
 'Intermediário': 'Intermediário',
 'Avançado': 'Avançado',
 'Fluente': 'Fluente'
 }

 const showCompanyInfo = !vacancy.is_confidential && (
 vacancy.company_name || 
 vacancy.company_description || 
 vacancy.company_logo || 
 vacancy.company_website
 )

 return (
 <div className="min-h-screen bg-lia-bg-primary dark:bg-lia-bg-primary">
 <div className="max-w-3xl mx-auto px-4 py-12 sm:px-6 lg:px-8">
 
 {showCompanyInfo && (
 <div className="flex items-center gap-4 mb-8">
 {vacancy.company_logo ? (
 <NextImage 
 src={vacancy.company_logo} 
 alt={vacancy.company_name || "Logo"} 
 width={56}
 height={56}
 className="w-14 h-14 rounded-xl object-contain border border-lia-border-subtle dark:border-lia-border-strong"
 />
 ) : (
 <div className="w-14 h-14 rounded-xl bg-lia-bg-tertiary dark:bg-lia-bg-elevated flex items-center justify-center">
 <Building2 className="w-7 h-7 text-lia-text-tertiary dark:text-lia-text-secondary" />
 </div>
 )}
 <div>
 <h2 className="text-lg font-medium text-lia-text-primary dark:text-lia-text-primary">
 {vacancy.company_name}
 </h2>
 {vacancy.company_website && (
 <a 
 href={vacancy.company_website}
 target="_blank"
 rel="noopener noreferrer"
 className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary hover:text-lia-text-primary dark:hover:text-lia-text-disabled flex items-center gap-1"
 >
 Visitar website
 <ExternalLink className="w-3 h-3" />
 </a>
 )}
 </div>
 </div>
 )}

 <header className="mb-10">
 <div className="flex flex-wrap gap-2 mb-4">
 {vacancy.is_affirmative && (
 <Badge className="bg-wedo-magenta/10 text-wedo-magenta border-wedo-magenta/30 font-normal">
 <Heart className="w-3 h-3 mr-1" />
 Vaga Afirmativa
 </Badge>
 )}
 {vacancy.department && (
 <Badge variant="outline" className="border-lia-border-subtle dark:border-lia-border-medium text-lia-text-secondary dark:text-lia-text-disabled font-normal">
 {vacancy.department}
 </Badge>
 )}
 </div>
 
 <h1 className="text-3xl sm:text-4xl font-semibold text-lia-text-primary dark:text-lia-text-primary tracking-tight mb-6">
 {vacancy.title}
 </h1>
 
 <div className="flex flex-wrap gap-6 text-sm text-lia-text-secondary dark:text-lia-text-secondary">
 {vacancy.location && (
 <div className="flex items-center gap-2">
 <MapPin className="w-4 h-4 text-lia-text-tertiary dark:text-lia-text-secondary" />
 <span>{vacancy.location}</span>
 </div>
 )}
 {vacancy.work_model && (
 <div className="flex items-center gap-2">
 <Globe className="w-4 h-4 text-lia-text-tertiary dark:text-lia-text-secondary" />
 <span>{workModelLabels[vacancy.work_model.toLowerCase()] || vacancy.work_model}</span>
 </div>
 )}
 {vacancy.employment_type && (
 <div className="flex items-center gap-2">
 <Briefcase className="w-4 h-4 text-lia-text-tertiary dark:text-lia-text-secondary" />
 <span>{vacancy.employment_type}</span>
 </div>
 )}
 {vacancy.seniority_level && (
 <div className="flex items-center gap-2">
 <GraduationCap className="w-4 h-4 text-lia-text-tertiary dark:text-lia-text-secondary" />
 <span>{vacancy.seniority_level}</span>
 </div>
 )}
 </div>
 </header>

 {showCompanyInfo && vacancy.company_description && (
 <section className="mb-10 pb-10 ">
 <h3 className="text-xs font-medium text-lia-text-tertiary dark:text-lia-text-secondary uppercase tracking-wider mb-3">
 Sobre a Empresa
 </h3>
 <p className="text-lia-text-secondary dark:text-lia-text-secondary leading-relaxed">
 {vacancy.company_description}
 </p>
 </section>
 )}

 {vacancy.description && (
 <section className="mb-10 pb-10 ">
 <h3 className="text-xs font-medium text-lia-text-tertiary dark:text-lia-text-secondary uppercase tracking-wider mb-3">
 Sobre a Vaga
 </h3>
 <p className="text-lia-text-primary dark:text-lia-text-primary whitespace-pre-wrap leading-relaxed">
 {vacancy.description}
 </p>
 </section>
 )}
 
 {vacancy.requirements && vacancy.requirements.length > 0 && (
 <section className="mb-10 pb-10 ">
 <h3 className="text-xs font-medium text-lia-text-tertiary dark:text-lia-text-secondary uppercase tracking-wider mb-4">
 Requisitos
 </h3>
 <ul className="space-y-3">
 {vacancy.requirements.map((req, idx) => (
 <li key={`req-${idx}`} className="flex items-start gap-3 text-lia-text-primary dark:text-lia-text-primary">
 <CheckCircle2 className="w-4 h-4 text-lia-text-disabled dark:text-lia-text-secondary mt-0.5 flex-shrink-0" />
 <span>{req}</span>
 </li>
 ))}
 </ul>
 </section>
 )}
 
 {vacancy.technical_requirements && vacancy.technical_requirements.length > 0 && (
 <section className="mb-10 pb-10 ">
 <h3 className="text-xs font-medium text-lia-text-tertiary dark:text-lia-text-secondary uppercase tracking-wider mb-4">
 <Code2 className="w-4 h-4 inline mr-2" />
 Stack Técnico
 </h3>
 <div className="flex flex-wrap gap-2">
 {vacancy.technical_requirements.map((tech, idx) => (
 <Badge 
 key={`tech-${idx}`} 
 variant="outline"
 className={
 tech.required 
 ? "border-lia-border-default dark:border-lia-border-medium text-lia-text-primary dark:text-lia-text-disabled bg-lia-bg-secondary dark:bg-lia-bg-inverse font-normal"
 : "border-lia-border-subtle dark:border-lia-border-strong text-lia-text-secondary dark:text-lia-text-tertiary font-normal"
 }
 >
 {tech.technology}
 {tech.level && (
 <span className="ml-1 text-lia-text-tertiary dark:text-lia-text-secondary">
 · {tech.level}
 </span>
 )}
 </Badge>
 ))}
 </div>
 </section>
 )}
 
 {vacancy.languages && vacancy.languages.length > 0 && (
 <section className="mb-10 pb-10 ">
 <h3 className="text-xs font-medium text-lia-text-tertiary dark:text-lia-text-secondary uppercase tracking-wider mb-4">
 <Languages className="w-4 h-4 inline mr-2" />
 Idiomas
 </h3>
 <div className="flex flex-wrap gap-2">
 {vacancy.languages.map((lang, idx) => (
 <Badge 
 key={`lang-${idx}`}
 variant="outline"
 className={
 lang.required 
 ? "border-lia-border-default dark:border-lia-border-medium text-lia-text-primary dark:text-lia-text-disabled bg-lia-bg-secondary dark:bg-lia-bg-inverse font-normal"
 : "border-lia-border-subtle dark:border-lia-border-strong text-lia-text-secondary dark:text-lia-text-tertiary font-normal"
 }
 >
 {lang.language}
 {lang.level && (
 <span className="ml-1 text-lia-text-tertiary dark:text-lia-text-secondary">
 · {levelLabels[lang.level] || lang.level}
 </span>
 )}
 </Badge>
 ))}
 </div>
 </section>
 )}
 
 {vacancy.behavioral_competencies && vacancy.behavioral_competencies.length > 0 && (
 <section className="mb-10 pb-10 ">
 <h3 className="text-xs font-medium text-lia-text-tertiary dark:text-lia-text-secondary uppercase tracking-wider mb-4">
 <Users className="w-4 h-4 inline mr-2" />
 Competências
 </h3>
 <div className="flex flex-wrap gap-2">
 {vacancy.behavioral_competencies.map((comp, idx) => (
 <Badge 
 key={`comp-${idx}`}
 variant="outline"
 className="border-lia-border-subtle dark:border-lia-border-medium text-lia-text-secondary dark:text-lia-text-disabled font-normal"
 >
 {comp.competency}
 </Badge>
 ))}
 </div>
 </section>
 )}
 
 {vacancy.benefits && vacancy.benefits.length > 0 && (
 <section className="mb-10 pb-10 ">
 <h3 className="text-xs font-medium text-lia-text-tertiary dark:text-lia-text-secondary uppercase tracking-wider mb-4">
 Benefícios
 </h3>
 <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
 {vacancy.benefits.map((benefit, idx) => (
 <div 
 key={`benefit-${idx}`} 
 className="flex items-center gap-3 text-lia-text-primary dark:text-lia-text-primary py-2"
 >
 <CheckCircle2 className="w-4 h-4 text-lia-text-disabled dark:text-lia-text-secondary flex-shrink-0" />
 <span className="text-sm">{benefit}</span>
 </div>
 ))}
 </div>
 </section>
 )}

 <section className="mb-10 pb-10 ">
 <h3 className="text-xs font-medium text-lia-text-tertiary dark:text-lia-text-secondary uppercase tracking-wider mb-6">
 Como funciona o processo
 </h3>
 
 <div className="relative">
 <div className="absolute left-5 top-8 bottom-8 w-px bg-lia-bg-tertiary dark:bg-lia-bg-inverse hidden sm:block" />
 
 <div className="space-y-6">
 {processSteps.map((step, idx) => (
 <div key={`step-${idx}`} className="flex items-start gap-4 relative">
 <div className={`
 w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 z-10
 ${step.highlight 
 ? 'bg-lia-btn-primary-bg text-white dark:bg-lia-bg-inverse'
 : 'bg-lia-bg-tertiary dark:bg-lia-bg-inverse text-lia-text-secondary dark:text-lia-text-tertiary'
 }
 `}>
 <step.icon className="w-4 h-4" />
 </div>
 <div className="pt-2">
 <h4 className={`font-medium ${step.highlight ? 'text-lia-text-primary dark:text-lia-text-primary' : 'text-lia-text-primary dark:text-lia-text-primary'}`}>
 {step.title}
 </h4>
 <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary mt-0.5">
 {step.description}
 </p>
 </div>
 {idx < processSteps.length - 1 && (
 <ArrowRight className="w-4 h-4 text-lia-text-disabled dark:text-lia-text-primary absolute left-3 -bottom-3 hidden sm:block" />
 )}
 </div>
 ))}
 </div>
 </div>
 
 <div className="mt-8 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl p-4 border border-lia-border-subtle dark:border-lia-border-subtle">
 <div className="flex items-start gap-3">
 <Bot className="w-5 h-5 text-lia-text-tertiary dark:text-lia-text-secondary mt-0.5" />
 <div>
 <p className="text-sm text-lia-text-secondary dark:text-lia-text-secondary">
 <strong className="text-lia-text-primary dark:text-lia-text-disabled">Triagem inteligente com LIA.</strong>{" "}
 Nossa assistente de IA conduz uma conversa amigável para conhecer você melhor, 
 garantindo uma avaliação justa e feedback em todas as etapas.
 </p>
 </div>
 </div>
 </div>
 </section>

 <section className="mb-12">
 <div className="bg-lia-btn-primary-bg dark:bg-lia-btn-primary-hover rounded-xl p-6 sm:p-8 text-center">
 <h3 className="text-xl font-semibold text-white mb-2">
 Interessado na vaga?
 </h3>
 <p className="text-lia-text-tertiary dark:text-lia-text-tertiary text-sm mb-6 max-w-md mx-auto">
 Candidate-se online ou via WhatsApp em menos de 10 minutos. 
 Basta enviar seu currículo e responder algumas perguntas.
 </p>
 
 <div className="flex flex-col sm:flex-row gap-3 justify-center">
 <Button 
 size="lg" 
 className="bg-lia-bg-primary dark:bg-lia-interactive-active text-lia-text-primary hover:bg-lia-bg-tertiary font-medium px-8"
 onClick={handleOpenForm}
 >
 <Monitor className="w-5 h-5 mr-2" />
 Candidatar-se Online
 </Button>
 <Button 
 size="lg" 
 variant="outline"
 className="border-lia-border-medium dark:border-lia-border-medium text-lia-text-disabled hover:bg-lia-btn-primary-hover dark:hover:bg-lia-bg-inverse hover:text-white font-medium px-8"
 onClick={handleApplyWhatsApp}
 >
 <MessageCircle className="w-5 h-5 mr-2" />
 Candidatar-se via WhatsApp
 </Button>
 </div>
 </div>
 </section>

 {showForm && (
 <section className="mb-12" ref={formRef}>
 {applicationResult && applicationResult.status !== "error" ? (
 <div className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl p-6 sm:p-8 text-center dark:bg-lia-bg-secondary">
 <div className="w-16 h-16 rounded-full bg-status-success/10 flex items-center justify-center mx-auto mb-4">
 <CheckCircle className="w-8 h-8 text-status-success" />
 </div>
 <h3 className="text-xl font-semibold text-lia-text-primary dark:text-lia-text-primary mb-2">
 {applicationResult.status === "applied" ? "Candidatura Enviada!" : 
 applicationResult.status === "queued" ? "Dados Registrados!" :
 applicationResult.status === "already_applied" ? "Candidatura Existente" :
 "Obrigado pela Candidatura"}
 </h3>
 <p className="text-lia-text-secondary dark:text-lia-text-secondary text-sm max-w-md mx-auto">
 {applicationResult.message}
 </p>
 </div>
 ) : (
 <div className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl p-6 sm:p-8 dark:bg-lia-bg-secondary">
 <div className="flex items-center justify-between mb-6">
 <h3 className="text-lg font-semibold text-lia-text-primary dark:text-lia-text-primary">
 Candidatura Online
 </h3>
 <button
 onClick={() => setShowForm(false)}
 className="text-lia-text-tertiary dark:text-lia-text-secondary hover:text-lia-text-secondary dark:hover:text-lia-text-disabled"
 >
 <X className="w-5 h-5" />
 </button>
 </div>

 {applicationResult?.status === "error" && (
 <div className="mb-4 p-3 bg-status-error/10 border border-status-error/30 rounded-xl">
 <p className="text-sm text-status-error">{applicationResult.message}</p>
 </div>
 )}

 <div className="space-y-4">
 <div>
 <label className="block text-sm font-medium text-lia-text-primary dark:text-lia-text-primary mb-1">
 Nome completo *
 </label>
 <input
 type="text"
 value={form.name}
 onChange={(e) => setForm(prev => ({ ...prev, name: e.target.value }))}
 className={`w-full px-3 py-2 border rounded-md text-sm text-lia-text-primary dark:text-lia-text-disabled dark:bg-lia-btn-primary-hover placeholder-lia-text-tertiary focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg focus:border-transparent ${
 formErrors.name ? "border-status-error/30" : "border-lia-border-subtle dark:border-lia-border-medium"
 }`}
 placeholder="Seu nome completo"
 />
 {formErrors.name && (
 <p className="text-xs text-status-error mt-1">{formErrors.name}</p>
 )}
 </div>

 <div>
 <label className="block text-sm font-medium text-lia-text-primary dark:text-lia-text-disabled mb-1">
 Email *
 </label>
 <input
 type="email"
 value={form.email}
 onChange={(e) => setForm(prev => ({ ...prev, email: e.target.value }))}
 className={`w-full px-3 py-2 border rounded-md text-sm text-lia-text-primary dark:text-lia-text-disabled dark:bg-lia-btn-primary-hover placeholder-lia-text-tertiary focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg focus:border-transparent ${
 formErrors.email ? "border-status-error/30" : "border-lia-border-subtle dark:border-lia-border-medium"
 }`}
 placeholder="seu@email.com"
 />
 {formErrors.email && (
 <p className="text-xs text-status-error mt-1">{formErrors.email}</p>
 )}
 </div>

 <div>
 <label className="block text-sm font-medium text-lia-text-primary dark:text-lia-text-disabled mb-1">
 Telefone / WhatsApp *
 </label>
 <input
 type="tel"
 value={form.phone}
 onChange={(e) => setForm(prev => ({ ...prev, phone: e.target.value }))}
 className={`w-full px-3 py-2 border rounded-md text-sm text-lia-text-primary dark:text-lia-text-disabled dark:bg-lia-btn-primary-hover placeholder-lia-text-tertiary focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg focus:border-transparent ${
 formErrors.phone ? "border-status-error/30" : "border-lia-border-subtle dark:border-lia-border-medium"
 }`}
 placeholder="+55 (11) 99999-9999"
 />
 {formErrors.phone && (
 <p className="text-xs text-status-error mt-1">{formErrors.phone}</p>
 )}
 </div>

 <div>
 <label className="block text-sm font-medium text-lia-text-primary dark:text-lia-text-disabled mb-1">
 Currículo (PDF ou DOC) *
 </label>
 <input
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
 onClick={() => fileInputRef.current?.click()}
 className={`w-full px-3 py-4 border-2 border-dashed rounded-md text-center cursor-pointer transition-colors motion-reduce:transition-none hover:border-lia-border-medium dark:hover:border-lia-border-medium hover:bg-lia-bg-secondary dark:hover:bg-lia-bg-inverse ${
 formErrors.cvFile ? "border-status-error/30" : form.cvFile ? "border-lia-border-medium dark:border-lia-border-medium bg-lia-bg-secondary dark:bg-lia-bg-inverse" : "border-lia-border-subtle dark:border-lia-border-medium"
 }`}
 >
 {form.cvFile ? (
 <div className="flex items-center justify-center gap-2 text-sm text-lia-text-primary dark:text-lia-text-disabled">
 <FileText className="w-4 h-4" />
 <span>{form.cvFile.name}</span>
 <button
 onClick={(e) => {
 e.stopPropagation()
 setForm(prev => ({ ...prev, cvFile: null }))
 if (fileInputRef.current) fileInputRef.current.value = ""
 }}
 className="text-lia-text-tertiary dark:text-lia-text-secondary hover:text-lia-text-secondary dark:hover:text-lia-text-disabled ml-1"
 >
 <X className="w-4 h-4" />
 </button>
 </div>
 ) : (
 <div className="flex flex-col items-center gap-1">
 <Upload className="w-5 h-5 text-lia-text-tertiary dark:text-lia-text-secondary" />
 <span className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">
 Clique para enviar seu currículo
 </span>
 <span className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary">PDF ou DOC, até 10MB</span>
 </div>
 )}
 </div>
 {formErrors.cvFile && (
 <p className="text-xs text-status-error mt-1">{formErrors.cvFile}</p>
 )}
 </div>

 <div className="pt-2">
 <label className="flex items-start gap-3 cursor-pointer">
 <input
 type="checkbox"
 checked={form.lgpdConsent}
 onChange={(e) => setForm(prev => ({ ...prev, lgpdConsent: e.target.checked }))}
 className="mt-0.5 h-4 w-4 rounded-md border-lia-border-default dark:border-lia-border-medium text-lia-text-primary focus:ring-lia-btn-primary-bg"
 />
 <span className={`text-xs leading-relaxed ${formErrors.lgpdConsent ? "text-status-error" : "text-lia-text-secondary dark:text-lia-text-tertiary"}`}>
 Autorizo a coleta e tratamento dos meus dados pessoais para fins deste processo seletivo, 
 conforme a Lei Geral de Proteção de Dados (LGPD). Entendo que posso solicitar a exclusão 
 dos meus dados a qualquer momento. *
 </span>
 </label>
 {formErrors.lgpdConsent && (
 <p className="text-xs text-status-error mt-1">{formErrors.lgpdConsent}</p>
 )}
 </div>

 <div className="pt-4">
 <Button
 size="lg"
 className="w-full bg-lia-btn-primary-bg dark:bg-lia-bg-inverse text-white hover:bg-lia-btn-primary-hover dark:hover:bg-lia-border-medium font-medium"
 onClick={handleSubmitApplication}
 disabled={submitting}
 >
 {submitting ? (
 <>
 <Loader2 className="w-5 h-5 mr-2 animate-spin motion-reduce:animate-none" />
 Enviando candidatura...
 </>
 ) : (
 <>
 <Send className="w-5 h-5 mr-2" />
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

 <section className="text-center">
 <div className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl p-6 bg-lia-bg-secondary/50 dark:bg-lia-bg-secondary">
 <div className="flex items-center justify-center gap-2 mb-3">
 <Shield className="w-4 h-4 text-lia-text-tertiary dark:text-lia-text-secondary" />
 <h4 className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">
 Privacidade e Proteção de Dados
 </h4>
 </div>
 <p className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary leading-relaxed max-w-lg mx-auto mb-2">
 Este processo seletivo utiliza inteligência artificial (LIA) para auxiliar na triagem. 
 Seus dados são tratados conforme a LGPD. Ao se candidatar, você autoriza a coleta 
 e análise dos seus dados para fins deste processo.
 </p>
 <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary">
 <a href="/privacidade" className="hover:text-lia-text-secondary dark:hover:text-lia-text-disabled underline">
 Política de Privacidade
 </a>
 {" · "}
 <a href="mailto:dpo@wedotalent.com" className="hover:text-lia-text-secondary dark:hover:text-lia-text-disabled">
 dpo@wedotalent.com
 </a>
 </p>
 </div>
 </section>

 <footer className="text-center mt-12 pt-8 border-t border-lia-border-subtle dark:border-lia-border-subtle">
 <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary">
 Powered by{" "}
 <span className="font-medium text-lia-text-secondary dark:text-lia-text-tertiary">WeDOTalent</span>
 </p>
 </footer>
 </div>
 </div>
 )
}
