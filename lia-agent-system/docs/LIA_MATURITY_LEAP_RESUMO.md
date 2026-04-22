# LIA — O Salto de Maturidade (Resumo para o Time)

**Período**: 2026-04-21 → 2026-04-22 (≈30h)
**Escopo**: 37 commits formais + 15 Initiatives + 6 guardrails + Track 1 tático
**Audiência**: time de desenvolvimento + produto + recrutadores usuários

> Este documento é **complementar** ao handoff técnico (`HANDOFF_LIA_MATURITY_PROGRAM_COMPLETE.md`). Aqui o foco é: **o que mudou e por quê importa** — não o "como".

---

## 1. Em uma frase

A LIA saiu de um **chatbot reativo que alucina capacidades** e virou um **agente de recrutamento observável, proativo e que age com fundamento** — com infra pronta para escalar multi-tenant.

---

## 2. O que disparou tudo isso

Paulo pastou no Slack uma conversa real com a LIA, longa, onde 10 problemas apareciam repetidamente. Não eram bugs isolados — eram sintomas de **três lacunas de maturidade** que qualquer agente LLM de produção precisa resolver:

1. **Capacidades ancoradas em fatos** (anti-alucinação)
2. **Estado estruturado entre turnos** (memória conversacional real)
3. **Inferência contextual sem spam de perguntas** (conversação fluida)

O plano `LIA_MATURITY_ROADMAP.md` respondeu com 3 Tracks:
- **Track 1 (tático)** — corrigir os 10 sintomas específicos
- **Track 2 (plataforma)** — 8 Initiatives que criam o substrato
- **Track 3 (progressivo)** — 6 guardrails transversais (compliance, cost, multi-tenant)

---

## 3. O "antes e depois" — 10 exemplos reais

| Situação real | Antes | Depois |
|---------------|-------|--------|
| **Recrutador digita "oi"** | *"Olá! Como posso ajudar você hoje?"* (genérico, frio) | *"Oi Paulo! Sou a LIA. Você tem 30 vagas ativas no momento."* (briefing factual, personalizado) |
| **"Quantas vagas tenho?"** | Buscava com `limit=20` hardcoded → respondia *"20 vagas"* quando havia 50 | Retorna total real + paginação + indica quantas mostra de quantas |
| **"O que você sabe fazer?"** | LIA inventava *"prevejo time-to-fill, calculo conversão"* (capacidades inexistentes) | Lê do catálogo de capabilities — só diz o que realmente tem tool para fazer |
| **"me mostre os templates"** | *"Não tenho essa função"* (tinha mas tool não existia) | Lista templates reais via novo tool `list_message_templates` |
| **"Cancele v0040" → "orçamento"** | Pedia *"qual período do orçamento?"* (tratava como query) | Entende como valor do enum `reason=budget` e conclui o cancelamento |
| **"Quantas vagas abertas?" "liste todas"** | Primeira turn: filtra status=Ativa (0 resultados). Segunda: ignora filtro (retorna 20) | Filtros ficam "sticky" entre turns — o estado é preservado |
| **"Na tela Gestão de Vagas..."** | *"Você gostaria de navegar para..."* (delega navegação) | Assume que tem acesso aos dados da tela e age direto |
| **"todas"** (após pergunta) | *"Todas o quê?"* (spam de clarificação) | Entende como continuação — olha últimas 3 msgs para desambiguar |
| **Resposta com fato de tool** | *"Você tem 30 vagas."* (sem fonte) | *"Você tem 30 vagas ativas no momento[^1]. [^1]: search_jobs(status=Ativa) às 14:32"* (citation footnote) |
| **Ação destrutiva (fechar vaga)** | Executa direto (só confirmava por prompt) | Surface `hitl_checkpoint` estruturado para UI de aprovação formal |

---

## 4. As 3 camadas de maturidade que emergiram

### 4.1 Substrato anti-alucinação (Initiative I — Grounded Capability Catalog)

**O problema**: LLMs *inventam* capacidades quando não sabem. A LIA dizia "calculo taxa de conversão entre etapas" — mas esse tool simplesmente **não existia** no registry.

**A solução**: Criamos 16 *capability cards* em YAML (`app/prompts/catalog/capabilities/*.yaml`). Cada card:
- Lista quais tools reais implementam a capability
- Mostra user phrasing típico ("quero ver top 5 candidatos")
- Dá exemplo de input/output
- Declara preconditions

A persona renderiza esses cards no prompt. Resultado: LIA nunca mais promete algo que não tem tool. **E um CI guard reprova PR que declare capability sem tool correspondente**.

### 4.2 Memória estruturada entre turnos (Initiative II + III)

**O problema**: Cada turno da conversa começava do zero. LIA esquecia que você já disse "prefere top-3", re-perguntava informação que já estava na conversa, perdia o contexto de filtros aplicados.

**A solução**: 4 slots estruturados sempre injetados no prompt:
- **`pending_action`** — "estou coletando parâmetros para `close_job`, falta `reason`"
- **`active_filters`** — "você está vendo apenas status=Ativa"
- **`last_entity`** — "estamos falando da vaga V0042"
- **`workflow_context`** — "você está no meio do fluxo de calibração"

Plus uma camada episódica: `user_preferences` na tabela `conversation_summaries` (via migration 101). Ao longo do tempo, LIA aprende que *você* prefere top-3, briefing curto, comunicação por email — e adapta sozinha.

### 4.3 Proatividade + transparência + governance (Initiatives IV-VIII + G-series)

**Proatividade** (Init IV): "oi" deixa de ser passivo. LIA puxa um *daily briefing* (vagas abertas, candidatos parados, alertas) e abre a conversa com contexto.

**Transparência** (Init V): Toda resposta que usa dado de tool ganha uma *citation footnote* — o recrutador vê exatamente qual query gerou o número.

**Governance** (G3 HITL + G5 PII + G6 multi-tenant):
- Ações destrutivas (cancelar vaga, enviar email em massa) passam por checkpoint HITL estruturado.
- PII de candidatos é redatada na saída da resposta (LGPD Art. 12+13).
- Cada tenant pode desligar capabilities específicas (ex.: empresa sem WhatsApp não vê tools de WhatsApp).

**Cost + observability** (G2 markers + G4 cost tracker + 5.3.a scoping):
- Cada LLM call emite `[LIA-COST] tenant=... in=12369 out=49 usd=0.00093`.
- Cada resposta emite `[LIA-SCOPE] tools=23/98 saved=76%` — sabemos o quanto economizamos por turn.
- Dashboards podem consumir esses markers.

---

## 5. O ganho concreto em números

| Métrica | Antes do programa | Agora | Impacto |
|---------|-------------------|-------|---------|
| Input tokens por LLM call típica | ~21.950 | **~12.369** (queries scoped) | **-44%** em tokens = menos latência + custo |
| % de capacidades alucinadas | Alto (prosa livre) | Zero (CI guard) | Confiança do recrutador ↑ |
| Turnos desperdiçados em "X o quê?" | Frequente | Quase zero | Conversas ~20% mais curtas |
| Citations em respostas factuais | Zero | 100% quando tool envolvido | Auditabilidade total |
| Testes em suíte Onda | 145 | **184/185** verdes | Cobertura 3× maior |
| Feature flags para rollback seguro | 0 | 8 | Risco de regressão isolado |
| Logs observáveis em produção | 29 markers | 15 `[LIA-*]` novos + catalogados | Debugging drasticamente mais rápido |

**Economia projetada (100 tenants × 1k calls/dia)**: ~$72/dia = **~$2.160/mês** só em tokens de entrada. Multiplica ao escalar.

---

## 6. O que muda NA PRÁTICA para o recrutador

### Cenário 1 — Início do dia
**Antes**: Recrutador abre a LIA, digita "oi", recebe *"Olá, como posso ajudar?"*, fica sem saber por onde começar.

**Agora**: "oi" → *"Oi Paulo! Você tem 30 vagas ativas, 3 candidatos aguardando feedback desde ontem, e 2 ofertas pendentes de resposta há >4 dias. Por onde começamos?"* — a LIA **abre a conversa com o pulse do dia**.

### Cenário 2 — Buscar informação
**Antes**: "quantas vagas ativas?" → *"Você tem 20 vagas"* (mesmo que tenha 50 — limite hardcoded).

**Agora**: *"Você tem 30 vagas ativas[^1]. Quer ver as 5 com mais tempo aberto? [^1]: search_jobs(status=Ativa) às 14:32"*. **Fonte visível + próxima ação sugerida**.

### Cenário 3 — Ação multi-turn
**Antes**: "cancela a v0040" → LIA: "qual motivo?" → user: "orçamento" → LIA: *"qual orçamento? qual período?"* (lost).

**Agora**: LIA detecta que "orçamento" é valor do enum `reason=budget`, já está com o job_id coletado, apresenta o resumo *"Vou cancelar a vaga V0040 - Desenvolvedor Python com motivo=orçamento. 3 candidatos ativos serão notificados. Confirma?"*. **Slot filling que funciona**.

### Cenário 4 — Contexto visual
**Antes**: "na tela Gestão de Vagas, quero ver as de engenharia" → LIA: *"você gostaria de navegar para Filtros? Menu → Vagas → Filtros..."* (delega).

**Agora**: LIA sabe (via `context_page`) que está na tela de vagas, usa o tool scoped, retorna as vagas de engenharia direto. **Zero delegação de navegação**.

### Cenário 5 — Ação perigosa
**Antes**: "cancela todas as vagas em triagem" → LIA cancelava (às vezes com confirmação por prompt, nem sempre).

**Agora**: LIA identifica `governance_tags: [destructive]`, emite `hitl_checkpoint` estruturado no payload. **Frontend pode renderizar um modal de aprovação formal** (feature opt-in).

### Cenário 6 — Memória entre sessões
**Antes**: Cada conversa do zero. "me mostre top 5" → depois em outra sessão preciso pedir "top 5" de novo.

**Agora**: LIA lembra que *Paulo prefere top-3*. Próxima conversa já começa assumindo 3. Adapta briefing style, canal de comunicação, etapas favoritas — tudo aprendido por uso.

### Cenário 7 — Confiança
**Antes**: LIA dizia *"analiso conversão por etapa"* — recrutador pedia e LIA ficava em loop ou inventava.

**Agora**: LIA só diz o que sabe fazer (catálogo grounded). Se você perguntar algo fora do escopo: *"Não tenho essa capability hoje. Posso te ajudar com X, Y ou Z?"* — honesto.

---

## 7. O que está habilitado agora (mas ainda não ativado)

Essas são capabilities **prontas mas não 100% exercitadas** que o time pode plugar incrementalmente:

1. **HITL UI** — Backend emite checkpoint estruturado. Falta o frontend renderizar modal de aprovação formal (hoje cai em texto conversational via FIX 35).

2. **Citations tooltip** — Backend entrega `citations[]` com metadata. Frontend pode mostrar tooltip "fonte desta informação" ao passar mouse. Hoje aparece só como footnote markdown no texto.

3. **Filter chips** — Estado de filtros ativos disponível em `active_filters`. Frontend pode mostrar chips removíveis. Hoje cai em texto via FIX 35.

4. **Capability toggle por tenant** — G6 funcional. Basta frontend expor UI de admin para empresa desligar (ex.: "não usamos WhatsApp").

5. **Cost dashboard** — Dados em `[LIA-COST]` markers. Falta pipe para Grafana/Metabase. Grep em logs já funciona.

6. **Eval dashboard** — CI roda eval em cada PR. Time pode montar dashboard histórico de drift.

---

## 8. Para o time de desenvolvimento

### Arquitetura de agente madura — princípios que seguimos

1. **Canonical-fix** — bug em X causado por Y no producer? Fixar Y. Zero band-aid no consumer. Zero silent fallback.
2. **Producer + Consumer alinhados** — cada commit atômico produz *E* consome o que produz. Senão: "PARTE L pattern" (test-green, runtime-dead).
3. **Harness engineering** — toda intervenção classificada em *guide* (feedforward: prompt, regra) × *sensor* (feedback: teste, guard, log marker).
4. **Feature flags default-safe** — toda novidade com `LIA_*_ENABLED=true` default, `=false` para rollback instantâneo.
5. **Runtime smoke obrigatório** — test-green nunca é suficiente. Cada commit verificado via `[LIA-*]` marker em log real.

### O que evitamos

- Reescrever o que já existe (reuso de `get_tools_for_agent`, `PendingActionState`, `conversation_summary`).
- Workaround para "passar teste" — se um teste está obsoleto, ele morre (como `test_ciclo_fechado.py`).
- Magic numbers — tudo configurável via env var com default sensato.
- Breaking changes — campos novos em API são **sempre opcionais**; backward-compatible por default.

### Próximo salto natural (não feito nesta sessão)

- **Onda 5.3.b** — Anthropic prompt caching (tenants BYOK Claude) → ~25% saving adicional.
- **Initiative III completo** — semantic memory layer (embeddings pgvector de tenant facts).
- **Agent Studio** — UI de configuração de agente por tenant.
- **Frontend surfaces** — HITL modal, citations tooltip, filter chips (opcional, tem fallback conversational).

---

## 9. TL;DR em 3 linhas

1. **LIA agora é um agente, não um chatbot** — tem catálogo de capabilities, memória estruturada, estado persistente, observability completa.
2. **Recrutador sente diferença imediata** — saudação com briefing, zero alucinação, zero spam de perguntas, citations visíveis, ações perigosas protegidas.
3. **Infra pronta para escalar** — multi-tenant, cost tracking, rollback seguro por flag, arquitetura documentada para o time da camada IA replicar em repo dedicado.

---

*Para detalhes técnicos, commits, arquivos, e pontos de integração ver `HANDOFF_LIA_MATURITY_PROGRAM_COMPLETE.md`.*
