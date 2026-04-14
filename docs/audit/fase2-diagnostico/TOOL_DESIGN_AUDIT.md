# TOOL_DESIGN_AUDIT.md — Auditoria de Tool Design (ACI)
> P08 · Fase 2 · Data: 2026-04-14 · Plataforma: WeDOTalent / LIA
> Auditor: Claude Sonnet 4.6 (ACI Expert Mode)
> Escopo: `/home/runner/workspace/lia-agent-system/app/` — todos os dominios de tools

---

## Sumário Executivo

A plataforma WeDOTalent/LIA foi auditada em **38 tools de domínio** mais **16 tools compartilhadas/orquestradoras**, totalizando 54 tools avaliadas com critérios ACI (Agent-Computer Interface) de 8 dimensões. O sistema demonstra maturidade de infraestrutura surpreendentemente alta para um produto em fase inicial — o registro dual (ToolRegistry + GlobalToolRegistry), permissões declarativas em YAML, isolamento de tenant via ToolExecutionContext e enforcement de HITL (Human-in-the-Loop) em 38 tools restritas são todos implementados corretamente. No entanto, a camada que o LLM realmente lê e usa para tomar decisões — descrições, contratos de output, guidance de erro — está em estado crítico, resultando em um Índice de Maturidade Geral de **61/100**.

O maior problema sistêmico não é o código em si, mas a **desonestidade estrutural de 15 tools completamente simuladas** que se comportam como tools reais. `audit_hiring_decision` promete conformidade SOX sem persistir nada. `get_compliance_report` sempre retorna `lgpd_compliant: True` para qualquer vaga, incluindo vagas com violações reais. `get_interview_status` usa `random.Random(hash(interview_id))` — o agente toma decisões de pipeline baseadas em dados aleatórios. Esse nível de desonestidade entre o contrato declarado e a implementação real é uma falha de categoria-1 em ACI. Um segundo problema crítico é que **74% das tools (28/38) têm zero steering behavior** — após executar uma tool com sucesso, o agente fica sem orientação sobre o próximo passo, levando a loops de confirmação ou inação.

O que está funcionando bem: as tools de análise real (CV screening, talent intelligence, insight/predictive layer compartilhada) têm qualidade acima da média do mercado. `analyze_cv_match` com score BARS, `forecast_hiring_needs` com queries SQL reais e output rico, e `check_pipeline_risks` com output estruturado e acionável demonstram o padrão que o restante do sistema deve alcançar. A infraestrutura de permissões (YAML-driven, fail-closed, lru_cache, module gating para features premium) está no nível de produto maduro e não requer mudanças.

---

## Tool Design Maturity Index

| Camada | Score | Status |
|--------|-------|--------|
| Infraestrutura (registry, HITL, permissions, tenant isolation) | 88/100 | Forte |
| Qualidade LLM-visível (descriptions, params, output schema) | 56/100 | Deficiente |
| Backend Reality (real vs simulado) | 39% real | Critico |
| **Indice Geral** | **61/100** | Atencao |

**Racional do calculo:** Infraestrutura (peso 25%) = 22/25. LLM-visible quality (peso 45%) = 25.2/45, calculado como media ponderada de description quality (52/100), parameter design (71/100), output contracts (61/100), error ergonomics (74/100), steering quality (55/100). Backend reality (peso 30%): 39% real tools * 30 = 11.7/30. Total: 22 + 25.2 + 11.7 = ~59, arredondado para **61** incluindo bonus pelo HITL e module gating.

---

## Inventario de Tools — Visao Geral

| Dominio | N Tools | Score Medio | Backend Real |
|---------|---------|-------------|--------------|
| Communication | 5 | 6.2/15 | Parcial (fallback mock) |
| CV Screening | 4 | 9.3/15 | Real |
| Job Management | 5 | 7.0/15 | Parcial |
| Interview Scheduling | 5 | 4.4/15 | Totalmente simulado |
| Pipeline | 5 | 4.8/15 | Totalmente simulado |
| Hiring Policy | 5 | 6.8/15 | Misto |
| ATS Integration | 2 | 5.5/15 | Totalmente simulado |
| Talent Intelligence | 5 | 10.4/15 | Real |
| Sourcing | 1 | 7.0/15 | Real |
| Recruiter Assistant | 1 | 7.0/15 | Real |
| Shared Export | 4 | 8.75/15 | Stub parcial |
| Shared Insight (ReAct) | 4 | 11.5/15 | Real SQL |
| Shared Predictive (ReAct) | 4 | 10.75/15 | Real |
| Shared Proactive (ReAct) | 4 | 11.0/15 | Real |
| **TOTAL (domain tools)** | **38** | **7.1/15** | **39% real** |
| **TOTAL (todas)** | **54** | **8.4/15** | — |

---

## Achados Criticos (P0 — Bloqueiam Confianca dos Agentes)

### C-01: `audit_hiring_decision` — Falsa Garantia Legal SOX
**Arquivo:** `app/domains/hiring_policy/tools/policy_tools.py`
**Evidencia:** Tool gera `audit_id` fake, retorna `immutable: True` e menciona "SOX compliance" — sem persistir nada em banco de dados. O audit_id gerado nao pode ser recuperado posteriormente.
**Risco:** Agente pode reportar ao recrutador que a decisao foi auditada em conformidade com SOX quando nenhum registro existe. Em contexto de auditoria real, isso constitui falsa declaracao de conformidade regulatoria.
**Score:** 5/15

### C-02: `get_compliance_report` — Stub LGPD Retornando Sempre Positivo
**Arquivo:** `app/domains/hiring_policy/tools/policy_tools.py`
**Evidencia:** O proprio codigo contem `logger.warning("returning simulation stub")`. Retorna `lgpd_compliant: True` para qualquer job_id, incluindo vagas que podem ter violacoes reais de LGPD.
**Risco:** Agente reporta conformidade LGPD quando nao ha verificacao real. Campo `simulation_stub: True` presente no output mas agente LLM pode ignorar campos nao listados na description.
**Score:** 6/15

### C-03: `get_interview_status` — Dados Aleatorios em Producao
**Arquivo:** `app/domains/interview_scheduling/tools/scheduling_tools.py`
**Evidencia:** Usa `random.Random(hash(interview_id))` para gerar status. O status retornado ("completed", "cancelled", "scheduled") nao reflete estado real da entrevista.
**Risco:** Agente toma decisoes de pipeline (avancar candidato, reagendar) baseadas em dados completamente aleatorios. Candidatos podem ser descartados ou avancados por razoes fictícias.
**Score:** 4/15

### C-04: `export_candidates` — Contador Hardcoded de 25 Candidatos
**Arquivo:** `app/shared/tools/export_tools.py` (linha 69)
**Evidencia:** `candidates_count = 25` hardcoded quando nenhum `candidate_id` e fornecido. Tool retorna `success: True` com contagem falsa. URL de download e fake (`/api/v1/exports/{export_id}/download`).
**Risco:** LLM reporta ao recrutador que exportou 25 candidatos quando nenhuma exportacao ocorreu. Phantom Success categoria-1.
**Score:** 8/15

### C-05: `generate_report` — Metricas Falsas Retornadas como Reais
**Arquivo:** `app/shared/tools/export_tools.py` (linhas 120-140)
**Evidencia:** `sample_metrics` e um dict hardcoded com numeros falsos de pipeline (ex: 245 candidatos, 42% taxa de resposta). Tool retorna esses numeros como se fossem dados reais do banco.
**Risco:** Recrutadores recebem relatorios baseados em dados inventados, tomam decisoes de hiring com base em metricas falsas.
**Score:** 8/15

### C-06: `send_email` — Schema Mismatch YAML vs Python
**Arquivo:** YAML `tool_registry_metadata.yaml` vs `app/domains/communication/tools/communication_tools.py`
**Evidencia:** YAML declara `to: array[string]` como parametro. Handler Python espera `candidate_id: str`. LLM passa `to: ["uuid"]`, Python recebe `candidate_id` vazio → falha silenciosa sem envio de email.
**Risco:** Emails criticos (convites de entrevista, notificacoes de rejeicao) nao sao enviados. Candidatos nao sao notificados. Tool retorna success: True via fallback mock.
**Score:** 5/15 (dominio) / 6/15 (compartilhado)

### C-07: 15+ Tools Declaradas Sem Handler Python
**Arquivo:** `app/tools/tool_permissions.yaml`, `app/config/scope_config.py`
**Evidencia:** Tools como `get_recruiter_metrics`, `get_velocity_metrics`, `get_efficiency_metrics`, `get_workload_distribution`, `get_hiring_quality`, `get_cost_metrics`, `get_trends`, `get_market_benchmarks`, `get_talent_quality`, `get_talent_engagement`, `get_talent_availability`, `get_diversity_metrics`, `get_candidate_history`, `get_ml_predictions`, `get_conversion_patterns`, `compare_candidates`, `get_smart_alerts`, `get_prediction_metrics`, `get_job_benchmark` aparecem em YAML/scope allowlists mas nenhum `tool_registry.register()` foi encontrado.
**Risco:** LLM e direcionado a chamar essas tools (aparecem em prompts e scopes), executor retorna `{"error": "Tool not found: get_recruiter_metrics"}`, agente pode alucinar resposta ou entrar em loop.

### C-08: 28/38 Tools (74%) Sem Steering Behavior
**Evidencia:** `"next_steps"` ausente no output de 28 das 38 tools de dominio avaliadas. Agente executa acao e fica sem orientacao sobre proximo passo.
**Risco:** Loops de confirmacao desnecessarios, inacao do agente apos operacoes que deveriam encadear outras acoes (ex: apos `move_candidate_to_stage` deveria sugerir `schedule_interview`).

---

## Ranking de Tools por Score

### Top 10 Melhores

| Rank | Tool | Dominio | Score | Destaque |
|------|------|---------|-------|---------|
| 1 | check_pipeline_risks | Shared Proactive | 14/15 | Melhor overall — 3 dimensoes em 3/3 |
| 2 | get_strategic_recommendations | Shared Predictive | 13/15 | "Consultive brain" — framing unico e eficaz |
| 3 | analyze_cv_match | CV Screening | 12/15 | Melhor tool de dominio — BARS + output rico |
| 4 | forecast_hiring_needs | Workforce Planning | 12/15 | SQL real + steering com feasibility enum |
| 5 | get_pipeline_health | Shared Insight | 12/15 | SQL real, output documentado, threshold explicito |
| 6 | get_conversion_rates | Shared Insight | 12/15 | Output tipado e predicavel para parsing LLM |
| 7 | analyze_skill_gaps | Skills Ontology | 11/15 | gap_severity + effective_match_percentage |
| 8 | get_market_intelligence | Market Intelligence | 11/15 | confidence + is_estimate orientam confiabilidade |
| 9 | get_time_to_fill | Shared Insight | 11/15 | median, fastest, slowest por departamento |
| 10 | predict_dropout_risk | Shared Predictive | 11/15 | Risk categorization + recommended_actions |

### Bottom 10 Piores

| Rank | Tool | Dominio | Score | Principal Problema |
|------|------|---------|-------|-------------------|
| 38 | send_interview_invitation | Interview Scheduling | 3/15 | Stub simulado; retorna "sent" sem enviar nada |
| 37 | reschedule_interview | Scheduling | 4/15 | old_datetime: "N/A" — sem estado persistente |
| 36 | get_interview_status | Scheduling | 4/15 | random.Random(hash) gerando status aleatorio |
| 35 | extend_offer | Pipeline | 4/15 | offer_details: str (JSON) anti-pattern; stub |
| 34 | bulk_advance_candidates | Pipeline | 4/15 | candidate_ids: str (CSV); stub sem persistencia |
| 33 | update_job | Job Management | 4/15 | updates: dict sem schema — pior anti-pattern ACI |
| 32 | reschedule_interview | Scheduling | 4/15 | — |
| 31 | reject_candidate | Pipeline | 5/15 | notify: True retorna input como confirmacao |
| 30 | move_candidate_to_stage | Pipeline | 5/15 | old_stage: "unknown"; duplicata do tool real |
| 29 | send_interview_invitation | Scheduling | 3/15 | Pior score do sistema |

---

## Avaliacao por Dominio

### Dominio: Communication

**Arquivo:** `app/domains/communication/tools/communication_tools.py`
**Backend:** Parcial — DB real com fallback silencioso para mock em falha de modelo

#### [send_email] — Score: 5/15

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza de proposito | 1/3 | Sem contexto de quando usar template vs conteudo; sem mencao ao fallback simulado |
| B. Qualidade dos parametros | 1/3 | candidate_id sem UUID explicito; sem mutual exclusivity de template_id vs body |
| C. Output specification | 1/3 | campo simulated: True nao documentado; sem schema de output |
| D. Error guidance | 2/3 | candidate_not_found e no_email em PT mas sem sugestao de proximo passo |
| E. Steering behavior | 0/3 | Sem hints de proximos passos |

**Anti-patterns:** Fallback silencioso retorna success: True com simulated: True quando DB falha. Schema YAML (to: array) incompativel com handler Python (candidate_id: str).

**Description recomendada:**
```
Envia email para um candidato especifico via integracao de email da plataforma.
Use quando o recrutador pedir para entrar em contato por email, enviar convite de entrevista,
ou comunicar decisoes por escrito. Prefira template_id para comunicacoes padronizadas
(rejeicao, aprovacao, next steps) — so passe subject+body para mensagens completamente customizadas.
NAO use para envio em massa (use send_bulk_email). Requer que o candidato tenha email cadastrado.
Apos sucesso, considere registrar no historico com add_candidate_note.
```

**Schema corrigido:**
```python
{
    "candidate_id": {"type": "string", "format": "uuid", "description": "UUID do candidato. Obtenha com search_candidates."},
    "template_id": {"type": "string", "description": "ID do template. Mutuamente exclusivo com body."},
    "subject": {"type": "string", "maxLength": 200},
    "body": {"type": "string", "maxLength": 10000},
    "cc": {"type": "array", "items": {"type": "string", "format": "email"}, "maxItems": 5},
    "attachments": {"type": "array", "items": {"type": "string", "format": "uuid"}, "maxItems": 3}
}
```

**Error response corrigido:**
```python
{"success": False, "error": "no_email", "message": "Candidato {name} nao possui email cadastrado.",
 "suggestion": "Use send_whatsapp se o candidato tiver telefone, ou update_candidate para cadastrar email."}
```

---

#### [send_whatsapp] — Score: 5/15

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza de proposito | 1/3 | Sem contexto de integracao (WhatsApp Business API?) |
| B. Qualidade dos parametros | 1/3 | message sem limite (WA tem 4096 chars); template_id sem catalogo |
| C. Output specification | 1/3 | message_preview trunca em 100 chars sem informar total enviado |
| D. Error guidance | 2/3 | no_phone legivel mas sem sugestao |
| E. Steering behavior | 0/3 | — |

**Anti-patterns:** Fallback silencioso identico ao send_email.

**Description recomendada:**
```
Envia mensagem WhatsApp via API WhatsApp Business. Preferivel ao email para comunicacoes urgentes.
Limite: 4096 caracteres. Para mensagens estruturadas use template_id para conformidade com politicas WA Business.
NAO use para textos longos — prefira email. Requer telefone cadastrado (campo phone ou whatsapp).
```

---

#### [schedule_interview] (Communication) — Score: 8/15

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza de proposito | 2/3 | Boa mas nao menciona que NAO cria evento de calendario real |
| B. Qualidade dos parametros | 2/3 | interview_type enum documentado; interviewers sem formato UUID |
| C. Output specification | 2/3 | invite_sent bool mas nao confirma entrega real |
| D. Error guidance | 2/3 | Valida datetime_str; erro generico de DB sem sugestao |
| E. Steering behavior | 1/3 | Sem hint sobre envio de convite de calendario |

**Description recomendada:**
```
Agenda uma entrevista criando o registro no sistema. ATENCAO: registra o agendamento mas NAO envia
convite de calendario automaticamente — use send_email com template 'interview_invite' apos chamar esta tool.
Use check_interviewer_availability antes para verificar horarios. NAO use para reagendar — use reschedule_interview.
```

---

#### [send_bulk_email] — Score: 5/15

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza de proposito | 1/3 | Sem limite de IDs; sem mencao que e sequencial (lento para 100+) |
| B. Qualidade dos parametros | 1/3 | candidate_ids sem limite maximo; custom_variables sem schema |
| C. Output specification | 2/3 | success_count, failed_count, failed_ids uteis mas sem razao de falha por ID |
| D. Error guidance | 1/3 | Lista IDs que falharam sem razao de falha |
| E. Steering behavior | 0/3 | Sem orientacao sobre o que fazer com failed_ids |

**Anti-patterns:** O(n) calls sequenciais sem batching. success: True quando 90/100 falham.

---

#### [send_feedback] — Score: 8/15

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza de proposito | 2/3 | Boa mas nao menciona que rejeicoes passam por FairnessGuard e podem ter mensagem alterada |
| B. Qualidade dos parametros | 2/3 | feedback_type enum presente; feedback_message sem limite de chars |
| C. Output specification | 1/3 | Nao indica canal usado (email/whatsapp); nao retorna mensagem final apos FairnessGuard |
| D. Error guidance | 2/3 | Erros legiveis sem sugestao |
| E. Steering behavior | 1/3 | Sem hint sobre canal ou confirmacao de delivery |

**Anti-patterns:** FairnessGuard pode substituir mensagem silenciosamente sem informar o agente no output.

---

### Dominio: CV Screening

**Arquivos:** `cv_match_tool.py`, `cv_upload_tool.py`, `candidate_tools.py`
**Backend:** Real — chama CVScoringService, DB commits reais

#### [analyze_cv_match] — Score: 12/15

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza de proposito | 3/3 | Excelente: cobre quando usar, palavras-gatilho, busca por nome |
| B. Qualidade dos parametros | 2/3 | Boa distincao candidate_id vs name; falta UUID explicito |
| C. Output specification | 3/3 | match_score, matched_skills, missing_skills, recommendation, BARS evaluations |
| D. Error guidance | 2/3 | Erros claros em PT com sugestao; erro generico menos informativo |
| E. Steering behavior | 2/3 | Output bem formatado com secoes; sem next steps explicito |

**Melhoria marginal:** Adicionar aviso se vaga nao tiver requirements cadastrados.

---

#### [parse_and_create_candidate] — Score: 8/15

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza de proposito | 1/3 | Falta mencionar duplicate handling, scan de seguranca, que e passo 1 de fluxo multi-step |
| B. Qualidade dos parametros | 1/3 | cv_text sem tamanho minimo documentado; source sem enum |
| C. Output specification | 2/3 | candidate_id, duplicate flag — estruturado; nao documenta duplicate: True no schema |
| D. Error guidance | 2/3 | cv_text_too_short e bom; DB error retorna string de exception |
| E. Steering behavior | 2/3 | Output sugere candidate_id para proximo passo; sem "use add_to_vacancy em seguida" |

**Description recomendada:**
```
Parseia texto bruto de CV com IA e cria (ou reutiliza) cadastro de Candidato.
Passo 1 de 3: use add_to_vacancy em seguida, depois analyze_cv_match.
Se ja existir candidato com mesmo email, retorna existente (duplicate: true).
Entrada deve ser texto puro — minimo 30 caracteres.
NAO use para candidatos ja cadastrados — use search_candidates primeiro.
```

**Schema corrigido — source:**
```python
"source": {"type": "string", "enum": ["cv_upload", "linkedin", "referral", "headhunting", "job_board", "internal"], "default": "cv_upload"}
```

---

#### [add_to_vacancy] — Score: 8/15

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza de proposito | 1/3 | Muito curto; nao menciona passo 2 do fluxo; nao menciona duplicata |
| B. Qualidade dos parametros | 2/3 | Boa alternativa vacancy_id vs vacancy_title; initial_stage sem enum |
| C. Output specification | 2/3 | vacancy_candidate_id util para WSI; nao documenta uso posterior |
| D. Error guidance | 2/3 | candidate_not_found e vacancy_not_found claros |
| E. Steering behavior | 1/3 | Retorna vacancy_candidate_id sem instrucao de uso |

---

#### [create_and_screen_candidate] — Score: 9/15

**Funcao:** Orquestra parse → add_to_vacancy → analyze_cv_match → (opcional) wsi_screening em um call.

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza de proposito | 2/3 | Claro sobre o que faz; falta quando preferir vs steps individuais |
| B. Qualidade dos parametros | 2/3 | run_bars e run_wsi booleans bem documentados |
| C. Output specification | 2/3 | Retorna steps com resultado de cada sub-operacao |
| D. Error guidance | 2/3 | Herda errors das tools individuais |
| E. Steering behavior | 1/3 | Sem hint de proximos passos apos conclusao |

---

### Dominio: Job Management

**Arquivo:** `app/domains/job_management/tools/job_tools.py`
**Backend:** Misto — create_job/update_job real; pause_job/close_job/publish_job com fallback simulado

#### [create_job] — Score: 8/15

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza de proposito | 2/3 | Boa mas company_id sobrescrito pelo context nao documentado |
| B. Qualidade dos parametros | 2/3 | seniority e work_model com enum; requirements vs skills sem distincao semantica clara |
| C. Output specification | 2/3 | job_id e campos retornados; salary_range aninhado nao documentado |
| D. Error guidance | 1/3 | Erro generico retorna str(e) |
| E. Steering behavior | 1/3 | Sem hint sobre proximos passos |

**Description recomendada:**
```
Cria nova vaga. Cria como rascunho por padrao — use publish=true somente quando completa e aprovada.
requirements = texto descritivo ("5 anos de Python, experiencia com AWS").
skills = tags para matching ("python", "aws", "docker").
NAO use para editar vagas — use update_job.
```

---

#### [update_job] — Score: 4/15

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza de proposito | 1/3 | Nao menciona campos editaveis nem campos protegidos |
| B. Qualidade dos parametros | 0/3 | **updates: dict sem schema** — pior anti-pattern ACI |
| C. Output specification | 1/3 | Retorna updated_fields mas nao confirma novo valor |
| D. Error guidance | 2/3 | cross_tenant_access_denied e job_not_found sao bons |
| E. Steering behavior | 0/3 | — |

**Schema corrigido (excertp):**
```python
"updates": {
    "type": "object",
    "description": "Campos editaveis apenas. Campos protegidos (id, company_id) sao ignorados.",
    "properties": {
        "title": {"type": "string", "maxLength": 200},
        "seniority_level": {"type": "string", "enum": ["Estagio", "Junior", "Pleno", "Senior", "Especialista", "Coordenador", "Gerente", "Diretor"]},
        "work_model": {"type": "string", "enum": ["Remoto", "Hibrido", "Presencial"]},
        "requirements": {"type": "array", "items": {"type": "string"}},
        "salary_range": {"type": "object", "properties": {"min": {"type": "number"}, "max": {"type": "number"}, "currency": {"type": "string", "default": "BRL"}}}
    },
    "additionalProperties": false
}
```

---

#### [pause_job] — Score: 8/15

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza de proposito | 2/3 | "Pausa vaga deixando-a invisivel para candidatos" — bom; nao menciona que candidatos em processo NAO sao notificados |
| B. Qualidade dos parametros | 2/3 | reason sem enum; job_id sem formato |
| C. Output specification | 2/3 | Campo simulated: True pode aparecer |
| D. Error guidance | 2/3 | job_not_found claro; sem cross-tenant check |
| E. Steering behavior | 0/3 | — |

**Anti-patterns:** Sem cross-tenant check. Fallback silencioso retorna success: True.

---

#### [close_job] — Score: 10/15

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza de proposito | 2/3 | "Acao sensivel que requer confirmacao" no registry e bom |
| B. Qualidade dos parametros | 2/3 | reason tem enum; hired_candidate_id bem descrito |
| C. Output specification | 2/3 | requires_confirmation e confirmation_message no output |
| D. Error guidance | 2/3 | job_not_found claro; fallback simulado em acao irreversivel e critico |
| E. Steering behavior | 2/3 | requires_confirmation e confirmation_message sao steering |

**Anti-patterns:** requires_confirmation: True retornado APOS acao ja executada — flag e decorativa, nao funcional.

---

#### [publish_job] — Score: 5/15

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza de proposito | 2/3 | Claro; sem mencao que channels e apenas metadata |
| B. Qualidade dos parametros | 1/3 | channels sem enum; sem indicacao de que e apenas metadata |
| C. Output specification | 1/3 | Retorna channels sem confirmar publicacao real em plataformas externas |
| D. Error guidance | 1/3 | Apenas job_not_found; sem validacao de estado anterior |
| E. Steering behavior | 0/3 | — |

**Anti-patterns:** `channels: ["linkedin", "indeed"]` implica integracao real inexistente.

---

### Dominio: Interview Scheduling

**Arquivo:** `app/domains/interview_scheduling/tools/scheduling_tools.py`
**Backend:** TOTALMENTE SIMULADO — todos os 5 tools sao stubs

> AVISO CRITICO: Todo este dominio e simulado. Tools retornam dados aleatorios ou hardcoded.
> Nenhuma tool faz chamada real a sistemas de calendario ou banco de dados de agendamento.

#### [check_interviewer_availability] — Score: 6/15

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza de proposito | 1/3 | Docstring boa mas OCULTA que e simulacao |
| B. Qualidade dos parametros | 2/3 | date_range com formato documentado |
| C. Output specification | 2/3 | available_slots e busy_slots — schema adequado mas random |
| D. Error guidance | 1/3 | Data invalida tem fallback silencioso para hoje+7 dias |
| E. Steering behavior | 0/3 | — |

**CRITICO:** `random.shuffle` com seed baseado em hash. Slots "disponiveis" nao refletem realidade.

---

#### [schedule_interview] (Scheduling) — Score: 5/15
**STUB SIMULADO — gera interview_id fake, calendar_link falso.**

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza de proposito | 1/3 | NAO menciona que e stub |
| B. Qualidade dos parametros | 2/3 | interview_type com enum; datetime_str sem validacao |
| C. Output specification | 2/3 | interview_id e calendar_link — IDs sao fake |
| D. Error guidance | 0/3 | Sem validacao ou tratamento de erros |
| E. Steering behavior | 0/3 | — |

**Duplicata funcional** de schedule_interview em communication_tools.py (que e real).

---

#### [send_interview_invitation] — Score: 3/15 (PIOR DO SISTEMA)
**STUB SIMULADO — retorna status: "sent" sem enviar nada.**

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza de proposito | 1/3 | Unica tool que menciona "(simulated)" na docstring |
| B. Qualidade dos parametros | 1/3 | candidate_email no schema mas LGPD comment diz para nao logar |
| C. Output specification | 1/3 | status: "sent" sem envio real |
| D. Error guidance | 0/3 | — |
| E. Steering behavior | 0/3 | — |

---

#### [reschedule_interview] — Score: 4/15

**STUB SIMULADO — retorna old_datetime: "N/A" (sem estado persistente).**

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza de proposito | 1/3 | "N/A" e honesto mas inutilizavel em producao |
| B. Qualidade dos parametros | 2/3 | reason sem enum |
| C. Output specification | 1/3 | old_datetime: "N/A" e output enganoso |
| D. Error guidance | 0/3 | — |
| E. Steering behavior | 0/3 | — |

---

#### [get_interview_status] — Score: 4/15

**STUB SIMULADO — usa random.Random(hash(interview_id)) para status.**

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza de proposito | 1/3 | Status aleatorio oculto |
| B. Qualidade dos parametros | 2/3 | Simples e direto |
| C. Output specification | 1/3 | "source": "simulated" — unico campo honesto |
| D. Error guidance | 0/3 | — |
| E. Steering behavior | 0/3 | — |

---

### Dominio: Pipeline

**Arquivo:** `app/domains/pipeline/tools/pipeline_tools.py`
**Backend:** TOTALMENTE SIMULADO — todos os 5 tools sao stubs sem persistencia

#### [move_candidate_to_stage] — Score: 5/15

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza de proposito | 2/3 | Docstring rica com lista de stages validos |
| B. Qualidade dos parametros | 2/3 | new_stage com enum na docstring |
| C. Output specification | 1/3 | old_stage: "unknown" expoe o stub |
| D. Error guidance | 0/3 | Sem validacao de new_stage contra enum |
| E. Steering behavior | 0/3 | — |

**Duplicata** de update_candidate_stage em candidate_tools.py que e REAL.

---

#### [get_pipeline_overview] — Score: 6/15

**STUB — retorna dados hardcoded (applied: 24, screening: 12) para qualquer job_id.**

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza de proposito | 2/3 | Docstring clara; log interno diz "simulation stub" |
| B. Qualidade dos parametros | 2/3 | Simples e adequado |
| C. Output specification | 2/3 | simulation_stub: True presente — honesto |
| D. Error guidance | 0/3 | — |
| E. Steering behavior | 0/3 | — |

---

#### [reject_candidate] — Score: 5/15

**STUB — sem persistencia, sem FairnessGuard (ao contrario de send_feedback).**

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza de proposito | 2/3 | Nao menciona que notify: True nao envia nada real |
| B. Qualidade dos parametros | 2/3 | notify bem descrito |
| C. Output specification | 1/3 | notified: notify retorna input como confirmacao — enganoso |
| D. Error guidance | 0/3 | — |
| E. Steering behavior | 0/3 | — |

---

#### [extend_offer] — Score: 4/15

**STUB — gera offer_id fake sem persistencia.**

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza de proposito | 2/3 | Menciona que offer_details deve ser JSON |
| B. Qualidade dos parametros | 1/3 | offer_details: str (JSON) — anti-pattern |
| C. Output specification | 1/3 | Nao retorna campos do offer |
| D. Error guidance | 0/3 | JSON invalido causa erro nao tratado |
| E. Steering behavior | 0/3 | — |

**Schema corrigido:**
```python
"offer_details": {
    "type": "object",
    "properties": {
        "salary": {"type": "number", "description": "Salario mensal em BRL"},
        "start_date": {"type": "string", "format": "date"},
        "benefits": {"type": "array", "items": {"type": "string"}},
        "contract_type": {"type": "string", "enum": ["CLT", "PJ", "Estagio"]}
    }
}
```

---

#### [bulk_advance_candidates] — Score: 4/15

**STUB — conta IDs sem avancar nada.**

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza de proposito | 2/3 | Bem descrito; "comma-separated string" e anti-pattern documentado |
| B. Qualidade dos parametros | 0/3 | candidate_ids: str (CSV) — pior anti-pattern de input |
| C. Output specification | 2/3 | advanced_count, from_stage, to_stage |
| D. Error guidance | 0/3 | — |
| E. Steering behavior | 0/3 | — |

---

### Dominio: Hiring Policy

**Arquivo:** `app/domains/hiring_policy/tools/policy_tools.py`
**Backend:** Misto — check_diversity_targets e validate_job_requirements sao reais; audit_hiring_decision e get_compliance_report sao stubs criticos

#### [check_diversity_targets] — Score: 7/15

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza de proposito | 2/3 | IEEE 7003-2023 mencionado; nao menciona que current_pipeline deve ser passado pelo agente |
| B. Qualidade dos parametros | 1/3 | current_pipeline: str (JSON) — anti-pattern; sem exemplo |
| C. Output specification | 2/3 | disparate_impact_ratio, targets_met, recommendations |
| D. Error guidance | 1/3 | JSON invalido usa {} silenciosamente |
| E. Steering behavior | 1/3 | recommendations com textos de acao |

---

#### [validate_job_requirements] — Score: 9/15

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza de proposito | 2/3 | LGPD, EU AI Act, anti-discriminacao — bom contexto legal |
| B. Qualidade dos parametros | 2/3 | Simples e bem descritos |
| C. Output specification | 2/3 | issues, severity, compliant — estruturado |
| D. Error guidance | 2/3 | Sem erros possiveis; sem orientacao para correcao |
| E. Steering behavior | 1/3 | Sem recommendations de correcao |

---

#### [generate_explanation_report] — Score: 7/15

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza de proposito | 3/3 | Excelente contexto legal (LGPD Art. 20) |
| B. Qualidade dos parametros | 1/3 | decision_factors: str (JSON ou CSV) — anti-pattern duplo |
| C. Output specification | 2/3 | report_id nao e persistido |
| D. Error guidance | 1/3 | JSON parse com fallback silencioso para split por virgula |
| E. Steering behavior | 0/3 | Sem orientacao sobre como armazenar o report |

---

#### [audit_hiring_decision] — Score: 5/15

**STUB CRITICO — gera audit_id fake, immutable: True e decorativo.**

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza de proposito | 2/3 | "SOX compliance" mencionado; contradiz ausencia de DB |
| B. Qualidade dos parametros | 2/3 | Claros e bem descritos |
| C. Output specification | 1/3 | immutable: True e mentira — nada e persistido |
| D. Error guidance | 0/3 | — |
| E. Steering behavior | 0/3 | — |

---

#### [get_compliance_report] — Score: 6/15

**STUB CRITICO — lgpd_compliant: True sempre para qualquer job.**

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza de proposito | 2/3 | simulation_stub: True no output e a unica honestidade |
| B. Qualidade dos parametros | 2/3 | Simples |
| C. Output specification | 2/3 | simulation_stub: True presente |
| D. Error guidance | 0/3 | — |
| E. Steering behavior | 0/3 | — |

---

### Dominio: ATS Integration

**Arquivo:** `app/domains/ats_integration/tools/ats_tools.py`
**Backend:** TOTALMENTE SIMULADO

#### [sync_candidate_from_ats] — Score: 5/15

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza de proposito | 2/3 | ATS suportados listados (gupy, greenhouse, workday, lever) |
| B. Qualidade dos parametros | 2/3 | ats_name com enum na docstring |
| C. Output specification | 1/3 | fields_imported hardcoded — nao reflete o que foi importado |
| D. Error guidance | 0/3 | Sem validacao de ats_name |
| E. Steering behavior | 0/3 | — |

---

#### [get_ats_sync_status] — Score: 6/15

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza de proposito | 2/3 | Boa docstring |
| B. Qualidade dos parametros | 2/3 | Simples |
| C. Output specification | 2/3 | simulation_stub: True honesto; records_synced: 142 hardcoded |
| D. Error guidance | 0/3 | — |
| E. Steering behavior | 0/3 | — |

---

### Dominio: Talent Intelligence

**Arquivos:** `skills_ontology_tools.py`, `market_intelligence_tools.py`, `candidate_nurture_tools.py`, `workforce_planning_tools.py`, `interview_intelligence_tools.py`
**Backend:** Real — SkillsOntologyEngine, MarketBenchmarkService, queries SQL reais

#### [infer_related_skills] — Score: 9/15

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza de proposito | 1/3 | Tecnica mas sem contexto de quando usar vs analyze_skill_gaps |
| B. Qualidade dos parametros | 2/3 | depth e limit com min/max implicitos; sem default documentado |
| C. Output specification | 3/3 | related_skills, embedding_similarity, hybrid_score, scoring_mode — output rico |
| D. Error guidance | 2/3 | missing_skills retorna erro legivel |
| E. Steering behavior | 1/3 | scoring_mode informa qualidade da analise |

**Description recomendada:**
```
Descobre skills relacionadas usando grafo de ontologia.
Use para expandir busca de candidatos (Python -> FastAPI, Django), sugerir skills de desenvolvimento,
ou identificar skills transferiveis. NAO use para gap analysis (use analyze_skill_gaps).
depth=2 para relacoes primeiro/segundo grau; depth=3 para skills mais distantes.
```

---

#### [analyze_skill_gaps] — Score: 11/15

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza de proposito | 2/3 | Claro; sem documentar que e mais preciso que BARS para skills puras |
| B. Qualidade dos parametros | 2/3 | Suporte a ID direto ou listas de skills — flexivel |
| C. Output specification | 3/3 | match_percentage, effective_match_percentage, gap_severity, adjacency_matches |
| D. Error guidance | 2/3 | Erro se ambos os inputs vazios; DB errors como warning |
| E. Steering behavior | 2/3 | gap_severity e effective_match_percentage orientam decisao |

---

#### [get_market_intelligence] — Score: 11/15

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza de proposito | 2/3 | Fontes citadas (Glassdoor, LinkedIn, Indeed); sem mencao de latencia |
| B. Qualidade dos parametros | 2/3 | industry sem enum de valores suportados |
| C. Output specification | 3/3 | salary_benchmark, market_trends, competitive_position, confidence, is_estimate |
| D. Error guidance | 2/3 | job_title validado; erros de servico nao tratados |
| E. Steering behavior | 2/3 | confidence e is_estimate orientam confiabilidade |

---

#### [forecast_hiring_needs] — Score: 12/15

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza de proposito | 2/3 | Claro; sem mencionar que usa candidates.source IN ('internal', 'employee') |
| B. Qualidade dos parametros | 2/3 | growth_rate como float (0.10 = 10%) — pouco intuitivo |
| C. Output specification | 3/3 | feasibility enum, recommendations acionaveis, breakdown detalhado |
| D. Error guidance | 2/3 | Erros de DB causam fallback para zeros |
| E. Steering behavior | 3/3 | recommendations com textos acionaveis, feasibility como enum de 3 niveis |

---

#### [analyze_interview_recording] — Score: 9/15

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza de proposito | 2/3 | Claro; tool_handler nao registra no tool_registry publico — pode nao ser descoberta |
| B. Qualidade dos parametros | 2/3 | transcript com minimo 50 chars documentado; interview_type sem enum formal |
| C. Output specification | 2/3 | Output rico via _analyze_inline; estrutura nao documentada no schema |
| D. Error guidance | 2/3 | Valida transcript vazio e interview_id sem DB |
| E. Steering behavior | 1/3 | Sem orientacao de proximos passos |

---

### Dominio: Sourcing

**Arquivo:** `app/domains/sourcing/tools/query_tools.py`
**Backend:** Real — DB queries tenant-scoped

#### [search_candidates] — Score: 7/15

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza de proposito | 2/3 | Sem indicacao que retorna somente candidatos da empresa (company_id do context) |
| B. Qualidade dos parametros | 2/3 | min_score/max_score implicito 0-100; seniority sem enum; limit sem maximo |
| C. Output specification | 2/3 | Lista de candidatos sem total_count para paginacao |
| D. Error guidance | 1/3 | Erros de DB retornam string de exception |
| E. Steering behavior | 0/3 | Sem hint se limite foi atingido ou ha mais resultados |

**Anti-patterns:** Sem total_count. Limite default=20 sem maximo documentado.

---

### Dominio: Recruiter Assistant

#### [create_pipeline_stage] — Score: 7/15

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza de proposito | 1/3 | Sem docstring no handler; sem description no registry |
| B. Qualidade dos parametros | 1/3 | position aceita "before_final" sem documentacao de valores |
| C. Output specification | 2/3 | stage_id e dados completos; erros bem tratados |
| D. Error guidance | 2/3 | stage_already_exists bem tratado |
| E. Steering behavior | 1/3 | suggested_behavior e behavior_confidence retornados |

---

### Camada Compartilhada: Export Tools

**Arquivo:** `app/shared/tools/export_tools.py`

#### [export_candidates] — Score: 8/15

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza | 2/3 | Funcional mas nao distingue de export_job_analytics |
| B. Parametros | 2/3 | enum para format; filters: object opaco |
| C. Output | 1/3 | candidates_count = 25 hardcoded (linha 69). URL de download fake. |
| D. Erros | 2/3 | invalid_format; sem candidate_not_found |
| E. Steering | 1/3 | Sem warning sobre PII |

**CRITICO:** Phantom Success — retorna success: True com 25 candidatos sem exportar nada.

---

#### [generate_report] — Score: 8/15

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza | 2/3 | Lista 7 tipos de relatorio |
| B. Parametros | 2/3 | Enum para report_type e format |
| C. Output | 1/3 | sample_metrics hardcoded (linhas 120-140) retornados como dados reais |
| D. Erros | 2/3 | invalid_report_type e invalid_format |
| E. Steering | 1/3 | Sem nota que metricas sao samples |

**CRITICO:** Phantom Success — numeros falsos de pipeline retornados como dados reais.

---

#### [schedule_report] — Score: 9/15

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza | 2/3 | "recorrente" distingue de generate_report |
| B. Parametros | 2/3 | recipients array; time_of_day apenas no default |
| C. Output | 2/3 | schedule_id, next_run calculado corretamente; scheduler in-memory stub |
| D. Erros | 2/3 | invalid_frequency; sem validacao de email em recipients |
| E. Steering | 1/3 | Sem aviso que scheduler externo precisa ser configurado |

---

#### [export_job_analytics] — Score: 10/15

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza | 2/3 | Distinto de export_candidates (job-scoped) |
| B. Parametros | 2/3 | Tres flags booleanas claras; enum para format |
| C. Output | 2/3 | Busca titulo de job no DB (dado real); resto e metadata |
| D. Erros | 2/3 | Fallback para erro de DB em job title |
| E. Steering | 2/3 | job_id obrigatorio enforced no schema |

---

### Camada Compartilhada: Insight Tools (ReAct)

**Arquivo:** `app/shared/tools/insight_tools.py`
**Backend:** Real — SQL queries diretas

#### [get_pipeline_health] — Score: 12/15 (Melhor da camada compartilhada)

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza | 3/3 | "candidates per stage, avg days in stage, stalled candidates (>7 days), bottleneck" |
| B. Parametros | 2/3 | company_id required; job_id opcional com descricao clara |
| C. Output | 3/3 | total_candidates, by_stage, stalled_candidates, avg_days, bottleneck_stage — todos documentados |
| D. Erros | 2/3 | Sem codigos de erro distintos |
| E. Steering | 2/3 | Threshold de 7 dias explicito; sem aviso sobre multi-job vs single-job |

---

#### [get_conversion_rates] — Score: 12/15

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza | 3/3 | "stage-to-stage conversion rates, overall funnel rate, weakest conversion point" |
| B. Parametros | 2/3 | Clean |
| C. Output | 3/3 | conversion_rates keyed por "applied_to_screening" — predicavel para LLM |
| D. Erros | 2/3 | Erro path retorna apenas str(e) |
| E. Steering | 2/3 | overall_funnel_rate explicado |

---

#### [get_time_to_fill] — Score: 11/15

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza | 2/3 | "filled/closed vacancies" e qualificador importante |
| B. Parametros | 2/3 | Minimais mas adequados |
| C. Output | 3/3 | avg_days_to_fill, median_days, fastest, slowest, by_department |
| D. Erros | 2/3 | Resultado vazio tratado graciosamente |
| E. Steering | 2/3 | Apenas vagas fechadas/preenchidas — previne interpretacao errada |

---

#### [get_candidate_quality_distribution] — Score: 9/15

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza | 2/3 | "score distribution across buckets" e claro |
| B. Parametros | 2/3 | Standard |
| C. Output | 2/3 | top_candidates[:10] hardcoded |
| D. Erros | 2/3 | Standard |
| E. Steering | 1/3 | Sem nota que candidatos sem lia_score ficam invisiveis |

---

### Camada Compartilhada: Predictive Tools (ReAct)

**Arquivo:** `app/shared/tools/predictive_tools.py`

#### [predict_dropout_risk] — Score: 11/15

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza | 3/3 | Categoriza low/medium/high/critical + identifica candidatos criticos |
| B. Parametros | 2/3 | Threshold de inatividade (3 dias) hardcoded sem exposicao |
| C. Output | 2/3 | candidates_at_risk, risk_distribution, critical_candidates, recommended_actions |
| D. Erros | 2/3 | Sem distincao para company_id nao encontrado |
| E. Steering | 2/3 | Fatores de risco explicados na description |

---

#### [predict_time_to_fill] — Score: 9/15

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza | 2/3 | Nao distingue de get_time_to_fill (historico vs preditivo) |
| B. Parametros | 2/3 | Standard |
| C. Output | 2/3 | Predicao por job; metodologia nao documentada |
| D. Erros | 2/3 | Standard |
| E. Steering | 1/3 | RISCO: LLM pode confundir com get_time_to_fill |

**Risco de naming collision** — ver AP-05.

---

#### [get_pipeline_forecast] — Score: 10/15

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza | 2/3 | "next 4 weeks" e ancora temporal concreta |
| B. Parametros | 2/3 | Horizonte hardcoded em 4 semanas; nao configuravel |
| C. Output | 2/3 | projected_hires, fill_probability, stage_progression |
| D. Erros | 2/3 | Standard |
| E. Steering | 2/3 | Janela temporal mencionada na description |

---

#### [get_strategic_recommendations] — Score: 13/15

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza | 3/3 | "'consultive brain' tool that synthesizes actionable insights" — unico e memorizavel |
| B. Parametros | 2/3 | Standard |
| C. Output | 3/3 | recommendations com priority (high/medium/low) — machine-readable |
| D. Erros | 2/3 | Standard |
| E. Steering | 3/3 | "Consultive brain" framing ensina LLM a chamar DEPOIS de coletar contexto |

---

### Camada Compartilhada: Proactive Tools (ReAct)

**Arquivo:** `app/shared/tools/proactive_tools.py`

#### [check_stagnant_candidates] — Score: 11/15

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza | 2/3 | "Stuck in same stage for more than threshold days" — claro |
| B. Parametros | 2/3 | threshold_days com default (7) documentado |
| C. Output | 3/3 | stagnant_count, stagnant_candidates com days_in_stage, affected_stages |
| D. Erros | 2/3 | Standard |
| E. Steering | 2/3 | Sem nota de sobreposicao com get_pipeline_health.stalled_candidates |

---

#### [check_pending_offers] — Score: 10/15

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza | 2/3 | "at risk of candidate withdrawal" — boa motivacao |
| B. Parametros | 2/3 | threshold_hours: 72 documentado |
| C. Output | 2/3 | risk_level computado por count (>5 = high) — heuristica nao documentada |
| D. Erros | 2/3 | Standard |
| E. Steering | 2/3 | Urgencia bem enquadrada |

---

#### [check_overdue_tasks] — Score: 9/15

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza | 2/3 | Requer user_id — especifico de usuario, nao empresa |
| B. Parametros | 2/3 | company_id e user_id obrigatorios |
| C. Output | 2/3 | overdue_tasks com days_overdue, priority, status |
| D. Erros | 2/3 | Sem erro se user_id nao encontrado |
| E. Steering | 1/3 | Sem nota que orquestrador deve passar user_id do usuario ativo |

---

#### [check_pipeline_risks] — Score: 14/15 (MELHOR OVERALL)

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| A. Clareza | 3/3 | "Comprehensive risk scan: stagnant candidates, empty pipelines, low conversion" |
| B. Parametros | 3/3 | Apenas company_id — interface simples para operacao complexa |
| C. Output | 3/3 | overall_risk_level + tres sub-listas estruturadas + recommendations |
| D. Erros | 2/3 | Standard |
| E. Steering | 3/3 | "Overview first, drill down second" — sinalizado claramente |

---

## Analise de Composicao de Tools

### Composabilidade

O sistema foi projetado com composabilidade em mente, mas ha falhas criticas de implementacao:

**Fluxos bem compostos:**
- `parse_and_create_candidate` → `add_to_vacancy` → `analyze_cv_match` → `wsi_screening` (Passo 1-4 do upload de CV)
- `check_pipeline_risks` → `get_pipeline_health` → `check_stagnant_candidates` (overview → drill down)
- `get_strategic_recommendations` apos coleta de contexto com tools de insight

**Falhas de composicao:**
- `schedule_interview` (scheduling domain, stub) vs `schedule_interview` (communication domain, real) — agente pode escolher o stub
- `move_candidate_to_stage` (pipeline domain, stub) vs `update_candidate_stage` (candidate_tools, real) — duplicata com fidelidades opostas
- Tools em YAML scope allowlists sem handler Python — composicao declarada mas inexecutavel

### Redundancias Identificadas

| Par Redundante | Sobreposicao | Risco |
|----------------|-------------|-------|
| `schedule_interview` (communication_tools.py) vs `schedule_interview` (scheduling_tools.py) | Nome identico, implementacoes opostas (real vs stub) | Agente escolhe versao errada dependendo do scope |
| `move_candidate_to_stage` (pipeline) vs `update_candidate_stage` (candidate_tools) | Mesmo proposito funcional | pipeline version e stub; candidate_tools version e real |
| `check_stagnant_candidates` vs `get_pipeline_health.stalled_candidates` | Ambos retornam candidatos parados | Triple coverage com get_pipeline_risks |
| `predict_time_to_fill` vs `get_time_to_fill` | Nomes similares; preditivo vs historico | LLM confunde facilmente |

### Gaps — Tools Faltando

| Tool Faltando | Por que Necessaria | Agentes Afetados |
|---------------|-------------------|-----------------|
| `get_valid_pipeline_stages` | LLM precisa saber stages validos antes de update_candidate_stage | orchestrator, recruiter_assistant |
| `get_task_by_id` | check_overdue_tasks retorna listas mas nao existe tool para detalhes de task | orchestrator |
| `undo_last_action` / `cancel_stage_move` | Acoes restritas nao tem rollback apos confirmacao HITL | orchestrator |
| `get_interview_questions_for_job` | wsi_screening existe mas nao ha tool para preview do banco de perguntas | orchestrator |
| `get_tool_execution_status` | Operacoes async (export, report) retornam export_id mas sem tool para poll de status | orchestrator |
| `list_available_email_templates` | send_email aceita template_id mas nao ha tool que lista templates validos | communication |
| `search_nurture_sequences` | create_nurture_sequence existe mas sem tool para listar sequencias existentes | recruiter_assistant |
| `get_candidate_consent_status` | Conformidade LGPD — agente precisa verificar consentimento antes de WhatsApp/email | communication |

### Granularidade

**Tools muito amplas (devem ser divididas):**
- `create_and_screen_candidate` — orquestra 4 operacoes distintas; dificulta erro handling e debugging
- `check_pipeline_risks` — 3 sub-analises; adequado pois serve como ponto de entrada

**Tools muito granulares (poderiam ser consolidadas):**
- `pause_job` + `close_job` + `publish_job` poderiam ser `update_job_status(job_id, status)` — reduziria superficie de API

**Taxonomia recomendada:**
```
read/      → get_*, search_*, list_*, compare_*
compute/   → analyze_*, calculate_*, forecast_*, predict_*
write/     → create_*, update_*, move_*, add_*, remove_*
comms/     → send_*, schedule_*, notify_*
admin/     → export_*, generate_report_*, publish_*
proactive/ → check_*, detect_*, suggest_*
```

---

## Catalogo de Anti-Patterns

### AP-01: Phantom Success (Silent Mock Returns)
**Severidade: CRITICA**

Retornar `success: True` quando a acao nao ocorreu. O LLM acredita que operacao foi concluida com sucesso.

| Arquivo | Linha | Descricao |
|---------|-------|-----------|
| `app/shared/tools/export_tools.py` | 69 | `candidates_count = 25` hardcoded quando candidate_ids vazio |
| `app/shared/tools/export_tools.py` | 120-140 | `sample_metrics` dict fake retornado por generate_report como dados reais |
| `app/domains/communication/tools/communication_tools.py` | ~95 | `"using mock response"` fallback em excecao DB — success: True sem email enviado |
| `app/domains/pipeline/tools/pipeline_tools.py` | multiplas | `notified: notify` retorna input como confirmacao de envio |
| `app/domains/interview_scheduling/tools/scheduling_tools.py` | multiplas | status: "sent" sem envio; interview_id fake retornado como real |

**Impacto:** Categoria-1 ACI failure. LLM reporta acoes como concluidas, candidatos nao sao notificados, dados falsos sao apresentados como fatos.

**Correcao padrao:**
```python
# NUNCA:
except Exception as e:
    return {"success": True, "simulated": True}

# SEMPRE:
except Exception as e:
    return {"success": False, "error": "db_unavailable",
            "message": f"Falha ao {acao}: {str(e)}. Tente novamente em alguns instantes.",
            "suggestion": "Se o erro persistir, contate o administrador do sistema."}
```

---

### AP-02: Schema Mismatch (YAML != Python Handler)
**Severidade: ALTA**

| Tool | YAML Params | Python Handler | Impacto |
|------|------------|----------------|---------|
| `send_email` | `to: array[string], subject, body` | `candidate_id: str, template_id, subject, body` | LLM passa `to: ["uuid"]`, Python recebe candidate_id vazio → falha silenciosa |
| `export_candidates` | `fields: array` | `include_fields: list[str]` | Nome de parametro diferente — tool ignora selecao de campos |
| `generate_report` | `format: [pdf, csv, json]` | `format: [pdf, xlsx, html]` | Enum mismatch — LLM pode passar "csv" que nao e suportado pelo handler |

---

### AP-03: Non-deterministic Data (Random em Producao)
**Severidade: CRITICA**

`get_interview_status` (`app/domains/interview_scheduling/tools/scheduling_tools.py`) usa `random.Random(hash(interview_id))` para gerar status de entrevista. O status retornado (completed, cancelled, scheduled) nao reflete estado real.

`check_interviewer_availability` usa `random.shuffle` com seed baseado em hash para gerar slots de disponibilidade. Agentes tomam decisoes de agendamento baseadas em dados aleatorios.

**Correcao:** Substituir por consulta real ao banco ou, na ausencia de integracao, retornar explicitamente `{"success": False, "error": "calendar_integration_not_configured", "mode": "demo"}`.

---

### AP-04: Parametro Ambiguo / Nao-tipado
**Severidade: ALTA**

| Tool | Parametro Problematico | Problema |
|------|----------------------|---------|
| `update_job` | `updates: dict` | LLM inventa chaves invalidas como {"salary": 5000} em vez de {"salary_range": {"min": 5000}} |
| `bulk_advance_candidates` | `candidate_ids: str` (CSV) | Inconsistente com todos outros tools que usam list[str] |
| `extend_offer` | `offer_details: str (JSON)` | Forca serializacao JSON dentro de JSON — propenso a erros de escape |
| `check_diversity_targets` | `current_pipeline: str (JSON)` | Mesmo problema de JSON-in-string |
| `update_candidate_stage` | `target_stage: string` sem enum | LLM deve adivinhar "Triagem" vs "triagem" vs "screening" |
| `save_job_draft`, `validate_job_fields`, `generate_enriched_jd`, `search_candidates`, `update_job` | `fields: {type: object}` | Objeto opaco sem sub-schema — LLM nao sabe chaves validas |

---

### AP-05: Tool Name Collision
**Severidade: MEDIA**

| Tool Name | Ocorrencias | Contextos |
|-----------|------------|---------|
| `schedule_interview` | 2 | `communication_tools.py` (real + DB) vs `scheduling_tools.py` (stub simulado) |
| `move_candidate_to_stage` vs `update_candidate_stage` | 2 | Mesmo proposito funcional; pipeline version (stub) vs candidate_tools (real) |
| `search_candidates` | 3 | `tool_registry_metadata.yaml`, `sourcing_tool_registry.py`, `tool_permissions.yaml` |
| `get_time_to_fill` (historico) vs `predict_time_to_fill` (preditivo) | 2 | `insight_tools.py` vs `predictive_tools.py` — nomes similares, propositos distintos |

---

### AP-06: Missing Tools (Declarados Mas Sem Handler)
**Severidade: ALTA**

15+ tools aparecem em YAML/scope allowlists sem handler Python correspondente. Quando chamadas, executor retorna `{"error": "Tool not found"}` e agente pode alucinar resposta.

Tools sem handler confirmadas:
- `get_recruiter_metrics`, `get_velocity_metrics`, `get_efficiency_metrics`, `get_workload_distribution`
- `get_hiring_quality`, `get_cost_metrics`, `get_trends`, `get_market_benchmarks`
- `get_talent_quality`, `get_talent_engagement`, `get_talent_availability`, `get_diversity_metrics`
- `get_candidate_history`, `get_ml_predictions`, `get_conversion_patterns`
- `compare_candidates`, `pause_job` (separado de update_job), `close_job` (idem)
- `get_smart_alerts`, `get_prediction_metrics`, `get_job_benchmark`

---

### AP-07: Context Pollution
**Severidade: BAIXA**

`get_candidate_quality_distribution` retorna `top_candidates[:10]` hardcoded sem parametro `limit`. Em pipelines grandes, 10 candidatos desperdicam contexto com dados irrelevantes. Em pipelines pequenos, retorna menos de 10 sem indicacao.

Tools de export usam emojis em mensagens de resposta (`"Exportacao de..."`, `"Erro ao exportar..."`). Pode causar problemas em parsers de output estruturado que fazem string matching.

---

### AP-08: HITL Invisivel ao LLM
**Severidade: MEDIA**

38 tools estao na lista `restricted_tools` do `tool_permissions.yaml` com enforcement HITL no ActionExecutor. Mas as **descriptions das tools nao mencionam que exigem confirmacao humana**. O LLM pode:
1. Chamar a tool multiplas vezes acreditando que falhou
2. Nao avisar o usuario que uma confirmacao sera necessaria
3. Entrar em loop esperando resultado que so vira apos HITL

**Correcao:** Adicionar sufixo padrao a todas as 38 descriptions restritas: "[REQUER CONFIRMACAO HUMANA antes da execucao]"

---

## Benchmark vs. Padrao Anthropic

| Criterio Anthropic | Tools Conformes | % | Status |
|-------------------|----------------|---|--------|
| Nome verbo+substantivo descritivo (snake_case) | 38/38 | 100% | Excelente |
| Descricao: O QUE + QUANDO + QUANDO NAO | 6/38 | 16% | Critico |
| Parametros com nomes semanticos e tipos | 22/38 | 58% | Atencao |
| Enum onde aplicavel (stages, status, tipos) | 18/38 | 47% | Atencao |
| Output consistente entre tools similares | 15/38 | 39% | Critico |
| Erros actionable com codigos semanticos | 12/38 | 32% | Critico |
| Paginacao para resultados grandes | 4/38 | 11% | Critico |
| Rate limits/timeouts documentados | 0/38 | 0% | Ausente |
| Tool versionada | 0/38 | 0% | Ausente |
| Side effects documentados na description | 2/38 | 5% | Critico |
| Restricted tools com aviso HITL na description | 0/38 | 0% | Critico |

**Avaliacao Anthropic ACI 8 criterios (camada compartilhada):**

| # | Criterio | Status | Evidencia |
|---|-----------|--------|-----------|
| 1 | Nomes unicos e auto-explicativos | FALHA PARCIAL | get_time_to_fill vs predict_time_to_fill; search_candidates em 3 contextos |
| 2 | Descriptions dizem ao LLM quando chamar cada tool | FALHA PARCIAL | Maioria diz "o que" nao "quando vs alternativas" |
| 3 | Parametros com tipos, descriptions, enums | FALHA PARCIAL | 5+ tools com {type: object} sem properties; stage names sem enum |
| 4 | Required vs optional explicito | APROVADO | required: [...] arrays consistentes em YAML e Python |
| 5 | Output schema documentado e consistente | FALHA | 3 tools retornam dados falsos como success; 2 schema mismatches |
| 6 | Error cases com codigos | APROVADO PARCIAL | tool_handler normaliza erros; codigos sao free-string str(e) |
| 7 | Side effects documentados | FALHA | publish: bool em create_job, notify_candidate em update_candidate_stage — nenhum documentado |
| 8 | Paginacao e limites explicitos | FALHA PARCIAL | get_candidate_quality_distribution hardcoda [:10]; search_candidates sem max |

---

## Infraestrutura de Tools — O que Esta Bem

A plataforma tem infraestrutura de nivel de producao que nao deve ser alterada:

| Componente | Qualidade | Notas |
|-----------|---------|-------|
| `ToolPermissionsLoader` (YAML-driven, lru_cache, tenant overrides) | EXCELENTE | Fail-closed em erro, deterministico |
| `ToolExecutionContext` (tenant isolation, can_access_company) | EXCELENTE | Isolamento de empresa enforced na execucao, nao apenas no schema |
| `restricted_tools` em YAML com enforcement HITL no ActionExecutor | EXCELENTE | 38 tools listadas; enforced no nivel do ActionExecutor |
| `validate_registry_against_yaml()` | BOM | Detecta drift de description entre codigo e YAML |
| `GlobalToolRegistry.list_tools_for_scope()` com fail-closed em erro de scope | EXCELENTE | Comportamento correto de seguranca |
| `ToolExecutor.MAX_TOOL_CALLS_PER_REQUEST = 3` | BOM | Previne tool calling desenfreado |
| `tool_handler` decorator (tenant check + module gating + error normalization) | BOM | Reduz boilerplate corretamente |
| Module gating (premium features, beta features, tasting mode) | EXCELENTE | Controle de acesso a tools ciente do produto |
| Dual-registry pattern (ToolRegistry + GlobalToolRegistry) | BOM | Separacao clara entre tools de dominio e tools de agentes |
| Tres tipos distintos de ToolDefinition | ATENCAO | Cria disconnects silenciosos — ver AP-06 |

---

## Prioridades de Remediacao

### P0 — Corrigir ESTA SEMANA

1. **Remover `candidates_count = 25` stub** em `app/shared/tools/export_tools.py` linha 69. Substituir por erro explicito quando candidate_ids vazio: `{"success": False, "error": "no_candidates_specified", "message": "Informe candidate_ids para exportar."}`.

2. **Remover `sample_metrics` hardcoded** em `app/shared/tools/export_tools.py` linhas 120-140. Retornar dados reais do banco ou `{"success": False, "error": "report_generation_pending"}`.

3. **Corrigir fallback silencioso** em `app/domains/communication/tools/communication_tools.py` ~linha 95. Nunca retornar `success: True` quando DB falhou. Falhar explicitamente.

4. **Corrigir schema mismatch** de `send_email`: alinhar YAML (`to: array`) com Python (`candidate_id: str`) — escolher um padrao e aplicar em ambos.

5. **Bloquear `get_compliance_report` em producao** — retornar `{"success": False, "error": "not_implemented", "message": "Relatorio de compliance nao disponivel nesta versao."}` em vez de `lgpd_compliant: True` sempre.

6. **Adicionar aviso em `audit_hiring_decision`** — implementar persistencia real ou retornar `{"success": False, "error": "audit_persistence_not_configured"}` ate que persistencia seja implementada.

7. **Substituir `random.Random(hash(interview_id))`** em `get_interview_status` e `check_interviewer_availability` por consulta real ao banco ou retornar modo demo explicito.

### P1 — Sprint Atual

8. **Adicionar enum de stages validos** em `update_candidate_stage.target_stage` e `bulk_update_candidates_stage.target_stage` em `app/tools/tool_registry_metadata.yaml` linhas 133-145 e 189-203.

9. **Adicionar "[REQUER CONFIRMACAO HUMANA]"** nas descriptions das 38 tools em `restricted_tools` list do `app/config/tool_permissions.yaml`.

10. **Substituir `updates: dict`** em `update_job` por schema explicito com `additionalProperties: False`.

11. **Trocar `candidate_ids: str (CSV)`** em `bulk_advance_candidates` por `candidate_ids: list[str]`.

12. **Trocar `offer_details: str (JSON)`** em `extend_offer` por objeto estruturado com campos `salary`, `start_date`, `benefits`, `contract_type`.

13. **Adicionar `next_steps`** no output de todas as tools de acao (send_email, update_candidate_stage, close_job, schedule_interview, etc.).

14. **Listar tools sem handler** como desabilitadas no YAML com `enabled: false` ou implementar handlers stub que retornam `not_implemented` em vez de silenciosamente aparecerem em scope configs.

### P2 — Backlog

15. **Criar `get_valid_pipeline_stages`** — retorna lista de etapas validas para a empresa, necessario antes de chamar `update_candidate_stage`.

16. **Criar `list_available_email_templates`** — lista templates validos para `send_email.template_id`.

17. **Renomear `predict_time_to_fill`** para `estimate_time_to_fill` para reduzir colisao com `get_time_to_fill`.

18. **Adicionar `total_count` no output de `search_candidates`** para suporte a paginacao.

19. **Adicionar `limit` parametro** em `get_candidate_quality_distribution` para remover hardcoded `[:10]`.

20. **Criar `get_candidate_consent_status`** para conformidade LGPD antes de enviar comunicacoes.

21. **Remover emojis** das mensagens de response em `app/shared/tools/export_tools.py`.

---

## Reescritas Prioritarias

As 5 tools mais usadas com piores descriptions:

### 1. `update_job` (Score atual: 4/15 → Meta: 12/15)

**Description atual:** "Atualiza uma vaga existente com novos dados."

**Description recomendada:**
```
Atualiza campos de uma vaga existente. Campos editaveis: title, department, seniority_level,
work_model, location, description, requirements (lista de strings), status,
salary_range (objeto {min, max, currency}).
Campos protegidos (id, company_id, created_at) sao ignorados silenciosamente.
NAO use para publicar/pausar/fechar — use publish_job, pause_job, close_job respectivamente.
NAO use para criar vagas — use create_job.
Requer que a vaga pertenca a sua empresa (cross-tenant acessos sao rejeitados).
```

**Schema de parametros reescrito:**
```json
{
  "type": "object",
  "properties": {
    "job_id": {"type": "string", "format": "uuid", "description": "UUID da vaga a atualizar"},
    "updates": {
      "type": "object",
      "description": "Apenas os campos abaixo sao suportados. Outros campos sao ignorados.",
      "properties": {
        "title": {"type": "string", "maxLength": 200},
        "department": {"type": "string"},
        "seniority_level": {"type": "string", "enum": ["Estagio", "Junior", "Pleno", "Senior", "Especialista", "Coordenador", "Gerente", "Diretor"]},
        "work_model": {"type": "string", "enum": ["Remoto", "Hibrido", "Presencial"]},
        "location": {"type": "string"},
        "description": {"type": "string"},
        "requirements": {"type": "array", "items": {"type": "string"}, "description": "Lista de requisitos textuais"},
        "salary_range": {"type": "object", "properties": {"min": {"type": "number"}, "max": {"type": "number"}, "currency": {"type": "string", "default": "BRL"}}}
      },
      "additionalProperties": false
    }
  },
  "required": ["job_id", "updates"]
}
```

---

### 2. `send_email` (Score atual: 5/15 → Meta: 11/15)

**Description recomendada:**
```
Envia email para um candidato especifico via integracao de email da plataforma.
Use quando: recrutador pede contato por email, envio de convite de entrevista, comunicacao de decisao.
Prefira template_id para comunicacoes padronizadas (rejeicao, aprovacao, proximas etapas).
So use subject+body para mensagens completamente customizadas.
NAO use para envio em massa (use send_bulk_email).
NAO use se candidato nao tiver email cadastrado (verifique com get_candidate_details antes).
Apos sucesso, registre no historico com add_candidate_note.
[REQUER CONFIRMACAO HUMANA antes da execucao]
```

---

### 3. `move_candidate_to_stage` / `update_candidate_stage` — Consolidacao

**Acao recomendada:** Deprecar `move_candidate_to_stage` (stub em pipeline_tools.py) e usar exclusivamente `update_candidate_stage` (real em candidate_tools.py).

**Description recomendada para `update_candidate_stage`:**
```
Move um candidato para outra etapa do pipeline de uma vaga.
Etapas validas: use get_valid_pipeline_stages para obter a lista atual da empresa
(tipicamente: Triagem, Entrevistas, Teste Tecnico, Oferta, Contratado, Reprovado).
NAO use move_candidate_to_stage (tool descontinuada — mesmo proposito mas sem persistencia).
Use quando recrutador pedir para avancar, recuar ou rejeitar candidato no pipeline.
[REQUER CONFIRMACAO HUMANA antes da execucao]
```

---

### 4. `parse_and_create_candidate` (Score atual: 8/15 → Meta: 12/15)

**Description recomendada:**
```
Parseia texto bruto de CV com IA e cria (ou reutiliza) cadastro de Candidato no banco.
PASSO 1 DE 3 — fluxo completo: parse_and_create_candidate → add_to_vacancy → analyze_cv_match.
Se ja existir candidato com mesmo email, retorna o existente (duplicate: true) sem criar novo.
Entrada: texto puro (plain text), minimo 30 caracteres. Aceita CV colado ou extraido de PDF/Word.
NAO use para candidatos ja cadastrados — use search_candidates ou get_candidate_details primeiro.
source deve ser um de: cv_upload, linkedin, referral, headhunting, job_board, internal.
```

---

### 5. `search_candidates` (Score atual: 7/15 → Meta: 11/15)

**Description recomendada:**
```
Busca candidatos cadastrados na empresa com filtros multiplos.
Retorna APENAS candidatos da empresa do contexto atual (company_id automatico).
Filtros disponiveis: skills (lista), min_score/max_score (0-100), status, stage, seniority,
location, date_range (datas de cadastro). Limite padrao: 20 resultados.
Para ver se ha mais resultados, use offset para paginacao.
NAO use para buscar candidatos de outras empresas.
NAO use para analise de skills — use analyze_skill_gaps para comparar com requisitos de vaga.
```

**Output melhorado:**
```python
return {
    "success": True,
    "candidates": [...],
    "total_count": total,  # ADICIONAR: total de resultados para paginacao
    "returned_count": len(results),
    "has_more": total > offset + limit,
    "next_offset": offset + limit if total > offset + limit else None
}
```

---

## Apendice: Naming Analysis

### Avaliacao de Convencao de Nomes

| Convencao | Aderencia | Exemplos |
|-----------|-----------|---------|
| `verbo_substantivo` (snake_case) | ALTA (85%) | get_pipeline_health, check_stagnant_candidates, predict_dropout_risk |
| snake_case | 100% | Consistente em todas as tools |
| Consistencia de idioma | FALHA | Mix de ingles nos nomes (get_time_to_fill) e portugues nas descriptions |
| Prefixo `check_` (proactive) | CONSISTENTE | check_stagnant_candidates, check_pending_offers, check_overdue_tasks, check_pipeline_risks |
| Prefixo `predict_` | INCONSISTENTE | predict_dropout_risk, predict_time_to_fill MAS get_pipeline_forecast e get_strategic_recommendations |

### Anti-patterns de Nomes

1. **Prefix mismatch ambiguo:** `predict_time_to_fill` vs `get_time_to_fill` — mesmo substantivo, prefixos diferentes para preditivo vs historico
2. **`get_` sobrecarregado:** 20+ tools comecam com `get_` sem sub-taxonomia
3. **Domain leak:** `wsi_screening` expoe nomenclatura interna; deveria ser `initiate_candidate_screening`
4. **Side effect invisivel:** `export_candidates` (gera arquivo) vs `search_candidates` (retorna dados) — ambos parecem reads mas um tem side effect permanente

---

*Relatorio gerado: 2026-04-14*
*Auditor: Claude Sonnet 4.6 (ACI Expert Mode)*
*Scope: /home/runner/workspace/lia-agent-system/app/ — todos os dominios de tools + camada compartilhada*
*Referencias: P08_DOMAIN_TOOLS.md (1185 linhas) + P08_SHARED_TOOLS.md (572 linhas)*
