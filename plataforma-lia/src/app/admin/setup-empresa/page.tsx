"use client"

import React from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog"
import {
  Building2,
  Users,
  Gift,
  Heart,
  Upload,
  Plus,
  Brain,
  FileSpreadsheet,
  Loader2,
  Linkedin,
  Globe,
  MapPin,
  Building,
  Save,
  Star,
  CheckCircle,
} from "lucide-react"

import { useSetupEmpresa } from "./useSetupEmpresa"
import {
  BENEFIT_CATEGORIES,
  SENIORITY_LEVELS,
  VALUE_TYPES,
  WAITING_PERIODS,
  defaultBenefit,
} from "./setup-empresa.constants"
import { BenefitsContent } from "./components/BenefitsContent"

export default function SetupEmpresaPage() {
  const {
    mounted,
    activeTab,
    setActiveTab,
    benefits,
    isLoading,
    isSaving,
    showBenefitModal,
    setShowBenefitModal,
    editingBenefit,
    setEditingBenefit,
    expandedCategories,
    showImportModal,
    setShowImportModal,
    importFile,
    setImportFile,
    isImporting,
    companyProfile,
    setCompanyProfile,
    showTemplateModal,
    setShowTemplateModal,
    isEnriching,
    enrichmentError,
    isSavingProfile,
    isGeneratingEvp,
    evpData,
    evpError,
    handleEnrichProfile,
    handleSaveProfile,
    handleGenerateEvp,
    handleSaveBenefit,
    handleDeleteBenefit,
    handleToggleBenefitStatus,
    handleImportFile,
    toggleCategory,
  } = useSetupEmpresa()

  if (!mounted) {
    return (
      <div className="p-8" suppressHydrationWarning>
        <div className="mb-8">
          <h1 className="text-3xl font-semibold mb-2 text-lia-text-primary dark:text-lia-text-primary">
            Setup Empresa
          </h1>
          <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">
            Configure as informações da empresa, departamentos, benefícios e cultura organizacional
          </p>
        </div>
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin motion-reduce:animate-none text-lia-text-tertiary" />
        </div>
      </div>
    )
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-semibold mb-2 text-lia-text-primary dark:text-lia-text-primary">
          Setup Empresa
        </h1>
        <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">
          Configure as informações da empresa, departamentos, benefícios e cultura organizacional
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="mb-6">
          <TabsTrigger value="profile" className="gap-2">
            <Building2 className="w-4 h-4" />
            Perfil
          </TabsTrigger>
          <TabsTrigger value="departments" className="gap-2">
            <Users className="w-4 h-4" />
            Departamentos
          </TabsTrigger>
          <TabsTrigger value="benefits" className="gap-2">
            <Gift className="w-4 h-4" />
            Benefícios
          </TabsTrigger>
          <TabsTrigger value="culture" className="gap-2">
            <Heart className="w-4 h-4" />
            Cultura
          </TabsTrigger>
        </TabsList>

        {/* ── Profile Tab ── */}
        {activeTab === "profile" && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Perfil da Empresa</CardTitle>
                    <CardDescription>Informações gerais da organização</CardDescription>
                  </div>
                  <Button onClick={handleSaveProfile} disabled={isSavingProfile} className="gap-2 bg-lia-btn-primary-hover">
                    {isSavingProfile ? (
                      <><Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none" />Salvando...</>
                    ) : (
                      <><Save className="w-4 h-4" />Salvar Perfil</>
                    )}
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Nome da Empresa *</Label>
                    <Input value={companyProfile.name} onChange={(e) => setCompanyProfile({ ...companyProfile, name: e.target.value })} placeholder="Ex: WeDo Talent" />
                  </div>
                  <div className="space-y-2">
                    <Label>Nome Fantasia</Label>
                    <Input value={companyProfile.trading_name || ""} onChange={(e) => setCompanyProfile({ ...companyProfile, trading_name: e.target.value })} placeholder="Ex: WeDo" />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>CNPJ</Label>
                    <Input value={companyProfile.cnpj || ""} onChange={(e) => setCompanyProfile({ ...companyProfile, cnpj: e.target.value })} placeholder="00.000.000/0000-00" />
                  </div>
                  <div className="space-y-2">
                    <Label className="flex items-center gap-2"><Globe className="w-4 h-4 text-lia-text-secondary" />Website</Label>
                    <Input value={companyProfile.website || ""} onChange={(e) => setCompanyProfile({ ...companyProfile, website: e.target.value })} placeholder="https://www.empresa.com.br" />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Setor/Indústria</Label>
                    <Input value={companyProfile.industry || ""} onChange={(e) => setCompanyProfile({ ...companyProfile, industry: e.target.value })} placeholder="Ex: Tecnologia, Varejo, Saúde" />
                  </div>
                  <div className="space-y-2">
                    <Label className="flex items-center gap-2"><Building className="w-4 h-4 text-lia-text-secondary" />Porte da Empresa</Label>
                    <Select value={companyProfile.company_size || ""} onValueChange={(value) => setCompanyProfile({ ...companyProfile, company_size: value })}>
                      <SelectTrigger><SelectValue placeholder="Selecione o porte" /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="1-10">1-10 funcionários</SelectItem>
                        <SelectItem value="11-50">11-50 funcionários</SelectItem>
                        <SelectItem value="51-200">51-200 funcionários</SelectItem>
                        <SelectItem value="201-500">201-500 funcionários</SelectItem>
                        <SelectItem value="501-1000">501-1000 funcionários</SelectItem>
                        <SelectItem value="1001-5000">1001-5000 funcionários</SelectItem>
                        <SelectItem value="5001+">5001+ funcionários</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="flex items-center gap-2"><MapPin className="w-4 h-4 text-lia-text-secondary" />Cidade (Sede)</Label>
                    <Input value={companyProfile.headquarters_city || ""} onChange={(e) => setCompanyProfile({ ...companyProfile, headquarters_city: e.target.value })} placeholder="Ex: São Paulo" />
                  </div>
                  <div className="space-y-2">
                    <Label>Estado</Label>
                    <Input value={companyProfile.headquarters_state || ""} onChange={(e) => setCompanyProfile({ ...companyProfile, headquarters_state: e.target.value })} placeholder="Ex: SP" />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Descrição da Empresa</Label>
                  <Textarea value={companyProfile.description || ""} onChange={(e) => setCompanyProfile({ ...companyProfile, description: e.target.value })} placeholder="Descreva a empresa, seus produtos/serviços e diferenciais..." rows={4} />
                </div>
              </CardContent>
            </Card>

            {/* AI Enrichment */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2"><Brain className="w-5 h-5 text-wedo-cyan" />Enriquecimento com IA</CardTitle>
                <CardDescription>Preencha automaticamente os dados da empresa usando LinkedIn e Glassdoor</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex gap-4 items-end">
                  <div className="flex-1 space-y-2">
                    <Label className="flex items-center gap-2"><Linkedin className="w-4 h-4 text-brand-linkedin" />URL do LinkedIn da Empresa</Label>
                    <Input value={companyProfile.linkedin_url || ""} onChange={(e) => setCompanyProfile({ ...companyProfile, linkedin_url: e.target.value })} placeholder="https://www.linkedin.com/company/nome-da-empresa" />
                  </div>
                  <Button onClick={handleEnrichProfile} disabled={isEnriching || !companyProfile.linkedin_url} className="gap-2 h-10 bg-lia-btn-primary-bg">
                    {isEnriching ? (<><Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none" />Enriquecendo...</>) : (<><Brain className="w-4 h-4 text-wedo-cyan" />Enriquecer com IA</>)}
                  </Button>
                </div>
                {enrichmentError && (
                  <div className="bg-status-error/10 dark:bg-status-error/20 border border-status-error/30 dark:border-status-error/30 rounded-md p-3">
                    <p className="text-sm text-status-error dark:text-status-error">{enrichmentError}</p>
                  </div>
                )}
                <div className="bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-md p-4">
                  <div className="flex items-start gap-3">
                    <Brain className="w-5 h-5 text-wedo-cyan mt-0.5" />
                    <div>
                      <p className="text-sm font-medium text-lia-text-primary">A LIA irá buscar e preencher automaticamente:</p>
                      <ul className="text-xs text-lia-text-primary dark:text-lia-text-secondary mt-2 space-y-1">
                        <li>• Descrição e tagline da empresa</li>
                        <li>• Setor, porte e localização</li>
                        <li>• Missão, visão e valores (via Glassdoor)</li>
                        <li>• Avaliações e cultura organizacional</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Culture & Values */}
            <Card>
              <CardHeader>
                <CardTitle>Cultura e Valores</CardTitle>
                <CardDescription>Missão, visão e valores organizacionais</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Tagline / Slogan</Label>
                  <Input value={companyProfile.tagline || ""} onChange={(e) => setCompanyProfile({ ...companyProfile, tagline: e.target.value })} placeholder="Ex: Conectando talentos ao sucesso" />
                </div>
                <div className="space-y-2">
                  <Label>Missão</Label>
                  <Textarea value={companyProfile.mission || ""} onChange={(e) => setCompanyProfile({ ...companyProfile, mission: e.target.value })} placeholder="Qual é a razão de existir da empresa?" rows={3} />
                </div>
                <div className="space-y-2">
                  <Label>Visão</Label>
                  <Textarea value={companyProfile.vision || ""} onChange={(e) => setCompanyProfile({ ...companyProfile, vision: e.target.value })} placeholder="Onde a empresa quer chegar?" rows={3} />
                </div>
                <div className="space-y-2">
                  <Label>Valores</Label>
                  <Textarea value={companyProfile.values || ""} onChange={(e) => setCompanyProfile({ ...companyProfile, values: e.target.value })} placeholder="Quais são os valores que guiam a empresa?" rows={3} />
                </div>
              </CardContent>
            </Card>

            {/* EVP Insights */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2"><Star className="w-5 h-5 text-lia-text-primary" />EVP Insights</CardTitle>
                <CardDescription>Análise de Employee Value Proposition gerada por IA</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {evpError && (
                  <div className="bg-status-error/10 dark:bg-status-error/20 border border-status-error/30 dark:border-status-error/30 rounded-md p-3">
                    <p className="text-sm text-status-error dark:text-status-error">{evpError}</p>
                  </div>
                )}
                {!evpData ? (
                  <div className="text-center py-8">
                    <Star className="w-12 h-12 mx-auto mb-4 text-lia-text-disabled" />
                    <p className="text-sm mb-4 text-lia-text-secondary dark:text-lia-text-tertiary">Nenhuma análise EVP gerada ainda. Enriqueça o perfil com LinkedIn/Glassdoor ou clique para gerar manualmente.</p>
                    <Button onClick={() => handleGenerateEvp()} disabled={isGeneratingEvp || !companyProfile.id} className="gap-2 bg-lia-btn-primary-bg">
                      {isGeneratingEvp ? (<><Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none" />Gerando EVP...</>) : (<><Brain className="w-4 h-4 text-wedo-cyan" />Gerar EVP</>)}
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-6">
                    <div className="bg-gradient-to-r from-lia-bg-tertiary dark:from-lia-btn-primary-hover to-blue-50 dark:to-blue-900/20 rounded-md p-4 border border-lia-border-default">
                      <p className="text-lg font-medium text-lia-text-primary dark:text-lia-text-primary">&ldquo;{evpData.statement}&rdquo;</p>
                    </div>
                    <div>
                      <h4 className="font-medium mb-3 flex items-center gap-2 text-lia-text-primary dark:text-lia-text-primary"><Building2 className="w-4 h-4 text-lia-text-primary" />Pilares do EVP</h4>
                      <div className="grid gap-3">
                        {evpData.pillars.map((pillar, idx) => (
                          <div key={idx} className="bg-lia-bg-primary dark:bg-lia-bg-secondary border rounded-md p-4 border-lia-border-subtle dark:border-lia-border-subtle">
                            <div className="flex items-start gap-3">
                              <Badge className="shrink-0 bg-lia-btn-primary-bg text-lia-btn-primary-text">{pillar.name}</Badge>
                              <div className="flex-1">
                                <p className="text-sm mb-2 text-lia-text-primary dark:text-lia-text-primary">{pillar.description}</p>
                                <p className="text-xs italic text-lia-text-tertiary dark:text-lia-text-secondary">Evidência: {pillar.evidence}</p>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                    <div>
                      <h4 className="font-medium mb-3 flex items-center gap-2 text-lia-text-primary dark:text-lia-text-primary"><Heart className="w-4 h-4 text-lia-text-primary" />Tom de Comunicação</h4>
                      <div className="flex flex-wrap gap-2">
                        {evpData.tone_guidance.map((tone, idx) => (<Badge key={idx} variant="outline" className="border-lia-border-default">{tone}</Badge>))}
                      </div>
                    </div>
                    <div className="bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 rounded-md p-4">
                      <h4 className="font-medium mb-2 flex items-center gap-2 text-lia-text-primary dark:text-lia-text-primary"><Users className="w-4 h-4 text-lia-text-primary" />Promessa ao Candidato</h4>
                      <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">{evpData.candidate_promise}</p>
                    </div>
                    <div className="flex items-center justify-between pt-2 border-t border-lia-border-subtle dark:border-lia-border-subtle">
                      <div className="flex items-center gap-2 text-xs text-lia-text-tertiary dark:text-lia-text-secondary">
                        <span>Fontes: {evpData.sources.join(", ")}</span>
                        <span>•</span>
                        <span>Gerado em: {new Date(evpData.generated_at).toLocaleDateString("pt-BR")}</span>
                      </div>
                      <Button variant="outline" size="sm" onClick={() => handleGenerateEvp()} disabled={isGeneratingEvp} className="gap-2 border-lia-border-default">
                        {isGeneratingEvp ? (<Loader2 className="w-3 h-3 animate-spin motion-reduce:animate-none" />) : (<Brain className="w-3 h-3 text-wedo-cyan" />)}
                        Regenerar
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {/* ── Departments Tab ── */}
        {activeTab === "departments" && (
          <Card>
            <CardHeader>
              <CardTitle>Departamentos</CardTitle>
              <CardDescription>Estrutura organizacional</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-lia-text-secondary">Em construção...</p>
            </CardContent>
          </Card>
        )}

        {/* ── Benefits Tab ── */}
        {activeTab === "benefits" && (
          <BenefitsContent
            key={`benefits-${isLoading ? "loading" : "loaded"}-${benefits.length}`}
            isLoading={isLoading}
            benefits={benefits}
            expandedCategories={expandedCategories}
            showImportModal={showImportModal}
            setShowImportModal={setShowImportModal}
            setShowTemplateModal={setShowTemplateModal}
            setEditingBenefit={setEditingBenefit}
            setShowBenefitModal={setShowBenefitModal}
            toggleCategory={toggleCategory}
            handleToggleBenefitStatus={handleToggleBenefitStatus}
            handleDeleteBenefit={handleDeleteBenefit}
            defaultBenefit={defaultBenefit}
          />
        )}

        {/* ── Culture Tab ── */}
        {activeTab === "culture" && (
          <Card>
            <CardHeader>
              <CardTitle>Cultura Organizacional</CardTitle>
              <CardDescription>Valores e cultura da empresa</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-lia-text-secondary">Em construção...</p>
            </CardContent>
          </Card>
        )}
      </Tabs>

      {/* ── Benefit Modal ── */}
      <Dialog open={showBenefitModal} onOpenChange={setShowBenefitModal}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingBenefit?.id ? "Editar Benefício" : "Novo Benefício"}</DialogTitle>
            <DialogDescription>Configure os detalhes do benefício oferecido</DialogDescription>
          </DialogHeader>
          {editingBenefit && (
            <div className="space-y-6 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Nome do Benefício *</Label>
                  <Input value={editingBenefit.name} onChange={(e) => setEditingBenefit({ ...editingBenefit, name: e.target.value })} placeholder="Ex: Plano de Saúde Bradesco" />
                </div>
                <div className="space-y-2">
                  <Label>Categoria *</Label>
                  <Select value={editingBenefit.category} onValueChange={(value) => setEditingBenefit({ ...editingBenefit, category: value })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {BENEFIT_CATEGORIES.map((cat) => (
                        <SelectItem key={cat.id} value={cat.id}>
                          <div className="flex items-center gap-2"><cat.icon className={`w-4 h-4 ${cat.color}`} />{cat.name}</div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-2">
                <Label>Descrição</Label>
                <Textarea value={editingBenefit.description} onChange={(e) => setEditingBenefit({ ...editingBenefit, description: e.target.value })} placeholder="Descreva os detalhes do benefício..." rows={3} />
              </div>
              <div className="space-y-3">
                <Label>Tipo de Valor</Label>
                <div className="grid grid-cols-3 gap-3">
                  {VALUE_TYPES.map((type) => (
                    <div key={type.id} className={`p-3 rounded-md border cursor-pointer transition-colors ${editingBenefit.value_type === type.id ? "border-lia-border-default dark:border-lia-border-default bg-lia-bg-secondary dark:bg-lia-bg-primary" : "border-lia-border-subtle dark:border-lia-border-subtle hover:border-lia-border-default"}`} onClick={() => setEditingBenefit({ ...editingBenefit, value_type: type.id })}>
                      <div className="flex items-center gap-2 mb-1">
                        <type.icon className={`w-4 h-4 ${editingBenefit.value_type === type.id ? "text-lia-text-primary dark:text-lia-text-secondary" : "text-lia-text-secondary"}`} />
                        <span className="font-medium text-sm">{type.name}</span>
                      </div>
                      <p className="text-xs text-lia-text-secondary">{type.description}</p>
                    </div>
                  ))}
                </div>
              </div>
              {editingBenefit.value_type === "monetary" && (
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Valor (R$)</Label>
                    <Input type="number" value={editingBenefit.value || ""} onChange={(e) => setEditingBenefit({ ...editingBenefit, value: parseFloat(e.target.value) || undefined })} placeholder="0,00" />
                  </div>
                  <div className="space-y-2">
                    <Label>É desconto em folha?</Label>
                    <div className="flex items-center gap-2 pt-2">
                      <Switch checked={editingBenefit.is_discount} onCheckedChange={(checked: boolean) => setEditingBenefit({ ...editingBenefit, is_discount: checked })} />
                      <span className="text-sm text-lia-text-secondary">{editingBenefit.is_discount ? "Sim, desconto" : "Não, empresa custeia"}</span>
                    </div>
                  </div>
                </div>
              )}
              {editingBenefit.value_type === "percentage" && (
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Percentual (%)</Label>
                    <Input type="number" value={editingBenefit.percentage_value || ""} onChange={(e) => setEditingBenefit({ ...editingBenefit, percentage_value: parseFloat(e.target.value) || undefined })} placeholder="Ex: 5" />
                  </div>
                  <div className="space-y-2">
                    <Label>Detalhes adicionais</Label>
                    <Input value={editingBenefit.value_details || ""} onChange={(e) => setEditingBenefit({ ...editingBenefit, value_details: e.target.value })} placeholder="Ex: Contribuição sobre salário" />
                  </div>
                </div>
              )}
              {editingBenefit.value_type === "informative" && (
                <div className="space-y-2">
                  <Label>Detalhes</Label>
                  <Textarea value={editingBenefit.value_details || ""} onChange={(e) => setEditingBenefit({ ...editingBenefit, value_details: e.target.value })} placeholder="Descreva os detalhes do benefício..." rows={2} />
                </div>
              )}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Elegibilidade - Níveis</Label>
                  <Select value={editingBenefit.seniority_levels?.[0] || "all"} onValueChange={(value) => setEditingBenefit({ ...editingBenefit, seniority_levels: [value] })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {SENIORITY_LEVELS.map((level) => (<SelectItem key={level.id} value={level.id}>{level.name}</SelectItem>))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Carência</Label>
                  <Select value={String(editingBenefit.waiting_period_days)} onValueChange={(value) => setEditingBenefit({ ...editingBenefit, waiting_period_days: parseInt(value) })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {WAITING_PERIODS.map((period) => (<SelectItem key={period.id} value={String(period.id)}>{period.name}</SelectItem>))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-2">
                <Label>Fornecedor/Operadora</Label>
                <Input value={editingBenefit.provider || ""} onChange={(e) => setEditingBenefit({ ...editingBenefit, provider: e.target.value })} placeholder="Ex: Bradesco Seguros, Sodexo, etc." />
              </div>
              <div className="flex items-center justify-between pt-2">
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <Switch checked={editingBenefit.is_highlighted} onCheckedChange={(checked: boolean) => setEditingBenefit({ ...editingBenefit, is_highlighted: checked })} />
                    <Label className="text-sm">Benefício em destaque</Label>
                  </div>
                  <div className="flex items-center gap-2">
                    <Switch checked={editingBenefit.is_mandatory} onCheckedChange={(checked: boolean) => setEditingBenefit({ ...editingBenefit, is_mandatory: checked })} />
                    <Label className="text-sm">Obrigatório</Label>
                  </div>
                </div>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowBenefitModal(false)}>Cancelar</Button>
            <Button onClick={() => editingBenefit && handleSaveBenefit(editingBenefit)} disabled={isSaving || !editingBenefit?.name || !editingBenefit?.category} className="bg-lia-btn-primary-hover">
              {isSaving ? (<><Loader2 className="w-4 h-4 mr-2 animate-spin motion-reduce:animate-none" />Salvando...</>) : (<><CheckCircle className="w-4 h-4 mr-2" />Salvar Benefício</>)}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ── Import Modal ── */}
      <Dialog open={showImportModal} onOpenChange={setShowImportModal}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2"><Brain className="w-5 h-5 text-wedo-cyan" />Importar Benefícios com LIA</DialogTitle>
            <DialogDescription>Faça upload de uma planilha ou documento e a LIA irá extrair e cadastrar os benefícios automaticamente</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="border-2 border-dashed rounded-md p-8 text-center hover:border-lia-border-medium dark:hover:border-lia-border-medium transition-colors cursor-pointer"
              onClick={() => document.getElementById("file-upload")?.click()}
              onDragOver={(e) => { e.preventDefault(); e.stopPropagation() }}
              onDrop={(e) => { e.preventDefault(); e.stopPropagation(); const file = e.dataTransfer.files[0]; if (file) setImportFile(file) }}
            >
              <input id="file-upload" type="file" className="hidden" accept=".xlsx,.xls,.csv,.pdf,.doc,.docx" onChange={(e) => { const file = e.target.files?.[0]; if (file) setImportFile(file) }} />
              {importFile ? (
                <div className="flex items-center justify-center gap-3">
                  <FileSpreadsheet className="w-8 h-8 text-status-success" />
                  <div className="text-left">
                    <p className="font-medium">{importFile.name}</p>
                    <p className="text-xs text-lia-text-secondary">{(importFile.size / 1024).toFixed(1)} KB</p>
                  </div>
                </div>
              ) : (
                <>
                  <Upload className="w-10 h-10 text-lia-text-disabled mx-auto mb-3" />
                  <p className="font-medium mb-1">Arraste um arquivo ou clique para selecionar</p>
                  <p className="text-xs text-lia-text-secondary">Suportado: Excel, CSV, PDF, Word</p>
                </>
              )}
            </div>
            <div className="bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-md p-4">
              <div className="flex items-start gap-3">
                <Brain className="w-5 h-5 text-wedo-cyan mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-lia-text-primary">A LIA irá analisar o arquivo e:</p>
                  <ul className="text-xs text-lia-text-primary dark:text-lia-text-secondary mt-2 space-y-1">
                    <li>• Identificar todos os benefícios listados</li>
                    <li>• Categorizar automaticamente (saúde, alimentação, etc)</li>
                    <li>• Extrair valores, elegibilidade e carência</li>
                    <li>• Criar os cadastros prontos para sua revisão</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowImportModal(false); setImportFile(null) }}>Cancelar</Button>
            <Button onClick={handleImportFile} disabled={isImporting || !importFile} className="gap-2 bg-lia-btn-primary-hover">
              {isImporting ? (<><Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none" />Processando...</>) : (<><Brain className="w-4 h-4 text-wedo-cyan" />Importar com LIA</>)}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
