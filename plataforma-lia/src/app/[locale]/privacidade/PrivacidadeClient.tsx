"use client"

import React, { useState } from"react"
import Link from"next/link"
import { Shield, Eye, Edit, Trash2, ArrowRightLeft, XCircle, FileSearch, Send, Loader2, CheckCircle2, AlertCircle, Clock, Search, User, Mail, Phone, FileText, ChevronRight, Bot, Scale, Info, ChevronDown, ChevronUp } from"lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from"@/components/ui/card"
import { Button } from"@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import { Input } from"@/components/ui/input"
import { Label } from"@/components/ui/label"
import { Textarea } from"@/components/ui/textarea"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from"@/components/ui/select"

const REQUEST_TYPES = [
  { value: 'access', label: 'Acesso aos meus dados', description: 'Obter cópia dos dados pessoais tratados', icon: Eye },
  { value: 'correction', label: 'Correção de dados', description: 'Corrigir dados incompletos ou incorretos', icon: Edit },
  { value: 'deletion', label: 'Exclusão de dados', description: 'Solicitar a eliminação dos dados pessoais', icon: Trash2 },
  { value: 'portability', label: 'Portabilidade', description: 'Transferir dados para outro serviço', icon: ArrowRightLeft },
  { value: 'explanation', label: 'Revisão de decisão por IA', description: 'Contestar triagem automatizada e solicitar revisão humana (LGPD Art. 20)', icon: FileSearch },
]

const STATUS_CONFIG: Record<string, { label: string, color: string, icon: typeof Clock }> = {
  'pending': { label: 'Aguardando Análise', color: 'amber', icon: Clock },
  'in_review': { label: 'Em Revisão', color: 'cyan', icon: FileSearch },
  'processing': { label: 'Em Processamento', color: 'cyan', icon: Loader2 },
  'completed': { label: 'Concluído', color: 'emerald', icon: CheckCircle2 },
  'rejected': { label: 'Não Aprovado', color: 'red', icon: XCircle },
  'cancelled': { label: 'Cancelado', color: 'gray', icon: XCircle },
}


interface TrackingResult {
  id?: string
  status?: string
  request_type?: string
  created_at?: string
  deadline_at?: string
  completed_at?: string
  response?: string
  [key: string]: unknown
}


export default function PrivacidadePage() {
  const [activeTab, setActiveTab] = useState<'request' | 'track'>('request')
  const [requestType, setRequestType] = useState("")
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [cpf, setCpf] = useState("")
  const [phone, setPhone] = useState("")
  const [description, setDescription] = useState("")
  const [submitting, setSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [submittedId, setSubmittedId] = useState("")
  const [error, setError] = useState("")

  const [trackingId, setTrackingId] = useState("")
  const [tracking, setTracking] = useState(false)
  const [trackingResult, setTrackingResult] = useState<TrackingResult | null>(null)
  const [trackingError, setTrackingError] = useState("")

  const [art20Expanded, setArt20Expanded] = useState(false)

  const formatCpf = (value: string) => {
    const numbers = value.replace(/\D/g, '')
    if (numbers.length <= 3) return numbers
    if (numbers.length <= 6) return `${numbers.slice(0, 3)}.${numbers.slice(3)}`
    if (numbers.length <= 9) return `${numbers.slice(0, 3)}.${numbers.slice(3, 6)}.${numbers.slice(6)}`
    return `${numbers.slice(0, 3)}.${numbers.slice(3, 6)}.${numbers.slice(6, 9)}-${numbers.slice(9, 11)}`
  }

  const formatPhone = (value: string) => {
    const numbers = value.replace(/\D/g, '')
    if (numbers.length <= 2) return `(${numbers}`
    if (numbers.length <= 7) return `(${numbers.slice(0, 2)}) ${numbers.slice(2)}`
    return `(${numbers.slice(0, 2)}) ${numbers.slice(2, 7)}-${numbers.slice(7, 11)}`
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setSubmitting(true)

    try {
      const response = await fetch('/api/backend-proxy/data-subject-requests', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          request_type: requestType,
          requester_name: name,
          requester_email: email,
          requester_cpf: cpf.replace(/\D/g, ''),
          requester_phone: phone.replace(/\D/g, ''),
          description: description,
        })
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.error || 'Erro ao enviar solicitação')
      }

      const data = await response.json()
      setSubmittedId(data.id)
      setSubmitted(true)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err) || 'Erro ao enviar solicitação. Tente novamente.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleTrack = async (e: React.FormEvent) => {
    e.preventDefault()
    setTrackingError("")
    setTrackingResult(null)
    setTracking(true)

    try {
      const response = await fetch(`/api/backend-proxy/data-subject-requests/track/${trackingId}`)
      
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Solicitação não encontrada. Verifique o código informado.')
        }
        throw new Error('Erro ao consultar solicitação')
      }

      const data = await response.json()
      setTrackingResult(data)
    } catch (err: unknown) {
      setTrackingError(err instanceof Error ? err.message : String(err) || 'Erro ao consultar solicitação')
    } finally {
      setTracking(false)
    }
  }

  const resetForm = () => {
    setSubmitted(false)
    setSubmittedId("")
    setRequestType("")
    setName("")
    setEmail("")
    setCpf("")
    setPhone("")
    setDescription("")
  }

  const getStatusDisplay = (status: string) => {
    const config = STATUS_CONFIG[status]
    if (!config) return { label: status, color: 'gray', icon: Clock }
    return config
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-lia-bg-secondary to-white">
      <header className="bg-lia-bg-primary">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-md flex items-center justify-center bg-lia-interactive-active/30">
              <Shield className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-lia-text-primary dark:text-lia-text-primary">Portal de Privacidade</h1>
              <p className="text-xs text-lia-text-secondary">Seus dados, seus direitos</p>
            </div>
          </div>
          <div className="flex gap-2 flex-wrap">
            <Chip variant="neutral" muted className="bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary dark:text-lia-text-tertiary border-lia-border-default dark:border-lia-border-default">
              LGPD Art. 18
            </Chip>
            <Chip variant="neutral" muted className="bg-wedo-cyan/10 text-wedo-cyan-dark border-wedo-cyan/30">
              Art. 20 — IA
            </Chip>
          </div>
        </div>
      </header>

      <main id="main-content" className="max-w-4xl mx-auto px-4 py-8">
        <div className="text-center mb-8">
          <h2 className="text-2xl font-semibold text-lia-text-primary dark:text-lia-text-primary mb-2">
            Exercite seus Direitos de Privacidade
          </h2>
          <p className="text-lia-text-secondary max-w-2xl mx-auto">
            Conforme a Lei Geral de Proteção de Dados (LGPD), você tem o direito de saber 
            como seus dados pessoais são tratados e solicitar ações sobre eles.
          </p>
        </div>

        <div className="mb-8 rounded-xl border-2 border-wedo-cyan/30 bg-wedo-cyan/5 overflow-hidden">
          <div className="p-5">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-xl flex items-center justify-center bg-wedo-cyan/15 flex-shrink-0">
                <Bot className="w-6 h-6 text-wedo-cyan-dark" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap mb-1">
                  <h3 className="font-semibold text-lia-text-primary dark:text-lia-text-primary">
                    Direito à Revisão de Decisão Automatizada
                  </h3>
                  <Chip variant="neutral" muted className="bg-wedo-cyan/10 text-wedo-cyan-dark border-wedo-cyan/30 text-xs">
                    LGPD Art. 20
                  </Chip>
                  <Chip variant="neutral" muted className="bg-wedo-cyan/10 text-wedo-cyan-dark border-wedo-cyan/30 text-xs">
                    EU AI Act
                  </Chip>
                </div>
                <p className="text-sm text-lia-text-secondary">
                  Se você foi eliminado de um processo seletivo por triagem automatizada de IA, a lei garante seu direito de contestar essa decisão e solicitar revisão humana.
                </p>

                <div className="mt-4 flex flex-col sm:flex-row gap-3">
                  <Button
                    className="bg-wedo-cyan-dark hover:bg-wedo-cyan text-white"
                    onClick={() => {
                      setRequestType('explanation')
                      setActiveTab('request')
                    }}
                  >
                    <Scale className="w-4 h-4 mr-2" />
                    Solicitar Revisão da Decisão
                  </Button>
                  <Button
                    variant="outline"
                    className="border-wedo-cyan/40 text-wedo-cyan-dark hover:bg-wedo-cyan/10"
                    onClick={() => setArt20Expanded((v) => !v)}
                  >
                    <Info className="w-4 h-4 mr-2" />
                    {art20Expanded ? 'Ocultar detalhes' : 'Ver seus direitos completos'}
                    {art20Expanded ? <ChevronUp className="w-4 h-4 ml-2" /> : <ChevronDown className="w-4 h-4 ml-2" />}
                  </Button>
                </div>
              </div>
            </div>
          </div>

          {art20Expanded && (
            <div className="border-t border-wedo-cyan/20 bg-wedo-cyan/5 p-5 space-y-5">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="rounded-xl border border-wedo-cyan/20 bg-lia-bg-primary p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Scale className="w-4 h-4 text-wedo-cyan-dark flex-shrink-0" />
                    <h4 className="font-medium text-sm text-lia-text-primary dark:text-lia-text-primary">
                      LGPD — Art. 20
                    </h4>
                  </div>
                  <p className="text-xs text-lia-text-secondary leading-relaxed mb-3">
                    O titular dos dados tem direito a solicitar revisão de decisões tomadas unicamente com base em tratamento automatizado, incluindo decisões que afetem seus interesses profissionais ou em processos seletivos.
                  </p>
                  <ul className="space-y-1.5">
                    {[
                      'Solicitar revisão humana da triagem automatizada',
                      'Obter explicação sobre os critérios e procedimentos utilizados',
                      'Contestar decisões que afetam sua candidatura',
                      'Receber resposta fundamentada em até 15 dias úteis',
                    ].map((right) => (
                      <li key={right} className="flex items-start gap-2 text-xs text-lia-text-secondary">
                        <CheckCircle2 className="w-3.5 h-3.5 text-wedo-cyan-dark flex-shrink-0 mt-0.5" />
                        {right}
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="rounded-xl border border-wedo-cyan/20 bg-lia-bg-primary p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Shield className="w-4 h-4 text-wedo-cyan-dark flex-shrink-0" />
                    <h4 className="font-medium text-sm text-lia-text-primary dark:text-lia-text-primary">
                      EU AI Act — Transparência
                    </h4>
                  </div>
                  <p className="text-xs text-lia-text-secondary leading-relaxed mb-3">
                    O Regulamento Europeu de Inteligência Artificial classifica sistemas de IA utilizados em recrutamento como de alto risco, impondo obrigações adicionais de transparência e supervisão humana.
                  </p>
                  <ul className="space-y-1.5">
                    {[
                      'Ser informado quando uma decisão é tomada por IA',
                      'Receber explicação sobre o funcionamento do sistema',
                      'Supervisão humana obrigatória em decisões de alto impacto',
                      'Registro e auditabilidade das decisões automatizadas',
                    ].map((right) => (
                      <li key={right} className="flex items-start gap-2 text-xs text-lia-text-secondary">
                        <CheckCircle2 className="w-3.5 h-3.5 text-wedo-cyan-dark flex-shrink-0 mt-0.5" />
                        {right}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              <div className="rounded-xl border border-wedo-cyan/20 bg-lia-bg-primary p-4">
                <h4 className="font-medium text-sm text-lia-text-primary dark:text-lia-text-primary mb-3 flex items-center gap-2">
                  <FileSearch className="w-4 h-4 text-wedo-cyan-dark" />
                  Como funciona o processo de revisão
                </h4>
                <ol className="space-y-2">
                  {[
                    { step: '1', text: 'Preencha o formulário abaixo selecionando "Explicação de decisão" como tipo de solicitação.' },
                    { step: '2', text: 'Informe o nome da vaga ou empresa para qual se candidatou e descreva sua solicitação.' },
                    { step: '3', text: 'Você receberá um código de acompanhamento por e-mail.' },
                    { step: '4', text: 'Um revisor humano analisará sua candidatura e os critérios de triagem aplicados.' },
                    { step: '5', text: 'Receberá uma resposta fundamentada em até 15 dias úteis, conforme exigido pela LGPD Art. 18, §3º.' },
                  ].map(({ step, text }) => (
                    <li key={step} className="flex items-start gap-3 text-xs text-lia-text-secondary">
                      <span className="w-5 h-5 rounded-full bg-wedo-cyan/20 text-wedo-cyan-dark font-semibold flex items-center justify-center flex-shrink-0 text-xs">
                        {step}
                      </span>
                      {text}
                    </li>
                  ))}
                </ol>
              </div>

              <p className="text-xs text-lia-text-tertiary text-center">
                Base legal: LGPD Lei nº 13.709/2018, Art. 20 · EU AI Act Regulamento (UE) 2024/1689, Art. 86 · ANPD Resolução CD/ANPD nº 15/2024
              </p>
            </div>
          )}
        </div>

        <div className="flex gap-2 mb-6 justify-center">
          <Button
            variant={activeTab ==="request" ?"primary" :"outline"}
            onClick={() => setActiveTab('request')}
            className={activeTab === 'request' ? 'bg-lia-btn-primary-bg text-lia-btn-primary-text dark:bg-lia-bg-secondary dark:text-lia-text-primary hover:bg-lia-btn-primary-hover dark:hover:bg-lia-interactive-active' : ''}
          >
            <Send className="w-4 h-4 mr-2" />
            Nova Solicitação
          </Button>
          <Button
            variant={activeTab ==="track" ?"primary" :"outline"}
            onClick={() => setActiveTab('track')}
            className={activeTab === 'track' ? 'bg-lia-btn-primary-bg text-lia-btn-primary-text dark:bg-lia-bg-secondary dark:text-lia-text-primary hover:bg-lia-btn-primary-hover dark:hover:bg-lia-interactive-active' : ''}
          >
            <Search className="w-4 h-4 mr-2" />
            Acompanhar Solicitação
          </Button>
        </div>

        {activeTab === 'request' && (
          <>
            {submitted ? (
              <Card className="border-status-success/30 bg-status-success/10">
                <CardContent className="pt-6">
                  <div className="text-center">
                    <div className="w-16 h-16 rounded-full bg-status-success/15 flex items-center justify-center mx-auto mb-4">
                      <CheckCircle2 className="w-8 h-8 text-status-success" />
                    </div>
                    <h3 className="text-xl font-semibold text-status-success mb-2">
                      Solicitação Enviada com Sucesso!
                    </h3>
                    <p className="text-status-success mb-4">
                      Sua solicitação foi registrada e será analisada em até 15 dias úteis.
                    </p>
                    <div className="bg-lia-bg-primary rounded-xl p-4 inline-block mb-4">
                      <p className="text-sm text-lia-text-secondary mb-1">Código de Acompanhamento:</p>
                      <p className="text-2xl font-mono font-semibold text-lia-text-primary dark:text-lia-text-primary">{submittedId}</p>
                    </div>
                    <p className="text-sm text-status-success mb-6">
                      Guarde este código para acompanhar o status da sua solicitação.
                    </p>
                    <div className="flex gap-3 justify-center">
                      <Button variant="outline" onClick={resetForm}>
                        Nova Solicitação
                      </Button>
                      <Button 
                        className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:bg-lia-bg-secondary dark:text-lia-text-primary dark:hover:bg-lia-interactive-active"
                        onClick={() => {
                          setTrackingId(submittedId)
                          setActiveTab('track')
                        }}
                      >
                        Acompanhar Status
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Nova Solicitação de Direito</CardTitle>
                  <CardDescription>
                    Preencha o formulário abaixo para exercer seus direitos previstos na LGPD
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleSubmit} className="space-y-6">
                    <div className="space-y-3">
                      <Label>Tipo de Solicitação *</Label>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {REQUEST_TYPES.map((type) => {
                          const Icon = type.icon
                          return (
                            <div
                              key={type.value}
                              className={`p-4 rounded-md border-2 cursor-pointer transition-colors motion-reduce:transition-none ${
                                requestType === type.value
                                  ? 'border-lia-btn-primary-bg dark:border-lia-border-subtle bg-lia-bg-secondary dark:bg-lia-bg-secondary/50'
                                  : 'border-lia-border-subtle hover:border-lia-border-default'
                              }`}
                              onClick={() => setRequestType(type.value)}
                            >
                              <div className="flex items-start gap-3">
                                <div className={`w-10 h-10 rounded-md flex items-center justify-center ${
                                  requestType === type.value ? 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary' : 'bg-lia-bg-tertiary'
                                }`}>
                                  <Icon className={`w-5 h-5 ${
                                    requestType === type.value ? 'text-lia-text-secondary dark:text-lia-text-tertiary' : 'text-lia-text-secondary'
                                  }`} />
                                </div>
                                <div>
                                  <p className={`font-medium ${
 requestType === type.value ? 'text-lia-text-secondary' : 'text-lia-text-primary dark:text-lia-text-primary'
                                  }`}>
                                    {type.label}
                                  </p>
                                  <p className="text-xs text-lia-text-secondary">{type.description}</p>
                                </div>
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="name">Nome Completo *</Label>
                        <div className="relative">
                          <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-lia-text-tertiary" />
                          <Input
                            id="name"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            placeholder="Seu nome completo"
                            className="pl-10"
                            required
                          />
                        </div>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="email">E-mail *</Label>
                        <div className="relative">
                          <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-lia-text-tertiary" />
                          <Input
                            id="email"
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="seu@email.com"
                            className="pl-10"
                            required
                          />
                        </div>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="cpf">CPF *</Label>
                        <Input
                          id="cpf"
                          value={cpf}
                          onChange={(e) => setCpf(formatCpf(e.target.value))}
                          placeholder="000.000.000-00"
                          maxLength={14}
                          required
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="phone">Telefone</Label>
                        <div className="relative">
                          <Phone className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-lia-text-tertiary" />
                          <Input
                            id="phone"
                            value={phone}
                            onChange={(e) => setPhone(formatPhone(e.target.value))}
                            placeholder="(00) 00000-0000"
                            className="pl-10"
                            maxLength={15}
                          />
                        </div>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="description">Descrição da Solicitação</Label>
                      <Textarea
                        id="description"
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        placeholder="Descreva detalhes adicionais sobre sua solicitação (opcional)"
                        rows={4}
                      />
                    </div>

                    {error && (
                      <div className="p-4 rounded-xl bg-status-error/10 border border-status-error/30 flex items-start gap-3">
                        <AlertCircle className="w-5 h-5 text-status-error flex-shrink-0 mt-0.5" />
                        <p className="text-sm text-status-error">{error}</p>
                      </div>
                    )}

                    <div className="flex justify-end">
                      <Button 
                        type="submit" 
                        className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:bg-lia-bg-secondary dark:text-lia-text-primary dark:hover:bg-lia-interactive-active"
                        disabled={submitting || !requestType || !name || !email || !cpf}
                      >
                        {submitting ? (
                          <>
                            <Loader2 className="w-4 h-4 mr-2 animate-spin motion-reduce:animate-none" />
                            Enviando...
                          </>
                        ) : (
                          <>
                            <Send className="w-4 h-4 mr-2" />
                            Enviar Solicitação
                          </>
                        )}
                      </Button>
                    </div>
                  </form>
                </CardContent>
              </Card>
            )}
          </>
        )}

        {activeTab === 'track' && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Acompanhar Solicitação</CardTitle>
                <CardDescription>
                  Informe o código de acompanhamento recebido ao enviar sua solicitação
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleTrack} className="flex gap-3">
                  <div className="flex-1">
                    <Input
                      value={trackingId}
                      onChange={(e) => setTrackingId(e.target.value)}
                      placeholder="Digite o código de acompanhamento"
                      className="text-lg"
                    />
                  </div>
                  <Button 
                    type="submit" 
                    className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:bg-lia-bg-secondary dark:text-lia-text-primary dark:hover:bg-lia-interactive-active"
                    disabled={tracking || !trackingId}
                  >
                    {tracking ? (
                      <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none" />
                    ) : (
                      <>
                        <Search className="w-4 h-4 mr-2" />
                        Consultar
                      </>
                    )}
                  </Button>
                </form>
              </CardContent>
            </Card>

            {trackingError && (
              <Card className="border-status-error/30 bg-status-error/10">
                <CardContent className="pt-6">
                  <div className="flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-status-error flex-shrink-0" />
                    <p className="text-status-error">{trackingError}</p>
                  </div>
                </CardContent>
              </Card>
            )}

            {trackingResult && (
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-lg">Status da Solicitação</CardTitle>
                      <CardDescription>Código: {trackingResult.id}</CardDescription>
                    </div>
                    {(() => {
                      const status = getStatusDisplay(trackingResult.status ?? '')
                      const Icon = status.icon
                      const colorClasses: Record<string, string> = {
                        'amber': '',
                        'cyan': 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-primary dark:text-lia-text-primary',
                        'emerald': '',
                        'red': '',
                        'gray': 'bg-lia-bg-tertiary text-lia-text-primary dark:text-lia-text-primary',
                      }
                      return (
                        <Chip variant="neutral" muted className={colorClasses[status.color]}>
                          <Icon className="w-3 h-3 mr-1" />
                          {status.label}
                        </Chip>
                      )
                    })()}
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-xs text-lia-text-secondary mb-1">Tipo de Solicitação</p>
                        <p className="font-medium">
                          {REQUEST_TYPES.find(t => t.value === trackingResult.request_type)?.label || trackingResult.request_type}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-lia-text-secondary mb-1">Data da Solicitação</p>
                        <p className="font-medium">
                          {new Date(trackingResult.created_at as string).toLocaleDateString('pt-BR')}
                        </p>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-xs text-lia-text-secondary mb-1">Prazo para Resposta</p>
                        <p className="font-medium">
                          {new Date(trackingResult.deadline_at as string).toLocaleDateString('pt-BR')}
                        </p>
                      </div>
                      {trackingResult.completed_at && (
                        <div>
                          <p className="text-xs text-lia-text-secondary mb-1">Data de Conclusão</p>
                          <p className="font-medium text-status-success">
                            {new Date(trackingResult.completed_at).toLocaleDateString('pt-BR')}
                          </p>
                        </div>
                      )}
                    </div>

                    {trackingResult.response && (
                      <div className="mt-4 p-4 bg-status-success/10 rounded-xl border border-status-success/30">
                        <p className="text-xs text-status-success mb-2 font-medium">Resposta:</p>
                        <p className="text-sm text-status-success">{trackingResult.response}</p>
                      </div>
                    )}

                    <div className="mt-4 p-4 bg-lia-bg-secondary rounded-xl">
                      <div className="flex items-start gap-3">
                        <Clock className="w-5 h-5 text-lia-text-tertiary flex-shrink-0 mt-0.5" />
                        <div>
                          <p className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">Acompanhamento</p>
                          <p className="text-xs text-lia-text-secondary mt-1">
                            Sua solicitação será respondida em até 15 dias úteis conforme previsto na LGPD (Art. 18, §3º).
                            Você receberá atualizações por e-mail.
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        )}

        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="bg-lia-bg-secondary">
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-lia-bg-tertiary dark:bg-lia-bg-secondary">
                  <Shield className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
                </div>
                <div>
                  <h3 className="font-medium text-lia-text-primary dark:text-lia-text-primary">Seus Dados Protegidos</h3>
                  <p className="text-xs text-lia-text-secondary mt-1">
                    Tratamos seus dados com segurança e transparência
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="bg-lia-bg-secondary">
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-lia-bg-tertiary dark:bg-lia-bg-secondary">
                  <Clock className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
                </div>
                <div>
                  <h3 className="font-medium text-lia-text-primary dark:text-lia-text-primary">Prazo de 15 Dias</h3>
                  <p className="text-xs text-lia-text-secondary mt-1">
                    Respondemos sua solicitação no prazo legal
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="bg-lia-bg-secondary">
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-lia-bg-tertiary dark:bg-lia-bg-secondary">
                  <FileSearch className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
                </div>
                <div>
                  <h3 className="font-medium text-lia-text-primary dark:text-lia-text-primary">Acompanhamento</h3>
                  <p className="text-xs text-lia-text-secondary mt-1">
                    Consulte o status da sua solicitação a qualquer momento
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="mt-8 text-center text-sm text-lia-text-secondary">
          <p>
            Este portal é disponibilizado em conformidade com a{' '}
            <a href="https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm" target="_blank" rel="noopener noreferrer" className="text-lia-text-secondary dark:text-lia-text-tertiary hover:underline">
              Lei nº 13.709/2018 (LGPD)
            </a>
          </p>
          <p className="mt-2">
            Em caso de dúvidas, entre em contato com nosso DPO através do e-mail{' '}
            <a href="mailto:dpo@wedotalent.com.br" className="text-lia-text-secondary dark:text-lia-text-tertiary hover:underline">
              dpo@wedotalent.com.br
            </a>
          </p>
        </div>
      </main>
    </div>
  )
}
