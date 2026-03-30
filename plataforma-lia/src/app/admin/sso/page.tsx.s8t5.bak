'use client'

import { useState } from 'react'
import useSWR from 'swr'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { 
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow 
} from '@/components/ui/table'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue
} from '@/components/ui/select'
import { Shield, Users, Clock, AlertCircle, CheckCircle2, ExternalLink, Database, Cloud } from 'lucide-react'
import { getWorkOSLinks } from '@/lib/workos-links'
import { WorkOSAdminPortal } from '@/components/admin/workos-admin-portal'
import { useWorkOSMetrics } from '@/hooks/use-workos-metrics'

const COMPANY_ID = 'demo_company'
const fetcher = (url: string) => fetch(url).then(res => res.json())

interface SSOStatus {
  company_id: string
  sso_enabled: boolean
  scim_enabled: boolean
  sso_users_count: number
  scim_users_count: number
  groups_count: number
  recent_events_count: number
  organization_id?: string
}

interface WorkOSGroup {
  id: string
  workos_id: string
  name: string
  directory_id: string | null
  mapped_role: string | null
  mapped_permissions: string[]
}

export default function SSOAdminPage() {
  const [selectedTab, setSelectedTab] = useState('overview')
  
  const { metrics: realtimeMetrics, isFromWorkOS, isLoading: metricsLoading } = useWorkOSMetrics(COMPANY_ID)
  
  const { data: status, error: statusError } = useSWR<SSOStatus>(
    `/api/backend-proxy/workos/admin/status?company_id=${COMPANY_ID}`,
    fetcher
  )
  
  const { data: groups, mutate: mutateGroups } = useSWR<WorkOSGroup[]>(
    `/api/backend-proxy/workos/admin/groups?company_id=${COMPANY_ID}`,
    fetcher
  )
  
  const handleRoleMapping = async (groupId: string, role: string) => {
    try {
      await fetch(`/api/backend-proxy/workos/admin/groups/${groupId}/role-mapping?company_id=${COMPANY_ID}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role, permissions: [] })
      })
      mutateGroups()
    } catch (error) {
    }
  }

  if (statusError) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Card className="p-6">
          <div className="flex items-center gap-3 text-status-error">
            <AlertCircle className="h-6 w-6" />
            <span>Erro ao carregar configurações SSO</span>
          </div>
        </Card>
      </div>
    )
  }

  const totalUsers = (status?.sso_users_count || 0) + (status?.scim_users_count || 0)
  const workosLinks = getWorkOSLinks(status?.organization_id)

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-950 dark:text-gray-50">Configurações SSO / SCIM</h1>
          <p className="text-gray-500 mt-1">Gerenciamento de autenticação empresarial e sincronização de diretório</p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="outline" className="bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 border-gray-300 dark:border-gray-600">
            <Shield className="h-3 w-3 mr-1" />
            WorkOS
          </Badge>
          {!metricsLoading && (
            <Badge 
              variant="outline" 
              className={isFromWorkOS 
                ? "bg-status-success/10 text-status-success border-status-success/30" 
                : "bg-gray-50 text-gray-600 border-gray-200"
              }
            >
              {isFromWorkOS ? (
                <>
                  <Cloud className="h-3 w-3 mr-1" />
                  API em tempo real
                </>
              ) : (
                <>
                  <Database className="h-3 w-3 mr-1" />
                  Dados locais
                </>
              )}
            </Badge>
          )}
          <Button 
            onClick={() => window.open(workosLinks.dashboard, '_blank')}
            className="bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
          >
            <ExternalLink className="h-4 w-4 mr-2" />
            Abrir WorkOS Dashboard
          </Button>
          <WorkOSAdminPortal organizationId={status?.organization_id} triggerText="Admin Portal" />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>SSO Status</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              {status?.sso_enabled ? (
                <CheckCircle2 className="h-5 w-5 text-status-success" />
              ) : (
                <AlertCircle className="h-5 w-5 text-gray-400" />
              )}
              <span className="text-lg font-medium">
                {status?.sso_enabled ? 'Ativo' : 'Inativo'}
              </span>
            </div>
            <p className="text-sm text-gray-500 mt-1">{status?.sso_users_count || 0} usuários SSO</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>SCIM Status</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              {status?.scim_enabled ? (
                <CheckCircle2 className="h-5 w-5 text-status-success" />
              ) : (
                <AlertCircle className="h-5 w-5 text-gray-400" />
              )}
              <span className="text-lg font-medium">
                {status?.scim_enabled ? 'Ativo' : 'Inativo'}
              </span>
            </div>
            <p className="text-sm text-gray-500 mt-1">{status?.scim_users_count || 0} usuários gerenciados</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Grupos</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <Users className="h-5 w-5 text-gray-600 dark:text-gray-400" />
              <span className="text-lg font-medium">{status?.groups_count || 0}</span>
            </div>
            <p className="text-sm text-gray-500 mt-1">grupos do diretório</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Eventos (7 dias)</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <Clock className="h-5 w-5 text-gray-600 dark:text-gray-400" />
              <span className="text-lg font-medium">{status?.recent_events_count || 0}</span>
            </div>
            <p className="text-sm text-gray-500 mt-1">eventos de auditoria</p>
          </CardContent>
        </Card>
      </div>

      <Tabs value={selectedTab} onValueChange={setSelectedTab}>
        <TabsList>
          <TabsTrigger value="overview">Visão Geral</TabsTrigger>
          <TabsTrigger value="groups">Grupos</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="mt-4 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Integração WorkOS</CardTitle>
              <CardDescription>
                Configure SSO empresarial (SAML, OIDC) e sincronização de diretório (SCIM) para sua organização.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 border rounded-md">
                  <h3 className="font-medium mb-2">Single Sign-On (SSO)</h3>
                  <p className="text-sm text-gray-500">
                    Permite que usuários façam login usando credenciais corporativas (Azure AD, Okta, Google Workspace).
                  </p>
                </div>
                <div className="p-4 border rounded-md">
                  <h3 className="font-medium mb-2">Directory Sync (SCIM)</h3>
                  <p className="text-sm text-gray-500">
                    Sincroniza automaticamente usuários e grupos do diretório corporativo.
                  </p>
                </div>
              </div>
              <div className="p-4 bg-gray-50 rounded-md">
                <h4 className="font-medium text-sm mb-2">Conformidade</h4>
                <div className="flex flex-wrap gap-2">
                  <Badge variant="outline">SOC 2 Type II</Badge>
                  <Badge variant="outline">BCB 498/2025</Badge>
                  <Badge variant="outline">LGPD</Badge>
                  <Badge variant="outline">ISO 27001</Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5 text-gray-600 dark:text-gray-400" />
                Usuários SSO/SCIM
              </CardTitle>
              <CardDescription>
                Gerencie usuários diretamente no painel do WorkOS
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-md">
                <div>
                  <p className="text-2xl font-semibold text-gray-950 dark:text-gray-50">{totalUsers}</p>
                  <p className="text-sm text-gray-500">usuários totais ({status?.sso_users_count || 0} SSO, {status?.scim_users_count || 0} SCIM)</p>
                </div>
                <Button 
                  variant="outline"
                  onClick={() => window.open(workosLinks.users, '_blank')}
                >
                  <ExternalLink className="h-4 w-4 mr-2" />
                  Gerenciar Usuários no WorkOS
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="groups" className="mt-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Mapeamento de Roles</CardTitle>
                  <CardDescription>
                    Configure mapeamento de grupos do diretório para roles da plataforma.
                  </CardDescription>
                </div>
                <Button 
                  variant="outline"
                  onClick={() => window.open(workosLinks.directorySync, '_blank')}
                >
                  <ExternalLink className="h-4 w-4 mr-2" />
                  Gerenciar no WorkOS
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {groups && groups.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Nome do Grupo</TableHead>
                      <TableHead>WorkOS ID</TableHead>
                      <TableHead>Role Mapeado</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {groups.map((group) => (
                      <TableRow key={group.id}>
                        <TableCell className="font-medium">{group.name}</TableCell>
                        <TableCell className="text-gray-500 text-sm">{group.workos_id}</TableCell>
                        <TableCell>
                          <Select
                            value={group.mapped_role || ''}
                            onValueChange={(value) => handleRoleMapping(group.id, value)}
                          >
                            <SelectTrigger className="w-40">
                              <SelectValue placeholder="Selecionar role" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="admin">Admin</SelectItem>
                              <SelectItem value="recruiter">Recrutador</SelectItem>
                              <SelectItem value="viewer">Visualizador</SelectItem>
                            </SelectContent>
                          </Select>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <Users className="h-12 w-12 mx-auto mb-3 opacity-50" />
                  <p>Nenhum grupo sincronizado</p>
                  <p className="text-sm">Configure SCIM no WorkOS para sincronizar grupos.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

      </Tabs>

      <Card className="mt-6 border-dashed">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Clock className="h-5 w-5 text-gray-400" />
              <div>
                <p className="font-medium text-gray-800 dark:text-gray-200">Logs de Auditoria SSO/SCIM</p>
                <p className="text-sm text-gray-500">
                  Visualize eventos de autenticação e sincronização no painel do WorkOS.
                </p>
              </div>
            </div>
            <Button 
              variant="outline" 
              onClick={() => window.open(workosLinks.events, '_blank')}
            >
              <ExternalLink className="h-4 w-4 mr-2" />
              Ver Logs no WorkOS
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
