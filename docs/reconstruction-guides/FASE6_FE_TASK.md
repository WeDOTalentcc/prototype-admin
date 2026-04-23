# Fase 6 FE — Tarefa para Execução no Claude Code

> **Projeto:** WeDOTalent / plataforma-lia (Frontend Next.js)
> **Origem:** Cross-Cutting Audit 2026-04-23 — pendências G3, G4, G5 deferidas por decisão de produto
> **Prioridade:** P2 — sem impacto operacional, mas dívida arquitetural
> **Repositório:** `wedotalent02202026/plataforma-lia/src/`

---

## Contexto

Durante a auditoria cross-cutting de 2026-04-22/23, todos os P0/P1 foram resolvidos.
Restaram 3 itens P2 no frontend que foram deferidos para janela FE dedicada:

| ID | Problema | Arquivos |
|----|---------|---------|
| G3 | `permissions.ts` com importação cíclica type-only | `lib/` + `utils/` |
| G4 | `config/pricing.ts` é alias morto | `config/` vs `lib/` |
| G5 | 6 hooks vivendo dentro de `components/` em vez de `hooks/` | `components/` top-level |

---

## G3 — Importação Cíclica em `permissions.ts`

### Problema

Existe uma importação cíclica type-only entre dois arquivos de permissions:

```
plataforma-lia/src/lib/permissions.ts       ← importa de utils/permissions.ts
plataforma-lia/src/utils/permissions.ts     ← importa de lib/permissions.ts
plataforma-lia/src/utils/permissions.test.ts
```

O ciclo é **type-only** (não quebra o Next.js build), mas viola o princípio de
responsabilidade única e dificulta manutenção.

### O que fazer

1. Ler os dois arquivos (`lib/permissions.ts` e `utils/permissions.ts`) para entender
   quais tipos/funções cada um exporta e qual importa do outro

2. Escolher **uma** das duas abordagens:
   - **Opção A (preferida):** Consolidar em um único canonical em `lib/permissions.ts`.
     Mover tudo para `lib/`, transformar `utils/permissions.ts` em shim de re-export
     (`export * from '@/lib/permissions'`) e marcar para remoção futura
   - **Opção B:** Quebrar o ciclo usando `import type` onde há import de valor,
     reorganizando quais types ficam em cada arquivo para eliminar a dependência bidirecional

3. Mover o arquivo de teste `utils/permissions.test.ts` para `lib/permissions.test.ts`
   se optar pela Opção A

4. Verificar se o build passa: `npm run build` dentro de `plataforma-lia/`

### Validação

```bash
# Não deve encontrar ciclo de import (zero saída = OK)
npx madge --circular src/lib/permissions.ts src/utils/permissions.ts

# Build deve passar sem warnings de ciclo
cd plataforma-lia && npm run build
```

---

## G4 — `config/pricing.ts` é Alias Morto

### Problema

Existem dois arquivos de pricing:

```
plataforma-lia/src/lib/pricing.ts        ← CANONICAL REAL (usar este)
plataforma-lia/src/config/pricing.ts     ← ALIAS MORTO (re-exporta ou duplica lib/pricing.ts)
```

O arquivo `config/pricing.ts` não tem razão de existir — é um alias sem uso
ou que duplica desnecessariamente o canonical em `lib/`.

### O que fazer

1. Ler `config/pricing.ts` para confirmar que é realmente um re-export/alias

2. Buscar todos os imports que apontam para `config/pricing`:
   ```bash
   grep -r "from.*config/pricing\|from.*@/config/pricing" src/ --include="*.ts" --include="*.tsx"
   ```

3. Para cada arquivo encontrado: substituir o import por `@/lib/pricing`

4. Deletar `plataforma-lia/src/config/pricing.ts`

5. Verificar que não existem mais referências:
   ```bash
   grep -r "config/pricing" src/ --include="*.ts" --include="*.tsx"
   # Deve retornar vazio
   ```

### Validação

```bash
# Zero referências ao arquivo deletado
grep -r "config/pricing" plataforma-lia/src/ --include="*.ts" --include="*.tsx"

# Build passa
cd plataforma-lia && npm run build
```

---

## G5 — 6 Hooks Misplaced em `components/`

### Problema

Os seguintes 6 arquivos de hooks estão dentro de `components/` (pasta para componentes React),
violando o padrão arquitetural do projeto onde hooks ficam em `hooks/`:

```
plataforma-lia/src/components/useBatchApproval.ts
plataforma-lia/src/components/useLiaMetrics.ts
plataforma-lia/src/components/useLiaMetricsData.ts
plataforma-lia/src/components/useLiaScreeningDialogue.ts
plataforma-lia/src/components/useMetricsCalculations.ts
plataforma-lia/src/components/useRubricEvaluation.ts
```

### Estrutura de destino

`hooks/` já tem 12 subpastas com `index.ts` barrel export em cada uma:

```
hooks/
├── agents/     ← Agent Studio
├── ai/         ← IA/ML hooks  ← destino provável para useLiaMetrics*, useRubricEvaluation, useLiaScreeningDialogue
├── candidates/ ← Candidatos
├── chat/       ← Chat
├── company/    ← Empresa
├── jobs/       ← Vagas
├── prompt/     ← Prompts
├── recruitment/← Recrutamento
├── search/     ← Busca
├── settings/   ← Configurações
├── shared/     ← Utilitários compartilhados
└── ui/         ← UI hooks  ← destino provável para useBatchApproval, useMetricsCalculations
```

### O que fazer

1. Ler cada um dos 6 hooks para decidir o subdiretório correto de destino:
   - Hooks de IA/métricas/screening → `hooks/ai/`
   - Hooks de UI/aprovação/cálculo → `hooks/ui/`

2. Para cada hook:
   a. Mover o arquivo para o subdiretório correto em `hooks/`
      (ex: `components/useLiaMetrics.ts` → `hooks/ai/use-lia-metrics.ts`)
   b. Renomear para kebab-case se ainda não estiver (padrão do projeto)
   c. Adicionar export no `index.ts` do subdiretório de destino

3. Buscar todos os components que importam esses hooks:
   ```bash
   grep -r "useBatchApproval\|useLiaMetrics\|useLiaMetricsData\|useLiaScreeningDialogue\|useMetricsCalculations\|useRubricEvaluation" src/ --include="*.ts" --include="*.tsx" -l
   ```

4. Atualizar os imports em cada arquivo encontrado para apontar para o novo caminho

5. Verificar que `components/` não tem mais arquivos `use*.ts`:
   ```bash
   find src/components -name "use*.ts" -not -path "*/__tests__/*"
   # Deve retornar vazio
   ```

### Validação

```bash
# Zero hooks em components/
find plataforma-lia/src/components -name "use*.ts" | grep -v test

# Build passa
cd plataforma-lia && npm run build

# Testes passam
cd plataforma-lia && npm test -- --passWithNoTests
```

---

## Ordem de execução recomendada

```
1. G4 primeiro (mais simples — deletar um arquivo e atualizar imports)
2. G3 segundo (requer decisão sobre consolidação vs. quebra de ciclo)
3. G5 por último (mais trabalhoso — 6 arquivos + todos os imports dependentes)
```

---

## Regras obrigatórias ao executar

1. **NUNCA git push** — apenas commit local no Replit. Push é exclusivo do Paulo via branch `replit-sync`
2. **Design System v4.2.1** — não alterar nenhuma lógica de UI durante a refatoração, apenas mover arquivos e atualizar imports
3. **Build verde antes de commitar** — `npm run build` deve passar sem erros
4. **Um commit por tarefa** — G4 em commit separado de G3, G5 em commit separado de G3
5. **Verificar testes existentes** — `npm test` não deve quebrar nenhum teste existente

---

## Commit messages sugeridos

```
G4: remove dead alias config/pricing.ts → canonical is lib/pricing.ts
G3: resolve circular import in permissions.ts (type-only cycle)
G5: move 6 misplaced hooks from components/ to hooks/ai/ and hooks/ui/
```

---

## Referência

- Auditoria completa: `docs/reconstruction-guides/` (no Replit) ou `/Users/paulomoraes/Documents/Python/CROSS_CUTTING_AUDIT_AND_REMEDIATION_PLAN.md`
- Seção relevante: `0.8.8 Duplicatas de Frontend` + `0.8.9 Hooks Organização (FE)`
- Rastreamento: G3, G4, G5 em `COMPLIANCE_CROSS_CUTTING_MATRIX.md`
