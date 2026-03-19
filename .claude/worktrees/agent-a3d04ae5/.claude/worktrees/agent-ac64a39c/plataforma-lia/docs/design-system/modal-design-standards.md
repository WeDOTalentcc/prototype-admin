# Padrão de Design - Modais WedoTalent v3.2

> Referência oficial para padronização de modais da Plataforma LIA.
> Baseado na padronização aplicada nos 6 modais de Job Action + análise de 58+ modais do sistema.

---

## 1. Dimensões do Modal

### Escala de Tamanhos (6 níveis)

| Tamanho | Largura | Pixels | Uso |
|---------|---------|--------|-----|
| **XS (Micro)** | `max-w-sm` | 384px | Alertas, confirmações rápidas, bloqueios |
| **S (Compacto)** | `max-w-md` | 448px | Formulários simples, 1 coluna, configurações |
| **M (Médio)** | `max-w-lg` | 512px | Formulários médios, seleções, ações bulk |
| **L (Amplo)** | `max-w-2xl` | 672px | Formulários complexos, 2 colunas leves, edição |
| **XL (Extra)** | `max-w-4xl` | 896px | Tabelas, comparações, dados densos, comunicação |
| **XXL (Full)** | `max-w-6xl` | 1152px | Modais operacionais multi-seção com conteúdo denso (ex: roteiro WSI, perfil de candidato, war room) |

### Tamanhos Proibidos

| Largura | Status | Ação |
|---------|--------|------|
| `max-w-xl` (576px) | Redundante | Usar max-w-lg ou max-w-2xl |
| `max-w-3xl` (768px) | Redundante | Usar max-w-2xl ou max-w-4xl |
| `max-w-5xl` (1024px) | Redundante | Usar max-w-4xl ou max-w-6xl |

---

## 2. Mapeamento de Modais por Tamanho

### XS - Micro (max-w-sm)
| Modal | Uso |
|-------|-----|
| data-blocking-modal | Aviso de bloqueio |
| insufficient-data-modal | Dados insuficientes |

### S - Compacto (max-w-md)
| Modal | Uso |
|-------|-----|
| add-to-list-modal | Adicionar a lista |
| ScreeningSettingsModal | Config triagem |
| ScreeningChannelsModal | Canais triagem |
| ScreeningSchedulingModal | Agendamento triagem |
| new-candidate-unified-modal | Novo candidato |

### M - Médio (max-w-lg)
| Modal | Uso |
|-------|-----|
| close-vacancy-modal | Fechar vaga |
| data-request-modal | Solicitar dados |
| bulk-action-modal | Ações em massa |
| big-five-modal (empty) | Estado vazio Big Five |

### L - Amplo (max-w-2xl)
| Modal | Uso |
|-------|-----|
| edit-job-modal | Edição de vaga |
| smart-transition-modal | Transição inteligente |
| job-status-modal | Status de vagas |
| job-publish-modal | Publicar vagas |
| job-assign-recruiter-modal | Atribuir recrutador |
| job-duplicate-modal | Duplicar vaga |
| general-score-modal | Nota Geral LIA |

### XL - Extra (max-w-4xl)
| Modal | Uso |
|-------|-----|
| job-insights-modal | Insights de vagas |
| job-compare-modal | Comparar vagas |
| unified-communication-modal | Hub de comunicação |
| stage-transition-actions-modal | Ações de transição |
| big-five-modal (full) | Relatório Big Five completo |

### XXL - Full (max-w-6xl)
| Modal | Uso |
|-------|-----|
| roteiro-wsi-triagem | Roteiro WSI de Triagem (geração, edição, aceite de perguntas) |
| candidate-modal | Perfil completo do candidato |
| war-room | War Room operacional |
| lia-screening-guide | Guia de triagem LIA |
| pipelines-tab | Gestão de pipelines |

---

## 3. Estrutura do Modal

```
DialogContent
├── DialogHeader
│   ├── Ícone (opcional) - w-4 h-4, cor contextual
│   ├── DialogTitle - text-[14px] font-semibold text-gray-950
│   └── DialogDescription - text-[12px] text-gray-600
├── Conteúdo Principal
│   ├── Seções com headers
│   ├── Cards/Listas
│   └── Inputs/Selects
└── DialogFooter
    ├── Botão Cancelar (outline)
    └── Botão Primário (gray-800)
```

---

## 4. Tipografia

| Elemento | Tamanho | Peso | Cor |
|----------|---------|------|-----|
| **Título do Modal** | `text-[14px]` | `font-semibold` | `text-gray-950` |
| **Subtítulo/Descrição** | `text-[12px]` | `font-normal` | `text-gray-600` |
| **Título de Card** | `text-[13px]` | `font-semibold` | `text-gray-950` |
| **Headers de Seção** | `text-[11px]` | `font-medium uppercase` | `text-gray-600` |
| **Labels** | `text-[11px]` | `font-medium` | `text-gray-800` |
| **Texto Body** | `text-[12px]` | `font-normal` | `text-gray-800` |
| **Metadados** | `text-[11px]` | `font-normal` | `text-gray-600` |
| **Badges** | `text-[10px]` | `font-medium` | Contextual |
| **Valores Numéricos** | `text-[18px]` | `font-bold` | Contextual |
| **Botões** | `text-[12px]` | `font-medium` | - |

**Regra**: Tamanho mínimo = `10px` (badges). Nunca usar `8px` ou `9px`.

---

## 5. Hierarquia de Cores

| Nível | Cor | Uso |
|-------|-----|-----|
| **Primário** | `text-gray-950` | Títulos, valores importantes |
| **Secundário** | `text-gray-800` | Body text, labels |
| **Terciário** | `text-gray-600` | Descrições, metadados, subtítulos |
| **Quaternário** | `text-gray-500` | Placeholders apenas |
| **Accent** | `text-[#60BED1]` | Destaques, links, badges especiais |

---

## 6. Botões

### Botão Primário (Ação Principal)
```tsx
className="h-9 px-4 text-[12px] font-medium bg-gray-800 hover:bg-gray-900 text-white"
```
- Com ícone: `<Icon className="w-3.5 h-3.5 mr-1.5" />`
- Estado disabled: adicionar `disabled:opacity-50`

### Botão Secundário (Cancelar/Fechar)
```tsx
variant="outline"
className="h-9 px-4 text-[12px] font-medium border-[#E5E7EB] text-gray-700 hover:bg-gray-50"
```

### Botão Terciário (Ação Alternativa)
```tsx
variant="outline"
className="h-9 px-4 text-[12px] font-medium border-[#E5E7EB] bg-gray-50 text-gray-700 hover:bg-gray-100"
```

---

## 7. Badges

| Tipo | Estilo |
|------|--------|
| **Accent/Destaque** | `bg-[#60BED1]/10 text-[#60BED1]` |
| **Neutro** | `bg-gray-100 text-gray-800` |
| **Sucesso** | `bg-green-50 text-green-700` |
| **Alerta** | `bg-amber-50 text-amber-700` |
| **Erro** | `bg-red-50 text-red-700` |

```tsx
className="px-1.5 py-0.5 rounded-full text-[10px] font-medium"
```

---

## 8. Inputs e Selects

```tsx
className="h-9 text-[12px] border-[#E5E7EB] focus:ring-[#60BED1] focus:border-[#60BED1]"
```

- Placeholder: `text-gray-500`
- Valor: `text-gray-800`

---

## 9. Cards e Containers

### Card Selecionável
```tsx
className={cn(
  "p-3 rounded-lg border cursor-pointer transition-all",
  isSelected 
    ? "border-[#60BED1] bg-[#60BED1]/5" 
    : "border-[#E5E7EB] hover:border-gray-300 hover:bg-gray-50"
)}
```

### Container de Seção
```tsx
className="space-y-3 p-3 bg-gray-50 rounded-lg border border-[#E5E7EB]"
```

---

## 10. Ícones

| Contexto | Tamanho | Cor |
|----------|---------|-----|
| No título do modal | `w-4 h-4` | Contextual |
| Em botões | `w-3.5 h-3.5 mr-1.5` | Herda do texto |
| Em labels/metadados | `w-3 h-3` | `text-gray-500` |
| Indicadores de status | `w-2 h-2` ou `w-2.5 h-2.5` | Status color |

---

## 11. Espaçamento

| Elemento | Valor |
|----------|-------|
| Padding interno do modal | `p-0` (usando DialogContent padrão) |
| Gap entre seções | `space-y-4` |
| Gap dentro de cards | `space-y-2` ou `gap-2` |
| Gap entre badges | `gap-1` |
| Margem do footer | `mt-4` (implícito no DialogFooter) |

---

## 12. Bordas e Sombras

| Elemento | Estilo |
|----------|--------|
| Borda padrão | `border-[#E5E7EB]` |
| Borda hover | `border-gray-300` |
| Borda selecionada | `border-[#60BED1]` |
| Border radius cards | `rounded-lg` |
| Border radius badges | `rounded-full` ou `rounded` |

---

## 13. Estados

| Estado | Visual |
|--------|--------|
| **Hover** | `hover:bg-gray-50` ou `hover:bg-gray-100` |
| **Selecionado** | `border-[#60BED1] bg-[#60BED1]/5` |
| **Disabled** | `opacity-50 cursor-not-allowed` |
| **Loading** | `<Loader2 className="w-3.5 h-3.5 animate-spin" />` |

---

## 14. Cores de Status

| Status | Background | Text |
|--------|------------|------|
| Ativo/Sucesso | `bg-green-50` | `text-green-700` |
| Pausado/Warning | `bg-amber-50` | `text-amber-700` |
| Fechado/Erro | `bg-red-50` | `text-red-700` |
| Draft/Neutro | `bg-gray-100` | `text-gray-700` |
| Accent/Destaque | `bg-[#60BED1]/10` | `text-[#60BED1]` |

---

## Regras Gerais

1. **Cores**: 90% monocromático (grays), #60BED1 apenas para accent/destaque
2. **Fonte mínima**: 10px (badges), nunca 8px ou 9px
3. **Botão primário**: Sempre gray-800, nunca cyan
4. **Consistência**: Mesma estrutura de header/content/footer em todos os modais
5. **Acessibilidade**: Contraste adequado, estados visuais claros
6. **Tamanhos**: Usar apenas os 6 tamanhos definidos (XS, S, M, L, XL, XXL)

---

## Modais de Referência (100% Padronizados)

Os seguintes modais seguem 100% este padrão e podem ser usados como referência:

1. `job-status-modal.tsx` - Modal M com seleção de status
2. `job-publish-modal.tsx` - Modal M com formulário e checkboxes
3. `job-assign-recruiter-modal.tsx` - Modal M com lista selecionável
4. `job-duplicate-modal.tsx` - Modal M com inputs
5. `job-insights-modal.tsx` - Modal XL com tabela e navegação
6. `job-compare-modal.tsx` - Modal XL com tabela comparativa

---

## Plano de Correção por Prioridade

### Alta Prioridade (Botão Cyan → Gray-800)

| Modal | Correções Necessárias |
|-------|----------------------|
| edit-job-modal | Ícone 10x10→w-4 h-4, botão cyan→gray-800, max-w-2xl |
| ScreeningSettingsModal | Botão cyan→gray-800 |
| ScreeningChannelsModal | Botão cyan→gray-800 |
| ScreeningSchedulingModal | Botão cyan→gray-800 |
| smart-transition-modal | Botão cyan→gray-800, header padronizar |
| bulk-action-modal | Botão cyan→gray-800 |
| data-request-modal | Botão cyan→gray-800 |
| data-blocking-modal | Botão cyan→gray-800, max-w-sm |
| add-to-list-modal | Botão cyan→gray-800 |
| new-candidate-unified-modal | Botão cyan→gray-800 |

### Média Prioridade (Ajustes de Tamanho/Layout)

| Modal | Correções Necessárias |
|-------|----------------------|
| unified-communication-modal | max-w-5xl→max-w-4xl, ícone 10x10→w-4 h-4, botão cyan→gray-800 |
| stage-transition-actions-modal | max-w-5xl→max-w-4xl |
| close-vacancy-modal | Padronizar header |

### Baixa Prioridade (Componentes Standalone)

| Modal | Status |
|-------|--------|
| wsi-triagem-invite-modal | Não usa Dialog - avaliar conversão futura |
| wsi-text-screening-modal | Componente standalone - manter |
| english-test-modal | Ajustar tipografia para escala v3.0 |
| technical-test-modal | Ajustar tipografia para escala v3.0 |

---

## Checklist de Padronização

Ao criar ou revisar um modal, verifique:

### Tamanho
- [ ] Tamanho apropriado (XS/S/M/L/XL/XXL)
- [ ] Não usar max-w-xl, max-w-3xl ou max-w-5xl

### Tipografia
- [ ] Título: 14px semibold gray-950
- [ ] Descrição: 12px normal gray-600
- [ ] Labels: 11px medium gray-800
- [ ] Body text: 12px normal gray-800
- [ ] Badges: 10px minimum
- [ ] Nenhum texto 8px ou 9px

### Cores
- [ ] Títulos em gray-950
- [ ] Body em gray-800
- [ ] Descrições em gray-600
- [ ] Accent (#60BED1) apenas para destaques

### Botões
- [ ] Botão primário: bg-gray-800 (não cyan)
- [ ] Botão secundário: outline com border-[#E5E7EB]
- [ ] Ícones em botões: w-3.5 h-3.5 mr-1.5

### Componentes
- [ ] Cards selecionados: border-[#60BED1] bg-[#60BED1]/5
- [ ] Ícone no header: w-4 h-4 (não 10x10)
- [ ] Footer com DialogFooter padrão

---

*Última atualização: Fevereiro 2026 - v3.2*
