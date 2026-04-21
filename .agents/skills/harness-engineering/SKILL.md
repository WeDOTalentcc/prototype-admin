---
name: harness-engineering
description: "Aplica a disciplina de harness engineering (Agent = Model + Harness) em qualquer trabalho agentico. Use OBRIGATORIAMENTE quando: (a) o mesmo bug aparece mais de uma vez, (b) for revisar/atualizar CLAUDE.md, AGENTS.md ou .cursorrules, (c) for propor guardrail, lint customizado, tool permission ou checkpoint humano, (d) for fazer auditoria de agente IA ou consolidar findings de auditoria, (e) o usuario falar em 'guide', 'sensor', 'feedforward', 'feedback', 'Hashimoto harness', 'Bockeler', 'agent reliability', 'agente repete o mesmo erro', 'erro recorrente', 'regressao', (f) for projetar tratamento de erro de agente nao-deterministico em producao. Forca tratar erro como defeito de ambiente (nao de prompt), distinguir guide x sensor e computacional x inferencial, e persistir cada regra aprendida em CLAUDE.md / AGENTS.md / skill correspondente."
license: Proprietary
---

# Harness Engineering — Meta-Skill da Plataforma LIA

Disciplina que codifica como o ambiente em volta de um LLM (guides, sensors, guardrails, tool layer, memoria, error handling) e o verdadeiro determinante de confiabilidade de agente em producao. O modelo e commodity. O harness e o moat.

## Princípio governante

> **Agent = Model + Harness** (Mitchell Hashimoto, fev/2026).
>
> Quando um agente falha, a solucao default **NAO** e refazer o prompt nem trocar de modelo. E engenheirar o ambiente para que aquela falha especifica seja impossivel ou automaticamente corrigida na proxima vez. Toda vez que o agente comete um erro, voce engenheira uma solucao para que ele nunca mais cometa aquele erro.

Distincao critica:

- **Prompt engineering** = o que perguntar.
- **Context engineering** = o que mostrar ao modelo.
- **Harness engineering** = como o sistema inteiro opera (subconjunto de context engineering focado em alavancar os pontos de configuracao do harness).

## Quando esta skill esta ativa — três obrigações

Toda vez que esta skill estiver carregada, voce atua sob TRES obrigacoes inegociaveis:

1. **Tratar cada erro observado como defeito de harness, nao de prompt.** A pergunta default e: *que guide ou sensor teria impedido isso?* Nunca "como reescrevo o prompt?".
2. **Distinguir explicitamente guide (feedforward, antes do ato) de sensor (feedback, depois do ato).** Nunca entregar um sem considerar o outro. Guide reduz P(erro). Sensor detecta e realimenta.
3. **Distinguir explicitamente controle computacional (deterministico, CPU, rapido, barato) de controle inferencial (LLM-as-judge, nao-deterministico, caro).** Preferir computacional sempre que factivel. LLM-as-judge so quando o check determinista e impossivel.

Se voce entrega uma solucao sem nomear em qual celula da matriz 2x2 ela vive, **a entrega esta incompleta**.

## Taxonomia operacional (matriz 2x2)

Antes de qualquer intervencao, classifique o problema/solucao em uma das quatro celulas:

|                    | Guide (feedforward — antes do ato)                                      | Sensor (feedback — depois do ato)                                  |
|--------------------|--------------------------------------------------------------------------|--------------------------------------------------------------------|
| **Computacional**  | Regra em CLAUDE.md, convencao de naming, schema/contrato, template de commit, linter config, system prompt determinístico | Linter customizado, teste unitario/integracao, schema validator, pre-commit hook, CI guard, regex bias check |
| **Inferencial**    | Instrucao em linguagem natural sobre como decidir, exemplos few-shot, descricao de tool, persona/role | LLM-as-judge em PR, AI code review, semantic diff, eval com golden dataset, juiz semantico de fairness |

Cada intervencao proposta precisa **nomear a celula** e justificar por que nao desceu para uma celula mais barata (computacional > inferencial).

## Mapeamento explícito para skills LIA existentes

| Categoria do harness                         | Skill LIA que implementa                                               |
|----------------------------------------------|------------------------------------------------------------------------|
| Guide computacional (regra de codigo na fonte) | `canonical-fix` (corrigir na origem, nao no consumidor)                |
| Guide computacional (auditoria pre-merge)     | `feature-audit` (14 dimensoes obrigatorias antes de marcar concluido) |
| Guide computacional + inferencial (planning)  | `lia-planning` (4 modos + spec-driven 4 fases)                        |
| Guide inferencial (decisao de cascata)        | `lia-orchestrator` (decide quais skills convocar)                     |
| Guardrail (permission gating, separado do prompt) | `lia-compliance` PARTE 1 (Governanca WeDO) + PARTE 3 (FairnessGuard 3 camadas) + PARTE 4 (LGPD/PII) |
| Sensor computacional (testes estruturais)     | `lia-testing` (TDD, piramide 5 camadas, golden dataset)               |
| Sensor inferencial (revisao semantica)        | `code_review` (subagente architect para analise profunda)             |
| Sensor inferencial (eval offline de agente)   | `lia-testing` (LLM-as-judge sobre golden dataset)                     |
| Tool layer / state / memoria de agente        | `ai-architecture` (LangGraph: state tipado, tool isolada, fallback)   |
| Error handling de integracao externa          | `integration-patterns` (timeout, retry, circuit breaker, DLQ)         |
| Persistencia da regra aprendida               | `skill-creator` / edicao direta em `CLAUDE.md` / `AGENTS.md`          |

A skill `harness-engineering` **nao substitui** essas skills — ela e a camada conceitual que diz **quando** e **por que** invoca-las.

## Workflow default em 6 passos

Quando o usuario reportar bug recorrente, falha de agente, regressao, ou pedir para melhorar confiabilidade:

1. **Diagnostico do harness existente.** Leia `CLAUDE.md` / `AGENTS.md` / `.cursorrules` do repo (rode `scripts/scan_claude_md.py` se nao tiver mapa pronto). Se nao existir, esse ja e o primeiro achado. Verifique se a falha e coberta por algum guide ou sensor existente — se sim, ele falhou (por que?); se nao, o gap e estrutural.
2. **Root cause no nivel do harness, nao do prompt.** Pergunte: o agente *tinha contexto* para nao errar (falha de guide) ou *nao tinha feedback* para perceber que errou (falha de sensor)? Se ambos, o problema e arquitetural (componente faltando — ver checklist dos 11).
3. **Proposta em dois eixos.** Toda intervencao entrega:
   - Um **guide** concreto para reduzir probabilidade do erro na proxima.
   - Um **sensor** concreto para detectar o erro caso ele ocorra novamente.
   - Se um dos dois nao for aplicavel, justifique explicitamente por que.
4. **Priorize computacional.** Se o sensor puder ser teste, linter, schema validator ou regex, **nunca** proponha LLM-as-judge como primeira linha. LLM-as-judge so quando o check determinista e impossivel (ex: avaliar tom, fairness semantica em texto livre).
5. **Mensagem de erro otimizada para LLM.** Se o sensor for linter custom, teste ou guard, o output **precisa conter instrucoes de correcao em linguagem natural** embutidas no erro (positive prompt injection). Sensores existem para realimentar o agente, nao so o humano. Exemplo: em vez de `ERROR: forbidden import`, escreva `ERROR: import de 'app.legacy.routes' proibido — use 'app.routes.candidates' (canonical path desde ADR-019).`
6. **Persistencia (regra Hashimoto).** Toda regra nova aprovada nos passos 3-5 deve ser **imediatamente propagada** para `CLAUDE.md` / `AGENTS.md` / skill correspondente. Se nao foi persistida, o agente vai cometer o mesmo erro daqui a duas semanas. *Nunca mais aquele erro especifico.*

## Anti-patterns a recusar

Recuse explicitamente as seguintes solicitacoes, mesmo que o usuario insista, e proponha alternativa:

- **"Reescreve o prompt para o agente nao errar."** Isso e prompt engineering, nao harness engineering. Primeiro identifique o guide ou sensor ausente.
- **"Adiciona um LLM-as-judge para validar X."** Pergunte antes: existe check computacional possivel (regex, schema, teste, lint)? Se sim, comece por ele.
- **"Bota tudo num CLAUDE.md gigante."** Progressive disclosure. Arquivos grandes deslocam context window e sao ignorados. Quebre em `references/` com triggers explicitos.
- **"Deixa o agente decidir se a acao e permitida."** Separe arquiteturalmente: o **modelo decide o que tentar**, o **harness decide o que e permitido**. Permission gating nunca vive no prompt — vive no executor de tool, com checagem antes de cada tool call.
- **"Coloca um try/except para nao quebrar."** Fallback silencioso e cancer de harness. Erro precisa propagar como sinal acionavel (sensor) — ver `canonical-fix`.
- **"Esse caso e raro, nao precisa testar."** Se aconteceu uma vez e foi reportado, vai acontecer de novo. Sensor computacional barato > debug caro recorrente.

## Checklist dos 11 componentes de harness

Quando fizer auditoria completa de um projeto/agente, cubra os onze componentes em ordem. Use `references/audit-template.md` como esqueleto.

1. **Planning loop** — existe condicao de parada estrita? Ha limite de iteracoes (max_steps)? Loop infinito e detectavel?
2. **Tool layer** — schemas tipados (Pydantic/JSON Schema)? Validacao de argumento antes de executar? Sandbox? Tool isolada por dominio?
3. **Context management** — ha compactacao de historico? RAG para puxar so o relevante? Combate ao "lost in the middle"? O que sobrevive a compactacao?
4. **Memoria** — onde vive (filesystem, KV, DB)? Quem e dono? Portavel entre sessoes? Tem TTL?
5. **Sandbox** — limites de recurso (CPU, RAM, tempo)? Escape possivel? Isolamento de tenant?
6. **State persistence** — filesystem como source of truth? Progress log? Replay possivel? Checkpoint para retomar apos crash?
7. **Guides** — `CLAUDE.md` / `AGENTS.md` existem? Atualizados com aprendizados recentes? Carregam por progressive disclosure?
8. **Sensors** — linters custom? Testes estruturais? Pre-commit hooks? CI guards? LLM-as-judge offline? Eval com golden dataset?
9. **Error handling** — quatro tipos cobertos: transient (retry), LLM-recoverable (volta como ToolMessage), user-fixable (HITL), unexpected (escala)? Ver `references/failure-taxonomy.md`.
10. **Guardrails** — permission gating por ferramenta (separado do modelo)? Confirmacao explicita para operacoes de alto risco? Trust em 3 estagios (load / pre-call / user-confirm)?
11. **Serving layer** — multi-surface (API + UI + CLI)? Event bus? Observabilidade (tracing, metricas, logs estruturados)? Audit trail inspecionavel?

Produza relatorio com **gap matrix por componente** (status: ausente / parcial / completo + acao proposta).

## Mapeamento do 6-stage remediation plan da LIA para a matriz harness

O 6-stage remediation plan executado na auditoria recente da LIA mapeia 1:1 para a matriz guide x sensor / computacional x inferencial. Use este mapa quando consolidar findings ou planejar proximo stage:

| Stage              | Tipo predominante                                  | Celula da matriz                            | Skills LIA que materializam                                  |
|--------------------|----------------------------------------------------|---------------------------------------------|--------------------------------------------------------------|
| **Stage 1 — Routing & Tool Decision** (DomainActions, governance_tags, requires_hitl) | Guide + Guardrail | Guide computacional (DomainActions) + Guardrail (requires_hitl como permission gating separado do prompt) | `ai-architecture`, `canonical-fix`              |
| **Stage 2 — Few-shot & Context Injection** (examples, suggested_next, cross-refs de cluster) | Guide inferencial | Inferencial feedforward (instrucoes em linguagem natural, exemplos)                                  | `ai-architecture`, `lia-planning`               |
| **Stage 3 — Fairness & Compliance Guards** (FairnessGuard L1 regex + L2 LLM + L3 audit) | Sensor + Guardrail | Sensor computacional (L1 regex) + Sensor inferencial (L2 LLM-as-judge) + Guardrail (L3 bloqueia handler)  | `lia-compliance` PARTE 3, `lia-testing`         |
| **Stage 4 — Wizard Coverage & Resolvers** (YAML coverage, resolve_requires_confirmation) | Guide computacional | Computacional feedforward (source of truth unico, schema completo)                                  | `canonical-fix`, `feature-audit` D2/D5          |
| **Stage 5 — HITL Envelope & Tool Emission** (envelope estruturado, emit_tool_call) | Sensor computacional | Computacional feedback (sinaliza estado pro frontend, base para LLM-as-judge offline)                  | `ai-architecture`, `lia-testing`                |
| **Stage 6 — Observability Consolidation** (audit_trail, tracing, eval em producao) | Sensor inferencial | Inferencial feedback (LLM-as-judge offline + observabilidade contínua + audit trail inspecionavel pelo DPO) | `lia-compliance` PARTE 4, `code_review`, `lia-testing` |

**Leitura estrategica:** os Stages 1-4 sao majoritariamente *feedforward* (reduzem P(erro) na primeira tentativa). Stages 5-6 sao majoritariamente *feedback* (detectam e realimentam). A maturidade do harness LIA hoje esta forte em guides computacionais (Stages 1, 4) e sensores L1 (Stage 3), e tem como gap principal os **sensores inferenciais em runtime** (Stage 6 ainda em consolidacao).

## Quando carregar referencias adicionais

- Usuario pede catalogo de guides prontos por categoria → leia `references/guides-catalog.md`.
- Usuario pede catalogo de sensors prontos por categoria → leia `references/sensors-catalog.md`.
- Usuario reporta falha especifica e quer classificar → leia `references/failure-taxonomy.md`.
- Usuario pede auditoria formal de harness → leia `references/audit-template.md` e use como contrato de entrega.
- Usuario pede para mapear FIX/Stage da remediacao LIA → leia `references/lia-stage-mapping.md` (instancias canonicas G-LIA-XX / S-LIA-XX referenciadas nos catalogos).

## Scripts disponiveis

Rode antes de propor intervencoes quando o usuario fornecer o repositorio ou o log:

- **`python3 .agents/skills/harness-engineering/scripts/scan_claude_md.py [<repo_path>]`** — varre o repo e lista os arquivos de guide presentes (`CLAUDE.md`, `AGENTS.md`, `.cursorrules`, `replit.md`, skills em `.agents/skills/` e `.local/skills/`), aponta lacunas por componente do harness e imprime resumo legivel.
  - **`--check`** — modo CI/pre-commit. Compara contra `harness-baseline.json` e falha (exit 1) quando um guide do baseline desaparece OU a cobertura de algum dos 11 componentes regride. Mensagens de erro ja vem com instrucao de correcao embutida (positive prompt injection). Wired automaticamente em `.pre-commit-config.yaml` (hook `harness-scan`) e em `.github/workflows/harness-scan.yml`.
  - **`--update-baseline`** — regrava `.agents/skills/harness-engineering/harness-baseline.json` com o estado atual. Use SOMENTE quando voce intencionalmente aceita uma remocao de guide (ex: deprecou um arquivo de proposito). Commitar o baseline junto com a remocao mantem a regra "nunca o mesmo erro duas vezes" sem virar burocracia.
  - **Granularidade do baseline (intencional):** o baseline guarda o *nome* do guide (ex: `CLAUDE.md`), nao o caminho exato. O scan procura cada nome em varios diretorios candidatos (`SEARCH_ROOTS`: raiz, `lia-agent-system/`, `plataforma-lia/`, etc.) e considera o guide presente se *qualquer* uma dessas localizacoes existir. Mover um guide entre subpastas validas nao falha o gate; remove-lo de todas falha. Se voce quiser enforcement por path-exato, adicione um teste mais estrito ao lado deste (ver follow-up #742).
- **`python3 .agents/skills/harness-engineering/scripts/propose_sensor.py "<descricao do erro>"`** — recebe a descricao do erro observado e gera draft em markdown contendo: (1) classificacao na matriz 2x2, (2) draft de sensor computacional (teste/lint/schema), (3) draft de sensor inferencial alternativo (LLM-as-judge) com aviso de custo, (4) mensagem de erro otimizada para LLM e (5) item de debito tecnico para propagar.

## Formato de entrega obrigatorio

Toda resposta sob esta skill termina com um bloco de acao estruturado. Sem esse bloco, a intervencao **nao e harness engineering — e opiniao**.

```
Guide proposto (feedforward):
  Onde vive: [arquivo / system prompt / schema]
  Conteudo:  [texto, regra ou diff]
  Tipo:      [computacional | inferencial]
  Justificativa: [por que nao desceu para celula mais barata]

Sensor proposto (feedback):
  Onde vive: [arquivo / pipeline / CI step]
  Conteudo:  [codigo, regra ou prompt do juiz]
  Tipo:      [computacional | inferencial]
  Mensagem de erro otimizada para LLM: [texto com instrucao de correcao embutida]

Debito tecnico de harness registrado:
  - [item a propagar para CLAUDE.md / AGENTS.md / skill X / catalog Y]
  - [follow-up se algum dos 11 componentes ficou descoberto]
```
