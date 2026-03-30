# OPORTUNIDADES DE PADRONIZACAO — Plataforma LIA

Este documento rastreia oportunidades de melhoria de performance, bundle size e padronização
identificadas durante revisões do codebase.

---

## STATUS DE EXECUÇÃO

### Sprint 6 — Performance & Motion (executado em 2026-03-29)

**OPT-027: CONCLUÍDO (sprint anterior)** — framer-motion migrado para CSS puro antes deste sprint.
Todos os 5 arquivos que continham `framer-motion` foram migrados para Tailwind CSS animations
(`animate-in`, `fade-in`, CSS keyframes). Os arquivos preservaram comentários `// OPT-027`
documentando o que foi substituído. Nenhum import ativo de framer-motion restou no codebase.
Estimativa de ganho de bundle: ~160KB.

**OPT-028: CONCLUÍDO** — 795 ocorrências de `transition-all` em 276 arquivos migradas para
transitions específicos:
- `hover:transition-all` → `transition-colors` (padrão incorreto em Tailwind, corrigido)
- Elementos com `hover:scale-*` → `transition-transform`
- Elementos com `hover:scale-*` + `hover:bg-*` → `transition-[color,background-color,border-color,transform]`
- Progress bars / `rounded-full` animados → `transition-[width,height]`
- Elementos com mudança de `opacity-*` → `transition-opacity`
- Demais (maioria: hover de cor/borda) → `transition-colors`

**OPT-029: CONCLUÍDO** — 5 keyframes NOP/órfãos removidos de globals.css:
- `@keyframes slideOutUp` — zero usos no TSX, removido
- `@keyframes slideOutLeft` — zero usos no TSX, removido
- `@keyframes fadeOut` — zero usos no TSX, removido
- `@keyframes pulse-subtle` — zero usos diretos; `.animate-pulse-hover` (única referência) também
  tinha zero usos no TSX, removido junto com a classe
- `@keyframes spin-smooth` — zero usos diretos; `.animate-loading` também tinha zero usos, removido
  junto com a classe
- Nota: `@keyframes fade-in`, `@keyframes slideDown`, `@keyframes slideUp` já haviam sido removidos
  em sprint anterior (comentários OPT-029 já presentes no arquivo).
- Total de keyframes ativos restantes no globals.css: 24 (todos com uso confirmado)

**OPT-030: CONCLUÍDO** — Comentário de documentação adicionado ao globals.css documentando
que as animações Radix UI (Dialog, Popover, DropdownMenu via `data-state=open/closed`) estão
desabilitadas globalmente por decisão arquitetural. Nenhuma animação Radix foi desabilitada
acidentalmente; a desativação é intencional para consistência com o design system WeDo.

---

## ITENS PENDENTES / DÍVIDA TÉCNICA

- Nenhum OPT pendente para estes itens. Sprint 6 concluído integralmente.

---

## HISTÓRICO DE SPRINTS

| Sprint | Data | OPTs | Status |
|--------|------|------|--------|
| 6 — Performance & Motion | 2026-03-29 | OPT-027..030 | Concluído |
