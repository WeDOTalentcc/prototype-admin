"use client"

  import { useState } from "react"
  import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
  import { Button } from "@/components/ui/button"
  import { Badge } from "@/components/ui/badge"
  import { RealTimeDashboardPage } from "@/components/pages/real-time-dashboard-page"
  import {
    Building, Network, Rocket, CreditCard, Activity,
    Search, Filter, UserPlus, Mail, Eye, MoreVertical,
    X, CheckCircle, AlertCircle, Send
  } from "lucide-react"

  export interface SettingsBillingTabProps {
    onSettingsChange: (changed: boolean) => void
  }

  // Componente de Administração WeDOTalent
export function SettingsBillingTab({ onSettingsChange }: { onSettingsChange: (changed: boolean) => void }) {
  const [activeSection, setActiveSection] = useState("clients")
  const [showAddClientModal, setShowAddClientModal] = useState(false)
  const [showSendInviteModal, setShowSendInviteModal] = useState(false)
  const [selectedClient, setSelectedClient] = useState<any>(null)

  const adminSections = [
    { id: "clients", name: "Clientes", icon: Building, desc: "Gerenciar empresas cliente" },
    { id: "tenants", name: "Tenants", icon: Network, desc: "Configurar ambientes" },
    { id: "onboarding", name: "Onboarding", icon: Rocket, desc: "Setup e ativação" },
    { id: "billing", name: "Faturamento", icon: CreditCard, desc: "Contratos e pagamentos" },
    { id: "performance", name: "Dashboard Performance", icon: Activity, desc: "Monitoramento em tempo real" }
  ]

  const mockClients = [
    {
      id: 1,
      name: "Sodexo Brasil",
      cnpj: "12.345.678/0001-90",
      status: "ativo",
      plan: "Enterprise",
      users: 45,
      setupDate: "2024-01-15",
      contact: {
        name: "Ana Silva",
        email: "ana.silva@sodexo.com.br",
        phone: "(11) 99999-9999"
      },
      tenant: "sodexo-prod",
      lastAccess: "2024-01-20 14:30"
    },
    {
      id: 2,
      name: "TechCorp Inovação",
      cnpj: "98.765.432/0001-10",
      status: "setup",
      plan: "Professional",
      users: 0,
      setupDate: "2024-01-18",
      contact: {
        name: "Carlos Santos",
        email: "carlos@techcorp.com.br",
        phone: "(11) 88888-8888"
      },
      tenant: "techcorp-prod",
      lastAccess: "Nunca"
    },
    {
      id: 3,
      name: "StartupXYZ",
      cnpj: "55.444.333/0001-22",
      status: "trial",
      plan: "Starter",
      users: 3,
      setupDate: "2024-01-19",
      contact: {
        name: "Maria Costa",
        email: "maria@startupxyz.com",
        phone: "(11) 77777-7777"
      },
      tenant: "startupxyz-trial",
      lastAccess: "2024-01-20 09:15"
    }
  ]

  const getStatusColor = (status: string) => {
    switch (status) {
      case "ativo": return "bg-status-success/15 text-status-success dark:bg-status-success/20 dark:text-status-success"
      case "setup": return "bg-wedo-orange/15 text-wedo-orange dark:bg-wedo-orange/20 dark:text-wedo-orange"
 case "trial": return "bg-gray-50 lia-text-700 dark:bg-lia-bg-secondary dark:text-lia-text-tertiary"
      case "suspenso": return "bg-status-error/15 text-status-error dark:bg-status-error/20 dark:text-status-error"
      default: return "bg-gray-100 lia-text-800 dark:bg-lia-bg-elevated dark:lia-text-500"
    }
  }

  const renderClientsSection = () => (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 lia-text-800" />
            <input
              type="text"
              placeholder="Buscar clientes..."
              className="pl-10 pr-4 py-2 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary w-64"
            />
          </div>
          <Button variant="outline" size="sm">
            <Filter className="w-4 h-4 mr-2" />
            Filtros
          </Button>
        </div>
        <Button onClick={() => setShowAddClientModal(true)} className="gap-2">
          <UserPlus className="w-4 h-4" />
          Novo Cliente
        </Button>
      </div>

      <div className="grid gap-4">
        {mockClients.map((client) => (
          <Card key={client.id} className="hover:transition-shadow">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-gray-100 dark:bg-lia-bg-elevated rounded-md flex items-center justify-center">
                    <Building className="w-6 h-6 lia-text-800 dark:text-lia-text-primary" />
                  </div>
                  <div>
                    <h3 className="font-medium lia-text-950 dark:lia-text-50">{client.name}</h3>
                    <p className="text-sm lia-text-800 dark:text-lia-text-primary">CNPJ: {client.cnpj}</p>
                    <div className="flex items-center gap-3 mt-1">
                      <Badge className={getStatusColor(client.status)}>
                        {client.status.toUpperCase()}
                      </Badge>
                      <span className="text-xs lia-text-800">Plano {client.plan}</span>
                      <span className="text-xs lia-text-800">{client.users} usuários</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setSelectedClient(client)
                      setShowSendInviteModal(true)
                    }}
                  >
                    <Mail className="w-4 h-4 mr-2" />
                    Enviar Link
                  </Button>
                  <Button variant="outline" size="sm">
                    <Eye className="w-4 h-4 mr-2" />
                    Ver Detalhes
                  </Button>
                  <Button variant="ghost" size="sm">
                    <MoreVertical className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-lia-border-subtle dark:border-lia-border-subtle">
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="lia-text-800 dark:text-lia-text-primary">Contato:</span>
                    <div className="font-medium">{client.contact.name}</div>
                    <div className="lia-text-800 dark:text-lia-text-primary">{client.contact.email}</div>
                  </div>
                  <div>
                    <span className="lia-text-800 dark:text-lia-text-primary">Tenant:</span>
                    <div className="font-medium font-mono text-xs">{client.tenant}</div>
                  </div>
                  <div>
                    <span className="lia-text-800 dark:text-lia-text-primary">Último acesso:</span>
                    <div className="font-medium">{client.lastAccess}</div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )

  const renderTenantsSection = () => (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Gerenciamento de Tenants</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-4 bg-status-success/10 dark:bg-status-success/20 rounded-md">
                <div className="text-2xl font-bold text-status-success dark:text-status-success">12</div>
                <div className="text-sm text-status-success dark:text-status-success">Tenants Ativos</div>
              </div>
              <div className="text-center p-4 bg-wedo-orange/10 dark:bg-wedo-orange/20 rounded-md">
                <div className="text-2xl font-bold text-wedo-orange dark:text-wedo-orange">3</div>
                <div className="text-sm text-wedo-orange dark:text-wedo-orange">Em Setup</div>
              </div>
              <div className="text-center p-4 bg-wedo-cyan/10 dark:bg-wedo-cyan/20 rounded-md">
                <div className="text-2xl font-bold lia-text-700 dark:text-lia-text-tertiary">2</div>
 <div className="text-sm lia-text-600">Trial</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderOnboardingSection = () => (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Central de Onboarding</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="p-4 border border-lia-border-subtle dark:border-lia-border-subtle rounded-md">
              <h4 className="font-medium mb-2">Templates de Email</h4>
              <div className="space-y-2">
                <Button variant="outline" size="sm" className="mr-2">Email de Boas-vindas</Button>
                <Button variant="outline" size="sm" className="mr-2">Instruções de Setup</Button>
                <Button variant="outline" size="sm">Link de Ativação</Button>
              </div>
            </div>

            <div className="p-4 border border-lia-border-subtle dark:border-lia-border-subtle rounded-md">
              <h4 className="font-medium mb-2">Checklist de Setup</h4>
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-status-success" />
                  <span>Criar tenant no banco de dados</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-status-success" />
                  <span>Configurar domínio personalizado</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-status-success" />
                  <span>Enviar credenciais de acesso</span>
                </div>
                <div className="flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-wedo-orange" />
                  <span>Agendar treinamento inicial</span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderPerformanceSection = () => (
    <div className="space-y-4">
      <RealTimeDashboardPage />
    </div>
  )

  return (
    <div className="space-y-6">
      {/* Navigation Tabs */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-1">
            {adminSections.map((section) => (
              <button
                key={section.id}
                onClick={() => setActiveSection(section.id)}
                className={`flex items-center gap-2 px-4 py-3 rounded-md text-sm font-medium transition-colors font-crimson ${
                  activeSection === section.id
 ? 'bg-gray-50 dark:bg-lia-bg-secondary lia-text-900 dark:text-lia-text-secondary'
                    : 'hover:bg-gray-50 dark:hover:bg-gray-800 lia-text-800 dark:text-lia-text-primary'
                }`}
              >
                <section.icon className="w-4 h-4" />
                {section.name}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Section Content */}
      {activeSection === "clients" && renderClientsSection()}
      {activeSection === "tenants" && renderTenantsSection()}
      {activeSection === "onboarding" && renderOnboardingSection()}
      {activeSection === "performance" && renderPerformanceSection()}

      {/* Modais */}
      {showAddClientModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-lia-bg-secondary rounded-md w-full max-w-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Novo Cliente</h3>
              <Button variant="ghost" size="sm" onClick={() => setShowAddClientModal(false)}>
                <X className="w-4 h-4" />
              </Button>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Nome da Empresa</label>
                <input
                  type="text"
                  className="w-full p-2 border border-lia-border-default dark:border-lia-border-default rounded-md"
                  placeholder="Ex: Sodexo Brasil"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">CNPJ</label>
                <input
                  type="text"
                  className="w-full p-2 border border-lia-border-default dark:border-lia-border-default rounded-md"
                  placeholder="00.000.000/0001-00"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">Nome do Contato</label>
                <input
                  type="text"
                  className="w-full p-2 border border-lia-border-default dark:border-lia-border-default rounded-md"
                  placeholder="Ex: Ana Silva"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">Email</label>
                <input
                  type="email"
                  className="w-full p-2 border border-lia-border-default dark:border-lia-border-default rounded-md"
                  placeholder="ana.silva@empresa.com"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">Telefone</label>
                <input
                  type="tel"
                  className="w-full p-2 border border-lia-border-default dark:border-lia-border-default rounded-md"
                  placeholder="(11) 99999-9999"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">Plano</label>
                <select className="w-full p-2 border border-lia-border-default dark:border-lia-border-default rounded-md">
                  <option>Starter</option>
                  <option>Professional</option>
                  <option>Enterprise</option>
                </select>
              </div>
            </div>

            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowAddClientModal(false)}>
                Cancelar
              </Button>
              <Button onClick={() => setShowAddClientModal(false)}>
                Criar Cliente
              </Button>
            </div>
          </div>
        </div>
      )}

      {showSendInviteModal && selectedClient && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-lia-bg-secondary rounded-md w-full max-w-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Enviar Link de Setup</h3>
              <Button variant="ghost" size="sm" onClick={() => setShowSendInviteModal(false)}>
                <X className="w-4 h-4" />
              </Button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Cliente</label>
                <input
                  type="text"
                  value={selectedClient.name}
                  disabled
                  className="w-full p-2 border border-lia-border-default dark:border-lia-border-default rounded-md bg-gray-50 dark:bg-lia-bg-elevated"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">Email do Contato</label>
                <input
                  type="email"
                  value={selectedClient.contact.email}
                  className="w-full p-2 border border-lia-border-default dark:border-lia-border-default rounded-md"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">Tipo de Link</label>
                <select className="w-full p-2 border border-lia-border-default dark:border-lia-border-default rounded-md">
                  <option>Setup Inicial Completo</option>
                  <option>Apenas Ativação</option>
                  <option>Resetar Senha Admin</option>
                </select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">Mensagem Personalizada</label>
                <textarea
                  rows={3}
                  className="w-full p-2 border border-lia-border-default dark:border-lia-border-default rounded-md"
                  placeholder="Adicione uma mensagem personalizada (opcional)"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 mt-6">
              <Button variant="outline" onClick={() => setShowSendInviteModal(false)}>
                Cancelar
              </Button>
              <Button onClick={() => setShowSendInviteModal(false)}>
                <Send className="w-4 h-4 mr-2" />
                Enviar Link
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
  