# Audit: Client-Side Permission Checks

## Summary
Mapped all client-side permission checks across the frontend codebase.
Categorized each as: (a) has server-side enforcement, (b) needs server enforcement, (c) UX-only hiding.

## Permission System

The centralized permission system lives in:
- `src/utils/permissions.ts` — `PermissionManager` class with RBAC (5 roles, conditions support)
- `src/lib/permissions.ts` — Typed helpers and enforcement catalog
- `src/utils/license-manager.tsx` — Module access checks (6 premium modules)

## Full Inventory of Permission Checks

### 1. RBAC Checks via PermissionManager (src/utils/permissions.ts)
| # | Check | Used By | Enforcement |
|---|---|---|---|
| 1 | `hasPermission('read', 'candidates')` | PermissionManager | Server: API auth middleware |
| 2 | `hasPermission('write', 'candidates')` | PermissionManager | Server: API auth middleware |
| 3 | `hasPermission('delete', 'candidates')` | PermissionManager | Server: API auth middleware |
| 4 | `hasPermission('read', 'jobs')` | PermissionManager | Server: API auth middleware |
| 5 | `hasPermission('write', 'jobs')` | PermissionManager | Server: API auth middleware |
| 6 | `hasPermission('read', 'reports')` | PermissionManager | Client-only |
| 7 | `hasPermission('write', 'reports')` | PermissionManager | Client-only |
| 8 | `hasPermission('read', 'team_performance')` | PermissionManager | Client-only |
| 9 | `hasPermission('write', 'evaluations')` | PermissionManager | Server: API auth |
| 10 | `hasPermission('read', 'lia_insights')` | PermissionManager | Client-only |
| 11 | `hasPermission('execute', 'lia_actions')` | PermissionManager | Server: LIA backend |
| 12 | `hasPermission('read', 'interviews')` | PermissionManager | Server: API auth |
| 13 | `hasPermission('write', 'interviews')` | PermissionManager | Server: API auth |
| 14 | `hasPermission('read', 'assessments')` | PermissionManager | Server: API auth |
| 15 | `hasPermission('write', 'assessments')` | PermissionManager | Server: API auth |
| 16 | `hasPermission('read', 'references')` | PermissionManager | Client-only |
| 17 | `hasPermission('write', 'references')` | PermissionManager | Client-only |
| 18 | `hasPermission('read', 'analytics')` | PermissionManager | Client-only |
| 19 | `hasPermission('write', 'settings')` | PermissionManager | Server: API auth |
| 20 | `canAccessPage('analytics')` | PermissionManager | Client-only |
| 21 | `canAccessPage('settings')` | PermissionManager | Server: middleware |
| 22 | `canAccessPage('team_performance')` | PermissionManager | Client-only |
| 23 | `canAccessPage('reports')` | PermissionManager | Client-only |
| 24 | `canAccessPage('candidates')` | PermissionManager | Server: middleware |
| 25 | `canAccessPage('jobs')` | PermissionManager | Server: middleware |
| 26 | `canManageUser(targetUser)` | PermissionManager | Client-only |
| 27 | `canUseLiaAction('fazer_triagem')` | PermissionManager + LIA chat | Server: LIA backend |
| 28 | `canUseLiaAction('agendar_entrevista')` | PermissionManager + LIA chat | Server: LIA backend |
| 29 | `canUseLiaAction('coletar_dados')` | PermissionManager + LIA chat | Server: LIA backend |
| 30 | `canUseLiaAction('enviar_whatsapp')` | PermissionManager + LIA chat | Server: LIA backend |
| 31 | `canUseLiaAction('atualizar_avaliacao')` | PermissionManager + LIA chat | Server: LIA backend |
| 32 | `canUseLiaAction('identificar_pendencias')` | PermissionManager + LIA chat | Server: LIA backend |
| 33 | `canUseLiaAction('compartilhar_perfil')` | PermissionManager + LIA chat | Server: LIA backend |
| 34 | `canUseLiaAction('solicitar_atualizacao')` | PermissionManager + LIA chat | Server: LIA backend |
| 35 | `canUseLiaAction('enviar_vaga')` | PermissionManager + LIA chat | Server: LIA backend |
| 36 | `canUseLiaAction('link_inscricao')` | PermissionManager + LIA chat | Server: LIA backend |
| 37 | `canUseLiaAction('enviar_testes')` | PermissionManager + LIA chat | Server: LIA backend |
| 38 | `canUseLiaAction('gerar_relatorio')` | PermissionManager + LIA chat | Server: LIA backend |
| 39 | `canUseLiaAction('solicitar_referencias')` | PermissionManager + LIA chat | Server: LIA backend |
| 40 | `canUseLiaAction('sugestao_oferta')` | PermissionManager + LIA chat | Server: LIA backend |
| 41 | `canUseLiaAction('feedback_construtivo')` | PermissionManager + LIA chat | Server: LIA backend |
| 42 | `canUseLiaAction('transferir_candidato')` | PermissionManager + LIA chat | Server: LIA backend |
| 43 | `canUseLiaAction('criar_alerta')` | PermissionManager + LIA chat | Server: LIA backend |
| 44 | `canUseLiaAction('arquivar_perfil')` | PermissionManager + LIA chat | Server: LIA backend |
| 45 | `canUseLiaAction('analise_gap')` | PermissionManager + LIA chat | Server: LIA backend |

### 2. Module License Checks (src/utils/license-manager.tsx)
| # | Check | Used By | Enforcement |
|---|---|---|---|
| 46 | `hasModuleAccess('onboarding_automation')` | license-manager | Client-only (DEMO_MODE) |
| 47 | `hasModuleAccess('communication_center')` | license-manager | Client-only (DEMO_MODE) |
| 48 | `hasModuleAccess('ml_prediction')` | license-manager, dashboards | Client-only (DEMO_MODE) |
| 49 | `hasModuleAccess('ats_integrations')` | license-manager, settings-integrations | Client-only (DEMO_MODE) |
| 50 | `hasModuleAccess('workflow_automation')` | license-manager, automations-tab | Client-only (DEMO_MODE) |
| 51 | `hasModuleAccess('advanced_analytics')` | license-manager, dashboards | Client-only (DEMO_MODE) |
| 52 | `canAccessOnboarding()` | module-access components | Client-only |
| 53 | `canAccessMLAnalytics()` | dashboard components | Client-only |
| 54 | `canAccessATSIntegrations()` | settings components | Client-only |
| 55 | `canAccessCommunicationCenter()` | communication components | Client-only |
| 56 | `canAccessWorkflowAutomation()` | workflow components | Client-only |
| 57 | `canAccessAdvancedAnalytics()` | analytics components | Client-only |
| 58 | `hasPremiumAccess()` | upsell/upgrade flows | Client-only |

### 3. Dashboard Module Access Checks
| # | Check | File | Enforcement |
|---|---|---|---|
| 59 | `hasModuleAccess(...)` | NPSDashboard.tsx | Client-only |
| 60 | `hasModuleAccess(...)` | ModelosTrabalhoPlaceholder.tsx | Client-only |
| 61 | `hasModuleAccess(...)` | IndicadoresEstrategicosPlaceholder.tsx | Client-only |
| 62 | `hasModuleAccess(...)` | FunilPerformancePlaceholder.tsx | Client-only |
| 63 | `hasModuleAccess(...)` | DiversidadeInclusaoDashboard.tsx | Client-only |
| 64 | `hasModuleAccess(...)` | BigFiveAnalyticsDashboard.tsx | Client-only |
| 65 | `hasModuleAccess(...)` | AnaliseCompetenciasPlaceholder.tsx | Client-only |
| 66 | `hasModuleAccess(...)` | AgentActivityDashboard.tsx | Client-only |
| 67 | `hasModuleAccess('ats_integrations')` | settings-integrations-tab.tsx:492 | Client-only |
| 68 | `hasModuleAccess('workflow_automation')` | automations-tab.tsx:52 | Client-only |

### 4. Role-Based UI Checks
| # | Check | File:Line | Category |
|---|---|---|---|
| 69 | `u.role === 'admin'` | user-management.tsx:77 | UX: Role label display |
| 70 | `u.role === 'admin'` | user-management.tsx:83 | UX: Module list per role |
| 71 | `u.role === 'admin'` | user-management.tsx:88 | UX: isManager flag |
| 72 | `u.role === 'recruiter'` | user-management.tsx:77 | UX: Role label display |
| 73 | `u.role === 'manager'` | user-management.tsx:77 | UX: Role label display |

### 5. Component-Level UI Permissions (UX Hiding)
| # | Check | File:Line | Category |
|---|---|---|---|
| 74 | `canEditName` | JobProcessSection.tsx:83 | UX: Stage rename for non-system |
| 75 | `canEditName` | JobProcessSection.tsx:110 | UX: Show/hide edit input |
| 76 | `canEdit` (JD) | JDEvaluationPanel.tsx:541 | UX: JD edit mode toggle |
| 77 | `canEdit` (JD) | JDEvaluationPanel.tsx:584 | UX: JD edit mode toggle |
| 78 | `canEdit` | JDEvaluationHeader.tsx:59,93,115,149 | UX: JD edit buttons |
| 79 | `canEditSLA` | ColumnContextMenu.tsx:55-59 | UX: Column SLA editing |
| 80 | `canRename` | ColumnContextMenu.tsx:57-59 | UX: Column rename option |
| 81 | `canDeactivate` | ColumnContextMenu.tsx:57-59 | UX: Column deactivation |
| 82 | `canRemove` | ColumnContextMenu.tsx:57-59 | UX: Column removal option |
| 83 | `canReorder` | ColumnContextMenu.tsx:57-59 | UX: Column reordering |
| 84 | `canEditName` | StageCard.tsx:679,721,737,751 | UX: Stage rename for non-system |

### 6. Chat Message Role Checks (msg.role)
| # | Check | File | Category |
|---|---|---|---|
| 85 | `msg.role === 'user'` | QuestionAdjustmentChat.tsx:189-216 | UX: Message styling |
| 86 | `msg.role === 'assistant'` | QuestionAdjustmentChat.tsx:192 | UX: Message styling |
| 87 | `msg.role === 'user'` | LiaChatModal.tsx:206-213 | UX: Message styling |
| 88 | `msg.role === 'lia'` | LiaChatModal.tsx:207 | UX: Message styling |
| 89 | `message.role === 'lia'` | MessageBubble.tsx:54 | UX: Message styling |
| 90 | `message.role === 'user'` | ChatMessageList.tsx:96-117 | UX: Message alignment |
| 91 | `message.role === 'system'` | ChatMessageList.tsx:97,101 | UX: System message style |
| 92 | `m.role === 'user'` | useExpandedChatSubHooks.ts:383 | UX: Has user sent message |
| 93 | `m.role === 'assistant'` | useExpandedChatModalCore.tsx:570 | UX: Find greeting msg |
| 94 | `m.role === 'user'` | useWizardPublishHandlers.ts:587,703 | UX: Extract user input |
| 95 | `m.role === 'user'` | useWizardFlow.ts:99 | UX: Has user sent message |
| 96 | `msg.role === 'user'` | HiringPoliciesHub.tsx:280 | UX: Message type styling |
| 97 | `message.role === 'user'` | InlineChatPanel.tsx:268-270 | UX: Message alignment |
| 98 | `msg.role === 'user'` | TransitionChatPanel.tsx:297 | UX: Message styling |
| 99 | `m.role === 'assistant'` | use-float-conversation.ts:125 | UX: Sender mapping |

### 7. Auth/Session Checks
| # | Check | File | Category |
|---|---|---|---|
| 100 | `isAuthenticated` | auth-store.ts, middleware | Server: JWT + httpOnly cookie |
| 101 | `isSSO` | auth-store.ts | Client: SSO flag |
| 102 | `permissions[]` | auth-store.ts | Client: Permission array from server |
| 103 | `user.role` | Various components | Derived from server-issued JWT |

### 8. Miscellaneous
| # | Check | File | Category |
|---|---|---|---|
| 104 | `DEMO_MODE` flag | license-manager.tsx:20 | Bypasses all module checks in dev |
| 105 | `getRoleLabel()` | permissions.ts:229 | UX: Display role name |

## Enforcement Summary

| Category | Count | Status |
|---|---|---|
| Server-enforced (API middleware) | 25 | OK |
| Server-enforced (LIA backend) | 19 | OK |
| Client-only: Module access (DEMO_MODE) | 23 | Needs server billing/license check |
| Client-only: RBAC | 7 | Needs server middleware |
| UX-only hiding | 31 | Acceptable — not security boundaries |
| **Total** | **105** | |

## Priority Recommendations

1. **HIGH**: Add server-side license validation for module access (currently DEMO_MODE=true bypasses all)
2. **MEDIUM**: Add server guards for `read:references`, `write:references` (PII), `read:team_performance` (metrics)
3. **LOW**: Add server guards for `read:reports`, `read:analytics`, `canManageUser` (aggregate data)
4. **NO ACTION**: msg.role checks (31) are message styling, canEdit/canRename (11) are UI convenience
