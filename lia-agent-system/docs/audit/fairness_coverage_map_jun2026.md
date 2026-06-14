# FairnessGuard — Mapa de Cobertura na Plataforma (Jun 2026)

**Data**: 2026-06-14
**Versao**: 2.0 (atualizacao pos-correcao do gap do Funil)
**Relacionado**: fairness_global.md (v1, Abr 2026) -- nao sobrescrever (auditabilidade historica)

---

## 1. O que e o FairnessGuard

app/shared/compliance/fairness_guard.py -- detecta queries discriminatorias com 3 camadas:
- Camada 1: regex explicito (~80 padroes, 19 categorias PT-BR+EN)
- Camada 2: lexico implicito (~60 termos, soft warnings nao-bloqueantes)
- Camada 3: LLM semantico (apenas HIGH_IMPACT_ACTIONS, claude-haiku)

Base legal: CLT Art. 373-A, CF Art. 5 I/VIII, Lei 9.029/95, Lei 7.716/89, LGPD Art. 20.

---

## 2. Onde esta wired (cobertura completa Jun 2026)

| Surface | Arquivo | Quando | Shape HTTP |
|---|---|---|---|
| Chat LIA | app/api/v1/chat.py ~1095 | Qualquer msg recruiter | 400 educational_message |
| Busca candidatos (Funil) | app/api/v1/candidate_search/search.py ~134 | Query NL antes hybrid search | 400 fairness_blocked + educational_message |
| Arquetipos de busca | app/api/v1/candidate_search/archetypes.py ~1234 | Descricao antes LLM | 400 mesmo shape |
| Motivo de rejeicao | app/domains/candidates/candidates_crud.py ~785 | Ao registrar rejeicao | 400 fairness_blocked |
| Salvar JD/vaga | app/api/v1/job_vacancies/_shared.py ~619 | Ao gravar descricao | 422 + educational_message |
| Importar JD | app/domains/job_management/services/jd_import.py ~133 | Import arquivo/URL | Aviso ou bloqueio |
| Parecer entrevista (IA) | app/api/v1/interview_notes.py ~1035 | Gerar parecer LLM | Texto substituido por placeholder |
| Bulk actions (notas) | app/api/v1/bulk_actions.py ~322 | Acao em massa com notas | Bloqueio |
| Agente Sourcing | app/domains/sourcing/sourcing_react_agent.py ~287 | Chat ReAct sourcing | educational_message no response |

---

## 3. Como aparece no FE por surface

### Chat LIA
Mensagem substituida por texto educativo como bolha da LIA no painel lateral.

### Funil de Talentos -- Busca (NOVO Jun 2026)
Dupla exibicao:
1. Banner ambar inline sob o campo de busca (role=alert, ShieldAlert icon, dismiss)
2. Bolha LIA no painel lateral (setChatMessages type=lia)

Estado limpo ao iniciar nova busca.
FE detecta: errBody.error === fairness_blocked OU errBody.fairness_blocked === true (flat JSON).

Commits: dee824604 (BE) + ed27c6d1b (FE).

### Motivo de rejeicao
HTTP 400 -- form validation inline no campo de motivo.

### JD/Vaga
HTTP 422 com educational_message -- validation error no form.

---

## 4. Gaps identificados

| Gap | Status |
|---|---|
| Busca NL do Funil | CORRIGIDO Jun 2026 |
| Filtros estruturados (dropdown/checkbox discriminatorio) | Nao coberto -- UI nao deveria oferecer esses filtros |
| Boolean search (modo avancado) | A verificar |

---

## 5. Padrao de implementacao para novos endpoints

from app.shared.compliance.fairness_guard import FairnessGuard

_fairness_guard = FairnessGuard()  # modulo-level

Se user_text nao for vazio:
    fg_result = _fairness_guard.check(user_text)
    Se fg_result.is_blocked:
        raise HTTPException(400, detail com error=fairness_blocked, fairness_blocked=True, educational_message, category, blocked_terms)

---

## 6. Sensores de contrato

- tests/unit/test_fairness_candidate_search.py (4 testes TDD, blocking)
- tests/contract/test_offer_approval_gate.py (gate hard toggle padrao)

---

Documento gerado Jun 2026. Para historico anterior ver fairness_global.md (Abr 2026).

## 8. Surfaces de Governanca no Menu Configuracoes (Jun 2026)

Auditoria dos 12 componentes de compliance/fairness/LGPD em
plataforma-lia/src/components/settings/.

### Status por componente

| Componente | Arquivo | Status |
|---|---|---|
| FairnessComplianceHub | FairnessComplianceHub.tsx | WIRED (dispatcher) |
| ComplianceOverviewPanel | ComplianceOverviewPanel.tsx | GHOST - valores mock P3 |
| StudioComplianceView | StudioComplianceView.tsx | WIRED |
| ConsentPanel (3 tabs) | governance/ConsentPanel.tsx | WIRED |
| DSRInboxPanel | governance/DSRInboxPanel.tsx | WIRED |
| AuditLogsSummaryPanel | compliance/AuditLogsSummaryPanel.tsx | WIRED |
| AuditLogsDrillDownClientPanel | compliance/AuditLogsDrillDownClientPanel.tsx | WIRED admin-only |
| PiiFieldVisibilityMatrix | PiiFieldVisibilityMatrix.tsx | WIRED |
| PiiVisibilityRoleDefaults | PiiVisibilityRoleDefaults.tsx | WIRED |
| RecruitmentScreeningTab | RecruitmentScreeningTab.tsx | WIRED |
| AutomationTemplatesView | recruitment/AutomationTemplatesView.tsx | GHOST hardcoded |
| PolicyEngine (3 modais) | governance/policy-engine/ | GHOST status desconhecido |

9/12 WIRED. 3/12 GHOST.

### Gaps

- ComplianceOverviewPanel: 5 KPI cards com valores -- (mock). Endpoints TODO P3.
- AutomationTemplatesView: 8 templates hardcoded. API TODO Sprint B.3.
- PolicyEngine: 3 modais existem sem integracao visivel.
- Dashboard DEI dedicado: nao existe.

Para detalhe completo ver Notion HANDOFF Fairness+LGPD (Jun 2026).

---

## 9. Detalhes tecnicos internos (fairness_global.md Abr 2026)

> Secao derivada de docs/audit/fairness_global.md v1 (Abr 2026 -- nao sobrescrito por este arquivo).
> Incorporada aqui para consolidar as duas fontes para engenheiros e auditores.

### Estado interno do FairnessGuard

- _PATTERNS_VERSION = 5 -- deve ser incrementada ao adicionar regras; requer redeploy para recarregar
- FAIRNESS_LAYER3_ENABLED=True -- camada semantica LLM ATIVA (verificado Jun 2026: .env:94 + runtime confirmado). fairness_global.md Abr 2026 afirmava False -- estava desatualizado.
  Em producao padrao apenas Camada 1 (regex) + Camada 2 (lexico) estao ativas.
- check_with_sector(sector) -- regras por setor: tech/finance/health/RPO (habilitados); retail/logistics (desabilitados)

### Cobertura por agente (lacuna identificada)

Apenas 4 de 14 agentes que herdam de EnhancedAgentMixin chamam _fairness_pre_check diretamente:
- WizardReActAgent
- TalentReActAgent
- KanbanReActAgent
- JobsManagementReActAgent

Os outros 10 dependem exclusivamente do gate no MainOrchestrator. Se um agente for invocado
diretamente (bypass do orquestrador), o gate de fairness nao dispara.

### Gaps de observability e correlacao de auditoria

| Gap | Local | Impacto |
|---|---|---|
| FairnessAuditLog sem execution_id / session_id | app/domains/compliance/ | Eventos de fairness nao correlacionaveis com ExecutionAuditRecord |
| AuditCallback sem campos de fairness | app/shared/audit_callback.py | Bloqueio de fairness dentro de agente nao aparece no audit trail de execucao |
| GET /v1/fairness-reports desconectado do timeline | app/api/v1/fairness_reports.py | API existe mas dados separados do audit trail principal |

### Propostas de roadmap (fairness_global.md Abr 2026)

- Tabela fairness_rules no DB -- regras editaveis via admin sem redeploy (CRUD API)
- Domain-scoped rules -- regras diferentes por dominio (sourcing, triagem, rejeicao)
- Integracao com observability -- fairness events no mesmo timeline que execucoes (via execution_id)
- Estimativa: 4-6 dias de engenharia
