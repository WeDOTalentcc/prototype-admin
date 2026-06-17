/**
 * WT-2022 P0.RBAC (registrado 2026-05-21) — escopo DESTE módulo:
 *
 * Este `UserRole` é uma TAXONOMIA DE PERMISSÕES LOCAL ao client-side
 * PermissionManager (RBAC role-based access control + LIA_ACTIONS_BY_ROLE).
 * Os 5 valores (`admin | manager | senior_recruiter | recruiter | intern`)
 * descrevem NÍVEIS DE PERMISSÃO de UI/cliente — NÃO são roles canonical
 * de autenticação.
 *
 * NÃO CONFUNDIR com `User.role` canonical em `src/services/auth-service.ts`:
 *   - `auth-service.ts` User.role = `'admin' | 'recruiter' | 'viewer' | 'wedotalent_admin'`
 *     → vem do JWT/backend, é authority. Use para gates de auth no client.
 *
 * Status atual deste módulo (2026-05-21): SEM CONSUMERS EXTERNOS.
 * Apenas `src/utils/permissions.test.ts` (próprio test) e
 * `src/lib/permissions.ts` (re-export do tipo) referenciam este arquivo.
 *
 * Mantido por enquanto (não-deletar sem autorização Paulo). Roadmap:
 * decidir entre (a) consolidar com `lib/permissions.ts` em um único
 * RBAC canonical, ou (b) deletar se PermissionManager nunca for
 * adotado pelo client real.
 */
export type UserRole = 'admin' | 'manager' | 'senior_recruiter' | 'recruiter' | 'intern'

export interface User {
  id: string
  name: string
  email: string
  role: UserRole
  department?: string
  company: string
}

export interface Permission {
  action: string
  resource: string
  conditions?: Record<string, unknown>
}

// Definição de permissões por role
const ROLE_PERMISSIONS: Record<UserRole, Permission[]> = {
  admin: [
    { action: '*', resource: '*' }, // Admin tem acesso total
  ],
  manager: [
    { action: 'read', resource: 'candidates' },
    { action: 'write', resource: 'candidates' },
    { action: 'delete', resource: 'candidates' },
    { action: 'read', resource: 'jobs' },
    { action: 'write', resource: 'jobs' },
    { action: 'read', resource: 'reports' },
    { action: 'write', resource: 'reports' },
    { action: 'read', resource: 'team_performance' },
    { action: 'write', resource: 'evaluations' },
    { action: 'read', resource: 'lia_insights' },
    { action: 'execute', resource: 'lia_actions' },
    { action: 'read', resource: 'interviews' },
    { action: 'write', resource: 'interviews' },
    { action: 'read', resource: 'assessments' },
    { action: 'write', resource: 'assessments' },
    { action: 'read', resource: 'references' },
    { action: 'write', resource: 'references' },
    { action: 'read', resource: 'analytics' },
    { action: 'write', resource: 'settings' },
  ],
  senior_recruiter: [
    { action: 'read', resource: 'candidates' },
    { action: 'write', resource: 'candidates' },
    { action: 'read', resource: 'jobs' },
    { action: 'write', resource: 'jobs', conditions: { own_jobs: true } },
    { action: 'read', resource: 'reports' },
    { action: 'write', resource: 'evaluations' },
    { action: 'read', resource: 'lia_insights' },
    { action: 'execute', resource: 'lia_actions' },
    { action: 'read', resource: 'interviews' },
    { action: 'write', resource: 'interviews' },
    { action: 'read', resource: 'assessments' },
    { action: 'write', resource: 'assessments' },
    { action: 'read', resource: 'references' },
    { action: 'write', resource: 'references' },
    { action: 'read', resource: 'analytics' },
  ],
  recruiter: [
    { action: 'read', resource: 'candidates' },
    { action: 'write', resource: 'candidates', conditions: { assigned_jobs: true } },
    { action: 'read', resource: 'jobs', conditions: { assigned_jobs: true } },
    { action: 'read', resource: 'lia_insights' },
    { action: 'execute', resource: 'lia_actions', conditions: { basic_actions: true } },
    { action: 'read', resource: 'interviews' },
    { action: 'write', resource: 'interviews', conditions: { own_interviews: true } },
    { action: 'read', resource: 'assessments' },
    { action: 'write', resource: 'assessments', conditions: { basic_assessments: true } },
    { action: 'read', resource: 'references' },
  ],
  intern: [
    { action: 'read', resource: 'candidates', conditions: { assigned_jobs: true } },
    { action: 'read', resource: 'jobs', conditions: { assigned_jobs: true } },
    { action: 'read', resource: 'lia_insights', conditions: { basic_insights: true } },
    { action: 'read', resource: 'interviews', conditions: { assigned_interviews: true } },
  ]
}

// Ações LIA por nível de permissão
export const LIA_ACTIONS_BY_ROLE: Record<UserRole, string[]> = {
  admin: [
    'fazer_triagem',
    'agendar_entrevista',
    'coletar_dados',
    'enviar_whatsapp',
    'atualizar_avaliacao',
    'identificar_pendencias',
    'compartilhar_perfil',
    'solicitar_atualizacao',
    'enviar_vaga',
    'link_inscricao',
    'enviar_testes',
    'gerar_relatorio',
    'arquivar_perfil',
    'transferir_candidato',
    'criar_alerta',
    'feedback_construtivo',
    'analise_gap',
    'solicitar_referencias',
    'sugestao_oferta'
  ],
  manager: [
    'fazer_triagem',
    'agendar_entrevista',
    'coletar_dados',
    'enviar_whatsapp',
    'atualizar_avaliacao',
    'identificar_pendencias',
    'compartilhar_perfil',
    'solicitar_atualizacao',
    'enviar_vaga',
    'link_inscricao',
    'enviar_testes',
    'gerar_relatorio',
    'solicitar_referencias',
    'sugestao_oferta',
    'feedback_construtivo',
    'transferir_candidato'
  ],
  senior_recruiter: [
    'fazer_triagem',
    'agendar_entrevista',
    'coletar_dados',
    'enviar_whatsapp',
    'atualizar_avaliacao',
    'identificar_pendencias',
    'compartilhar_perfil',
    'solicitar_atualizacao',
    'enviar_vaga',
    'link_inscricao',
    'enviar_testes',
    'solicitar_referencias',
    'feedback_construtivo'
  ],
  recruiter: [
    'fazer_triagem',
    'agendar_entrevista',
    'coletar_dados',
    'enviar_whatsapp',
    'identificar_pendencias',
    'compartilhar_perfil',
    'solicitar_atualizacao',
    'enviar_vaga',
    'link_inscricao'
  ],
  intern: [
    'coletar_dados',
    'identificar_pendencias',
    'solicitar_atualizacao'
  ]
}

class PermissionManager {
  private user: User | null = null

  setUser(user: User) {
    this.user = user
  }

  getUser(): User | null {
    return this.user
  }

  hasPermission(action: string, resource: string, context?: Record<string, unknown>): boolean {
    if (!this.user) return false

    const permissions = ROLE_PERMISSIONS[this.user.role] || []

    // Verificar se tem permissão global (admin)
    const globalPermission = permissions.find(p =>
      (p.action === '*' && p.resource === '*')
    )
    if (globalPermission) return true

    // Verificar permissão específica
    const specificPermission = permissions.find(p =>
      (p.action === action || p.action === '*') &&
      (p.resource === resource || p.resource === '*')
    )

    if (!specificPermission) return false

    // Verificar condições se existirem
    if (specificPermission.conditions && context) {
      return this.checkConditions(specificPermission.conditions, context)
    }

    return true
  }

  canUseLiaAction(actionId: string): boolean {
    if (!this.user) return false
    const allowedActions = LIA_ACTIONS_BY_ROLE[this.user.role] || []
    return allowedActions.includes(actionId)
  }

  canManageUser(targetUser: User): boolean {
    if (!this.user) return false

    const roleHierarchy: Record<UserRole, number> = {
      intern: 1,
      recruiter: 2,
      senior_recruiter: 3,
      manager: 4,
      admin: 5
    }

    return roleHierarchy[this.user.role] > roleHierarchy[targetUser.role]
  }

  canAccessPage(page: string): boolean {
    const pagePermissions: Record<string, { action: string, resource: string }> = {
      'analytics': { action: 'read', resource: 'analytics' },
      'settings': { action: 'read', resource: 'settings' },
      'team_performance': { action: 'read', resource: 'team_performance' },
      'reports': { action: 'read', resource: 'reports' },
      'candidates': { action: 'read', resource: 'candidates' },
      'jobs': { action: 'read', resource: 'jobs' },
    }

    const permission = pagePermissions[page]
    if (!permission) return true // Páginas não mapeadas são liberadas por padrão

    return this.hasPermission(permission.action, permission.resource)
  }

  getRoleLabel(): string {
    if (!this.user) return 'Usuário'

    const roleLabels: Record<UserRole, string> = {
      admin: 'Administrador',
      manager: 'Gestor',
      senior_recruiter: 'Recrutador Sênior',
      recruiter: 'Recrutador',
      intern: 'Estagiário'
    }

    return roleLabels[this.user.role]
  }

  getAvailableLiaActions(): { id: string, label: string, icon: string }[] {
    if (!this.user) return []

    const actionLabels: Record<string, { label: string, icon: string }> = {
      fazer_triagem: { label: 'Fazer Triagem', icon: 'target' },
      agendar_entrevista: { label: 'Agendar Entrevista', icon: 'calendar' },
      coletar_dados: { label: 'Coletar Dados', icon: 'clipboard' },
      enviar_whatsapp: { label: 'Enviar WhatsApp', icon: 'phone' },
      atualizar_avaliacao: { label: 'Atualizar Avaliação', icon: 'refresh' },
      identificar_pendencias: { label: 'Identificar Pendências', icon: 'alert' },
      compartilhar_perfil: { label: 'Compartilhar Perfil', icon: 'share' },
      solicitar_atualizacao: { label: 'Solicitar Atualização', icon: 'edit' },
      enviar_vaga: { label: 'Enviar Vaga', icon: 'briefcase' },
      link_inscricao: { label: 'Link de Inscrição', icon: 'link' },
      enviar_testes: { label: 'Enviar Testes', icon: 'test-tube' },
      gerar_relatorio: { label: 'Gerar Relatório', icon: 'file-text' },
      solicitar_referencias: { label: 'Solicitar Referências', icon: 'users' },
      sugestao_oferta: { label: 'Sugestão de Oferta', icon: 'dollar-sign' },
      feedback_construtivo: { label: 'Feedback Construtivo', icon: 'brain' },
      transferir_candidato: { label: 'Transferir Candidato', icon: 'arrow-right' },
      criar_alerta: { label: 'Criar Alerta', icon: 'bell' },
      arquivar_perfil: { label: 'Arquivar Perfil', icon: 'archive' },
      analise_gap: { label: 'Análise de Gap', icon: 'trending-up' }
    }

    const allowedActions = LIA_ACTIONS_BY_ROLE[this.user.role] || []

    return allowedActions.map(actionId => ({
      id: actionId,
      ...actionLabels[actionId]
    })).filter(action => action.label) // Remove ações sem label
  }

  private checkConditions(conditions: Record<string, unknown>, context: Record<string, unknown>): boolean {
    // Implementar lógica de verificação de condições
    for (const [key, value] of Object.entries(conditions)) {
      if (context[key] !== value) {
        return false
      }
    }
    return true
  }
}

// Instância global do gerenciador de permissões
export const permissionManager = new PermissionManager()

// Hook para usar permissões
export function usePermissions() {
  const user = permissionManager.getUser()

  return {
    user,
    hasPermission: (action: string, resource: string, context?: Record<string, unknown>) =>
      permissionManager.hasPermission(action, resource, context),
    canUseLiaAction: (actionId: string) => permissionManager.canUseLiaAction(actionId),
    canManageUser: (targetUser: User) => permissionManager.canManageUser(targetUser),
    canAccessPage: (page: string) => permissionManager.canAccessPage(page),
    getRoleLabel: () => permissionManager.getRoleLabel(),
    getAvailableLiaActions: () => permissionManager.getAvailableLiaActions(),
  }
}

// Função para definir usuário atual (usar no login)
export function setCurrentUser(user: User) {
  permissionManager.setUser(user)
}

// Usuários mock para teste
export const mockUsers: User[] = [
  {
    id: '1',
    name: 'Ana Silva',
    email: 'recrutador.senior@empresa.com',
    role: 'senior_recruiter',
    department: 'RH',
    company: 'Sodexo'
  },
  {
    id: '2',
    name: 'Carlos Mendes',
    email: 'carlos.mendes@sodexo.com',
    role: 'manager',
    department: 'Tecnologia',
    company: 'Sodexo'
  },
  {
    id: '3',
    name: 'Pedro Santos',
    email: 'pedro.santos@sodexo.com',
    role: 'admin',
    department: 'RH',
    company: 'Sodexo'
  },
  {
    id: '4',
    name: 'Maria Costa',
    email: 'maria.costa@sodexo.com',
    role: 'recruiter',
    department: 'RH',
    company: 'Sodexo'
  },
  {
    id: '5',
    name: 'João Estagiário',
    email: 'joao.estagiario@sodexo.com',
    role: 'intern',
    department: 'RH',
    company: 'Sodexo'
  }
]
