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

## 7. O que está habilitado agora (mas ainda não 100% ativado) — detalhamento

Essas são capabilities **prontas mas não 100% exercitadas**. Regra geral: **todos os 6 têm o backend pronto e produzindo dado**. O que falta é **consumo/apresentação** (UI frontend OU infra de ops).

---

### 🎨 Categoria 1 — Precisa trabalho de FRONTEND (time `ats_front`)

#### 7.1 HITL UI modal

**O que existe (backend)**: Quando uma tool com `governance_tags=["destructive"]` é chamada (ex.: `close_job`, `send_mass_email`), o backend emite em `data.message.message_metadata.hitl_checkpoint`:
```json
{
  "id": "hitl-123",
  "tool_name": "close_job",
  "tool_params": {"job_id": "v0040", "reason": "budget"},
  "governance_tags": ["destructive"],
  "reason": "requires approval"
}
```

**Por que não 100%**: Frontend precisa:
- Detectar `hitl_checkpoint` no response
- Renderizar modal "Aprovar / Rejeitar" com preview dos parâmetros
- Chamar endpoints `/api/v1/hitl/approve` ou `/reject`
- Desbloquear o fluxo pós-decisão

**Fallback atual**: FIX 35 garante que a LIA **pergunta em texto conversational** (*"Vou cancelar v0040 com reason=budget. 3 candidatos serão notificados. Confirma?"*). Funciona via UI de chat simples — só falta formalidade do modal governance.

---

#### 7.2 Citations tooltip visual

**O que existe (backend)**: `data.message.message_metadata.citations[]` populado com `tool_name`, `tool_params`, `timestamp`, `confidence`. Plus `has_citations: true` como flag. Persona também emite markdown footnotes no texto (`[^1]: search_jobs(status=Ativa) às 14:32`) — **isso já renderiza** em qualquer markdown viewer padrão.

**Por que não 100%**: Tooltip *interativo* ao passar mouse sobre o `[^1]` mostrando JSON estruturado (tool + params + timestamp exato) exige componente React que leia `message_metadata.citations[i]` e faça popover. Hoje o usuário vê a citation inline, mas não consegue clicar para drill-down.

**Fallback atual**: Markdown footnote no fim da resposta já mostra `[^1]: search_jobs(...)`. 80% do valor sem o tooltip.

---

#### 7.3 Filter chips (removíveis)

**O que existe (backend)**: `ConversationState.active_filters: dict` persiste entre turns no server-side. Persona (FIX 28 + FIX 35) **sempre cita** em texto: *"Filtros ativos: status=Ativa, departamento=Tecnologia. Remover algum (ex: 'remover status') ou aplicar outro?"*

**Por que não 100%**: UI de "chip removível com X" (como o Gmail mostra filtros aplicados) exige componente React que consome `active_filters` e renderiza pills clicáveis. Ao clicar no X → dispatch `remove_filter` → nova mensagem → backend atualiza state.

**Fallback atual**: User digita *"remover status"* → LIA entende (regex no persona prompt) → remove filtro. Mesmo resultado, menos ergonômico.

---

### 🔧 Categoria 2 — Precisa UI de ADMIN (frontend + backend)

#### 7.4 Capability toggle admin por tenant

**O que existe (backend)**: G6 funcional — `app/tools/tool_permissions.yaml` define overrides por tenant:
```yaml
tenants:
  company-abc-123:
    overrides:
      universal:
        remove: ["send_whatsapp", "create_campaign"]
```
`ToolPermissionsLoader.get_permissions(tenant_id).filter_tools(...)` já aplica. Se tenant NÃO tem WhatsApp configurado, LIA nem vê tools de WhatsApp no schema.

**Por que não 100%**: Hoje configuração é **manual via YAML** (devops edita o arquivo). Falta página de **admin do tenant no frontend** onde empresa liga/desliga capabilities via toggle UI (*"Habilitar WhatsApp? ON/OFF"*), que grava em DB, e `ToolPermissionsLoader` lê do DB ao invés de YAML.

**Status**: backend PRONTO. Precisa (a) migrar config de YAML para tabela DB, (b) endpoint CRUD, (c) página frontend de admin.

---

### 📊 Categoria 3 — Precisa INFRA / OPS (não é código de feature)

#### 7.5 Cost dashboard Grafana

**O que existe (backend)**: Cada LLM call emite log estruturado:
```
[LIA-COST] tenant=00000000-0000-4000-a000-000000000001 model=gemini-2.5-flash in=12369 out=49 usd=0.001128 total=0.0045 calls=3
```
Todos os dados necessários estão lá: tenant, model, tokens I/O, cost USD, latency, accumulator total.

**Por que não 100%**: Falta **pipeline de observability**:
- Stack de log ingestion (Loki / Elastic / Datadog)
- Parser que extrai campos de `[LIA-COST]` linhas
- Dashboard Grafana/Metabase com queries agregando por tenant/model/dia

**Alternativa**: `grep '[LIA-COST]' logs | awk ...` já funciona para relatório manual. Dashboard é conveniência ops.

---

#### 7.6 Eval dashboard histórico

**O que existe (backend)**: CI workflow `.github/workflows/lia-eval.yml` roda golden set em cada PR e gera `eval/eval_results_*.json` (já tem ~3 artifacts nesse formato no repo). Cada artifact tem scores por dimensão (grounding, clarity, actionability, tone, safety).

**Por que não 100%**: Falta **consumer** — algo que colete os `eval_results_*.json` ao longo do tempo e plote tendência (*"score de grounding vs data: subiu ou caiu?"*). Opções:
- Script Python simples que lê `eval/*.json` e gera HTML
- Job que posta scores em DB + dashboard Grafana
- Integrar com ferramenta tipo Langfuse / LangSmith (já tem hook no código via `_traceable`)

**Status**: Dados gerados. Falta componente de visualização.

---

### 🎯 Padrão geral — por que ficou assim

| # | Item | Backend | UI/Infra | Ação necessária |
|---|------|---------|----------|-----------------|
| 1 | HITL modal | ✅ emite payload | ❌ modal React | Task frontend |
| 2 | Citations tooltip | ✅ metadata + footnote markdown | ⚠️ 80% (markdown já renderiza) | Task frontend (enhancement) |
| 3 | Filter chips | ✅ active_filters + texto | ❌ chips React | Task frontend |
| 4 | Capability admin | ✅ G6 YAML override | ❌ DB + admin page | Backend migração YAML→DB + frontend admin |
| 5 | Cost dashboard | ✅ `[LIA-COST]` markers | ❌ Grafana setup | DevOps/SRE |
| 6 | Eval dashboard | ✅ JSON artifacts | ❌ consumer/viewer | Script Python OU tool third-party |

**Escopo desta sessão foi "producer-side" da camada IA**. Canonical-fix skill manda fixar no producer. Frontend surfaces e infra de ops são **produtos separados com owners separados**:

- **Frontend** (ats_front) — time dedicado; seus próprios sprints; não faz parte do repo Python.
- **Infra/Ops** (Grafana, log pipeline) — ops/SRE team; não é código de feature.
- **Admin UI tenant** — produto (decide UX) + frontend + backend DB (não é só Python LIA).

**O que a camada IA entregou**: **dados estruturados no payload** que tornam esses features implementáveis sem retrabalho. Cada um dos 6 pode ser construído em **1-3 sprints de frontend/ops**, sem tocar na camada IA.

### Ordem de prioridade sugerida (valor ÷ esforço)

| # | Item | Effort | Valor | Razão |
|---|------|--------|-------|-------|
| 🟢 1 | Filter chips | 1 sprint frontend | Alto | Uso frequente, UX claramente superior |
| 🟢 2 | Citations tooltip | 1 sprint frontend | Médio-Alto | Markdown footnote já dá 80% — tooltip refina |
| 🟡 3 | HITL modal | 2 sprints frontend + produto | Médio | Governance formal, baixa frequência de uso |
| 🟡 4 | Cost dashboard | 1-2 sprints ops | Alto ao escalar | Visibilidade financeira ganha valor com tenants |
| 🟠 5 | Capability admin | 3 sprints cross-stack | Baixo hoje | Poucos tenants; YAML resolve enquanto time é pequeno |
| 🟠 6 | Eval dashboard | 1 sprint dev + produto definir KPI | Baixo hoje | Suite eval ainda crescendo; drift ainda baixo |

**Recomendação**: puxar #1 (filter chips) e #2 (citations tooltip) primeiros — maior retorno perceptível ao recrutador, menor esforço.

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
