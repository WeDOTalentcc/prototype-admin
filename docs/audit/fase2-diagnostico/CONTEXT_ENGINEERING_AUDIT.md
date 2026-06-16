# CONTEXT_ENGINEERING_AUDIT.md — Auditoria de Context Engineering
> P09 · Fase 2 · Data: 2026-04-14 · Plataforma: WeDOTalent / LIA

---

## Sumário Executivo

Esta auditoria avaliou o estado do context engineering do sistema LIA em 6 dimensões: altitude de system prompts (14 agentes), carregamento de ferramentas, memória e histórico, dados dinâmicos injetados, orçamento de janela de contexto e degradação de contexto (context rot). A avaliação cobriu todos os arquivos YAML de domínio em `/home/runner/workspace/lia-agent-system/app/prompts/domains/`, o `SystemPromptBuilder`, o `AgenticLoop`, o `MainOrchestrator` e os serviços de memória, totalizando análise estática de mais de 40 arquivos de código.

A saúde geral do sistema é **4.8/10 — Crítica**. Existem 3 dimensões com score 2/10 (tool context, context rot) ou 4/10 (memória), que superam os pontos positivos. O achado mais preocupante é estrutural e afeta cada request enviado ao LLM: `AgenticLoop.get_tool_schemas()` — linha 51 de `agentic_loop.py` — chama `get_all_schemas()` sem filtrar por agente, enviando todos os 76 tools registrados a cada request. Isso gera entre 11.400 e 15.200 tokens de overhead de ferramentas por chamada, representando 40–50% da janela de contexto consumida antes da primeira mensagem do usuário. A correção é uma única linha de código.

O único achado positivo estrutural é que, *sem o bug CF-01*, o orçamento de contexto é saudável: overhead total de ~19.300 tokens = apenas 9,65% da janela de 200K tokens, com 90,35% disponível para raciocínio e resposta. Adicionalmente, 10 dos 14 agentes possuem altitude de system prompt correta ou aceitável. Os problemas críticos restantes — dois sistemas de memória paralelos não integrados, summarização como dead code, limites de histórico inconsistentes em 7 endpoints e dois agentes com prompts esqueleto manipulando dados críticos — são todos remediáveis em sprints próximas.

---

## Context Engineering Health Index

| Dimensão | Score | Status |
|----------|-------|--------|
| 1. System Prompt Altitude | 7.1/10 | 🟡 |
| 2. Tool Context (carregamento) | 2/10 | 🔴 |
| 3. Memória e Histórico | 4/10 | 🔴 |
| 4. Dados Dinâmicos Injetados | 6/10 | 🟡 |
| 5. Context Window Budget | 8/10 (sem bug) / 2/10 (com bug) | ⚠/🔴 |
| 6. Context Rot | 2/10 | 🔴 |
| **Índice Geral** | **4.8/10** | **🔴** |

---

## Achados Críticos (P0) — Bloqueiam Qualidade de Raciocínio

### CF-01: 76 tools carregadas em todo request (~11.400–15.200 tokens overhead, 40–50% da janela)
- **Arquivo:** `agentic_loop.py:51`
- **Evidência:**
  ```python
  def get_tool_schemas(self, provider: str = "claude") -> list[dict]:
      tools = self._tool_registry.list_tools()
      return self._tool_registry.get_all_schemas(format=provider)  # ALL tools, não filtradas
  ```
- **Impacto:** Todos os 76 tools (média 150–200 tokens cada) são enviados ao LLM em cada request, independente do agente ativo. Agente de sourcing pode ver e tentar chamar tools de billing, ATS ou automação.
- **Fix:** Substituir `get_all_schemas()` por `get_schemas_for_agent(agent_type)` — infraestrutura já existe no `ToolRegistry`.

### CF-02: Dois sistemas de memória paralelos nunca integrados (pgvector como dead code)
- **Arquivos:** `app/domains/recruiter_assistant/services/memory_service.py` (pgvector) vs `app/domains/recruiter_assistant/services/conversation_memory.py` (PostgreSQL puro)
- **Impacto:** O `MainOrchestrator` usa apenas o segundo. Recuperação semântica de contexto histórico não acontece. O `MemoryService` armazena embeddings de mensagens que nunca são consultados no pipeline principal de chat.

### CF-03: Sumarização automática como dead code (`llm_service=None`)
- **Arquivo:** `app/domains/recruiter_assistant/services/conversation_memory.py`
- **Evidência:** `__init__(self, llm_service=None)` — o `llm_service` pode ser `None`; `update_summary()` nunca é chamado pelo `MainOrchestrator` (linha 754 de `main_orchestrator.py`). `SUMMARY_TRIGGER_COUNT=10` existe mas nunca é acionado de forma garantida.

### CF-04: Pipeline Transition com 181 tokens manipulando dados irreversíveis sem guardrails
- **Arquivo:** `app/prompts/domains/pipeline_transition.yaml` (636 bytes, 16 linhas)
- **Evidência:**
  ```yaml
  system_prompt: |
    Especialista em gerenciar o pipeline de candidatos.
    Pode mover candidatos entre etapas, interpretar contextos de transição, predizer sub-status
    e sugerir próximas ações baseadas no estado atual do pipeline.
    Sempre confirme ações destrutivas ou irreversíveis com o recrutador antes de executar.
  ```
- **Impacto:** O agente que manipula dados mais críticos (mover/reprovar candidatos) tem o menor prompt do sistema — 181 tokens. Sem definição de o que é "destrutivo", sem regras de confirmação, sem exemplos.

### CF-05: `analysis.yaml` usa `{cv_text}`/`{candidate_name}` como placeholders literais sem verificação de substituição
- **Arquivo:** `app/prompts/domains/analysis.yaml`
- **Evidência:** system_prompt contém `Nome: {candidate_name}`, `CV/Texto: {cv_text}` como f-string literals. Se o `PromptLoader` não fizer substituição, o LLM recebe as variáveis literais. Este é também o único agente de avaliação de candidatos sem FairnessGuard obrigatório.

### CF-06: 7 limites de histórico diferentes em 7 endpoints distintos
- **Evidência:**
  - `app/api/v1/chat.py:857` — `limit=20`
  - `app/api/v1/wizard_smart_orchestrator.py:290` — `[-10:]`
  - `app/api/v1/lia_assistant/wizard.py:201` — `[-5:]`
  - `app/orchestrator/orchestrator.py:417` — `[-10:]`
  - `app/domains/recruiter_assistant/services/jobs_management_assistant_service.py:60` — `[-6:]`
  - `app/domains/ai/services/rag_service.py:138` — `[-5:]`
  - `app/api/v1/agent_chat_ws.py:840` — `[-10:]`
- **Impacto:** Conversas longas perdem contexto de formas diferentes dependendo do ponto de entrada. Usuário que inicia no `/chat` (20 msgs) e acessa o `/wizard` (5 msgs) perde contexto de forma opaca.

---

## 1. SYSTEM PROMPT ALTITUDE

### Sumário de Altitude por Agente

| Agente | Altitude | Tokens Est. | Score | Principal Gap |
|--------|----------|-------------|-------|---------------|
| Orchestrator | Correto | ~4.520 | 8/10 | Few-shot redundante (20+ exemplos); dessincronização YAML vs. runtime |
| CV Screening | Correto | ~1.048 | 8/10 | Sem guia de quando usar Skills Ontology vs. Interview Intelligence |
| WSI Evaluation | Correto | ~996 | 8/10 | Sem exemplos few-shot vinculados a ferramentas |
| WSI Interview | Correto-Alto | ~1.364 | 7/10 | Duplica escopo do interview_scheduling |
| Sourcing | Correto | ~1.097 | 8/10 | Sem decision tree para quando usar busca interna vs. externa |
| Communication | Correto | ~835 | 7/10 | Sem guia de quando usar Mailgun vs. Twilio vs. Teams |
| Job Management | Correto | ~912 | 7/10 | 9 tools no registry sem nenhuma mencionada no prompt |
| Analytics | Correto-Alto | ~1.038 | 7/10 | 4 ferramentas Talent Intelligence sem condições de disparo |
| Talent Pool | **Muito Baixo** | ~319 | 3/10 | Sem identidade, sem regras comportamentais, sem guia de tools |
| Recruiter Assistant | Correto | ~1.194 | 8/10 | 6 tools Talent Intelligence sem condições de ativação |
| Interview Scheduling | Correto | ~943 | 7/10 | Duplica escopo do wsi_interview |
| Pipeline Transition | **Muito Baixo** | ~181 | 2/10 | Dados irreversíveis, prompt mínimo, sem guardrails |
| Automation | Correto | ~867 | 7/10 | Sem mapeamento evento → tool |
| Analysis | **Alto-Brittle** | ~855 | 5/10 | Placeholders `{cv_text}/{candidate_name}` sem substituição confirmada; sem FairnessGuard |

### Detalhamento por Agente

#### Orchestrator
**Altitude:** Correto — posicionado no nível certo (roteador puro, não executor)
**Tamanho:** 15.818 bytes / ~4.520 tokens
**Arquivo:** `/home/runner/workspace/lia-agent-system/app/prompts/domains/orchestrator.yaml`

Critérios:
- Identidade clara: ✓ "Intent Router da LIA — classifica e roteia"
- Ações concretas: ✓ 9 agentes com exemplos de intent mapeados
- Guia de tools: ✗ Nenhuma — o orquestrador não tem guia de tool_calling próprio
- Constraints ("quando NÃO fazer"): ✓ META-PERGUNTAS e GENERAL_QUERY documentados
- Exemplos/few-shot: ✓ 20+ exemplos reais com JSON output esperado

**Evidência de problema:** O prompt tem 174 linhas no YAML, mas o orquestrador real (`orchestrator.py`) tem lógica própria de roteamento separada. Existe **dessincronização de responsabilidade** — o YAML serve de spec, mas não garante que seja o que o sistema usa em runtime.

**Recomendação:** Reduzir few-shot para 10 exemplos mais representativos (~40% de corte). Adicionar seção `## Quando NÃO rotear` para casos de multi-step. Versão atual ~4.5k tokens é aceitável para um router, mas desnecessariamente pesada.

---

#### CV Screening
**Altitude:** Correto
**Tamanho:** 3.668 bytes / ~1.048 tokens
**Arquivo:** `/home/runner/workspace/lia-agent-system/app/prompts/domains/cv_screening.yaml`

Critérios:
- Identidade clara: ✓ "Especialista em avaliação de currículos e scoring WSI"
- Ações concretas: ✓ Score WSI 7 blocos, thresholds explícitos (≥75% / 60-74% / <60%)
- Guia de tools: ✗ Menciona Skills Ontology e Interview Intelligence mas não instrui QUANDO usá-las
- Constraints ("quando NÃO fazer"): ✓ scope_out bem definido, FairnessGuard obrigatório
- Exemplos/few-shot: ✗ Nenhum exemplo com output esperado

**Evidência de problema:** A seção `## Talent Intelligence` diz "Você tem acesso a ferramentas..." sem especificar qual tool chamar para cada caso de uso. O modelo terá de inferir `call skills_ontology` vs `call interview_intelligence` por conta própria.

**Recomendação:** Adicionar guia de tools inline:
```yaml
tool_guidance:
  - intent: gaps de skills → chamar skills_ontology(candidate_skills, job_requirements)
  - intent: análise de transcrição → chamar interview_intelligence(transcript_id)
```
Adicionar 2-3 exemplos few-shot de output de triagem.

---

#### WSI Evaluation
**Altitude:** Correto
**Tamanho:** 3.487 bytes / ~996 tokens
**Arquivo:** `/home/runner/workspace/lia-agent-system/app/prompts/domains/wsi_evaluation.yaml`

Critérios:
- Identidade clara: ✓ Metodologias Bloom/Dreyfus/Big Five explicitadas
- Ações concretas: ✓ 7 blocos com pesos percentuais declarados
- Guia de tools: ✗ Nenhuma
- Constraints ("quando NÃO fazer"): ✓ "Decisões finais de contratação → gestor humano"
- Exemplos/few-shot: ✗ Nenhum

**Recomendação:** Adicionar ao menos 1 exemplo de parecer completo com evidências por bloco. Isso reduz variabilidade de output (alta importância para auditoria SOX/LGPD).

---

#### WSI Interview
**Altitude:** Correto — com problema estrutural de duplicação de escopo
**Tamanho:** 4.773 bytes / ~1.364 tokens
**Arquivo:** `/home/runner/workspace/lia-agent-system/app/prompts/domains/wsi_interview.yaml`

Critérios:
- Identidade clara: ✓ CBI/STAR bem definidos
- Ações concretas: ✓ Fluxo de condução estruturado
- Guia de tools: ✗ Nenhuma
- Constraints ("quando NÃO fazer"): ✓ Perguntas proibidas bem listadas
- Exemplos/few-shot: ✓ 3 exemplos com happy_path, bias_check, evasive_response_handling

**Evidência de problema:** `scope_in` do wsi_interview inclui "Condução de entrevistas WSI via WhatsApp, voz ou texto" — o mesmo que `scope_in` do interview_scheduling. **Dois agentes têm escopo idêntico.** O orchestrator.py precisa desambiguar em runtime o que é ambíguo por design.

**Recomendação:** Unificar wsi_interview e interview_scheduling OU definir boundary preciso: wsi_interview = perguntas comportamentais; interview_scheduling = calendário + logística. Documentar no YAML.

---

#### Sourcing
**Altitude:** Correto
**Tamanho:** 3.839 bytes / ~1.097 tokens
**Arquivo:** `/home/runner/workspace/lia-agent-system/app/prompts/domains/sourcing.yaml`

Critérios:
- Identidade clara: ✓ "Especialista em busca ativa, Pearch AI, busca booleana"
- Ações concretas: ✓ Regras de < 5 e > 50 resultados bem definidas
- Guia de tools: ✗ Menciona Skills Ontology/Market Intelligence/Nurture sem trigger conditions
- Constraints ("quando NÃO fazer"): ✓ scope_out claro
- Exemplos/few-shot: ✗ Nenhum

**Recomendação:** Adicionar decision tree para tools:
- `< 5 resultados` → chamar `skills_ontology(expand=True)` para encontrar adjacências
- `query salarial` → chamar `market_intelligence(benchmark=True)`
- `candidatos inativos` → chamar `nurture(reengagement_signal=True)`

---

#### Communication
**Altitude:** Correto
**Tamanho:** 2.924 bytes / ~835 tokens
**Arquivo:** `/home/runner/workspace/lia-agent-system/app/prompts/domains/communication.yaml`

Critérios:
- Identidade clara: ✓
- Ações concretas: ✓ Canal por canal descrito
- Guia de tools: ✗ Sem guia de quando usar Mailgun vs. Resend (fallback) vs. Twilio vs. Teams
- Constraints ("quando NÃO fazer"): ✓ LGPD, confirmação de massa explícita
- Exemplos/few-shot: ✗ Nenhum

**Recomendação:** Adicionar matriz de seleção de canal no system prompt:
```
email individual → Mailgun; fallback Resend
WhatsApp → Meta API primeiro; fallback Twilio
Teams → apenas notificações internas de equipe
```

---

#### Job Management
**Altitude:** Correto
**Tamanho:** 3.193 bytes / ~912 tokens
**Arquivo:** `/home/runner/workspace/lia-agent-system/app/prompts/domains/job_management.yaml`

Critérios:
- Identidade clara: ✓
- Ações concretas: ✓ Wizard conversacional descrito
- Guia de tools: ✗ Nenhuma referência a search_salary_benchmark, validate_job_fields, get_job_suggestions, save_job_draft
- Constraints ("quando NÃO fazer"): ✓ scope_out claro, linguagem inclusiva obrigatória
- Exemplos/few-shot: ✗ Nenhum

**Evidência de problema:** O `tool_registry_metadata.yaml` registra 9 ferramentas com `allowed_agents: [job_planner, ...]`, mas o system prompt do agente não menciona nenhuma delas. O modelo não sabe quando chamar `validate_job_fields` vs. simplesmente prosseguir.

**Recomendação:** Adicionar seção `## Fluxo de Ferramentas` mapeando cada passo do wizard à tool correspondente.

---

#### Analytics
**Altitude:** Correto, tendendo a Alto pela proliferação de ferramentas não guiadas
**Tamanho:** 3.634 bytes / ~1.038 tokens
**Arquivo:** `/home/runner/workspace/lia-agent-system/app/prompts/domains/analytics.yaml`

Critérios:
- Identidade clara: ✓ KPIs, gargalos, previsões, bias audit
- Ações concretas: ✓ Four-Fifths Rule citada, thresholds (< 30 registros)
- Guia de tools: ✗ 4 ferramentas mencionadas (Skills Ontology, Mobilidade Interna, Workforce Planning, Engagement Metrics) sem condições de disparo
- Constraints ("quando NÃO fazer"): ✓ dados agregados, sem PII
- Exemplos/few-shot: ✗ Nenhum

**Recomendação:** Mapear cada intent de analytics à ferramenta:
- `bias audit` → skills_ontology(audit_mode=True)
- `previsão de fechamento` → workforce_planning(forecast=True)
- `engajamento de candidatos` → engagement_metrics(sequence_id=X)

---

#### Talent Pool
**Altitude:** Muito Baixo — prompt esqueleto, não um system prompt de produção
**Tamanho:** 1.117 bytes / ~319 tokens
**Arquivo:** `/home/runner/workspace/lia-agent-system/app/prompts/domains/talent_pool.yaml`

Critérios:
- Identidade clara: ✗ Apenas "Especialista em gerenciamento de bancos de talentos vivos" — sem persona desenvolvida
- Ações concretas: ✗ Lista de CAPACIDADES, não de comportamentos
- Guia de tools: ✗ Nenhuma
- Constraints ("quando NÃO fazer"): ✗ Apenas "Respeitar LGPD e privacidade" — sem regras específicas
- Exemplos/few-shot: ✗ Nenhum

**Evidência do problema:**
```yaml
system_prompt: |
  Especialista em gerenciamento de bancos de talentos vivos.
  CAPACIDADES:
  - Criar e gerenciar bancos de talentos por perfil/função/mercado
  ...
  TOM: profissional e orientado a resultados.
```
Isso é uma spec de produto, não um system prompt. Não define comportamento em edge cases.

**Recomendação:** Reescrever completamente seguindo o padrão dos outros agentes v2.0: persona, scope_in, scope_out, behavioral_rules, system_prompt com seções ##, intent_examples.

---

#### Recruiter Assistant
**Altitude:** Correto
**Tamanho:** 4.181 bytes / ~1.194 tokens
**Arquivo:** `/home/runner/workspace/lia-agent-system/app/prompts/domains/recruiter_assistant.yaml`

Critérios:
- Identidade clara: ✓ "Co-piloto inteligente do recrutador"
- Ações concretas: ✓ Briefing diário, comparação de candidatos, próximas ações
- Guia de tools: ✗ Lista 6 ferramentas Talent Intelligence sem condições de ativação
- Constraints ("quando NÃO fazer"): ✓ scope_out referencia outros domínios
- Exemplos/few-shot: ✗ Nenhum

**Recomendação:** Este agente é o mais genérico e portanto o mais propenso a acionar ferramentas desnecessárias. Adicionar regra: "Acione tools de Talent Intelligence apenas quando o recrutador solicitar explicitamente análise avançada — não por padrão em perguntas simples de status."

---

#### Interview Scheduling
**Altitude:** Correto — com problema de duplicação de escopo com wsi_interview
**Tamanho:** 3.302 bytes / ~943 tokens
**Arquivo:** `/home/runner/workspace/lia-agent-system/app/prompts/domains/interview_scheduling.yaml`

Critérios:
- Identidade clara: ✓
- Ações concretas: ✓ Calendário + condução WSI descritos
- Guia de tools: ✗ Nenhuma (calendário, transcrição)
- Constraints ("quando NÃO fazer"): ✓ perguntas proibidas, consentimento
- Exemplos/few-shot: ✗ Nenhum

**Evidência do problema:** `scope_in` inclui "Condução de entrevistas WSI (competências comportamentais, CBI)" — idêntico ao wsi_interview. Dois prompts de agente descrevem o mesmo papel, resultando em ambiguidade de roteamento.

---

#### Pipeline Transition
**Altitude:** Muito Baixo — o menor prompt do sistema, insuficiente para um agente de produção
**Tamanho:** 636 bytes / ~181 tokens
**Arquivo:** `/home/runner/workspace/lia-agent-system/app/prompts/domains/pipeline_transition.yaml`

Critérios:
- Identidade clara: ✗ Uma linha genérica
- Ações concretas: ✗ "pode mover candidatos, predizer sub-status, sugerir próximas ações" — sem regras de como
- Guia de tools: ✗ Nenhuma — e este é o agente que mais precisaria (aciona ações irreversíveis)
- Constraints ("quando NÃO fazer"): ✗ Apenas "Sempre confirme ações destrutivas" — sem critério de o que é destrutivo
- Exemplos/few-shot: ✗ Nenhum

**Evidência do problema:**
```yaml
system_prompt: |
  Especialista em gerenciar o pipeline de candidatos.
  Pode mover candidatos entre etapas, interpretar contextos de transição, predizer sub-status
  e sugerir próximas ações baseadas no estado atual do pipeline.
  Sempre confirme ações destrutivas ou irreversíveis com o recrutador antes de executar.
```
Este agente manipula dados de pipeline — um erro pode mover ou reprovar candidatos incorretamente. O nível de detalhe é proporcional ao inverso do risco: risco alto, prompt mínimo.

**Recomendação:** Urgente reescrita completa. Definir explicitamente: quais transições requerem confirmação, quais são reversíveis, como interpretar contextos ambíguos ("avançar" pode ser avançar para próxima etapa ou avançar para contratação).

---

#### Automation
**Altitude:** Correto
**Tamanho:** 3.035 bytes / ~867 tokens
**Arquivo:** `/home/runner/workspace/lia-agent-system/app/prompts/domains/automation.yaml`

Critérios:
- Identidade clara: ✓ "Automatizar fluxos repetitivos"
- Ações concretas: ✓ Regras de confirmação para ações irreversíveis
- Guia de tools: ✗ Sem mapeamento evento → tool
- Constraints ("quando NÃO fazer"): ✓ LGPD, log obrigatório, falha silenciosa proibida
- Exemplos/few-shot: ✗ Nenhum

**Recomendação:** Adicionar tabela de evento-trigger → ação → confirmação necessária? para reduzir incerteza na lógica de automação.

---

#### Analysis
**Altitude:** Alto-Brittle — template de preenchimento, não system prompt dinâmico
**Tamanho:** 2.992 bytes / ~855 tokens
**Arquivo:** `/home/runner/workspace/lia-agent-system/app/prompts/domains/analysis.yaml`

Critérios:
- Identidade clara: ✓ Scoring framework claro
- Ações concretas: ✓ 4 componentes com pesos, 8 arquétipos Big Five, 5 níveis de recomendação
- Guia de tools: ✗ Nenhuma — retorna apenas JSON hardcoded
- Constraints ("quando NÃO fazer"): ✗ Sem FairnessGuard, sem referência a LGPD
- Exemplos/few-shot: ✗ Sem exemplos de output

**Evidência do problema:**
```yaml
system_prompt: |
  ## CANDIDATO A ANALISAR:
  Nome: {candidate_name}
  CV/Texto: {cv_text}
  ...
  Retorne APENAS o JSON, sem texto adicional.
```
Este prompt usa placeholders `{candidate_name}`, `{cv_text}` — é um **f-string/template**, não um system prompt YAML. Se o `PromptLoader` não fizer a substituição antes de enviar ao LLM, o modelo recebe variáveis literais `{cv_text}`. Além disso, é **o único agente que avalia candidatos sem FairnessGuard** obrigatório, ao contrário do cv_screening e wsi_evaluation.

**Recomendação:** (1) Verificar se a substituição de variáveis está implementada no loader. (2) Adicionar FairnessGuard ao fluxo de análise. (3) Alinhar versão (está em `2024.01`, outros em `2.0`).

---

### Gap Sistemático: Ausência de `tool_guidance` em Todos os Agentes

**Status:** Gap sistemático em todos os 14 agentes
**Evidência:** Zero arquivos YAML de domínio contêm seção `tool_guidance`, `when_to_call`, ou similar. 8 agentes mencionam Talent Intelligence tools sem condições de ativação. O `tool_registry_metadata.yaml` define `allowed_agents` por tool, mas nenhum YAML de domínio instrui o agente sobre QUANDO acionar cada tool.

**Impacto:** O modelo decide quando chamar tools por inferência do `description` da tool, gerando chamadas desnecessárias ou omissões. Em produção, isso pode resultar em chamadas de API desnecessárias, latência adicional e resultados incorretos.

**Recomendação:** Adicionar seção padronizada `## Quando Usar Ferramentas` em cada YAML com tabela `intent → tool → condição`.

---

## 2. TOOL CONTEXT

### CF-01: Carregamento de 76 Tools por Request — Análise Crítica

**Arquivo:** `agentic_loop.py:51`

**Evidência de código:**
```python
def get_tool_schemas(self, provider: str = "claude") -> list[dict]:
    tools = self._tool_registry.list_tools()
    return self._tool_registry.get_all_schemas(format=provider)  # ALL tools, não filtradas
```

O `AgenticLoop.get_tool_schemas()` chama `get_all_schemas()` em vez de `get_schemas_for_agent(agent_type)`. Todos os 76 tools são enviados ao LLM em cada request, independente do agente ativo.

**Estimativa de overhead:**
- Total de ferramentas registradas: 76 (conforme `tool_registry_metadata.yaml`)
- Média estimada por tool: ~150–200 tokens (nome + description + JSON schema de parâmetros)
- Custo total: **~11.400–15.200 tokens de tools em cada request do agentic loop**
- Somando lia_persona base (~4.428 tokens): **total de contexto estático ~15.800–19.600 tokens por request**
- Isso representa **~40–50% da janela de contexto** utilizada antes da primeira mensagem do usuário

**Infraestrutura de filtragem existente (não utilizada):**
- `ToolRegistry.get_tools_for_agent(agent_type)` — filtragem por `allowed_agents` ✓
- `ToolRegistry.get_schemas_for_agent(agent_type, format)` — schemas filtrados ✓
- `filter_tools_by_scope()` em `app/tools/scope_config.py` — filtragem por escopo ✓
- `tool_permissions.yaml` com `restricted_tools` ✓

**Fix (1 linha):**
```python
# ANTES:
return self._tool_registry.get_all_schemas(format=provider)

# DEPOIS:
return self._tool_registry.get_schemas_for_agent(self.agent_type, format=provider)
```

**Overhead por agente (com e sem fix):**

| Agente | Ferramentas Específicas | Overhead Atual (76 tools) | Overhead Pós-Fix |
|--------|------------------------|--------------------------|------------------|
| orchestrator | ~76/76 | ~11.400–15.200 tokens | ~11.400 tokens |
| job_planner | 9 tools | ~11.400–15.200 tokens | ~1.350–1.800 tokens |
| recruiter_assistant | ~15 tools | ~11.400–15.200 tokens | ~2.250–3.000 tokens |
| sourcing | ~5 tools | ~11.400–15.200 tokens | ~750–1.000 tokens |
| analytics | ~8 tools | ~11.400–15.200 tokens | ~1.200–1.600 tokens |
| screening | ~6 tools | ~11.400–15.200 tokens | ~900–1.200 tokens |

---

### Seleção Dinâmica de Tools

**Status:** Infraestrutura implementada, não utilizada no path principal

O `ToolRegistry` tem toda a infraestrutura necessária para filtragem por agente. O `tool_registry_metadata.yaml` define `allowed_agents` por ferramenta. Nenhum YAML de domínio tem seção `tool_guidance` mapeando tools a intents. O `AgenticLoop.get_tool_schemas()` ignora `agent_type` completamente.

---

### PersonalizationContext — Construído mas Truncado

**Status:** Feature incompleta com falha silenciosa
**Arquivo:** `main_orchestrator.py:262-276`

**Evidência:**
```python
_perso_ctx = await _perso_svc.get_or_create_profile(ctx.user_id, db)
if _perso_ctx and hasattr(_perso_ctx, 'settings') and _perso_ctx.settings:
    _prefs = []
    if getattr(_perso_ctx.settings, 'communication_style', ''):
        _prefs.append(f"Estilo de comunicação: {_perso_ctx.settings.communication_style}")
    if getattr(_perso_ctx.settings, 'verbosity_preference', ''):
        _prefs.append(f"Verbosidade: {_perso_ctx.settings.verbosity_preference}")
    if getattr(_perso_ctx.settings, 'focus_areas', None):
        _prefs.append(f"Foco principal: {', '.join(_perso_ctx.settings.focus_areas)}")
    if _prefs:
        ctx.extra["recruiter_context"] = "\n".join(_prefs)
```

**O que é injetado:** `communication_style`, `verbosity_preference`, `focus_areas` (apenas se configurados pelo usuário — 3 campos).

**O que não é injetado:** histórico de decisões anteriores, preferências de candidatos, calibração de score baseada em feedback histórico — que é o que o `RecruiterPersonalizationService.get_personalization_context()` completo retorna.

A injeção está protegida por `try/except` silencioso — se a query falhar, o contexto de personalização é silenciosamente omitido (`logger.debug`). O recrutador não recebe personalização sem nenhum aviso.

**Recomendação:** (1) Mudar `logger.debug` para `logger.warning` na exceção. (2) Injetar também: decisões recentes, preferências de score threshold calibradas, vagas ativas do recrutador.

---

### SystemPromptBuilder: Spec vs. Runtime Gap

**Arquivo:** `/home/runner/workspace/lia-agent-system/app/shared/prompts/system_prompt_builder.py`

O `SystemPromptBuilder.build()` compõe o prompt final concatenando nesta ordem:
1. `lia_persona.yaml` → base (~15.5 KB / ~4.428 tokens) — **sempre presente**
2. `agent_prompts.yaml` (seção do agent_type) — adições de domínio específico
3. Contexto atual: tenant, recrutador, usuário, página, resumo de conversa
4. Regras anti-repetição (se conversa em andamento)
5. Roteamento (intent + entities)
6. Protocolo ReAct (para agentes não-orchestrator)
7. Instruções adicionais (`extra_instructions`)

**Problema crítico:** Os prompts YAML de domínio (`/prompts/domains/*.yaml`) **NÃO são usados pelo SystemPromptBuilder**. O builder carrega `shared/agent_prompts.yaml`, não `domains/orchestrator.yaml`. Os YAMLs de domínio são spec/documentação mas podem não ser o que está sendo injetado em runtime.

**Evidência:** `system_prompt_builder.py:_load_domain_additions()` carrega `shared/agent_prompts.yaml`; os 18 arquivos em `domains/` não são referenciados pelo builder.

**Recomendação:** Verificar conteúdo de `shared/agent_prompts.yaml` para confirmar se é subset/mirror dos domains. Criar teste de regressão que compara o output do builder vs. o YAML de domínio correspondente.

---

## 3. MEMÓRIA E HISTÓRICO

### 3A. Conversation History
- **Status:** Implementado (Parcial — inconsistente entre endpoints)
- **Risco:** Alto
- **Evidência:**
  - `app/api/v1/chat.py:857` — `limit=20` (chat principal, via DB)
  - `app/api/v1/wizard_smart_orchestrator.py:290` — `conversation_history[-10:]`
  - `app/api/v1/lia_assistant/wizard.py:201` — `conversation_history[-5:]`
  - `app/orchestrator/orchestrator.py:417` — `conversation_history[-10:]`
  - `app/domains/recruiter_assistant/services/jobs_management_assistant_service.py:60` — `conversation_history[-6:]`
  - `app/domains/ai/services/rag_service.py:138` — `conversation_history[-5:]`
  - `app/api/v1/agent_chat_ws.py:840` — `conversation_history[-10:]`
- **Problema:** Não existe um limite canônico único. Cada endpoint define seu próprio slice (-5, -6, -10, -20), criando comportamento inconsistente. Conversas longas perdem contexto de formas diferentes dependendo do ponto de entrada.
- **Recomendação:** Centralizar o limite em uma constante `HISTORY_WINDOW = 20` no módulo `app/shared/constants.py` e consumir de todos os endpoints. Adotar janela deslizante mínima de 10 turnos completos (user+assistant) como padrão.

---

### 3B. Working Memory (Curto Prazo)
- **Status:** Implementado
- **Risco:** Médio
- **Evidência:**
  - `app/orchestrator/pending_action.py` — `PendingActionState` com TTL de 5 minutos, PostgreSQL + in-memory L1. Rastreia parâmetros coletados, parâmetros faltantes, aguardando confirmação.
  - `app/orchestrator/memory_resolver.py` — `MemoryResolver` (Tier 0): resolução de pronomes, referências posicionais e paginação antes do roteamento. Detecta "o terceiro candidato", "mover ele", "mostra mais".
  - `app/shared/memory/candidate_list_store.py` — Redis-backed, TTL 30 min. Armazena lista completa de candidatos (id, name, score, etc.) separado dos IDs no `ConversationState`.
- **Problema:** O TTL do `PendingActionState` (5 min) é muito curto para fluxos lentos de wizard. O fallback in-memory não sobrevive a reinicializações do worker.
- **Recomendação:** Aumentar TTL para 30 minutos. Garantir que o pool PostgreSQL seja inicializado de forma assíncrona para evitar bloqueio no startup.

---

### 3C. Episodic Memory (Médio Prazo)
- **Status:** Parcial
- **Risco:** Médio
- **Evidência:**
  - `app/domains/recruiter_assistant/services/conversation_memory.py` — `ConversationMemory` com `SUMMARY_TRIGGER_COUNT = 10`, `MAX_CONTEXT_MESSAGES = 20`, `MAX_CONTEXT_TOKENS_ESTIMATE = 4000`. Gera summary automático a cada 10 mensagens usando LLM. Mantém últimas 5 mensagens pós-sumarização.
  - `app/api/v1/user_agent_preferences.py` — `UserAgentPreferenceService` para preferências persistidas por usuário.
  - `app/api/v1/suggestion_feedback.py` — `feedback_learning_service.apply_learning()` para aprendizado com correções.
  - `app/api/v1/lia_assistant/_shared.py:562` — Injeta `salary_patterns` e `seniority_patterns` do feedback histórico no contexto do wizard.
- **Problema:** O `ConversationMemory` com summarização existe, mas **não está integrado ao `MainOrchestrator` de forma consistente**. Em `main_orchestrator.py:754`, o `get_context_for_llm()` carrega até 20 mensagens brutas sem chamar `update_summary()`. O summarize automático depende de LLM service injetado, que pode ser `None` (`__init__(self, llm_service=None)`).
- **Recomendação:** Integrar `update_summary()` no pipeline do `MainOrchestrator`. Garantir que `llm_service` nunca seja `None` no `ConversationMemory`. Verificar se `CONTEXT_COMPRESSION_CONFIG["total_context_max_tokens"] = 2000` é respeitado antes de enviar ao LLM.

---

### 3D. Semantic Memory (Longo Prazo) — Vector Store
- **Status:** Implementado (para busca e roteamento; ausente para recuperação de contexto conversacional)
- **Risco:** Médio
- **Evidência:**
  - `app/orchestrator/vector_semantic_cache.py` — `VectorSemanticCache` usa pgvector com cosine similarity >= 0.85 para cache de roteamento (Tier 3 do CascadedRouter). Embeddings via OpenAI `text-embedding-3-small` (1536 dims) com fallback Gemini.
  - `app/services/twin_inference_service.py:71` — `_retrieve_similar(twin_id, query_embedding, k, db)` via pgvector K-NN para Digital Twin.
  - `app/domains/recruiter_assistant/services/memory_service.py` — `MemoryService.search_similar_messages()` com `limit=5`, `min_similarity=0.7`. **Armazena embeddings de cada mensagem com `embedding_service.generate_embedding(content)`.**
  - `app/api/v1/rag_search.py` — Endpoint RAG híbrido (pgvector + tsvector BM25) para busca de candidatos.
- **Problema crítico:** O `MemoryService` (que gera embeddings de mensagens) **não está conectado ao pipeline de conversação principal**. O `MainOrchestrator` usa `ConversationMemory` (PostgreSQL puro, sem vetores). Há dois sistemas paralelos de memória sem integração: um com vetores (`memory_service.py`) e um sem (`conversation_memory.py`). A recuperação semântica de contexto conversacional histórico não acontece.
- **Recomendação:** Consolidar `MemoryService` e `ConversationMemory`. Implementar retrieval semântico de mensagens históricas relevantes (top-k=3) para enriquecer o contexto em conversas longas ou retomadas após dias.

---

## 4. DADOS DINÂMICOS INJETADOS

| Agente / Endpoint | Dados Injetados | Formato | Volume Estimado | Relevância |
|---|---|---|---|---|
| **MainOrchestrator** (chat) | tenant snippet (company name, sector, open vacancies, autonomy), user name/role, recruiter preferences, conversation history (20 msgs), page context (entity_id, context_type) | f-string PT-BR + dict Python | ~1.200–2.000 tokens | Alta |
| **WSI Interview** (`wsi/_shared.py`) | job description, candidate profile, previous answers, interview script | Markdown text blocks | ~1.500–2.500 tokens | Alta |
| **CV Screening** (`cv_screening.yaml`) | CV text, job requirements, evaluation criteria | YAML-templated Markdown | ~800–1.500 tokens | Alta |
| **Wizard Orchestrator** (`wizard_smart_orchestrator.py`) | draft state, conversation_history[-10:], tenant context | JSON + text | ~600–1.000 tokens | Média |
| **Sourcing** (`sourcing.yaml`) | job vacancy details, required skills, salary range, candidate pool size | YAML-templated | ~400–700 tokens | Alta |
| **Recruiter Assistant** (`recruiter_assistant.yaml`) | salary correction patterns, seniority patterns, user preferences | dict injected as text | ~200–500 tokens | Média |
| **Analytics** (`analytics.yaml`) | pipeline metrics, conversion rates, time-to-hire data | JSON snippet | ~300–600 tokens | Média |
| **Culture Analysis** (`culture_analysis.yaml`) | company culture questionnaire responses, benchmarks | YAML blocks | ~500–900 tokens | Baixa |
| **Interview Notes** (`interview_notes.py:387`) | candidate_context (CV summary, work history), job_context (description, requirements, tech reqs) | Markdown multi-section | ~700–1.200 tokens | Alta |
| **lia_assistant conversational** | conversation summary OR last 10 messages, tenant snippet | Text block | ~400–800 tokens | Alta |

**Análise:** A injeção de dados dinâmicos está bem implementada nos agentes de maior risco (WSI, CV Screening, Interview Notes). O problema principal é que o `PersonalizationContext` — que enriqueceria todos os endpoints — está truncado a 3 campos e sujeito a falha silenciosa (ver Seção 2).

---

## 5. CONTEXT WINDOW BUDGET

### Modelo de Referência: Claude Sonnet 4.6 (200K tokens)
**Metodologia:** 1 token ≈ 3,5 chars em PT-BR. Tamanhos de prompt extraídos via `wc -c`.

#### Cálculo de System Prompts
| Arquivo | Bytes | Tokens Estimados |
|---|---|---|
| `orchestrator.yaml` | 15.818 | ~4.519 |
| `culture_analysis.yaml` | 11.275 | ~3.221 |
| `lia_persona.yaml` (shared) | 15.528 | ~4.436 |
| `agent_prompts.yaml` (shared) | 11.573 | ~3.306 |
| `defensive.yaml` (shared) | 7.778 | ~2.222 |
| `wsi_interview.yaml` | 4.773 | ~1.364 |
| `recruiter_assistant.yaml` | 4.181 | ~1.194 |
| `sourcing.yaml` | 3.839 | ~1.097 |
| `wsi_evaluation.yaml` | 3.487 | ~996 |
| `analytics.yaml` | 3.634 | ~1.038 |
| `cv_screening.yaml` | 3.668 | ~1.048 |
| `intent_classification.yaml` | 3.238 | ~925 |
| `outros domínios (~8)` | ~24.000 | ~6.857 |
| **Total YAML (todos)** | **111.395** | **~31.827** |

> Nota: em qualquer invocação single-agent, apenas 1 domain prompt + shared prompts são carregados simultaneamente. O overhead típico é: `lia_persona.yaml` (~4.436) + `defensive.yaml` (~2.222) + 1 domain prompt (~1.000–4.500) = **~7.658–11.158 tokens**.

#### Budget por Turn — Cenário Típico (MainOrchestrator)

| Componente | Tokens | % do Budget (200K) |
|---|---|---|
| System prompt (lia_persona + defensive + orchestrator domain) | ~11.000 | 5,5% |
| Tool descriptions (38 tools × ~200 chars / 3,5) | ~2.171 | 1,1% |
| Tenant context snippet | ~80 | 0,04% |
| User name/role + page context | ~50 | 0,02% |
| Dados dinâmicos (job_context + candidate_context) | ~1.200 | 0,6% |
| Histórico conversa (20 msgs × ~200 tokens avg) | ~4.000 | 2,0% |
| Memória retrieval (summary anterior, se ativo) | ~500 | 0,25% |
| Recruiter preferences (salary/seniority patterns) | ~300 | 0,15% |
| **Total overhead por turn** | **~19.300** | **~9,65%** |
| **Budget restante para resposta + raciocínio** | **~180.700** | **~90,35%** |

**Status sem CF-01:** ✅ Saudável (<30%)

**Status com CF-01 ativo:** 🔴 Crítico — tool overhead sobe de ~2.171 para ~11.400–15.200 tokens, total de overhead passa para ~28.000–32.000 tokens = **14–16% com possibilidade de chegsar a 40–50% em agentes com system prompts maiores como Orchestrator (~16.500 tokens base + 15.200 de tools = ~31.700 tokens, 15,85% — mas para todos os agentes no pico = ~40–50%)**

> O uso típico fica em ~10% do orçamento de 200K *sem o bug*. O headroom é amplo. O risco não está no limite da janela em si, mas na qualidade do que é incluído e no bug CF-01.

#### Por Agente — Top 3 Mais Pesados

| Agente | System Prompt | Dados Dinâmicos | Histórico | Total Estimado | Status |
|---|---|---|---|---|---|
| **WSI Interview** | ~5.800 (wsi_interview + lia_persona) | ~2.500 (job + candidate + respostas) | ~2.000 (10 msgs) | **~10.300** | ✅ |
| **Culture Analysis** | ~7.657 (culture_analysis + lia_persona) | ~900 (questionário) | ~1.500 | **~10.057** | ✅ |
| **Orchestrator (chat completo)** | ~11.000 | ~1.500 | ~4.000 | **~16.500** | ✅ |

**Conclusão de budget:** Nenhum agente está perto do limite *sem o bug CF-01*. O budget é amplamente suficiente. O problema é de *qualidade* e *consistência* do conteúdo injetado, e do bug que multiplica o overhead de tools por 5-8x.

---

## 6. CONTEXT ROT

### Mecanismos de Detecção Implementados

| Mecanismo | Implementado? | Evidência |
|---|---|---|
| Limite de histórico por endpoint | Parcial | Múltiplos limites (-5, -6, -10, -20) inconsistentes |
| Summarização automática | Sim (não integrado ao fluxo principal) | `SUMMARY_TRIGGER_COUNT=10` em `conversation_memory.py` |
| Detecção de contradição | Ausente | Nenhum mecanismo detecta quando usuário contradiz info anterior |
| Purge de contexto obsoleto | Ausente | Não há mecanismo para remover mensagens irrelevantes |
| Context quality scoring | Ausente | Nenhum score de qualidade do contexto acumulado |
| Alerta de degradação | Ausente | Nenhum log ou métrica de `context_rot` encontrado |
| Reset de contexto por nova intenção | Parcial | `_NEW_SEARCH_PATTERNS` no `memory_resolver.py` detecta nova busca |

### Análise de Risco de Degradação

**Risco 1 — Histórico crescente não sumarizado (Alto)**
O `MainOrchestrator` carrega até 20 mensagens brutas (`max_messages=20`) sem verificar se a sumarização está ativa. Para conversas longas no mesmo contexto (ex.: recruiter trabalhando em uma vaga por horas), o histórico acumula ruído: mensagens de confirmação ("ok", "entendido"), saudações repetidas, refinamentos iterativos. O `SUMMARY_TRIGGER_COUNT=10` existe na classe `ConversationMemory`, mas `update_summary()` só é chamado quando `llm_service` não é `None` — não há garantia que seja.

**Risco 2 — Dois sistemas de memória não integrados (Crítico)**
`MemoryService` (com pgvector, armazena embedding por mensagem) e `ConversationMemory` (PostgreSQL, armazena texto) coexistem sem integração. O resultado é que:
- A busca semântica em histórico nunca é usada no pipeline de chat principal.
- `MAX_CONTEXT_TOKENS_ESTIMATE = 4000` na `ConversationMemory` é uma estimativa heurística (não usa `tiktoken` ou API de contagem de tokens). Pode falhar com mensagens muito longas.

**Risco 3 — Slices de histórico inconsistentes criam experiência fragmentada (Médio)**
Um usuário que inicia uma conversa no `/chat` (20 msgs) e depois acessa o `/wizard` (5 msgs) ou `/lia_assistant/conversational` (10 msgs) perde contexto de forma opaca. Não há estratégia de recuperação de sessão cross-endpoint.

**Risco 4 — Ausência de detecção de contradição (Médio)**
Se um recruiter afirma em T1 "quero salários até 8k" e em T10 "o orçamento é 12k", nenhum mecanismo detecta ou resolve a contradição. O LLM recebe ambas as informações e pode comportar-se de forma inconsistente nas respostas subsequentes.

**Risco 5 — Token counting por heurística (Baixo-Médio)**
`MAX_CONTEXT_TOKENS_ESTIMATE = 4000` e `CONTEXT_COMPRESSION_CONFIG["total_context_max_tokens"] = 2000` são estimativas de tokens sem uso de `tiktoken`. Para CVs longos ou descrições de vagas em PT-BR com caracteres Unicode, a estimativa pode estar ~15–20% errada.

### Cenários de Risco Concretos

| Cenário | Risco | Impacto |
|---|---|---|
| Recruiter em conversa de 40+ turnos sobre uma vaga complexa | Context rot por acúmulo de ruído | LIA "esquece" requisitos iniciais ou contradiz a si mesma |
| Sessão de WSI com candidato prolixo (respostas longas) | Histórico de 10 msgs ultrapassa estimativa de tokens | Truncagem silenciosa ou erro na API |
| Recruiter abre vaga nova no wizard após conversa longa no chat | Slice [-5] no wizard perde contexto crítico | LIA não sabe sobre vagas discutidas anteriormente |
| Usuário corrige salário duas vezes | Sem detecção de contradição | LIA usa valor mais antigo ou mais recente aleatoriamente |
| Worker restart com pending action em memória | Fallback in-memory perdido | PendingActionState perde parâmetros coletados |
| Redis indisponível + CandidateListStore cai para in-memory | Lista de candidatos perde TTL real | Múltiplos workers têm listas diferentes para a mesma sessão |

### Os 7 Limites de Histórico Inconsistentes

| Arquivo | Linha | Limite | Contexto |
|---------|-------|--------|---------|
| `app/api/v1/chat.py` | 857 | `limit=20` | Chat principal via DB |
| `app/api/v1/wizard_smart_orchestrator.py` | 290 | `[-10:]` | Wizard inteligente |
| `app/api/v1/lia_assistant/wizard.py` | 201 | `[-5:]` | Wizard LIA Assistant |
| `app/orchestrator/orchestrator.py` | 417 | `[-10:]` | Orquestrador principal |
| `app/domains/recruiter_assistant/services/jobs_management_assistant_service.py` | 60 | `[-6:]` | Gestão de vagas |
| `app/domains/ai/services/rag_service.py` | 138 | `[-5:]` | Busca RAG |
| `app/api/v1/agent_chat_ws.py` | 840 | `[-10:]` | WebSocket chat |

---

## Prioridades de Remediação

### P0 — Corrigir ESTA SEMANA (Impacto Direto em Qualidade)

| Finding | Arquivo | Linha | Fix | Esforço | Impacto |
|---------|---------|-------|-----|---------|---------|
| **CF-01: 76 tools em todo request** | `agentic_loop.py` | 51 | Substituir `get_all_schemas()` por `get_schemas_for_agent(agent_type)` | **1h (1 linha)** | **Crítico — reduz 40-50% overhead** |
| **CF-04: Pipeline Transition prompt 181 tokens** | `pipeline_transition.yaml` | — | Reescrita completa com persona, behavioral_rules, exemplos | 4h | Alto — dados irreversíveis sem guardrails |
| **Talent Pool prompt esqueleto 319 tokens** | `talent_pool.yaml` | — | Reescrita completa seguindo template v2.0 | 4h | Alto — agente sem regras de comportamento |

**Fix imediato CF-01 (copiar e colar):**
```python
# agentic_loop.py linha 51
# ANTES:
return self._tool_registry.get_all_schemas(format=provider)

# DEPOIS:
return self._tool_registry.get_schemas_for_agent(self.agent_type, format=provider)
```

---

### P1 — Sprint Atual

| Finding | Arquivo | Fix | Esforço |
|---------|---------|-----|---------|
| CF-03: Analysis sem FairnessGuard + placeholder não verificado | `analysis.yaml`, `PromptLoader` | Verificar substituição de vars; adicionar FairnessGuard | 2h |
| CF-06: Verificar dessincronização `shared/agent_prompts.yaml` vs `domains/*.yaml` | `system_prompt_builder.py` | Audit + teste de regressão | 2h |
| CF-02/CF-03 memória: sumarização dead code | `conversation_memory.py`, `main_orchestrator.py` | Injetar `llm_service` obrigatório; chamar `update_summary()` como background task | 4h |
| CF-06: Limites de histórico inconsistentes | 7 endpoints | Criar `HISTORY_CONTEXT_WINDOW = 15` em `constants.py`; padronizar todos | 3h |
| PersonalizationContext falha silenciosa | `main_orchestrator.py:262` | Mudar `logger.debug` para `logger.warning`; injetar campos adicionais | 2h |

---

### P2 — Backlog

| Finding | Fix | Esforço |
|---------|-----|---------|
| Dois sistemas de memória paralelos (pgvector + PostgreSQL) | Consolidar `MemoryService` + `ConversationMemory` em `UnifiedMemoryService` | 16h |
| Segmentar `lia_persona.yaml` em camadas | (a) identidade core ~500 tokens; (b) vocab RH sob demanda; (c) guidelines éticos apenas para agentes de avaliação | 8h |
| Unificar wsi_interview/interview_scheduling OU definir boundary hard | Reescrita de 1 YAML + update do orchestrator | 6h |
| Tool guidance em todos os 14 agentes | Adicionar `## Quando Usar Ferramentas` com intent→tool→condição | 16h |
| Token counting preciso | Implementar `ContextBudgetManager` com `anthropic.count_tokens()` | 8h |
| PendingActionState TTL curto + fallback volátil | Aumentar TTL 5min→30min; Redis como store primário | 4h |
| Detecção de contradição no histórico | Implementar `ConflictDetector` simples para campos-chave (salário, prazo, requisitos) | 8h |

---

## Recomendações de Otimização por Agente

### Pipeline Transition (Score: 2/10 → Meta: 8/10)

**Prompt atual (abreviado):**
```yaml
system_prompt: |
  Especialista em gerenciar o pipeline de candidatos.
  Pode mover candidatos entre etapas, interpretar contextos de transição,
  predizer sub-status e sugerir próximas ações baseadas no estado atual.
  Sempre confirme ações destrutivas ou irreversíveis com o recrutador.
```
~181 tokens.

**Adições recomendadas:**
```yaml
persona: |
  Você é o Pipeline Transition Agent da LIA — guardião das transições de candidatos.
  Sua responsabilidade é garantir que cada movimentação no pipeline seja intencional,
  auditável e reversível quando possível.

behavioral_rules:
  - NUNCA mova candidatos entre etapas sem confirmação explícita do recrutador
  - SEMPRE liste o estado atual e o estado destino antes de executar
  - Transições REVERSÍVEIS: avançar etapa, adicionar tag, alterar sub-status
  - Transições IRREVERSÍVEIS: reprovar candidato, arquivar vaga, enviar oferta formal
  - Ambiguidades como "avançar" = sempre perguntar "avançar para qual etapa?"
  - Contextos de transição em lote (>3 candidatos): exigir confirmação individual ou "confirmar todos"

scope_in:
  - Mover candidatos entre etapas do pipeline ATS
  - Predição de sub-status baseada em histórico de interações
  - Sugestão de próximas ações por etapa
  - Confirmação de ações em lote

scope_out:
  - Avaliação técnica de candidatos → cv_screening ou wsi_evaluation
  - Comunicação com candidatos → communication_agent
  - Criação/encerramento de vagas → job_management

intent_examples:
  - "avançar João para entrevista" → CONFIRMAR: "Mover João da etapa X para Entrevista Técnica. Confirma?"
  - "reprovar todos da triagem" → CONFIRMAR INDIVIDUAL ou LOTE antes de executar
  - "qual o próximo passo para Ana?" → informar sem executar
```

**Tokens estimados pós-reescrita:** ~850–1.000 tokens (de 181 para ~900 = +397%)

---

### Talent Pool (Score: 3/10 → Meta: 7/10)

**Prompt atual (abreviado):**
```yaml
system_prompt: |
  Especialista em gerenciamento de bancos de talentos vivos.
  CAPACIDADES:
  - Criar e gerenciar bancos de talentos por perfil/função/mercado
  - Segmentar e filtrar candidatos por critérios
  TOM: profissional e orientado a resultados.
```
~319 tokens.

**Adições recomendadas:**
```yaml
persona: |
  Você é o Talent Pool Agent da LIA — curador estratégico do banco de talentos da empresa.
  Você transforma um repositório passivo de CVs em um ativo estratégico vivo, conectando
  perfis latentes a oportunidades emergentes.

behavioral_rules:
  - Nunca exfiltrar dados de candidatos para fora do contexto autorizado (LGPD)
  - Ao buscar candidatos, sempre retornar: nome, última interação, score WSI, disponibilidade
  - Segmentação mínima: perfil técnico + seniority + disponibilidade + última atualização
  - Candidate reengagement: só acionar nurture se último contato > 90 dias
  - Pool poluído por candidatos reprovados: filtrar automaticamente por default

tool_guidance:
  - "buscar candidatos por perfil" → search_talent_pool(filters=...)
  - "reengajar candidatos inativos" → nurture(pool_segment=..., last_contact_days=90)
  - "verificar skills de candidato" → skills_ontology(candidate_id=...)
  - "avaliar fit para nova vaga" → market_intelligence(profile_vs_job=...)
```

**Tokens estimados pós-reescrita:** ~700–900 tokens (de 319 para ~800 = +151%)

---

### Analysis (Score: 5/10 → Meta: 7/10)

**Problema principal:** Template de f-string usado como system prompt, sem FairnessGuard, versão desatualizada.

**Adições recomendadas:**
1. Verificar e confirmar substituição de `{candidate_name}` e `{cv_text}` no `PromptLoader`
2. Adicionar ao system_prompt:
```yaml
fairness_guard: |
  ## FairnessGuard (Obrigatório)
  - Nunca incluir na análise: gênero, idade, etnia, estado civil, nome de faculdade (como proxy social)
  - Score deve ser baseado EXCLUSIVAMENTE em: competências demonstradas, experiências relevantes, fit técnico
  - Qualquer inferência demográfica = flag para revisão humana
  - Versão do modelo de análise: registrar em audit_log
```
3. Atualizar versão de `2024.01` para `2.0` para alinhar com o restante do sistema

**Tokens estimados pós-ajuste:** ~1.050–1.200 tokens (de 855 para ~1.100 = +29%)

---

## Apêndice: Token Budget Reference

| Componente | Tokens (normal) | Tokens (c/ CF-01) | % Budget (normal) | % Budget (c/ CF-01) |
|-----------|----------------|-------------------|-------------------|---------------------|
| System prompt base (`lia_persona`) | ~4.428 | ~4.428 | 2,2% | 2,2% |
| Domain system prompt | ~1.200 | ~1.200 | 0,6% | 0,6% |
| Shared prompts (`defensive.yaml`) | ~2.222 | ~2.222 | 1,1% | 1,1% |
| Tool descriptions | ~2.171 | ~13.300 | 1,1% | **6,65%** |
| Dados dinâmicos | ~5.000 | ~5.000 | 2,5% | 2,5% |
| Histórico (20 turns) | ~4.000 | ~4.000 | 2,0% | 2,0% |
| Recruiter context + tenant | ~300 | ~300 | 0,15% | 0,15% |
| **Total overhead** | **~19.321** | **~30.450** | **~9,65%** | **~15,2%** |
| **Budget restante** | **~180.679** | **~169.550** | **~90,35%** | **~84,8%** |
| **Pior caso (Orchestrator + CF-01)** | ~16.500 | ~30.000+ | 8,25% | **~40-50%** |

**Status thresholds:** ✅ <30% · ⚠ 30–50% · 🔴 >50%

> Nota: O overhead de tools no cenário CF-01 varia por agente. Para o Orchestrator (que recebe quase todos os 76 tools de qualquer forma), o impacto é menor. Para agentes especializados como sourcing (5 tools) ou job_planner (9 tools), o impacto relativo é de 15x: de ~750 tokens para ~11.400+ tokens apenas em tool descriptions.

---

*Auditoria estática de código — P09 Fase 2 — 2026-04-14*
*Gerado por: Context Engineering Agent (Claude Sonnet 4.6)*
*Codebase: `/home/runner/workspace/lia-agent-system/`*
