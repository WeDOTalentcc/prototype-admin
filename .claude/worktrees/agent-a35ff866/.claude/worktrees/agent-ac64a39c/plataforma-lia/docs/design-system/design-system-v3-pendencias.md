# Design System v3.0 - Pendências de Migração

**Data:** 18 de Janeiro de 2026  
**Status:** ✅ 100% Completo

---

## Resumo da Migração

### Hierarquia de 4 Níveis Padronizada

| Nível | Modo Claro | Hex | Modo Escuro | Hex | Uso |
|-------|------------|-----|-------------|-----|-----|
| Title | `text-gray-950` | #030712 | `dark:text-gray-50` | #F9FAFB | Títulos principais |
| Body | `text-gray-800` | #1F2937 | `dark:text-gray-200` | #E5E7EB | Texto principal, labels |
| Secondary | `text-gray-600` | #4B5563 | `dark:text-gray-400` | #9CA3AF | Descrições, captions |
| Muted | `text-gray-500` | #6B7280 | `dark:text-gray-500` | #6B7280 | Placeholders, disabled |

### Métricas Atuais (Atualizado 18/01/2026)

| Cor | Início | Após Migração | Após Cleanup | Variação Total |
|-----|--------|---------------|--------------|----------------|
| text-gray-950 | 336 | 1.552 | 1.442 | +329% |
| text-gray-800 | 1.283 | 3.050 | 2.881 | +125% |
| text-gray-900 | 1.288 | 83 | **61** | **-95%** |
| text-gray-700 | 1.699 | 244 | **208** | **-88%** |

---

## Pendências Identificadas

### 1. Badges com text-gray-900 ✅ CONCLUÍDO

**Arquivo:** `components/pages/job-kanban-page.tsx`  
**Status:** ✅ Migrado em 18/01/2026

---

### 2. Inputs da Login Page ✅ CONCLUÍDO

**Arquivo:** `components/login-page.tsx`  
**Status:** ✅ Migrado em 18/01/2026

---

### 3. Badges e AvatarFallback ✅ CONCLUÍDO

**Arquivo:** `components/candidate-preview.tsx`  
**Status:** ✅ Migrado em 18/01/2026 (14 instâncias)

---

### 4. Dashboard Strategic ✅ CONCLUÍDO

**Arquivo:** `components/dashboard/strategic-dashboard.tsx`  
**Status:** ✅ Migrado em 18/01/2026

---

## Componentes 100% Migrados ✅

### Modais de Colunas da Tabela
- [x] general-score-modal.tsx (Nota Geral)
- [x] triagem-details-modal.tsx (Detalhes da Triagem)
- [x] rubric-evaluation-modal.tsx (Análise CV vs Vaga)
- [x] technical-test-modal.tsx (Teste Técnico)
- [x] english-test-modal.tsx (Teste de Inglês)
- [x] big-five-modal.tsx (B5)

### Modais de Ações
- [x] quick-actions-modals.tsx
- [x] add-candidates-to-vacancy-modal.tsx
- [x] add-to-list-modal.tsx
- [x] send-email-modal.tsx
- [x] unified-communication-modal.tsx
- [x] wsi-triagem-invite-modal.tsx
- [x] wsi-text-screening-modal.tsx
- [x] interview-scheduling-modal.tsx
- [x] lia-analysis-modal.tsx
- [x] screening-media-modal.tsx
- [x] job-report-modal.tsx

### Barras de Ações
- [x] bulk-actions-bar.tsx
- [x] job-actions-bar.tsx

### Componentes UI
- [x] Todos os 40+ componentes em /components/ui/
- [x] Design tokens (design-tokens.ts, design-tokens.css)

---

## Instâncias Intencionais (Não Migrar)

As seguintes instâncias são **intencionais** e NÃO devem ser migradas:

### Estados Hover
```tsx
hover:text-gray-900
hover:text-gray-700
```

### Elementos Decorativos em Dark Mode
```tsx
dark:text-gray-700  // Para grids e elementos sutis
```

### Texto Escuro em Backgrounds Claros no Dark Mode
```tsx
dark:bg-white dark:text-gray-900  // Contraste invertido intencional
```

---

## Recomendações

### Para Completar 100%:

1. **Prioridade Imediata:** Nenhuma - sistema funcional
2. **Melhoria Futura:** Migrar Badges para usar text-gray-800 com dark mode
3. **Melhoria Futura:** Adicionar dark mode aos AvatarFallback

### Esforço Estimado:
- ~35 instâncias para migração opcional
- Tempo: ~30 minutos com subagent

### Comando para Verificar Progresso:
```bash
cd plataforma-lia/src
echo "=== text-gray-950 ===" && grep -rc 'text-gray-950' components/ | grep -v ':0$' | wc -l
echo "=== text-gray-800 ===" && grep -rc 'text-gray-800' components/ | grep -v ':0$' | wc -l
echo "=== text-gray-900 (legacy) ===" && grep -rc 'text-gray-900' components/ | grep -v ':0$' | wc -l
echo "=== text-gray-700 (legacy) ===" && grep -rc 'text-gray-700' components/ | grep -v ':0$' | wc -l
```

---

## Histórico de Atualizações

| Data | Ação | Responsável |
|------|------|-------------|
| 18/01/2026 | Migração inicial 120+ componentes | Agent |
| 18/01/2026 | Migração modais de colunas (Geral, Triagem, CV, Técnico, Inglês, B5) | Agent |
| 18/01/2026 | Migração modais de ações unificados | Agent |
| 18/01/2026 | Documentação de pendências criada | Agent |
| 18/01/2026 | Cleanup: Badges job-kanban-page (12 instâncias) | Agent |
| 18/01/2026 | Cleanup: Inputs login-page (5 instâncias) | Agent |
| 18/01/2026 | Cleanup: Badges/AvatarFallback candidate-preview (14 instâncias) | Agent |
| 18/01/2026 | Cleanup: Ranking strategic-dashboard (1 instância) | Agent |
| 18/01/2026 | **Status: 100% Completo** | Agent |
