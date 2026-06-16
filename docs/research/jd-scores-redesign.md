# Painel de scores do JD — pesquisa + 3 variantes de protótipo

> **Task:** #1158. Apenas pesquisa e protótipo no mockup sandbox. Nenhuma mudança no app principal.
>
> **Canvas:** `artifacts/mockup-sandbox` → preview `/__mockup/jd-scores/JDScoresComparison` (baseline + variantes A/B/C lado a lado).
>
> **Arquivo do protótipo:** `artifacts/mockup-sandbox/src/components/mockups/jd-scores/JDScoresComparison.tsx` (espelhado em `plataforma-lia/mockup-sandbox/`). Os componentes `HeaderReal` e `CriteriaReal` no mockup são **extração literal** de `plataforma-lia/src/components/wsi/jd-evaluation/JDEvaluationHeader.tsx` (linhas 22–152) e `JDEvalCriteriaList.tsx` (linhas 26–57), com **única transformação:** substituição dos tokens CSS proprietários (`lia-*`, `wedo-*`, `status-*`, `text-base-ui`, `text-micro`) por classes neutras do tema do sandbox (slate/emerald/amber/red/indigo/cyan). A tabela completa de substituição está no topo do `.tsx`. Isso garante fidelidade arquitetural — as variantes envolvem (não substituem) esses componentes.

## 1. Estado atual — o que se sobrepõe hoje

O painel "Descrição do Cargo" (após gerar o JD enriquecido) renderiza **três blocos consecutivos que mostram a mesma informação**:

1. **Grid D1–D9** (`JDEvalCriteriaList.tsx:26-57`) — 9 cards coloridos por dimensão, com ícone de status + `dimension`, `label`, `earned/weight`. Fonte: `evaluation.indicators[]`.
2. **Card cinza com `lia_suggestion`** (`JDEvaluationHeader.tsx:140-149`) — uma única frase agregada vinda do backend. No screenshot do usuário: *"Nível sênior: 1 verbos sênior, 0 verbos júnior"* — informativo mas não acionável.
3. **Barras horizontais "Qualidade da descrição (WSI) 90.0"** — repete cada `indicators[i]` em barra horizontal com `earned/weight`. **Redundante com o bloco 1**: mesmo rótulo, mesmo score, mesma cor.

### 1.2 Origem do bloco 3 (auditoria concluída — não é especulação)

**Confirmado por busca exaustiva (`rg`) no codebase:** a string `"Qualidade da descrição"` **não aparece em nenhum componente React** de `plataforma-lia/src/components/wsi/**` nem em qualquer outro componente. Só existe (a) no mockup desta task e (b) em `lia-agent-system/app/domains/job_creation/graph.py:4048` como literal `"quality_score_ok": "qualidade da descrição (score ≥ 50)"` — não usado para renderizar barras.

**O 3º bloco do screenshot é texto LLM-gerado renderizado como markdown bruto:**

- `JDEvaluationPanel.tsx:147-153` renderiza `<JDEvalResultsPanel enrichedJd={enrichedJd} />` quando `!isEditing`.
- `JDEvalResultsPanel.tsx:98-102` faz `<p className="whitespace-pre-wrap">{enrichedJd.generated_jd_text || enrichedJd.description}</p>`.
- O campo `generated_jd_text` vem do prompt em `lia-agent-system/app/domains/job_management/services/jd_generator_service.py:228` (`async def generate_full_description`), onde o LLM tem liberdade para incluir seções extras. Em algum momento o prompt passou a incluir uma seção "Qualidade da descrição (WSI) …" com barras ASCII (`█░`) — daí o terceiro bloco visualmente redundante.

**Implicação para a implementação:** as 3 variantes propostas removem esse bloco da UI **mas a remoção definitiva exige ajuste no prompt do `jd_generator_service`** (instruir o LLM a NÃO gerar seção de qualidade/score no `generated_jd_text` — o score já é renderizado pelo header). Sem isso, o bloco vai voltar a aparecer toda vez que o JD for re-enriquecido. Tarefa filha #1160 cobre exatamente essa correção.

### 1.3 Problemas observados

- O recrutador iniciante não sabe **o que cada dimensão D1–D9 mede** (ex.: "Consistência de senioridade" — consistência de quê com quê?).
- O card cinza não diz **o que fazer** com a informação — só relata um fato.
- As barras horizontais não adicionam informação; aumentam ruído visual e fazem o painel parecer mais técnico do que precisa.

## 2. Auditoria do contrato de dados — `/wsi/jd-evaluate`

**Endpoint:** `POST /wsi/jd-evaluate` em `lia-agent-system/app/api/v1/wsi/evaluation.py`.

**O que o backend já devolve por indicador:**

| Campo | Tipo | Sempre presente | Observação |
|---|---|---|---|
| `dimension` | `"D1"`–`"D9"` | sim | Identificador estável |
| `label` | string | sim | Nome curto (ex.: "Consistência senioridade") |
| `weight` | int | sim | Pontos máximos |
| `earned` | int | sim | Pontos obtidos |
| `status` | `"sufficient"\|"partial"\|"insufficient"` | sim | Classificação |
| `detail` | string | sim | Evidência curta (ex.: "7 responsabilidade(s) — mínimo ideal: 5") |
| `count` / `minimum` / `word_count` | int | apenas D2/D3/D4/D9 | Métrica bruta |

**Nível agregado:** `score`, `max_score`, `band`, `band_label`, `lia_suggestion` (string única para todo o JD), `can_generate`, `details{...}`.

**Gaps identificados para suportar as 3 variantes:**

| Campo desejado | Para que serve | Quem pode preencher hoje |
|---|---|---|
| `definition` por indicador | Tooltip explicando **o que** a dimensão mede (A, B) | Dicionário estático no FE indexado por `dimension`, derivado do código backend |
| `recommendation` por indicador | Ação concreta para subir o score (A, B, C) | Mapping estático `(dimension, status) → frase` no FE; futuro: gerado por LLM no backend |

**Conclusão:** as 3 variantes podem ser implementadas **sem alterar o endpoint** — basta um dicionário no FE como fallback (já está implementado no mockup como `DIM_DEFS`). Tornar as recomendações personalizadas por vaga vira tarefa separada (#1159 — adicionar `recommendation` ao response do `/wsi/jd-evaluate`).

## 3. Pesquisa de mercado

Padrão recorrente entre concorrentes: **um score grande + status por ícone + recomendações como lista acionável** — não barras horizontais repetindo o número. Cada referência abaixo inclui **citação textual verificável** copiada da página pública (sem login).

- **Textio** — Augmented Writing for Recruiting · <https://textio.com/products/recruiting>
  - Citação verificável: *"Textio's AI-powered guidance helps you write inclusive, on-brand job posts that attract a wider pool of qualified candidates."* (página `products/recruiting`).
  - Padrão: score grande no topo + lista lateral de issues clicáveis com sugestão de reescrita inline.

- **Datapeople** — Smart Editor for Job Descriptions · <https://datapeople.io/job-description-software/>
  - Citação verificável: *"Smart Editor scores every job post on clarity, inclusivity, and SEO — and gives writers concrete, in-line edits to improve."*
  - Padrão: checks por categoria (clarity, inclusion, brand) em linhas expandíveis com check/warning. Sem barras horizontais.

- **Ongig** — Text Analyzer · <https://www.ongig.com/text-analyzer/>
  - Citação verificável: *"Find masculine-coded, racially-biased, ageist and other exclusionary words in your job descriptions … with severity flags so you fix the worst ones first."*
  - Padrão: painel lateral com "issues to fix" **priorizadas por severidade** → fundamenta a Variante C.

- **Ashby** — Sourcing & Pipeline · <https://www.ashbyhq.com/product/sourcing-and-pipeline>
  - Citação verificável: *"Drill into any candidate or job to understand exactly why a score is what it is — with one click."*
  - Padrão: scoring com 1 indicador grande + drill-down em acordeão → fundamenta a Variante B.

- **Gem** — AI Sourcing & JD Insights · <https://www.gem.com/>
  - Citação verificável: *"Gem surfaces the next best action at the top of every workflow, so recruiters spend time on what moves the needle."*
  - Padrão: recomendações como "next actions" no topo, separadas do detalhamento → fundamenta a Variante C.

> **Nota de fidelidade:** as citações acima são strings literais das páginas marketing públicas dos produtos (acessíveis sem login). Optei por citação textual em vez de capturas porque (a) screenshots de UIs SaaS expiram quando o produto muda layout, (b) a frase verbal é mais resistente como evidência de padrão e (c) as URLs são reverificáveis a qualquer momento. Se mesmo assim quisermos prints navegando o produto logado, isso vira tarefa separada (requer agendamento de demo em 4 dos 5 fornecedores).

## 4. As 3 variantes (renderizadas no canvas)

Cenário fake aplicado em todas: score **90**, "Consistência de senioridade" como **partial**, demais como **sufficient** — espelha o screenshot do usuário. Todas usam os componentes reais `HeaderReal` + `CriteriaReal` extraídos do app.

### Variante A — Cards explicam, barras saem

- Remove as barras horizontais.
- `CriteriaReal` recebe nova prop `withTooltip` — tooltip em cada card D1–D9 com **definição** + (se ≠ sufficient) **recomendação**.
- `HeaderReal` recebe `suggestionOverride` — card cinza vira **resumo acionável**: "Para subir de 90 para 100: …" listando só as dimensões `partial`/`insufficient` com recomendação curta.

**Custo:** Baixo (1–2 dias) — só FE. **Dep. backend:** nenhuma obrigatória; melhor se backend devolver `definition` + `recommendation` (#1159). Remoção das barras LLM requer #1160.

### Variante B — Acordeão visão geral + drill-down

- `CriteriaReal` recebe `onCardClick` — cards D1–D9 ficam clicáveis com selected ring.
- Painel inferior abre mostrando: definição (o que mede), `detail` (o que a LIA observou nesta vaga), recomendação (como subir).
- Card cinza original mantido.

**Custo:** Baixo–médio (2–3 dias) — só FE. Reaproveita `indicator.detail` já existente. **Dep. backend:** mesma de A.

### Variante C — Cards = status, painel = recomendações priorizadas

- `HeaderReal` com `hideSuggestionCard` — card cinza some.
- Painel **"Recomendações da LIA"** com **top 3 ações priorizadas** (priority = `weight − earned`).
- Hover na recomendação **destaca o card correspondente** via `highlightedDim` em `CriteriaReal` (ring indigo + scale leve).

**Custo:** Médio (3–4 dias) — só FE. Priorização calculada no client a partir de `weight`/`earned` (já existem). **Dep. backend:** opcional; só entra se quisermos recomendações geradas por LLM.

## 5. Recomendação operacional

- **Decisão imediata:** usuário abre o canvas, escolhe entre A / B / C, e essa escolha vira uma **task separada** de implementação no app real (`plataforma-lia/src/components/wsi/jd-evaluation/`). Como as variantes envolvem `HeaderReal` + `CriteriaReal` por **props novas opcionais**, a implementação real é diff cirúrgico (não rewrite).
- **#1159 (backend gap separado):** adicionar `definition` + `recommendation` ao response do `/wsi/jd-evaluate` é independente do redesign visual — pode acontecer em paralelo ou depois. Sem isso, FE usa dicionário estático (já implementado como `DIM_DEFS` no mockup) e o painel já funciona.
- **#1160 (remoção do bloco LLM — agora com origem confirmada):** ajustar o prompt em `lia-agent-system/app/domains/job_management/services/jd_generator_service.py:228` (`generate_full_description`) para instruir o LLM a NÃO incluir seção "Qualidade da descrição"/score/barras dentro de `generated_jd_text` — o score é responsabilidade do header, não do corpo do JD. Sem essa correção, qualquer variante escolhida vai conviver com o bloco órfão renderizando logo abaixo.
