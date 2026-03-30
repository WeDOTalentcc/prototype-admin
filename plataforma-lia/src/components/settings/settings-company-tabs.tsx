"use client"

  import { useState } from "react"
  import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
  import { Button } from "@/components/ui/button"
  import { Badge } from "@/components/ui/badge"
  import {
    Building, Globe, MessageSquare, Target, Network,
    Upload, FileText, Heart, Edit, Trash2, Plus, ExternalLink
  } from "lucide-react"

  export interface SettingsCompanyTabProps {
    onSettingsChange: (changed: boolean) => void
  }

  // Componente de Dados Institucionais Completo
export function InstitutionalTab({ onSettingsChange }: { onSettingsChange: (changed: boolean) => void }) {
  const [activeSubTab, setActiveSubTab] = useState<'basic' | 'address' | 'social' | 'segment' | 'branches'>('basic')

  const subTabs = [
    { id: 'basic', name: 'Dados Básicos', icon: Building },
    { id: 'address', name: 'Endereço', icon: Globe },
    { id: 'social', name: 'Redes Sociais', icon: MessageSquare },
    { id: 'segment', name: 'Segmento', icon: Target },
    { id: 'branches', name: 'Filiais', icon: Network }
  ]

  const renderBasicData = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl font-medium font-inter">
            <Building className="w-4 h-4" />
            Informações Básicas
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-3 block">
                Razão Social
              </label>
              <input
                type="text"
                defaultValue="Sodexo do Brasil Comercial S.A."
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary"
              />
            </div>
            <div>
              <label className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-3 block">
                Nome Fantasia
              </label>
              <input
                type="text"
                defaultValue="Sodexo Brasil"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary"
              />
            </div>
            <div>
              <label className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-3 block">
                CNPJ
              </label>
              <input
                type="text"
                defaultValue="12.345.678/0001-90"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary"
              />
            </div>
            <div>
              <label className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-3 block">
                Inscrição Estadual
              </label>
              <input
                type="text"
                defaultValue="123.456.789.012"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary"
              />
            </div>
            <div>
              <label className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-3 block">
                Data de Fundação
              </label>
              <input
                type="date"
                defaultValue="1966-03-15"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary"
              />
            </div>
            <div>
              <label className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-3 block">
                Número de Funcionários
              </label>
              <select
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary"
              >
                <option>1-10 funcionários</option>
                <option>11-50 funcionários</option>
                <option>51-200 funcionários</option>
                <option>201-1000 funcionários</option>
                <option>1001-5000 funcionários</option>
                <option>5000+ funcionários</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-3 block">
                Site Institucional
              </label>
              <input
                type="url"
                defaultValue="https://sodexo.com.br"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary"
              />
            </div>
            <div>
              <label className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-3 block">
                Email Principal
              </label>
              <input
                type="email"
                defaultValue="contato@sodexo.com.br"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary"
              />
            </div>
            <div>
              <label className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-3 block">
                Telefone Principal
              </label>
              <input
                type="tel"
                defaultValue="(11) 3049-6300"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary"
              />
            </div>
            <div>
              <label className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-3 block">
                WhatsApp Corporativo
              </label>
              <input
                type="tel"
                placeholder="(11) 99999-9999"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary"
              />
            </div>
          </div>

          <div>
            <label className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-3 block">
              Descrição da Empresa
            </label>
            <textarea
              rows={4}
              defaultValue="A Sodexo é uma empresa francesa líder mundial em serviços de alimentação e facilities management, presente em 55 países. No Brasil desde 1997, oferece soluções integradas que melhoram a qualidade de vida diária."
              onChange={() => onSettingsChange(true)}
              className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary"
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Logotipo da Empresa</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-md p-6 text-center bg-gray-50 dark:bg-lia-bg-secondary">
            <Upload className="w-8 h-8 mx-auto mb-2 lia-text-800" />
            <p className="text-sm lia-text-800 dark:text-lia-text-primary mb-2">
              Faça upload do logotipo da empresa
            </p>
            <p className="text-xs lia-text-800">PNG, JPG ou SVG até 2MB • Tamanho recomendado: 400x400px</p>
            <Button variant="outline" className="mt-3" size="sm">
              Escolher Arquivo
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderAddress = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl font-medium font-inter">
            <Globe className="w-4 h-4" />
            Endereço da Matriz
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-3 block">
                CEP
              </label>
              <input
                type="text"
                defaultValue="04571-020"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary"
                placeholder="00000-000"
              />
            </div>
            <div className="md:col-span-2">
              <label className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-3 block">
                Logradouro
              </label>
              <input
                type="text"
                defaultValue="Rua Dr. Geraldo Campos Moreira"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-3 block">
                Número
              </label>
              <input
                type="text"
                defaultValue="375"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary"
              />
            </div>
            <div className="md:col-span-2">
              <label className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-3 block">
                Complemento
              </label>
              <input
                type="text"
                placeholder="Andar, sala, bloco..."
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary"
              />
            </div>
            <div>
              <label className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-3 block">
                Bairro
              </label>
              <input
                type="text"
                defaultValue="Cidade Monções"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-3 block">
                Cidade
              </label>
              <input
                type="text"
                defaultValue="São Paulo"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary"
              />
            </div>
            <div>
              <label className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-3 block">
                Estado
              </label>
              <select
                defaultValue="SP"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary"
              >
                <option value="">Selecione o estado</option>
                <option value="AC">Acre</option>
                <option value="AL">Alagoas</option>
                <option value="AP">Amapá</option>
                <option value="AM">Amazonas</option>
                <option value="BA">Bahia</option>
                <option value="CE">Ceará</option>
                <option value="DF">Distrito Federal</option>
                <option value="ES">Espírito Santo</option>
                <option value="GO">Goiás</option>
                <option value="MA">Maranhão</option>
                <option value="MT">Mato Grosso</option>
                <option value="MS">Mato Grosso do Sul</option>
                <option value="MG">Minas Gerais</option>
                <option value="PA">Pará</option>
                <option value="PB">Paraíba</option>
                <option value="PR">Paraná</option>
                <option value="PE">Pernambuco</option>
                <option value="PI">Piauí</option>
                <option value="RJ">Rio de Janeiro</option>
                <option value="RN">Rio Grande do Norte</option>
                <option value="RS">Rio Grande do Sul</option>
                <option value="RO">Rondônia</option>
                <option value="RR">Roraima</option>
                <option value="SC">Santa Catarina</option>
                <option value="SP">São Paulo</option>
                <option value="SE">Sergipe</option>
                <option value="TO">Tocantins</option>
              </select>
            </div>
          </div>

          <div>
            <label className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-3 block">
              País
            </label>
            <select
              defaultValue="BR"
              onChange={() => onSettingsChange(true)}
              className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary"
            >
              <option value="BR">Brasil</option>
              <option value="US">Estados Unidos</option>
              <option value="FR">França</option>
              <option value="DE">Alemanha</option>
              <option value="GB">Reino Unido</option>
            </select>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderSocialMedia = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl font-medium font-inter">
            <MessageSquare className="w-4 h-4" />
            Redes Sociais e Canais Digitais
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-3 block flex items-center gap-2">
                <div className="w-5 h-5 bg-wedo-magenta rounded-md"></div>
                Instagram
              </label>
              <input
                type="url"
                placeholder="https://instagram.com/sodexobrasil"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary"
              />
            </div>
            <div>
              <label className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-3 block flex items-center gap-2">
                <div className="w-5 h-5 bg-gray-700 dark:lia-bg-300 rounded-md"></div>
                Facebook
              </label>
              <input
                type="url"
                placeholder="https://facebook.com/sodexobrasil"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary"
              />
            </div>
            <div>
              <label className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-3 block flex items-center gap-2">
                <div className="w-5 h-5 bg-wedo-cyan-dark rounded-md"></div>
                LinkedIn
              </label>
              <input
                type="url"
                defaultValue="https://linkedin.com/company/sodexo"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary"
              />
            </div>
            <div>
              <label className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-3 block flex items-center gap-2">
                <div className="w-5 h-5 bg-gray-900 dark:lia-bg-50 rounded-md"></div>
                Twitter/X
              </label>
              <input
                type="url"
                placeholder="https://twitter.com/sodexobrasil"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary"
              />
            </div>
            <div>
              <label className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-3 block flex items-center gap-2">
                <div className="w-5 h-5 bg-status-error rounded-md"></div>
                YouTube
              </label>
              <input
                type="url"
                placeholder="https://youtube.com/@sodexobrasil"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary"
              />
            </div>
            <div>
              <label className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-3 block flex items-center gap-2">
                <div className="w-5 h-5 bg-black rounded-md"></div>
                TikTok
              </label>
              <input
                type="url"
                placeholder="https://tiktok.com/@sodexobrasil"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary"
              />
            </div>
          </div>

          <div className="pt-4 border-t border-lia-border-subtle dark:border-lia-border-subtle">
            <h4 className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-3">Outros Canais</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-3 block">
                  Blog Corporativo
                </label>
                <input
                  type="url"
                  placeholder="https://blog.sodexo.com.br"
                  onChange={() => onSettingsChange(true)}
                  className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary"
                />
              </div>
              <div>
                <label className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-3 block">
                  Portal de Carreiras
                </label>
                <input
                  type="url"
                  placeholder="https://carreiras.sodexo.com.br"
                  onChange={() => onSettingsChange(true)}
                  className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary"
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderSegment = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl font-medium font-inter">
            <Target className="w-4 h-4" />
            Segmento e Mercado
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-3 block">
                Setor Principal
              </label>
              <select
                defaultValue="servicos"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary"
              >
                <option value="">Selecione o setor</option>
                <option value="servicos">Alimentação e Serviços</option>
                <option value="tecnologia">Tecnologia</option>
                <option value="saude">Saúde</option>
                <option value="educacao">Educação</option>
                <option value="financeiro">Financeiro</option>
                <option value="industria">Indústria</option>
                <option value="varejo">Varejo</option>
                <option value="construcao">Construção</option>
                <option value="energia">Energia</option>
                <option value="agronegocio">Agronegócio</option>
                <option value="telecomunicacoes">Telecomunicações</option>
                <option value="consultoria">Consultoria</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-3 block">
                Subsetor
              </label>
              <input
                type="text"
                defaultValue="Facilities Management e Food Services"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary"
                placeholder="Ex: SaaS, E-commerce, Consultoria..."
              />
            </div>
            <div>
              <label className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-3 block">
                Fase da Empresa
              </label>
              <select
                defaultValue="grande"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary"
              >
                <option value="startup">Startup (até 50 funcionários)</option>
                <option value="scaleup">Scaleup (51-500 funcionários)</option>
                <option value="media">Empresa de médio porte (501-5000)</option>
                <option value="grande">Grande empresa (5000+ funcionários)</option>
                <option value="multinacional">Multinacional</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-3 block">
                Modelo de Negócio
              </label>
              <select
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary"
              >
                <option value="">Selecione o modelo</option>
                <option value="b2b">B2B (Business to Business)</option>
                <option value="b2c">B2C (Business to Consumer)</option>
                <option value="b2b2c">B2B2C (Business to Business to Consumer)</option>
                <option value="marketplace">Marketplace</option>
                <option value="saas">SaaS (Software as a Service)</option>
                <option value="consultoria">Consultoria/Serviços</option>
                <option value="produto">Produto Físico</option>
                <option value="hibrido">Híbrido</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-3 block">
                Faturamento Anual
              </label>
              <select
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary"
              >
                <option value="">Selecione a faixa</option>
                <option value="ate100k">Até R$ 100.000</option>
                <option value="100k500k">R$ 100.001 a R$ 500.000</option>
                <option value="500k2m">R$ 500.001 a R$ 2.000.000</option>
                <option value="2m10m">R$ 2.000.001 a R$ 10.000.000</option>
                <option value="10m50m">R$ 10.000.001 a R$ 50.000.000</option>
                <option value="acima50m">Acima de R$ 50.000.000</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-3 block">
                Países de Operação
              </label>
              <input
                type="text"
                defaultValue="Brasil, França, Estados Unidos, Reino Unido, Alemanha, +50 países"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary"
                placeholder="Ex: Brasil, Argentina, Chile..."
              />
            </div>
          </div>

          <div>
            <label className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-3 block">
              Principais Produtos/Serviços
            </label>
            <textarea
              rows={3}
              defaultValue="Serviços de alimentação corporativa, gestão de facilities, vouchers e cartões alimentação, benefícios para funcionários, gestão de espaços corporativos."
              onChange={() => onSettingsChange(true)}
              className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary"
              placeholder="Descreva os principais produtos ou serviços oferecidos..."
            />
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderBranches = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Network className="w-4 h-4" />
              Filiais e Unidades
            </div>
            <Button className="gap-2">
              <Plus className="w-4 h-4" />
              Nova Filial
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[
              {
                id: 1,
                name: "Sede São Paulo",
                cnpj: "12.345.678/0001-90",
                address: "Rua Dr. Geraldo Campos Moreira, 375 - Cidade Monções, São Paulo - SP",
                type: "Matriz",
                manager: "Ana Silva",
                employees: 450,
                status: "Ativa"
              },
              {
                id: 2,
                name: "Filial Rio de Janeiro",
                cnpj: "12.345.678/0002-71",
                address: "Av. Presidente Vargas, 1012 - Centro, Rio de Janeiro - RJ",
                type: "Filial",
                manager: "Carlos Santos",
                employees: 280,
                status: "Ativa"
              },
              {
                id: 3,
                name: "Unidade Belo Horizonte",
                cnpj: "12.345.678/0003-52",
                address: "Rua da Bahia, 1148 - Centro, Belo Horizonte - MG",
                type: "Filial",
                manager: "Maria Costa",
                employees: 150,
                status: "Ativa"
              }
            ].map((branch) => (
              <div key={branch.id} className="p-4 border border-lia-border-subtle dark:border-lia-border-subtle rounded-md">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h4 className="font-medium lia-text-950 dark:lia-text-50">{branch.name}</h4>
                    <p className="text-sm lia-text-800 dark:text-lia-text-primary">CNPJ: {branch.cnpj}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={branch.type === 'Matriz' ? 'default' : 'secondary'}>
                      {branch.type}
                    </Badge>
                    <Badge variant="outline" className="text-status-success border-status-success/30">
                      {branch.status}
                    </Badge>
                    <Button variant="ghost" size="sm">
                      <Edit className="w-4 h-4" />
                    </Button>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="lia-text-800 dark:text-lia-text-primary">Endereço:</span>
                    <p className="font-medium lia-text-950 dark:lia-text-50">{branch.address}</p>
                  </div>
                  <div>
                    <span className="lia-text-800 dark:text-lia-text-primary">Gestor:</span>
                    <p className="font-medium lia-text-950 dark:lia-text-50">{branch.manager}</p>
                  </div>
                  <div>
                    <span className="lia-text-800 dark:text-lia-text-primary">Funcionários:</span>
                    <p className="font-medium lia-text-950 dark:lia-text-50">{branch.employees}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )

  return (
    <div className="space-y-6">
      {/* Sub Navigation */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-1 overflow-x-auto">
            {subTabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveSubTab(tab.id as Parameters<typeof setActiveSubTab>[0])}
                className={`flex items-center gap-2 px-4 py-3 rounded-md text-sm font-medium whitespace-nowrap transition-colors motion-reduce:transition-none font-crimson ${
                  activeSubTab === tab.id
 ? 'bg-gray-50 dark:bg-lia-bg-secondary lia-text-900 dark:text-lia-text-secondary'
                    : 'hover:bg-gray-50 dark:hover:bg-gray-800 lia-text-800 dark:text-lia-text-primary'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.name}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Sub Tab Content */}
      {activeSubTab === 'basic' && renderBasicData()}
      {activeSubTab === 'address' && renderAddress()}
      {activeSubTab === 'social' && renderSocialMedia()}
      {activeSubTab === 'segment' && renderSegment()}
      {activeSubTab === 'branches' && renderBranches()}
    </div>
  )
}

  // Componente de Cultura (recuperado)
export function CultureTab({ onSettingsChange }: { onSettingsChange: (changed: boolean) => void }) {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl font-medium font-inter">
            <Heart className="w-4 h-4" />
            Identidade Corporativa
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-3 block">
              Missão
            </label>
            <textarea
              rows={3}
              defaultValue="Melhorar a qualidade de vida diária de todos os que servimos por meio de serviços de alimentação e facilities únicos e inovadores."
              onChange={() => onSettingsChange(true)}
              className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary text-sm"
            />
          </div>
          <div>
            <label className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-3 block">
              Visão
            </label>
            <textarea
              rows={3}
              defaultValue="Ser a empresa líder mundial em serviços de qualidade de vida, criando valor para todas as partes interessadas."
              onChange={() => onSettingsChange(true)}
              className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary text-sm"
            />
          </div>
          <div>
            <label className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-3 block">
              Propósito Institucional
            </label>
            <textarea
              rows={3}
              defaultValue="Conectar pessoas, lugares e experiências para criar um mundo melhor através de serviços essenciais que melhoram a vida diária."
              onChange={() => onSettingsChange(true)}
              className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary text-sm"
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Valores da Empresa</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            {[
              { value: 'Espírito de Serviço', description: 'Nos concentramos nas necessidades das pessoas que servimos' },
              { value: 'Espírito de Equipe', description: 'Construímos relacionamentos duradouros baseados na confiança' },
              { value: 'Espírito de Progresso', description: 'Inovamos e nos adaptamos para um mundo em mudança' },
              { value: 'Sustentabilidade', description: 'Comprometidos com um planeta mais sustentável' }
            ].map((item, index) => (
              <div key={item.value} className="p-4 border border-lia-border-subtle dark:border-lia-border-subtle rounded-md">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-medium lia-text-950 dark:lia-text-50">
                    {item.value}
                  </h4>
                  <div className="flex gap-1">
                    <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                      <Edit className="w-3 h-3" />
                    </Button>
                    <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                      <Trash2 className="w-3 h-3" />
                    </Button>
                  </div>
                </div>
                <p className="text-xs lia-text-800 dark:text-lia-text-tertiary">
                  {item.description}
                </p>
              </div>
            ))}
          </div>
          <Button variant="outline" className="gap-2" size="sm">
            <Plus className="w-4 h-4" />
            Adicionar Valor
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}

  // Componente de Estrutura (recuperado)
export function StructureTab({ onSettingsChange }: { onSettingsChange: (changed: boolean) => void }) {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl font-medium font-inter">
            <Network className="w-4 h-4" />
            Upload de Organograma
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-md p-8 text-center bg-gray-50 dark:bg-lia-bg-secondary">
            <Upload className="w-12 h-12 mx-auto mb-4 lia-text-800" />
            <h4 className="text-sm font-medium lia-text-950 dark:lia-text-50 mb-2">
              Faça upload do organograma da empresa
            </h4>
            <p className="text-sm lia-text-800 dark:text-lia-text-primary mb-4">
              Formatos aceitos: PNG, JPG, PDF, SVG até 10MB
            </p>
            <Button variant="outline">
              Escolher Arquivo
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Estrutura de Cargos</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-md p-6 text-center mb-4 bg-gray-50 dark:bg-lia-bg-secondary">
            <FileText className="w-8 h-8 mx-auto mb-2 lia-text-800" />
            <p className="text-sm lia-text-800 dark:text-lia-text-primary mb-2">
              Upload da planilha de cargos e descrições
            </p>
            <p className="text-xs lia-text-800 mb-3">Excel (.xlsx, .xls) ou CSV até 5MB</p>
            <Button variant="outline" size="sm">
              Upload de Cargos
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
  