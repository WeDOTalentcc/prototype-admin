# Taxonomia de Falhas (LangGraph + extensoes LIA)

Classificar a falha **antes** de propor intervencao garante que o sensor / guide certo seja escolhido. O LangGraph distingue 4 tipos canonicos; estendemos com 2 categorias relevantes para a LIA.

## Os 4 tipos canonicos

### 1. Transient (transiente)

**Definicao:** falha que tende a se resolver sozinha em retry (rede instavel, rate limit, timeout esporadico, 503/504).

**Exemplos LIA:**
- Pearch retorna 503 sob carga.
- GCS timeout em upload de CV grande.
- LLM provider 429 (rate limit).

**Tratamento canonico:**
- Retry com backoff exponencial + jitter.
- Circuit breaker apos N falhas seguidas.
- Limite duro de retries (nunca infinito).

**Sensor recomendado:** metrica de retry rate por integracao + alerta quando passa de threshold (skill `integration-patterns`).

**Guide recomendado:** "Toda chamada externa via cliente HTTP usa `retry(max=3, backoff=expo)`" no `CLAUDE.md`.

---

### 2. LLM-recoverable (recuperavel pelo LLM)

**Definicao:** o LLM tentou uma tool com argumentos invalidos / fez parse errado / inventou um campo. Devolvendo o erro como `ToolMessage`, o LLM consegue corrigir sozinho.

**Exemplos LIA:**
- LLM chama tool `search_candidates` com `min_experience: "muitos anos"` em vez de inteiro.
- LLM gera JSON malformado em `governance_tags`.
- LLM chama tool inexistente `get_candidate_by_email` quando o nome correto e `find_candidate_by_email`.

**Tratamento canonico:**
- Schema validator dispara, erro volta como `ToolMessage` legivel.
- Prompt de correcao embutido na mensagem de erro.
- Limite de N tentativas para evitar loop.

**Sensor recomendado:** Pydantic / JSON Schema no executor de tool (computacional).

**Guide recomendado:** descricao da tool com exemplos validos (`few-shot` na propria tool description) + lista exata de tools disponiveis no system prompt.

---

### 3. User-fixable (precisa de humano)

**Definicao:** o LLM nao tem informacao suficiente para decidir sozinho — precisa de input do usuario ou aprovacao explicita.

**Exemplos LIA:**
- Acao de alto risco: "deletar candidato" precisa confirmacao (HITL gate).
- Ambiguidade real: "qual dos 3 Joao Silva?".
- Decisao com impacto LGPD: enviar PII para terceiro precisa consentimento.

**Tratamento canonico:**
- HITL envelope estruturado retorna ao frontend.
- Estado pausa, aguarda input do usuario.
- Audit trail registra "interrupted_for_user_input".

**Sensor recomendado:** validador de envelope HITL + teste estrutural que garante que toda tool com `requires_hitl=True` retorna envelope correto.

**Guide recomendado:** lista canonica de tools com `requires_hitl=True` no policy file (computacional, fora do prompt — guardrail).

---

### 4. Unexpected (inesperado, escala para debug)

**Definicao:** falha que nao se enquadra nas tres anteriores. Bug genuino do sistema, nao do agente. Precisa de humano com contexto tecnico.

**Exemplos LIA:**
- DB constraint violation que nao deveria acontecer.
- Race condition em fila.
- Erro de import circular descoberto em runtime.

**Tratamento canonico:**
- Captura no observabilidade (Sentry / structured log).
- Alerta para canal de engenharia.
- Resposta segura ao usuario ("ocorreu um erro, time foi notificado").
- **Nao mascarar com try/except: pass** (anti-pattern grave).

**Sensor recomendado:** Sentry + log estruturado + apos resolver, *adicionar teste de regressao* para que esse caso especifico vire categoria 1, 2 ou 3.

**Guide recomendado:** runbook em `docs/runbooks/` mapeando classes de unexpected conhecidas para procedimento.

---

## Categorias estendidas LIA

### 5. Compliance / Fairness violation

**Definicao:** o agente produziu saida que viola regra de DEI, LGPD ou governanca WeDO.

**Exemplos:** linguagem viesada em descricao de vaga, vazamento de PII, score de candidato sem audit trail.

**Tratamento:** FairnessGuard 3 camadas (skill `lia-compliance` PARTE 3) bloqueia handler antes de retornar.

**Sensor:** L1 regex (computacional) + L2 LLM-as-judge (inferencial) + L3 audit trail (computacional).

### 6. Tenant isolation breach

**Definicao:** dado de uma empresa apareceu em contexto de outra.

**Tratamento:** falha alta, log critico, bloqueio imediato.

**Sensor:** teste estrutural que varre toda rota e confirma decorator `@require_tenant` (computacional, em CI).

**Guide:** template de novo endpoint ja inclui o decorator.

---

## Tabela de decisao rapida

| Falha observada                        | Tipo  | Primeiro sensor       | Primeiro guide                 |
|----------------------------------------|-------|-----------------------|--------------------------------|
| 503 esporadico de API externa          | 1     | retry metric          | "use cliente com retry"        |
| LLM chamou tool com arg invalido       | 2     | Pydantic validator    | exemplo na tool description    |
| LLM precisou perguntar ao usuario      | 3     | HITL envelope         | policy file de tools sensiveis |
| DB constraint nunca antes vista        | 4     | Sentry + teste novo   | runbook + ADR                  |
| Saida com termo viesado                | 5     | FairnessGuard L1      | guideline de tom no prompt     |
| Dado de outra empresa apareceu         | 6     | structural test       | template + decorator default   |
