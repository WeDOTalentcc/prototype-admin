# Rich Response Protocol (RRP) — guia do renderer de blocos do chat

As respostas da LIA no chat podem vir como **lista ordenada de blocos tipados**
(`message.response_blocks`), além do texto markdown (`message.content`). Este
diretório (`unified-chat/`) renderiza esses blocos via `ResponseBlockRenderer`.

> Chat ativo = `UnifiedChat` → `UnifiedMessageList` → `ResponseBlockRenderer`.
> O path legado (`ChatMessageList`/`LiaChatPanel`/cards em `chat/`) foi removido
> (dead code, 2026-06-05). Não reviva: use blocos RRP.

## Catálogo de blocos (`kind`)

| kind | papel | layout | o que mostra |
|---|---|---|---|
| `prose` | answer | inline | markdown rico (GFM completo via `render-markdown`) |
| `comparison_table` | support | wide | tabela de candidatos/vagas; score = mini-barra; transpõe em sidebar |
| `score_explainer` | support | inline | "por quê" do score (colapsável): fatores em barra + confiança. O **moat**. |
| `evidence_stack` | evidence | inline | fontes/proveniência colapsáveis |
| `funnel` | support | wide | etapas do pipeline: barra + count + retenção % |
| `candidate_card` | answer | inline | perfil inline: avatar, score, recomendação, skills |

**Envelope (todo bloco):** `block_id`, `role` (answer/support/evidence/action),
`layout` (inline/wide/panel), `state` (loading/partial/ready/error).

## Comportamentos do renderer

- **AD4 answer-first:** blocos ordenados por `role` (answer < support < evidence
  < action); sort estável preserva a ordem do produtor dentro do mesmo papel.
- **AD4 block budget:** mostra até 6 (sidebar/floating) / 12 (fullscreen); o
  excedente fica atrás de "Ver mais (N)". Limite generoso de propósito para não
  esconder o moat (`rank` emite ~7 blocos colapsados). Ajuste em `ResponseBlockRenderer`.
- **AD5 estados:** `state="loading"` → skeleton; `state="error"` → fallback que
  nunca quebra; kind desconhecido → fallback (nunca `throw`); error boundary por
  bloco (try/catch no map).
- **AD7 state-aware:** `comparison_table` transpõe em sidebar/floating; blocos
  `wide`/`panel` ganham CTA "Expandir em tela cheia" (evento `lia:request-chat-mode`).
- **Motion:** stagger sutil por índice, `motion-reduce` respeitado.
- **Fairness/LGPD:** score baixo = tom neutro/mudo (nunca vermelho).

## Como adicionar um bloco novo (scaffold)

1. **Backend contrato** — `lia-agent-system/app/shared/rrp_blocks.py`: nova classe
   herdando `_BlockBase` (`ConfigDict(extra="forbid")`), adicionar à union
   `ResponseBlock` **e** ao `_KIND_MAP`. Nunca `company_id` no bloco (vem do JWT).
2. **Builder (produtor único)** — `app/shared/rrp_ranking_builder.py`: função
   `build_<x>_block(...)` que retorna `[blk.model_dump(mode="json")]`.
3. **Emissão** — a tool relevante seta `data["response_blocks"] = build_<x>_block(...)`.
   O `agentic_loop` captura `data.response_blocks` genericamente (AD3).
   Proveniência honesta: número/fonte só com dado real; senão `unverified=True`.
4. **TS espelho** — `plataforma-lia/src/types/rrp-blocks.ts`: interface +
   adicionar à union `ResponseBlock`.
5. **View + case** — `ResponseBlockRenderer.tsx`: componente `<XView>` (tokens
   `lia-*`/`wedo-cyan`, sem nested-card/side-stripe/gradient-text) + `case "x"` no
   switch exaustivo.
6. **i18n** — chaves em `messages/pt-BR.json` **e** `messages/en.json` (namespace
   `rrp`) antes do JSX. Rodar `npm run lint:i18n:blocking`.
7. **Sensores** — contract test backend (`tests/contract/test_rrp_*`) + render test
   (`__tests__/ResponseBlockRenderer.test.tsx`, table-driven).

## agent_steps (raciocínio) — decisão de arquitetura

O pilar "progresso do agente / think-aloud" **NÃO é um `response_block`**. Ele é
entregue por uma superfície dedicada, melhor para streaming ao vivo:

- **Ao vivo:** `AgentActivityTimeline` — escuta `lia:agent-activity` (window event)
  e, no fallback, deriva itens de `thinkingSteps` (localizado + progressivo).
- **Persistente:** `AgentActivitySummary` — pílula "N passos" colapsável a partir
  do buffer `agent_activity` da mensagem.

Adicionar um `agent_steps` como `response_block` **duplicaria** essas superfícies.
Não fazer. Se precisar evoluir o raciocínio, mexer em `AgentActivityTimeline`/
`activity-labels.ts`, não no catálogo RRP.

## Sensores ativos
- `ResponseBlockRenderer.test.tsx` (render, state-aware, AD4/AD5, fairness, i18n).
- `tests/contract/test_rrp_*` (backend: contrato, proveniência, builders).
- `npm run lint:i18n:blocking` (chaves), eslint (`--max-warnings=0`), `tsc --noEmit`.
