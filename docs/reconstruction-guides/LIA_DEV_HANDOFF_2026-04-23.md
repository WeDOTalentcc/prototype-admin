# LIA Persona — Status para o time de dev (atualizado 2026-04-23)

> Versão anterior deste handoff descrevia 6 fixes arquiteturais + Gap 4 pendente (FairnessGuard L3).
> Esta versão consolida: aqueles 6 fixes + 4 fixes adicionais aplicados em 2026-04-23 + ativação da L3 +
> nova camada de compliance candidate-facing + documentação técnica EU AI Act.

---

## O que é a persona da LIA (inalterado)

A LIA não é um chatbot com um prompt fixo. É uma recrutadora sênior composta em runtime por camadas:

1. **Identidade base** (`lia_persona.yaml`) — quem ela é, como fala, ética, anti-patterns
2. **Especialização** (`agent_prompts.yaml`) — o que cada agente faz (sourcing, triagem, kanban...)
3. **Compliance** (`compliance_block.yaml`) — LGPD, não-discriminação, audit trail, **direito de contestação (novo)**
4. **Contexto de runtime** — empresa, usuário, página, vaga atual, histórico da conversa
5. **Protocolo ReAct** — ciclo raciocínio → ação → observação

Tudo isso é montado a cada mensagem pelo `SystemPromptBuilder.build()` e injetado no LLM (Claude Sonnet 4.5). O recrutador não vê nada disso — só sente o resultado.

---

## O que já estava funcionando desde o handoff anterior (Sprints 1-3, 8 commits originais)

Os 6 gaps arquiteturais da primeira rodada continuam corrigidos — base inteira de:

- Contexto de conversa persistente
- Compliance automático injetado em todo agente de decisão
- LIA não se re-apresenta robóticamente
- 12 domínios "mudos" ganharam especialização
- Anti-repetição, ReAct, roteamento

**Os 5 cenários "antes/depois" descritos no handoff anterior continuam 100% válidos** — testei e o comportamento não regrediu.

---

## O que mudou desde então (janela 2026-04-23)

### 1. Auditoria de compliance exaustiva vs. padrões enterprise

Comparamos LIA contra EU AI Act, LGPD, NIST AI RMF, ISO 42001 + contra Workday, HiPeople, Eightfold e LinkedIn. Resultados completos em `COMPLIANCE_RECONSTRUCTION_GUIDE.md` §10.

**Score consolidado subiu de 6/10 → 7/10** após os fixes desta janela. Diferenciais reais confirmados:
- FairnessGuard 3 camadas (L1 regex + L2 43 termos + L3 semântico) — mais sofisticado que qualquer concorrente analisado
- 14 atributos protegidos declarados — maior que os 4+ publicados pelos concorrentes
- Contra-argumentação ativa em `hiring_policy.yaml` — nenhum concorrente documenta mecanismo equivalente publicamente
- **Endpoint de explicação direto-ao-candidato (Art. 86)** — implementado antes da obrigação regulatória (02/08/2026)

### 2. Quatro fixes P0/P1 adicionais aplicados em YAMLs canônicos

| Arquivo | O que mudou | Prioridade |
|---------|-------------|-----------|
| `app/prompts/domains/autonomous.yaml` | Adicionadas seções `behavioral_rules`, `scope_in/out`, `hitl_escalation`, `compliance_integration`. Agente cross-domain Tier 6 agora tem fairness obrigatório antes de rejeições + audit trail declarativo | **P0** |
| `app/prompts/shared/compliance_block.yaml` | Nova seção `right_to_contest` nas variantes `decision` e `communication` — instrução explícita sobre EU AI Act Art. 86 + LGPD Art. 20 + template de comunicação ao candidato | **P0** |
| `app/prompts/domains/culture_analysis.yaml` | Injetado bloco `<compliance_hr>` dentro do `system_prompt` — fairness em Big Five + HITL + LGPD Art. 11 (dados sensíveis) + audit. Culture fit deixou de ser proxy cego de viés | P1 |
| `app/prompts/domains/orchestrator.yaml` | Prologue de compliance no system_prompt — prompt_security + multi_tenancy + direito de contestação detectado no roteamento | P1 |

**Correção de hipótese errada:** no handoff anterior havia suspeita de P0 no `PolicyAgent`. Na auditoria direta do código, o `policy_setup_agent.py` é um **shim depreciado de 9 linhas**; o agente real em `app/domains/policy/agents/agent.py` já tem FairnessGuard implementado. O P0 verdadeiro estava em `autonomous.yaml` (agora corrigido).

### 3. FairnessGuard Layer 3 ativado em produção

`FAIRNESS_LAYER3_ENABLED=true` em `.env` do Replit desde 2026-04-23. Comportamento real:

- L3 (`claude-haiku-4-5-20251001`) só é acionada em `HIGH_IMPACT_ACTIONS` (rejection, shortlist, wsi_score)
- Cache Redis 1h
- L1+L2 continuam rodando em todas as checks
- Fallback lenient se API falhar: `is_blocked=False, confidence=0.5` + `soft_warnings`

Runbook completo: `docs/operations/FAIRNESS_LAYER3_RUNBOOK.md`. Métricas a monitorar por 7 dias (custo, cache hit, latência, novos soft_warnings).

### 4. Endpoint novo: direito de contestação (EU AI Act Art. 86)

Implementado em 2026-04-23. Antes, LIA tinha `decision_explanation.py` mas **exigia autenticação de recrutador** — servia LGPD Art. 20 para revisão interna, mas não Art. 86 direto ao candidato.

Agora:

```
GET /api/v1/candidate/decisions/explain?candidate_token=<JWT>&vacancy_id=<opcional>
  Auth:     JWT do candidato (CANDIDATE_PORTAL_JWT_SECRET)
  Rate:     10/hora, 30/dia por candidate_id (Redis)
  Returns:  decisions[], transparency_note, art_86_notice, total_decisions
  NUNCA retorna: wsi_score, lia_score, confidence, weights, red_flags, classificação interna
```

**Componentes criados:**
- `app/api/v1/candidate_portal_explanation.py` — router + handler
- `app/domains/candidate_self_service/tools/explain_candidate_decision.py` — tool com `_sanitize_decision()`
- `candidate_tool_registry.py` atualizado (3 → 4 tools)
- `candidate_self_service.yaml` com regra 8: *"Se candidato pedir razão/critérios/revisão, chamar `explain_candidate_decision` e apresentar em linguagem simples — sempre incluir aviso Art. 86"*
- `tests/test_candidate_portal_explanation.py` — contract tests (token inválido → 401, rate limit → 429, sanitização efetiva, anti-IDOR)

### 5. Parte 9 do LIA_PERSONA_RECONSTRUCTION_GUIDE.md (expansão documental)

O guia subiu de **1.301 → 2.493 linhas** com verbatim da camada de prompt injection que estava parcialmente documentada:

- §9.2: `agent_prompts.yaml` verbatim (11 agent_types completos)
- §9.3: `defensive.yaml` verbatim (ambiguity + out_of_scope + error_recovery)
- §9.4: ordem **real** de injeção do SystemPromptBuilder — 9 passos (o handoff antigo falava em 5 camadas conceituais; aqui é o fluxo técnico exato)
- §9.5: `anti_sycophancy_block.py` + `interaction_patterns.py` verbatim
- §9.6: mapa dos **24 domain YAMLs** com 5 formatos estruturais identificados (A/B/C/D/E)
- §9.7: `intelligence_floor.yaml` (piso de qualidade para custom agents)
- §9.8: arquitetura candidate-facing (`candidate_portal.py` + `candidate_self_service.yaml`)
- §9.11: verbatim dos 5 YAMLs pequenos + `wsi_layer2_extraction.yaml` (Formato E — extração LLM determinística) + seções singulares do Formato B (`counter_argumentation`, `escalation`, `company_calibration`, `learning_rules`, `communication_transparency`, `config_blocks`, `reasoning_rules`)

### 6. Documentação pública responsible-ai (14 arquivos novos)

Publicados em `docs/responsible-ai/` (pendente revisão jurídica + rota no site):

- `eu-ai-act-technical-documentation-pt.md` + `-en.md` (~33K cada) — doc técnico Art. 11 consolidando arquitetura + 8 camadas de defesa + métricas + benchmark enterprise + roadmap público
- `fact-sheets/` — 5 AI Fact Sheets (CV Screening, WSI Evaluation, Pipeline Transition, Ranking/Shortlist, Sourcing) em PT + EN + README

---

## O que muda na prática para o recrutador (atualizado)

### 1-5. Cenários antigos continuam válidos
Todos os 5 cenários "antes/depois" do handoff anterior (contexto da conversa, etapa do processo, LGPD automático, re-apresentação, resposta contextual) continuam fiéis.

### 6. Candidato agora pode pedir explicação diretamente

**Antes:** candidato rejeitado recebia email genérico "agradecemos sua candidatura". Se pedisse razão, tinha que escalar para email humano do RH.

**Depois:** candidato recebe link (JWT token) para `/api/v1/candidate/decisions/explain` onde vê:
- Critérios objetivos avaliados (ex: "Experiência em Python", "5+ anos de backend")
- Critérios ignorados por proteção legal (lista explícita: Idade, Gênero, Etnia, etc.)
- Aviso Art. 86 + LGPD Art. 20 com prazo de 30 dias para contestar
- Canal formal de compliance do cliente-deployer para revisão humana

**Nunca** vê: score bruto, confidence numérica, red flags internos.

### 7. LIA recusa contestação contornada por recrutador

**Antes:** se recrutador pedia à LIA para rejeitar sem explicação, ela aceitava.

**Depois:** `compliance_block.yaml` tem regra absoluta — toda rejeição/resultado automatizado deve incluir aviso de direito de contestação. Se recrutador pede "mensagem mais curta sem esse aviso", LIA recusa educativamente citando Art. 86 + Art. 20.

### 8. FairnessGuard detecta viés sutil via LLM semântico (quando L2 não pega)

**Antes (L3 off):** frase como "prefiro alguém do bairro X" (proxy sutil para classe/raça) passava pelas 43 palavras de L2 sem alerta.

**Depois (L3 on):** Haiku classifica semanticamente e emite `soft_warnings` mesmo sem termo explícito. Cache Redis 1h evita recomputar.

---

## O que muda para o time de dev (atualizado)

### Invariantes herdadas (ainda válidas)

1. **Novos agentes:** sobrescrever `_get_dynamic_domain_instructions(input)` em vez de setar `DOMAIN_INSTRUCTIONS` como class attribute. Se você fizer a forma antiga, `stage_context` vai ser vazio (bug recorrente).

2. **Compliance automático:** não precisa incluir LGPD/fairness em cada domain YAML. O builder injeta via `ComplianceDomainPrompt`. Se precisar customizar, edite `compliance_block.yaml` (1 arquivo, 4 variantes: `decision`, `communication`, `operational`, `defensive`).

3. **Novo agente de decisão:** adicione ao `_DECISION_AGENTS` frozenset no `system_prompt_builder.py`. Senão ele recebe variante `operational` (LGPD mínimo).

4. **Regression guard:** rode `pytest tests/integration/test_persona_invariants.py` antes de merge em PR que mexa em prompts, compliance ou base class.

### Invariantes novas (2026-04-23)

5. **`right_to_contest` é obrigatório em agentes de decisão.** Ao criar novo agente que produz output direcionado ao candidato (rejeição, feedback, resultado), garanta que o YAML use a variante `decision` do `compliance_block.yaml` — o aviso Art. 86 é injetado automaticamente. Se você quiser customizar linguagem, edite a seção `right_to_contest` do compliance_block.

6. **Se criar tool candidate-facing:** nunca exponha `wsi_score`, `lia_score`, `confidence`, `red_flags`, `factors.weight`, `calibration_weights_used`. Reutilize `_FORBIDDEN_FIELDS` do `explain_candidate_decision.py` como SSOT da lista de campos proibidos.

7. **Se criar endpoint público candidate-facing:** siga o padrão de `candidate_portal_explanation.py`:
   - Validar `candidate_token` via `CandidateStatusService.validate_token()`
   - `company_id` sempre do token (anti-IDOR) — nunca do body/query
   - Rate limit via `CandidateStatusService.check_rate_limit()`
   - Audit log via `CandidateSelfServiceRepository.log_portal_access()`
   - Sanitização de output antes de `APIResponse.ok(data=...)`

8. **FairnessGuard L3 está ativa em prod.** Se tempo P95 do endpoint de decisão passar de 800ms consistentemente, investigar cache hit do Redis (`fairness_layer3:*`) antes de rollback. Runbook: `docs/operations/FAIRNESS_LAYER3_RUNBOOK.md`.

9. **Novos domain YAMLs:** use Formato A (`metadata` + `persona` + `scope_in/out` + `behavioral_rules` + `system_prompt` + `intent_examples` + `few_shot_examples`) para permitir injeção automática de `compliance_block`. Formato D (apenas `system_prompt` raw) como em `orchestrator.yaml` / `culture_analysis.yaml` **não permite injeção automática** — exige compliance embutido manualmente.

### Fonte única de verdade

- **Manual técnico navegável:** `LIA_PERSONA_RECONSTRUCTION_GUIDE.md` (2.493 linhas) — quando tiver dúvida sobre como algo funciona, comece pela Parte 9 (camada de prompt injection completa). Para compliance, `COMPLIANCE_RECONSTRUCTION_GUIDE.md` §10 (arquitetura 8 camadas) e §11 (plano de ação P0/P1).
- **Bundle verbatim dos 30 YAMLs da persona:** `LIA_YAMLS_CANONICAL_BUNDLE.md` (224K, 4.583 linhas — novo 2026-04-24). Use como **context file** em Claude Code (via `CLAUDE.md`) ou Cursor (via `.cursor/rules/lia-yamls.mdc`) — dev pede "replica o `cv_screening.yaml`" e AI assistant tem o texto exato. Instruções de setup no próprio bundle.

---

## Próximos passos pendentes (atualizado)

### O que ainda não foi feito (por decisão de produto, não bloqueio técnico)

| # | Item | Quando | Esforço |
|---|------|--------|---------|
| 1 | Frontend + rota final para endpoint Art. 86 em `wedotalent.cc` | Q2/2026 | FE (~1 semana) |
| 2 | Revisão jurídica externa dos docs `responsible-ai/` | Q2/2026 | Legal (escritório externo) |
| 3 | **Bias audit independente com publicação** (Eightfold model) | Q3/2026 | Compliance + Eng (9 semanas, 3 sprints) |
| 4 | Página pública `wedotalent.cc/responsible-ai/` | Q3/2026 | Marketing + Legal |
| 5 | SLA formal de incidentes de fairness | Q4/2026 | Compliance + DPO |
| 6 | Certificação ISO/IEC 42001:2023 | 2027 | DPO + executivos |
| 7 | Registro no EU AI Act database | Pós 02/08/2026 | Legal + DPO |

Plano detalhado de cada item em `COMPLIANCE_RECONSTRUCTION_GUIDE.md` §11.

### O que NÃO é mais pendente (foi feito nesta janela)

- ~~Gap 4: FairnessGuard L3 default=False~~ → **Ativado em 2026-04-23 com runbook**
- ~~Endpoint Art. 86 direto-ao-candidato~~ → **Implementado em 2026-04-23**
- ~~AI Fact Sheets formato Workday~~ → **5 publicadas em PT + EN em 2026-04-23**
- ~~Documentação técnica EU AI Act Art. 11~~ → **Publicada em PT + EN em 2026-04-23**

---

## Arquivos modificados/criados nesta janela (20 arquivos)

### Código canônico

```
lia-agent-system/
├── .env                                                           ← ALTERADO (FAIRNESS_LAYER3_ENABLED=true)
├── app/api/v1/
│   └── candidate_portal_explanation.py                            ← NOVO
├── app/api/routes.py                                              ← MODIFICADO (register router)
├── app/domains/candidate_self_service/
│   ├── agents/candidate_tool_registry.py                          ← MODIFICADO (3 → 4 tools)
│   └── tools/explain_candidate_decision.py                        ← NOVO
├── app/prompts/domains/
│   ├── autonomous.yaml                                            ← MODIFICADO (P0)
│   ├── candidate_self_service.yaml                                ← MODIFICADO (regra 8)
│   ├── culture_analysis.yaml                                      ← MODIFICADO (P1)
│   └── orchestrator.yaml                                          ← MODIFICADO (P1)
├── app/prompts/shared/
│   └── compliance_block.yaml                                      ← MODIFICADO (P0 right_to_contest)
└── tests/
    └── test_candidate_portal_explanation.py                       ← NOVO
```

### Documentação

```
docs/
├── operations/
│   └── FAIRNESS_LAYER3_RUNBOOK.md                                 ← NOVO
├── reconstruction-guides/
│   ├── CANONICAL_FILES_BY_THEME.md                                ← ATUALIZADO
│   ├── COMPLIANCE_RECONSTRUCTION_GUIDE.md                         ← ATUALIZADO (§10 + §11)
│   └── LIA_PERSONA_RECONSTRUCTION_GUIDE.md                        ← ATUALIZADO (Parte 9 + §9.11)
└── responsible-ai/                                                ← DIRETÓRIO NOVO
    ├── eu-ai-act-technical-documentation-pt.md                    ← NOVO
    ├── eu-ai-act-technical-documentation-en.md                    ← NOVO
    └── fact-sheets/
        ├── README.md                                              ← NOVO
        ├── cv-screening-fact-sheet-pt.md + -en.md                 ← NOVO (x2)
        ├── wsi-evaluation-fact-sheet-pt.md + -en.md               ← NOVO (x2)
        ├── pipeline-transition-fact-sheet-pt.md + -en.md          ← NOVO (x2)
        ├── ranking-shortlist-fact-sheet-pt.md + -en.md            ← NOVO (x2)
        └── sourcing-boolean-fact-sheet-pt.md + -en.md             ← NOVO (x2)
```

**Total: 11 novos + 9 modificados. Nenhum git push feito — commit local no Replit + push manual do Paulo pela branch `replit-sync`.**

---

## Validações executadas antes do handoff

- Fase 1: `settings.FAIRNESS_LAYER3_ENABLED = True` validado runtime no Replit ✅
- Fase 2: LIA_PERSONA §9.11 com verbatim de 6 YAMLs + seções singulares ✅
- Fase 3: 5 sanity checks no Replit ✅
  - `_sanitize_decision()` remove todos os 19 campos proibidos
  - Router `/api/v1/candidate/decisions/explain` registrado
  - Tool registry tem 4 tools
  - `app/api/routes.py` importa e registra o novo router
  - `candidate_self_service.yaml` tem regra 8 + menciona Art. 86
- Fase 4: 2 docs Art. 11 (PT + EN) uploadados — 64K total ✅
- Fase 5: 11 arquivos em `fact-sheets/` (10 fact sheets + README) ✅

---

*Handoff atualizado em 2026-04-23 | Substitui versão anterior (pré-auditoria enterprise) | Próxima revisão: após bias audit Q3/2026*

---

## Receitas Executáveis — Thematic Operational Docs

Para implementar qualquer tema deste handoff no v5, consulte os docs operacionais em:

**Mac:** `/Users/paulomoraes/Documents/Python/themes/`
**Replit:** `docs/reconstruction-guides/themes/`
**Índice:** `themes/README.md`

Temas mais relevantes para este handoff: P1, P2, P3, P4 (Persona), I1 (Agentes), I3 (Orchestration), C1 (Fairness), AS1 (Custom Agents)
