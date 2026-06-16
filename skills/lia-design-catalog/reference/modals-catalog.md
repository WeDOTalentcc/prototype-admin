# Modals Catalog Reference - Design System LIA v4.1

## 58+ Modals by Size

### XS - Micro (max-w-sm - 384px) - 5 modals
| Modal | Uso |
|-------|-----|
| data-blocking-modal | Aviso de bloqueio |
| insufficient-data-modal | Dados insuficientes |
| confirm-delete-modal | Confirmação exclusão |
| session-expired-modal | Sessão expirada |
| logout-confirm-modal | Confirmar logout |

### S - Compacto (max-w-md - 448px) - 12 modals
| Modal | Uso |
|-------|-----|
| add-to-list-modal | Adicionar a lista |
| screening-settings-modal | Config triagem |
| new-candidate-unified-modal | Novo candidato |
| quick-note-modal | Nota rápida |
| tag-management-modal | Gerenciar tags |
| share-job-modal | Compartilhar vaga |
| export-options-modal | Opções exportação |
| filter-save-modal | Salvar filtro |
| template-select-modal | Selecionar template |
| shortcut-help-modal | Atalhos teclado |

### M - Médio (max-w-lg - 512px) - 18 modals
| Modal | Uso |
|-------|-----|
| close-vacancy-modal | Fechar vaga |
| data-request-modal | Solicitar dados |
| bulk-action-modal | Ações em massa |
| interview-schedule-modal | Agendar entrevista |
| feedback-modal | Feedback candidato |
| reject-reason-modal | Motivo rejeição |
| stage-config-modal | Config etapa |
| notification-settings-modal | Config notificações |
| email-template-modal | Template email |
| user-invite-modal | Convidar usuário |
| role-permissions-modal | Permissões |
| integration-config-modal | Config integração |
| api-key-modal | Chave API |

### L - Amplo (max-w-2xl - 672px) - 15 modals
| Modal | Uso |
|-------|-----|
| edit-job-modal | Edição de vaga |
| smart-transition-modal | Transição inteligente |
| job-status-modal | Status de vagas |
| job-publish-modal | Publicar vagas |
| general-score-modal | Nota Geral LIA |
| candidate-profile-modal | Perfil candidato |
| interview-notes-modal | Notas entrevista |
| assessment-results-modal | Resultados avaliação |
| report-config-modal | Config relatório |
| pipeline-config-modal | Config pipeline |
| import-candidates-modal | Importar candidatos |

### XL - Extra (max-w-4xl - 896px) - 8 modals
| Modal | Uso |
|-------|-----|
| job-insights-modal | Insights de vagas |
| job-compare-modal | Comparar vagas |
| unified-communication-modal | Hub comunicação |
| big-five-modal (full) | Relatório Big Five |
| candidate-compare-modal | Comparar candidatos |
| analytics-detail-modal | Detalhe analytics |
| audit-log-modal | Log de auditoria |

## Modal Checklist

When creating or reviewing ANY modal:

**Tamanho:**
- [ ] Using one of 5 standard sizes: XS(384), S(448), M(512), L(672), XL(896)
- [ ] NOT using max-w-xl, max-w-3xl, or max-w-5xl

**Tipografia:**
- [ ] Title: 14px semibold gray-900 (Open Sans)
- [ ] Description: 12px normal gray-600 (Inter)
- [ ] Labels: 11px semibold gray-800 (Inter)
- [ ] Body text: 12-14px normal gray-700 (Inter)
- [ ] No text smaller than 10px

**Cores:**
- [ ] Titles in gray-900
- [ ] Body in gray-700/800
- [ ] Primary button: bg-gray-900 (NEVER cyan)
- [ ] Secondary buttons: border gray-300

**Componentes:**
- [ ] Icon in header: w-5 h-5
- [ ] Footer with buttons aligned right
- [ ] Focus ring implemented
- [ ] ARIA labels correct (role="dialog", aria-labelledby, aria-modal="true")

**Overlay:**
- [ ] bg-black/50 backdrop-blur-sm
- [ ] z-40 for overlay, z-50 for modal

**Animation:**
- [ ] modalFadeIn: scale(0.95) + translateY(10px) → scale(1) + translateY(0)
- [ ] Duration: 150ms cubic-bezier(0.4, 0, 0.2, 1)
