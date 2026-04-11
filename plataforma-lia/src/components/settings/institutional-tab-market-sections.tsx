"use client"

import { CURRENCY_SYMBOL } from"@/lib/pricing"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Button } from"@/components/ui/button"
import { Badge } from"@/components/ui/badge"
import {
  MessageSquare, Target, Network,
  Plus, Edit
} from"lucide-react"

interface SectionProps {
  onSettingsChange: (changed: boolean) => void
}

export function SocialMediaSection({ onSettingsChange }: SectionProps) {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm font-semibold">
            <MessageSquare className="w-4 h-4" />
            Redes Sociais e Canais Digitais
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block flex items-center gap-2">
                <div className="w-5 h-5 bg-wedo-magenta rounded-md"></div>
                Instagram
              </label>
              <input
                type="url"
                placeholder="https://instagram.com/sodexobrasil"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block flex items-center gap-2">
                <div className="w-5 h-5 bg-lia-bg-inverse rounded-xl"></div>
                Facebook
              </label>
              <input
                type="url"
                placeholder="https://facebook.com/sodexobrasil"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block flex items-center gap-2">
                <div className="w-5 h-5 bg-wedo-cyan-dark rounded-md"></div>
                LinkedIn
              </label>
              <input
                type="url"
                defaultValue="https://linkedin.com/company/sodexo"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block flex items-center gap-2">
                <div className="w-5 h-5 bg-lia-btn-primary-bg rounded-md"></div>
                Twitter/X
              </label>
              <input
                type="url"
                placeholder="https://twitter.com/sodexobrasil"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block flex items-center gap-2">
                <div className="w-5 h-5 bg-status-error rounded-md"></div>
                YouTube
              </label>
              <input
                type="url"
                placeholder="https://youtube.com/@sodexobrasil"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block flex items-center gap-2">
                <div className="w-5 h-5 bg-black rounded-md"></div>
                TikTok
              </label>
              <input
                type="url"
                placeholder="https://tiktok.com/@sodexobrasil"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
              />
            </div>
          </div>

          <div className="pt-4 border-t border-lia-border-subtle dark:border-lia-border-subtle">
            <h4 className="text-sm font-medium text-lia-text-primary mb-3">Outros Canais</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-lia-text-primary mb-3 block">
                  Blog Corporativo
                </label>
                <input
                  type="url"
                  placeholder="https://blog.sodexo.com.br"
                  onChange={() => onSettingsChange(true)}
                  className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
                />
              </div>
              <div>
                <label className="text-sm font-medium text-lia-text-primary mb-3 block">
                  Portal de Carreiras
                </label>
                <input
                  type="url"
                  placeholder="https://carreiras.sodexo.com.br"
                  onChange={() => onSettingsChange(true)}
                  className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export function SegmentSection({ onSettingsChange }: SectionProps) {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm font-semibold">
            <Target className="w-4 h-4" />
            Segmento e Mercado
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block">
                Setor Principal
              </label>
              <select
                defaultValue="servicos"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
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
              <label className="text-sm font-medium text-lia-text-primary mb-3 block">
                Subsetor
              </label>
              <input
                type="text"
                defaultValue="Facilities Management e Food Services"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
                placeholder="Ex: SaaS, E-commerce, Consultoria..."
              />
            </div>
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block">
                Fase da Empresa
              </label>
              <select
                defaultValue="grande"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
              >
                <option value="startup">Startup (até 50 funcionários)</option>
                <option value="scaleup">Scaleup (51-500 funcionários)</option>
                <option value="media">Empresa de médio porte (501-5000)</option>
                <option value="grande">Grande empresa (5000+ funcionários)</option>
                <option value="multinacional">Multinacional</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block">
                Modelo de Negócio
              </label>
              <select
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
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
              <label className="text-sm font-medium text-lia-text-primary mb-3 block">
                Faturamento Anual
              </label>
              <select
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
              >
                <option value="">Selecione a faixa</option>
                <option value="ate100k">{`Até ${CURRENCY_SYMBOL} 100.000`}</option>
                <option value="100k500k">{`${CURRENCY_SYMBOL} 100.001 a ${CURRENCY_SYMBOL} 500.000`}</option>
                <option value="500k2m">{`${CURRENCY_SYMBOL} 500.001 a ${CURRENCY_SYMBOL} 2.000.000`}</option>
                <option value="2m10m">{`${CURRENCY_SYMBOL} 2.000.001 a ${CURRENCY_SYMBOL} 10.000.000`}</option>
                <option value="10m50m">{`${CURRENCY_SYMBOL} 10.000.001 a ${CURRENCY_SYMBOL} 50.000.000`}</option>
                <option value="acima50m">{`Acima de ${CURRENCY_SYMBOL} 50.000.000`}</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block">
                Países de Operação
              </label>
              <input
                type="text"
                defaultValue="Brasil, França, Estados Unidos, Reino Unido, Alemanha, +50 países"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
                placeholder="Ex: Brasil, Argentina, Chile..."
              />
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-lia-text-primary mb-3 block">
              Principais Produtos/Serviços
            </label>
            <textarea
              rows={3}
              defaultValue="Serviços de alimentação corporativa, gestão de facilities, vouchers e cartões alimentação, benefícios para funcionários, gestão de espaços corporativos."
              onChange={() => onSettingsChange(true)}
              className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
              placeholder="Descreva os principais produtos ou serviços oferecidos..."
            />
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export function BranchesSection() {
  return (
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
                name:"Sede São Paulo",
                cnpj:"12.345.678/0001-90",
                address:"Rua Dr. Geraldo Campos Moreira, 375 - Cidade Monções, São Paulo - SP",
                type:"Matriz",
                manager:"Ana Silva",
                employees: 450,
                status:"Ativa"
              },
              {
                id: 2,
                name:"Filial Rio de Janeiro",
                cnpj:"12.345.678/0002-71",
                address:"Av. Presidente Vargas, 1012 - Centro, Rio de Janeiro - RJ",
                type:"Filial",
                manager:"Carlos Santos",
                employees: 280,
                status:"Ativa"
              },
              {
                id: 3,
                name:"Unidade Belo Horizonte",
                cnpj:"12.345.678/0003-52",
                address:"Rua da Bahia, 1148 - Centro, Belo Horizonte - MG",
                type:"Filial",
                manager:"Maria Costa",
                employees: 150,
                status:"Ativa"
              }
            ].map((branch) => (
              <div key={branch.id} className="p-4 border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h4 className="font-medium text-lia-text-primary">{branch.name}</h4>
                    <p className="text-sm text-lia-text-primary">CNPJ: {branch.cnpj}</p>
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
                    <span className="text-lia-text-primary">Endereço:</span>
                    <p className="font-medium text-lia-text-primary">{branch.address}</p>
                  </div>
                  <div>
                    <span className="text-lia-text-primary">Gestor:</span>
                    <p className="font-medium text-lia-text-primary">{branch.manager}</p>
                  </div>
                  <div>
                    <span className="text-lia-text-primary">Funcionários:</span>
                    <p className="font-medium text-lia-text-primary">{branch.employees}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
