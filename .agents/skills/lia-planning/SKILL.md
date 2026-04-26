---
name: lia-planning
description: "Metodologia de planning unificada para Plataforma LIA — combina GSD workflow (4 modos), spec-driven development (4 fases) e brainstorming estruturado. Use ao iniciar qualquer trabalho significativo, planejar sprints, diagnosticar bugs, especificar features ou quando o usuario pedir para seguir a metodologia. Triggers: gsd, metodologia, workflow, novo sprint, planejar feature, bug fix, especificar, brainstorming, como vamos trabalhar."
---

# LIA Planning — Metodologia Unificada

Combina 3 abordagens: GSD workflow (modos operacionais), spec-driven development (fases de profundidade) e brainstorming estruturado (exploracao de ideias).

## Quando ativar

- Ao iniciar trabalho significativo (feature nova, refactor amplo, sprint, debug com causa nao obvia)
- Quando o usuario disser "planeja", "vamos seguir a metodologia", "como vamos trabalhar?", "GSD", "novo sprint" ou "spec disso"
- Ao diagnosticar bug com causa nao obvia -> Modo Bug Fix (diagnosticar > isolar > corrigir > verificar)
- Ao especificar feature nova -> Modo Feature (spec > impacto > implementar > testar > auditar)
- Ao planejar refactor com metricas -> Modo Refactor (medir > planejar > executar > medir de novo)
- Ao decompor sprint em tasks atomicas -> Modo Sprint (inventariar > decompor > priorizar > delegar > integrar)
- Quando ha ambiguidade ou multiplas abordagens possiveis -> Brainstorming antes do Modo
- Antes de delegar conjunto de tarefas para subagents (decomposicao formal)

## Quando NAO ativar

- Typo trivial ou ajuste micro (1 prop, 1 string literal)
- Pergunta direta do usuario que nao envolve implementacao
- Usuario ja forneceu plano completo e so pediu execucao linear
- Continuacao imediata de tarefa em andamento sem mudanca de escopo

## Principio Central: Auto-Sizing

A profundidade do processo adapta-se ao tamanho do trabalho:

| Escopo | Exemplo | Workflow |
|--------|---------|----------|
| **Micro** | Typo, 1 prop faltando | Fix direto, sem cerimonia |
| **Small** | Bug isolado, <=3 arquivos | Bug Fix Mode (diagnosticar > isolar > corrigir > verificar) |
| **Medium** | Feature clara, <10 tasks | Feature Mode (spec > impacto > implementar > testar > auditar) |
| **Large** | Refactor multi-arquivo | Refactor Mode (medir > planejar > executar > medir de novo) |
| **Sprint** | Conjunto coordenado | Sprint Mode (inventariar > decompor > priorizar > delegar > integrar) |
| **Complex** | Ambiguidade, dominio novo | Brainstorming (explorar > propor > aprovar) + Feature Mode |

## Arquivos de Estado

```
docs/specs/frontend/PLANO_IMPLEMENTACAO_v2.md  -> Master spec (metricas, sprints, score)
replit.md                                       -> Memoria persistente (arquitetura, preferencias)
.local/session_plan.md                          -> Plano da sessao atual (descartavel)
```

**Regra**: `PLANO_IMPLEMENTACAO_v2.md` eh a fonte unica de verdade para metricas e progresso.

---

## Modo 1: Bug Fix

Para crashs, erros de runtime, funcionalidades quebradas.

```
DIAGNOSTICAR -> ISOLAR -> CORRIGIR -> VERIFICAR
```

1. **Diagnosticar** (maximo 10 min)
   - Reproduzir o erro (screenshot ou logs)
   - Identificar arquivo e linha exatos
   - Determinar causa raiz (nao o sintoma)
   - Classificar: crash vs visual vs logica vs performance
   - **Antes de propor o fix, rodar a skill `canonical-fix`** para confirmar qual arquivo e a fonte da verdade, mapear duplicatas/consumidores e evitar workaround no consumidor.

2. **Isolar**
   - Verificar se eh pre-existente (lista de erros a ignorar no scratchpad)
   - Identificar menor conjunto de arquivos afetados
   - Verificar se a correcao pode causar regressao

3. **Corrigir**
   - Correcao minima necessaria
   - Sem refactors oportunistas — fix apenas
   - Sem adicionar features — fix apenas

4. **Verificar**
   - Teste e2e com `runTest()` confirmando o fix
   - Screenshot antes/depois quando visual
   - Verificar que nao quebrou nada adjacente

**Checklist:**
- [ ] Causa raiz identificada (nao apenas sintoma)
- [ ] Correcao minima aplicada
- [ ] Nenhum debug log deixado no codigo
- [ ] Teste e2e passou
- [ ] Nenhuma regressao observada

---

## Modo 2: Feature

Para funcionalidades novas ou melhorias significativas.

```
SPEC -> IMPACTO -> IMPLEMENTAR -> TESTAR -> AUDITAR
```

1. **Spec** (o que, nao como)
   - Definir comportamento esperado em linguagem simples
   - Listar criterios de aceite
   - Identificar dependencias (APIs, componentes, dados)
   - Perguntar ao usuario se o design/layout muda

2. **Impacto** (usar skill `feature-impact` para features grandes)
   - Mapear arquivos afetados
   - Verificar impacto no Design System v4.2.1
   - Checar se afeta preparacao para migracao Vue

3. **Implementar**
   - Seguir convencoes existentes do codebase
   - `"use client"` sempre na primeira linha de client components
   - Hooks em `.tsx` quando contiverem JSX
   - Sem `any` — usar tipos especificos
   - Sem inline styles — usar Tailwind

4. **Testar**
   - `runTest()` com plano detalhado
   - Testar happy path E edge cases
   - Testar responsividade quando UI

5. **Auditar** (usar skill `feature-audit` para features medias/grandes)
   - Code review com `architect()`
   - Atualizar `PLANO_IMPLEMENTACAO_v2.md` com novas metricas

### Brainstorming para Features Complexas

Quando a feature tem ambiguidade ou multiplas abordagens possiveis, ANTES do Modo 2:

1. **Explorar contexto** — verificar arquivos, docs, commits recentes
2. **Perguntar** — uma pergunta por vez, preferir multipla escolha
3. **Propor 2-3 abordagens** — com trade-offs e recomendacao
4. **Apresentar design** — secoes proporcionais a complexidade, aprovar cada uma
5. **Aprovar** — so implementar apos aprovacao do usuario

**HARD-GATE:** NAO implementar ate ter design aprovado. Todo projeto passa por este processo. "Simples" eh onde suposicoes nao examinadas causam mais retrabalho.

---

## Modo 3: Refactor

Para melhorias de qualidade sem mudanca de comportamento.

```
MEDIR -> PLANEJAR -> EXECUTAR -> MEDIR DE NOVO
```

1. **Medir** (antes) — contar metricas: `:any`, `as any`, inline styles, linhas
2. **Planejar** — definir meta, listar arquivos alvo, estimar esforco
3. **Executar** — um arquivo por vez, compilar e testar apos cada um
4. **Medir de novo** — recontar, atualizar PLANO com delta

### Comandos de Medicao

```bash
# Contar :any
grep -r ": any" plataforma-lia/src --include="*.ts" --include="*.tsx" | grep -v node_modules | grep -v ".next/" | wc -l

# Contar as any
grep -r "as any" plataforma-lia/src --include="*.ts" --include="*.tsx" | grep -v node_modules | grep -v ".next/" | wc -l

# Contar inline styles
grep -rn "style={{" plataforma-lia/src --include="*.tsx" | grep -v node_modules | wc -l

# Listar monolitos >1500 linhas
find plataforma-lia/src -name "*.tsx" -o -name "*.ts" | grep -v node_modules | grep -v ".next" | xargs wc -l | sort -rn | head -20

# Score de qualidade
# Score = 10 - (any/100 * 1.5) - (as_any/50 * 1.0) - (inline/500 * 1.0) - (monolitos/5 * 0.5)
```

---

## Modo 4: Sprint

Para conjuntos coordenados de tarefas (Planning Mode do Replit).

```
INVENTARIAR -> DECOMPOR -> PRIORIZAR -> DELEGAR -> INTEGRAR
```

1. **Inventariar** — ler estado do PLANO, verificar tasks existentes
2. **Decompor** — tasks atomicas com objetivo claro, arquivos alvo, criterio de aceite
3. **Priorizar** — P0 crashs > P1 qualidade > P2 features > P3 polish > P4 performance
4. **Delegar** — tasks isoladas em paralelo, tasks com dependencia em sequencia
5. **Integrar** — verificar ambiente apos merge, rodar post_merge_setup, atualizar PLANO

---

## Spec-Driven: 4 Fases Adaptativas

Para features grandes ou complexas, usar profundidade proporcional:

```
SPECIFY -> DESIGN -> TASKS -> EXECUTE
(obrigatorio)  (opcional)  (opcional)  (obrigatorio)
```

| Escopo | Specify | Design | Tasks | Execute |
|--------|---------|--------|-------|---------|
| **Small** (<=3 arquivos) | Quick mode | - | - | Implementar direto |
| **Medium** (<10 tasks) | Spec breve | Inline | Implicitas | Implementar + verificar |
| **Large** (multi-componente) | Spec + IDs | Arquitetura + componentes | Breakdown + deps | Implementar + verificar por task |
| **Complex** (ambiguidade) | Spec + brainstorming | Research + arquitetura | Breakdown + paralelo | Implementar + UAT interativa |

**Safety valve:** Se ao listar steps no Execute surgirem >5 ou dependencias complexas, PARE e crie tasks formais.

---

## Regras Inegociaveis do Projeto

1. **`"use client"` sempre primeira linha** em client components
2. **Sem documentos de auditoria separados** — tudo no PLANO
3. **Sem git commit/push manual** — o Replit gerencia
4. **Perguntar antes de mudar design/layout** — o usuario avalia primeiro
5. **Chat eh a interface principal** — botoes sao atalhos opcionais
6. **Preparar para migracao Vue** — estrutura, naming, patterns
7. **Design System v4.2.1** — border-radius, tipografia, tokens canonicos

## Erros Pre-Existentes a Ignorar

- `.next/types/` route errors
- `exports/funil-candidatos-completo.tsx`
- Admin/conformidade pages
- `ScreeningConfigManager.tsx`
- `AgentActivityDashboard/NPSDashboard`
- `useChatPageCore.tsx` MESSAGE_COMPONENT_CONFIGS (lines 975-1069)

---

## Quality Gates

### Gate 1: Funcional
- [ ] Aplicacao compila sem novos erros
- [ ] Feature/fix funciona conforme especificado
- [ ] Teste e2e passou com `runTest()`

### Gate 2: Codigo
- [ ] Sem `console.log` de debug deixado
- [ ] Sem `any` introduzido (ou justificativa documentada)
- [ ] Sem inline styles introduzidos
- [ ] Code review com `architect()` passou

### Gate 3: Documentacao
- [ ] `PLANO_IMPLEMENTACAO_v2.md` atualizado (se metricas mudaram)
- [ ] `replit.md` atualizado (se arquitetura mudou)
- [ ] Commit message descreve o que e por que

---

## Template de Session Plan

```markdown
# Objetivo
[Uma frase clara do que sera feito]

# Modo
[Bug Fix | Feature | Refactor | Sprint]

# Baseline (se refactor)
- :any = X
- as any = Y
- inline styles = Z

# Tasks

### T001: [Nome descritivo]
- **Blocked By**: []
- **Arquivos**: [lista]
- **Aceite**: [como verificar que esta pronto]

### T002: [Nome descritivo]
- **Blocked By**: [T001]
- **Arquivos**: [lista]
- **Aceite**: [como verificar que esta pronto]

# Meta
- [ ] Gate 1: Funcional
- [ ] Gate 2: Codigo
- [ ] Gate 3: Documentacao
```

---

## Comandos Rapidos

| Acao | Como |
|------|------|
| Rodar testes e2e | `runTest({ testPlan: "..." })` via code_execution |
| Code review | `architect({ task, relevantFiles, includeGitDiff: true })` |
| Ver metricas | Comandos bash na secao Refactor |
| Criar task | Planning Mode -> skill `project_tasks` |
| Verificar impacto | Skill `feature-impact` |
| Auditoria completa | Skill `feature-audit` |
