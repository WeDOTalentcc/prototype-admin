# Plano de Migração: Design System LIA → Vue/Vuetify

> **Criado**: 02/02/2026  
> **Última atualização**: 02/02/2026  
> **Status**: FASE 0 - Ajustando Design System

---

## 📋 Contexto

A plataforma LIA está sendo recriada em **Vue 3 + Vuetify 3** pelo time de desenvolvimento. Para facilitar esse processo, precisamos:

1. **Ajustar o Design System v4** com cores e decisões pendentes
2. **Padronizar a plataforma atual** (Next.js/React) conforme o Design System v4
3. **Criar arquivos de configuração** (SASS/TypeScript) para o dev usar no projeto Vue
4. **Garantir consistência** entre Figma → MCP → Código Vue

---

## 🎯 Objetivos

### Objetivo Principal
Facilitar o workflow: **Figma → MCP/Cursor/Antigravity → Código Vue/Vuetify**

### Objetivos Específicos
1. Ajustar o Design System com cores faltantes e decisões pendentes
2. Eliminar variações inconsistentes de cores, espaçamentos e fontes na plataforma atual
3. Padronizar componentes usando tokens do Design System v4
4. Mapear tokens CSS para nomenclatura compatível com Vuetify
5. Gerar arquivo `_lia-vuetify-theme.scss` para importação direta
6. Gerar objeto de tema `vuetify.config.ts` pronto para uso

---

## 📊 Resultado da Auditoria (02/02/2026)

### Estatísticas Gerais
- **13.227** ocorrências de cores gray na plataforma
- **4.218** usos de #60BED1 (wedo-cyan) - cor mais usada
- **Múltiplas** cores hardcoded não padronizadas

### Uso de Cores de Texto (text-gray-*)
| Classe | Usos | Função no DS |
|--------|------|--------------|
| `text-gray-800` | 2.974 | Texto corpo (body) |
| `text-gray-600` | 2.380 | Texto secundário |
| `text-gray-950` | 1.655 | Texto mais escuro ✅ Decidido manter |
| `text-gray-500` | 1.384 | Texto muted |
| `text-gray-400` | 1.366 | Texto disabled |
| `text-gray-200` | 2.038 | Dark mode |
| `text-gray-50` | 1.399 | Dark mode |

### Uso de Backgrounds (bg-gray-*)
| Classe | Usos | Status |
|--------|------|--------|
| `bg-gray-50` | 1.359 | ✅ Fundo secundário |
| `bg-gray-100` | 1.042 | ✅ Fundo terciário |
| `bg-gray-900` | 407 | ✅ Botões primários |
| `bg-gray-750` | 4 | ❌ **NÃO EXISTE** - Remover |
| `bg-gray-850` | 1 | ❌ **NÃO EXISTE** - Remover |

### Cores Hardcoded - Ação Necessária
| Cor | Usos | Decisão |
|-----|------|---------|
| `#60BED1` | 4.218 | ✅ wedo-cyan - OK |
| `#5DA47A` | 89 | ✅ wedo-green - OK |
| `#D19960` | 62 | ✅ wedo-orange - OK |
| `#4DA8BB` | 215 | ⚠️ **Adicionar** como wedo-cyan-dark |
| `#F59E0B` | 73 | ⚠️ **Adicionar** como amber/warning-alt |
| `#E5E7EB` | 366 | 🔄 Substituir por `gray-200` |
| `#6B7280` | 119 | 🔄 Substituir por `gray-500` |
| `#9CA3AF` | 87 | 🔄 Substituir por `gray-400` |
| `#F9FAFB` | 83 | 🔄 Substituir por `gray-50` |
| `#374151` | 62 | 🔄 Substituir por `gray-700` |
| `#FAFAFA` | 81 | 🔄 Padronizar para `#F9FAFB` (gray-50) |
| `#E8E8E8` | 202 | ❌ **Eliminar** - usar gray-200 |
| `#666666` | 181 | ❌ **Eliminar** - usar gray-500 |
| `#2D2D2D` | 154 | ❌ **Eliminar** - usar gray-800 |
| `#E4EBEF` | 109 | ❌ **Eliminar** - usar gray-200 |
| `#999999` | 97 | ❌ **Eliminar** - usar gray-400 |

### Métricas de Sucesso (Pós-padronização)
- 100% dos componentes usando CSS Variables ou classes Tailwind
- Zero cores hardcoded não documentadas
- Zero uso de classes inexistentes (bg-gray-750, bg-gray-850)
- Tipografia usando apenas 3 fontes definidas

---

## 🗂️ Fases do Plano (Atualizado)

### FASE 0: Ajustar o Design System v4 ← **ATUAL**
**Objetivo**: Garantir que o documento esteja completo antes de aplicar na plataforma

#### 0.1 Adicionar Cores Faltantes
- [ ] Adicionar `wedo-cyan-dark` (#4DA8BB) como variação do cyan
- [ ] Documentar `amber` (#F59E0B) como cor de warning alternativa
- [ ] Confirmar `gray-950` (#030712) como tom mais escuro para textos

#### 0.2 Documentar Cores Deprecadas
- [ ] Criar seção "Cores a Eliminar" com mapeamento para substituição
- [ ] Listar: #666666, #999999, #E8E8E8, #FAFAFA, #E4EBEF, #2D2D2D

#### 0.3 Documentar Classes Inválidas
- [ ] Adicionar nota sobre `bg-gray-750` e `bg-gray-850` (não existem no Tailwind)
- [ ] Definir substituições: 750 → 700 ou 800, 850 → 800 ou 900

---

### FASE 1: Padronizar a Plataforma
**Módulo piloto: Menu Configurações**

#### 1.1 Menu Configurações - Principal
- [ ] Substituir cores hardcoded por classes Tailwind
- [ ] Remover bg-gray-750, bg-gray-850
- [ ] Padronizar #FAFAFA → gray-50
- [ ] Aplicar tipografia correta

#### 1.2 Subpáginas de Configurações
- [ ] Aplicar padrões em todas as tabs
- [ ] Garantir consistência de estados (hover, active, disabled)
- [ ] Aplicar Dark Mode conforme Design System

#### 1.3 Validação
- [ ] Verificar visualmente cada tela
- [ ] Testar responsividade
- [ ] Testar Dark Mode

---

### FASE 2: Documentar Integração Vuetify
**Após padronização do módulo piloto**

#### 2.1 Adicionar Seção 4.6 ao Design System
- [ ] Mapeamento de cores LIA → Vuetify
- [ ] Mapeamento de tipografia → $typography
- [ ] Exemplos de código Vue/Vuetify

#### 2.2 Criar Arquivos para o Dev
```
plataforma-lia/docs/design-system/vuetify/
├── _lia-vuetify-settings.scss   # Variáveis SASS do Vuetify
└── vuetify-theme.ts             # Objeto createVuetify()
```

---

### FASE 3: Padronização dos Demais Módulos
**Após validação do piloto**

#### Ordem de Prioridade
1. **Configurações** (piloto) ← Em andamento
2. **Pipeline/Kanban** (alta visibilidade)
3. **Job Wizard** (LIA conversacional)
4. **Candidatos** (listagens/detalhes)
5. **Dashboard** (KPIs/gráficos)
6. **Demais módulos**

---

## 📝 Decisões Tomadas (02/02/2026)

### ✅ Cores Confirmadas
| Decisão | Valor | Justificativa |
|---------|-------|---------------|
| gray-950 como tom mais escuro | `#030712` | Mantém consistência com Tailwind, usado para textos de alto contraste |
| wedo-cyan-dark | `#4DA8BB` | Variação escura do cyan para hovers e estados ativos |
| amber como warning-alt | `#F59E0B` | Cor de alerta mais vibrante que wedo-orange |

### ❌ Cores Deprecadas (Eliminar na padronização)
| Cor Atual | Substituir Por | Classe Tailwind |
|-----------|---------------|-----------------|
| `#FAFAFA` | `#F9FAFB` | `gray-50` |
| `#E8E8E8` | `#E5E7EB` | `gray-200` |
| `#666666` | `#6B7280` | `gray-500` |
| `#999999` | `#9CA3AF` | `gray-400` |
| `#2D2D2D` | `#1F2937` | `gray-800` |
| `#E4EBEF` | `#E5E7EB` | `gray-200` |

### ❌ Classes Inválidas (Remover)
| Classe | Substituir Por |
|--------|---------------|
| `bg-gray-750` | `bg-gray-700` ou `bg-gray-800` |
| `bg-gray-850` | `bg-gray-800` ou `bg-gray-900` |

---

## 🔧 Workflow de Conversão Figma → Vue

### Fluxo Ideal (após padronização)
```
┌─────────────────────────────────────────────────────────────────┐
│  1. FIGMA                                                       │
│     Designer cria/atualiza tela usando tokens LIA               │
│     (cores, espaçamentos, tipografia padronizados)              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  2. MCP/CURSOR/ANTIGRAVITY                                      │
│     Converte Figma → Código Vue                                 │
│     Classes CSS já mapeadas para Vuetify                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  3. PROJETO VUE                                                 │
│     Dev importa _lia-vuetify-settings.scss                      │
│     Componentes já vêm estilizados corretamente                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  4. AJUSTES MÍNIMOS                                             │
│     Apenas lógica de negócio e integrações API                  │
│     Design já vem pronto do Figma                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📝 Notas Importantes

### Design System v4 - Princípios Chave
- **Paleta**: 90% grayscale + 10% cores WeDo
- **Botões primários**: `bg-gray-900` (preto)
- **Accent color**: `#60BED1` (wedo-cyan) - usado no Brain icon
- **Tipografia**: Open Sans 85%, Inter 10%, Source Serif 4 5%
- **Espaçamento**: Sistema 4px base

### Arquivos de Referência
- Design System completo: `docs/design-system/00-design-system-v4.md`
- Tokens CSS: `src/styles/design-tokens.css`
- Tokens TypeScript: `src/lib/design-tokens.ts`
- Tailwind config: `tailwind.config.ts`

---

## ✅ Checklist de Entregáveis

### Fase 0 (Design System) ← ATUAL
- [ ] wedo-cyan-dark adicionado ao documento
- [ ] amber/warning-alt documentado
- [ ] gray-950 confirmado
- [ ] Cores deprecadas listadas
- [ ] Classes inválidas documentadas

### Fase 1 (Padronização Configurações)
- [ ] Menu principal padronizado
- [ ] Subpáginas padronizadas
- [ ] Validação visual aprovada

### Fase 2 (Integração Vuetify)
- [ ] Seção 4.6 adicionada ao documento
- [ ] `_lia-vuetify-settings.scss` criado
- [ ] `vuetify-theme.ts` criado
- [ ] Instruções de uso documentadas

### Fase 3 (Rollout)
- [ ] Pipeline/Kanban padronizado
- [ ] Job Wizard padronizado
- [ ] Demais módulos padronizados

---

## 📅 Próximos Passos

1. ✅ **Auditoria concluída** (02/02/2026)
2. ➡️ **FASE 0**: Atualizar Design System v4 com cores/decisões
3. ⏳ **FASE 1**: Padronizar módulo Configurações
4. ⏳ **FASE 2**: Documentar integração Vuetify
5. ⏳ **FASE 3**: Rollout para demais módulos

---

## 📎 Arquivos Vuetify (Preview)

### _lia-vuetify-settings.scss
```scss
// ==========================================
// DESIGN SYSTEM LIA v4.0 - VUETIFY SETTINGS
// ==========================================

@use 'vuetify/settings' with (
  // TIPOGRAFIA
  $body-font-family: ("Open Sans", sans-serif),
  $font-size-root: 16px,
  $line-height-root: 1.5,
  
  // BORDAS
  $border-radius-root: 8px,
  $border-color-root: rgba(0, 0, 0, 0.08),
  
  // ESPAÇAMENTO
  $spacer: 4px,
  
  // TRANSIÇÕES
  $transition-duration-root: 0.2s,
);

// CORES WEDO (para uso em componentes)
$wedo-cyan: #60BED1;
$wedo-cyan-dark: #4DA8BB;
$wedo-green: #5DA47A;
$wedo-orange: #D19960;
$wedo-purple: #9860D1;
$wedo-magenta: #D160AB;
$amber: #F59E0B;
```

### vuetify-theme.ts
```typescript
export const liaTheme = {
  dark: false,
  colors: {
    primary: '#111827',      // gray-900
    secondary: '#F3F4F6',    // gray-100
    accent: '#60BED1',       // wedo-cyan
    surface: '#FFFFFF',
    background: '#F9FAFB',   // gray-50
    
    success: '#5DA47A',      // wedo-green
    warning: '#D19960',      // wedo-orange
    'warning-alt': '#F59E0B', // amber
    error: '#DC2626',
    info: '#60BED1',         // wedo-cyan
    
    'wedo-cyan': '#60BED1',
    'wedo-cyan-dark': '#4DA8BB',
    'wedo-green': '#5DA47A',
    'wedo-orange': '#D19960',
    'wedo-purple': '#9860D1',
    'wedo-magenta': '#D160AB',
  }
}
```

---

*Este documento será atualizado conforme o progresso do trabalho.*
