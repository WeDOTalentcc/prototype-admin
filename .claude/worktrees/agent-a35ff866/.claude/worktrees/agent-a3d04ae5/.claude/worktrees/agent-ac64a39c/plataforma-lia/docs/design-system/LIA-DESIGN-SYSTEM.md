# LIA Design System

**Versão:** 1.0  
**Data:** 5 de Dezembro de 2025  
**Status:** Oficial

---

## 1. Filosofia de Design

### Princípios Fundamentais

1. **Minimalismo Monocromático** - Base em preto, branco e cinzas (90% da interface)
2. **Cores com Propósito** - Cores apenas onde têm significado semântico (10% da interface)
3. **Bordas ou Sombras** - Containers estruturais (kanban, busca, listas) usam bordas finas (border-gray-200); cards de destaque usam shadow-sm
4. **Sem Gradientes** - Apenas cores sólidas
5. **Hierarquia Clara** - Tipografia e espaçamento definem a estrutura visual
6. **Acessibilidade** - Contraste mínimo AA para textos

### Regra de Bordas vs Sombras

| Contexto | Estilo | Exemplo |
|----------|--------|---------|
| **Containers estruturais** | `border border-gray-200` | Kanban, Search Hero, Pills/Badges, Tabelas |
| **Cards de destaque** | `shadow-sm` (sem borda) | Modais, Popovers, Cards informativos |
| **Inputs** | `border border-gray-200 focus:border-cyan` | Campos de formulário |

**Regra:** Quando usar borda, NÃO usar sombra. Quando usar sombra, NÃO usar borda.

### Inspiração

Estilo inspirado em ElevenLabs, Linear e Vercel: interfaces limpas, sofisticadas e funcionais.

---

## 2. Tipografia

### Fontes

| Uso | Fonte | Fallback |
|-----|-------|----------|
| **Títulos/Headers** | Source Serif 4 | Georgia, serif |
| **Corpo/UI** | Open Sans | system-ui, sans-serif |
| **Código** | JetBrains Mono | Consolas, monospace |

### Hierarquia de Títulos

| Elemento | Fonte | Tamanho | Peso | Cor |
|----------|-------|---------|------|-----|
| H1 - Título de Página | Source Serif 4 | 24px (text-2xl) | Semibold (600) | #111827 |
| H2 - Seção Principal | Source Serif 4 | 20px (text-xl) | Semibold (600) | #111827 |
| H3 - Card Title | Source Serif 4 | 16px (text-base) | Semibold (600) | #1F2937 |
| H4 - Subseção | Source Serif 4 | 14px (text-sm) | Semibold (600) | #1F2937 |

### Texto Corpo

| Elemento | Fonte | Tamanho | Peso | Cor |
|----------|-------|---------|------|-----|
| Corpo principal | Open Sans | 14px (text-sm) | Regular (400) | #374151 |
| Corpo secundário | Open Sans | 13px (text-[13px]) | Regular (400) | #4B5563 |
| Labels/Captions | Open Sans | 12px (text-xs) | Medium (500) | #6B7280 |
| Texto pequeno | Open Sans | 11px (text-[11px]) | Regular (400) | #6B7280 |

### Regras de Tipografia

```css
/* Títulos - SEMPRE usar font-serif */
.heading {
  font-family: 'Source Serif 4', Georgia, serif;
  font-weight: 600;
  color: #111827; /* ou #1F2937 */
}

/* Corpo - SEMPRE usar font-sans */
.body {
  font-family: 'Open Sans', system-ui, sans-serif;
  font-weight: 400;
  color: #374151; /* ou #4B5563 */
}
```

### Proibições de Tipografia

- ❌ NUNCA usar text-gray-400 ou text-gray-500 para textos visíveis
- ❌ NUNCA usar font-light (peso 300)
- ❌ NUNCA usar cores de texto abaixo de #6B7280
- ✅ Mínimo permitido: text-gray-600 (#4B5563) para textos secundários

---

## 3. Paleta de Cores

### 3.1 Cores Neutras (Base Monocromática)

| Nome | Hex | Tailwind | Uso |
|------|-----|----------|-----|
| **Preto** | #111827 | gray-900 | Títulos, textos principais |
| **Cinza Escuro** | #1F2937 | gray-800 | Títulos secundários, botões primários |
| **Cinza Texto** | #374151 | gray-700 | Texto corpo principal |
| **Cinza Secundário** | #4B5563 | gray-600 | Texto corpo secundário |
| **Cinza Terciário** | #6B7280 | gray-500 | Labels, captions, placeholders |
| **Cinza Borda** | #E5E7EB | gray-200 | Divisores (quando necessário) |
| **Cinza Fundo** | #F3F4F6 | gray-100 | Backgrounds alternativos |
| **Quase Branco** | #F9FAFB | gray-50 | Backgrounds de cards |
| **Branco** | #FFFFFF | white | Background principal |

### 3.2 Cores de Categoria (Acentos Semânticos)

| Categoria | Principal | Claro (fundos) | Hover | Uso |
|-----------|-----------|----------------|-------|-----|
| **Vagas/LIA/Automação** | #60BED1 | #A8CED5 | #4DA8BB | Ícone LIA, vagas, tecnologia |
| **Candidatos/Sucesso** | #5DA47A | #A8D5B7 | #4A8A68 | Candidatos, aprovação, concluído |
| **Tempo/Custos** | #D19960 | #D5BFA8 | #BF8554 | Métricas de tempo, economia |
| **Insights/Premium** | #9860D1 | #BFA8D5 | #8652B8 | Análises IA, insights, premium |
| **Urgência/Crítico** | #D160AB | #D5A8C6 | #B84D95 | Urgência, prioridade alta |

### 3.3 Cores de Status

| Status | Principal | Fundo | Texto Sobre Fundo | Uso |
|--------|-----------|-------|-------------------|-----|
| **Sucesso** | #5DA47A | #A8D5B7 (20% opacity) | #166534 | Aprovado, concluído, ativo |
| **Alerta** | #E5A853 | #FEF3C7 | #92400E | Pendente, atenção |
| **Erro** | #C74446 | #FEE2E2 | #991B1B | Rejeitado, erro, inativo |
| **Info** | #60BED1 | #A8CED5 (20% opacity) | #0D7A8C | Informação neutra |

### 3.4 Cor da Marca LIA

| Cor | Hex | Uso |
|-----|-----|-----|
| **Coral LIA** | #C74446 | Logo, CTAs muito importantes, erros destrutivos |
| **Coral Hover** | #B23B3D | Estado hover do coral |
| **Coral Fundo** | #FEF2F2 | Background sutil para coral |

### 3.5 Regras de Uso de Cores

```
PROPORÇÃO DE USO:
├── 90% Monocromático (preto, branco, cinzas)
│   ├── Backgrounds: branco, gray-50, gray-100
│   ├── Textos: gray-900, gray-700, gray-600
│   └── Elementos UI: sombras, divisores sutis
│
└── 10% Cores de Acento
    ├── Dashboards: gráficos, métricas, KPIs
    ├── Badges: status, categorias
    ├── Ícones: indicadores de categoria
    └── Botões: ações primárias especiais
```

---

## 4. Componentes

### 4.1 Cards

**Estrutura Base:**
```css
.card {
  background: #FFFFFF;
  border-radius: 12px; /* rounded-xl */
  box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.05); /* shadow-sm */
  padding: 16px; /* p-4 */
  border: none; /* SEM BORDAS */
}
```

**Variações:**

| Tipo | Background | Sombra | Uso |
|------|------------|--------|-----|
| Card Padrão | white | shadow-sm | Cards gerais |
| Card Elevado | white | shadow-md | Cards de destaque |
| Card Secundário | gray-50 | shadow-sm | Cards dentro de cards |
| Card Hover | white | shadow-md on hover | Cards interativos |

**Proibições:**
- ❌ NUNCA usar border em cards
- ❌ NUNCA usar gradientes em cards
- ❌ NUNCA usar bordas coloridas de contorno

**Exceção Permitida:**
- ✅ Borda lateral colorida de 2-3px para indicar categoria (borda esquerda apenas)

### 4.2 Botões

**Botão Primário:**
```css
.btn-primary {
  background: #1F2937; /* gray-800 */
  color: #FFFFFF;
  border-radius: 8px; /* rounded-lg */
  padding: 10px 16px; /* px-4 py-2.5 */
  font-size: 11px;
  font-weight: 500;
  border: none;
  box-shadow: none;
}

.btn-primary:hover {
  background: #374151; /* gray-700 */
}
```

**Variações de Botão:**

| Tipo | Background | Texto | Hover | Uso |
|------|------------|-------|-------|-----|
| Primário | gray-800 | white | gray-700 | Ação principal |
| Secundário | gray-100 | gray-900 | gray-200 | Ação secundária |
| Ghost | transparent | gray-700 | gray-100 | Ação terciária |
| Destrutivo | #C74446 | white | #B23B3D | Deletar, cancelar |
| Categoria | cor-categoria | white | cor-hover | Ações de categoria |

**Proibições:**
- ❌ NUNCA usar bordas em botões (exceto outline quando necessário)
- ❌ NUNCA usar gradientes em botões
- ❌ NUNCA usar sombras coloridas

### 4.3 Inputs e Formulários

**Input Padrão:**
```css
.input {
  background: #FFFFFF;
  border: 1px solid #E5E7EB; /* gray-200 - exceção para inputs */
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 14px;
  color: #374151;
}

.input:focus {
  border-color: #60BED1; /* cyan para focus */
  outline: none;
  box-shadow: 0 0 0 3px rgba(96, 190, 209, 0.1);
}

.input::placeholder {
  color: #9CA3AF; /* gray-400 permitido APENAS para placeholder */
}
```

**Nota:** Inputs são a ÚNICA exceção onde bordas são permitidas (para acessibilidade).

### 4.4 Badges/Pills

**Estrutura:**
```css
.badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 9999px; /* rounded-full */
  font-size: 11px;
  font-weight: 500;
  border: none;
}
```

**Variações por Categoria:**

| Categoria | Background | Texto |
|-----------|------------|-------|
| Vagas/LIA | #A8CED5 (20% op) | #0D7A8C |
| Candidatos | #A8D5B7 (20% op) | #166534 |
| Tempo | #D5BFA8 (20% op) | #92400E |
| Insights | #BFA8D5 (20% op) | #6B21A8 |
| Urgência | #D5A8C6 (20% op) | #9D174D |

**Variações por Status:**

| Status | Background | Texto |
|--------|------------|-------|
| Ativo/Sucesso | bg-green-100 | text-green-800 |
| Pendente/Alerta | bg-yellow-100 | text-yellow-800 |
| Inativo/Erro | bg-red-100 | text-red-800 |
| Neutro | bg-gray-100 | text-gray-700 |

### 4.5 Tabelas

**Estrutura:**
```css
.table {
  width: 100%;
  border-collapse: collapse;
}

.table th {
  background: #F9FAFB;
  color: #6B7280;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid #E5E7EB;
}

.table td {
  padding: 16px;
  color: #374151;
  border-bottom: 1px solid #F3F4F6;
}

.table tr:hover {
  background: #F9FAFB;
}
```

### 4.6 Modais

**Estrutura:**
```css
.modal-overlay {
  background: rgba(0, 0, 0, 0.5);
}

.modal {
  background: #FFFFFF;
  border-radius: 16px;
  box-shadow: 0 25px 50px -12px rgb(0 0 0 / 0.25);
  max-width: 600px;
  border: none;
}

.modal-header {
  padding: 24px;
  border-bottom: 1px solid #F3F4F6;
}

.modal-body {
  padding: 24px;
}

.modal-footer {
  padding: 16px 24px;
  background: #F9FAFB;
  border-radius: 0 0 16px 16px;
}
```

---

## 5. Sombras

### Sistema de Elevação

| Nível | CSS | Uso |
|-------|-----|-----|
| **Nível 0** | none | Elementos inline |
| **Nível 1** | shadow-sm | Cards, dropdowns |
| **Nível 2** | shadow | Cards elevados, popovers |
| **Nível 3** | shadow-md | Modais, overlays |
| **Nível 4** | shadow-lg | Elementos flutuantes |

**Valores CSS:**
```css
--shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
--shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
--shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
--shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
```

---

## 6. Espaçamentos

### Sistema de Espaçamento (Base 4px)

| Token | Valor | Uso |
|-------|-------|-----|
| space-1 | 4px | Gaps mínimos |
| space-2 | 8px | Gaps internos pequenos |
| space-3 | 12px | Padding de elementos |
| space-4 | 16px | Padding de cards |
| space-5 | 20px | Gaps entre seções |
| space-6 | 24px | Padding de modais |
| space-8 | 32px | Gaps maiores |
| space-10 | 40px | Separação de seções |

### Paddings Padrão

| Componente | Padding |
|------------|---------|
| Card | 16px (p-4) |
| Card pequeno | 12px (p-3) |
| Modal header/body | 24px (p-6) |
| Botão | 10px 16px (py-2.5 px-4) |
| Botão pequeno | 8px 12px (py-2 px-3) |
| Input | 10px 12px (py-2.5 px-3) |
| Badge | 4px 10px (py-1 px-2.5) |
| Tabela th/td | 12-16px |

### Gaps Padrão

| Contexto | Gap |
|----------|-----|
| Entre cards | 16px (gap-4) |
| Entre itens de lista | 8px (gap-2) |
| Entre elementos inline | 8px (gap-2) |
| Entre seções | 24px (gap-6) |
| Grid de dashboard | 16-24px (gap-4 a gap-6) |

---

## 7. Bordas e Arredondamentos

### Arredondamentos

| Componente | Raio | Tailwind |
|------------|------|----------|
| Botões | 8px | rounded-lg |
| Inputs | 8px | rounded-lg |
| Cards | 12px | rounded-xl |
| Modais | 16px | rounded-2xl |
| Badges/Pills | 9999px | rounded-full |
| Avatares | 9999px | rounded-full |
| Imagens | 8px | rounded-lg |

### Bordas (Uso Mínimo!)

**REGRA GERAL:** Evitar bordas. Usar sombras.

**Exceções permitidas:**

| Elemento | Borda | Quando Usar |
|----------|-------|-------------|
| Inputs | 1px gray-200 | Sempre (acessibilidade) |
| Divisores | 1px gray-200 | Separar seções dentro de cards |
| Tabela header | 1px bottom gray-200 | Separar header do body |
| Borda de categoria | 2-3px left cor-categoria | Indicar categoria em cards |

---

## 8. Ícones

### Tamanhos

| Contexto | Tamanho | Tailwind |
|----------|---------|----------|
| Inline com texto | 16px | w-4 h-4 |
| Em botões | 16px | w-4 h-4 |
| Em cards | 20px | w-5 h-5 |
| Destaque/Header | 24px | w-6 h-6 |
| Hero/Grande | 32px | w-8 h-8 |

### Cores

- Ícones informativos: gray-500 (#6B7280)
- Ícones em textos: herdam cor do texto
- Ícones de categoria: cor da categoria
- Ícones em botões: herdam cor do botão

---

## 9. Dark Mode

### Cores Dark Mode

| Elemento | Light | Dark |
|----------|-------|------|
| Background principal | #FFFFFF | #0F1113 |
| Background secundário | #F9FAFB | #1A1D1F |
| Background terciário | #F3F4F6 | #2D3748 |
| Texto principal | #111827 | #F9FAFB |
| Texto secundário | #374151 | #D1D5DB |
| Texto terciário | #6B7280 | #9CA3AF |
| Bordas/Divisores | #E5E7EB | #374151 |
| Cards | #FFFFFF | #1F2937 |

### Cores de Categoria (Dark Mode)

As cores de categoria mantêm os mesmos valores principais, apenas ajustando opacidade dos fundos:

| Categoria | Fundo Light | Fundo Dark |
|-----------|-------------|------------|
| Cyan | #A8CED5/20% | #60BED1/20% |
| Verde | #A8D5B7/20% | #5DA47A/20% |
| Laranja | #D5BFA8/20% | #D19960/20% |
| Roxo | #BFA8D5/20% | #9860D1/20% |
| Magenta | #D5A8C6/20% | #D160AB/20% |

---

## 10. Padrões de Uso por Contexto

### 10.1 Dashboards

```
Fundo: gray-50 (#F9FAFB)
Cards: white com shadow-sm
Métricas: cores de categoria como destaque
Gráficos: paleta de categoria completa
Textos: hierarquia padrão
```

### 10.2 Kanban/Listas

```
Fundo: white ou gray-50
Colunas: white com shadow-sm
Cards: white com shadow-sm, hover shadow
Badges: cores de status
Interações: hover com gray-50
```

### 10.3 Tabelas

```
Header: gray-50, texto gray-500 uppercase
Rows: white, hover gray-50
Dividers: gray-100 sutil
Badges: cores de status inline
```

### 10.4 Formulários

```
Labels: gray-700, font-medium
Inputs: white, borda gray-200, focus cyan
Helpers: gray-500, text-xs
Erros: red-500 para texto e borda
```

### 10.5 Modais

```
Overlay: black/50%
Container: white, shadow-lg, rounded-2xl
Header: título em gray-900
Footer: gray-50 para área de ações
```

---

## 11. Proibições Globais

### NUNCA Fazer:

1. ❌ Usar gradientes em qualquer elemento
2. ❌ Usar bordas de contorno em cards/botões (exceto inputs)
3. ❌ Usar text-gray-400 ou text-gray-500 para textos legíveis
4. ❌ Usar cores fora da paleta oficial
5. ❌ Usar sombras coloridas
6. ❌ Usar mais de 2 cores de destaque por tela
7. ❌ Usar fontes diferentes de Source Serif 4 e Open Sans
8. ❌ Usar font-weight abaixo de 400

### SEMPRE Fazer:

1. ✅ Usar shadow-sm para definir cards
2. ✅ Usar font-serif para títulos
3. ✅ Manter 90% monocromático, 10% cores
4. ✅ Usar cores apenas com propósito semântico
5. ✅ Manter contraste AA mínimo
6. ✅ Usar a hierarquia tipográfica definida

---

## 12. Checklist de Implementação

Ao criar um novo componente, verificar:

- [ ] Título usa font-serif (Source Serif 4)?
- [ ] Textos usam cores permitidas (gray-600 ou mais escuro)?
- [ ] Cards usam shadow-sm sem bordas?
- [ ] Botões seguem o padrão de variantes?
- [ ] Cores de acento têm propósito semântico?
- [ ] Gradientes foram evitados?
- [ ] Espaçamentos seguem o sistema de 4px?
- [ ] Dark mode foi considerado?

---

## 13. Tokens CSS

### Variáveis Recomendadas

```css
:root {
  /* Cores de Categoria */
  --lia-cyan: #60BED1;
  --lia-cyan-light: #A8CED5;
  --lia-cyan-hover: #4DA8BB;
  
  --lia-green: #5DA47A;
  --lia-green-light: #A8D5B7;
  --lia-green-hover: #4A8A68;
  
  --lia-orange: #D19960;
  --lia-orange-light: #D5BFA8;
  --lia-orange-hover: #BF8554;
  
  --lia-purple: #9860D1;
  --lia-purple-light: #BFA8D5;
  --lia-purple-hover: #8652B8;
  
  --lia-magenta: #D160AB;
  --lia-magenta-light: #D5A8C6;
  --lia-magenta-hover: #B84D95;
  
  /* Cor da Marca */
  --lia-coral: #C74446;
  --lia-coral-hover: #B23B3D;
  --lia-coral-light: #FEF2F2;
  
  /* Status */
  --lia-success: #5DA47A;
  --lia-warning: #E5A853;
  --lia-error: #C74446;
  --lia-info: #60BED1;
  
  /* Sombras */
  --lia-shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --lia-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
  --lia-shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
  --lia-shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
}
```

---

## 14. Referências Visuais

### Páginas de Referência (Bom Exemplo)
- Job Kanban Page: estilo minimalista, cards limpos
- Candidates Page: tabela bem estruturada
- Dashboards Page: uso correto de cores em métricas

### Padrão ElevenLabs
- Interface monocromática sofisticada
- Cores pastéis apenas como backgrounds de categoria
- Tipografia clara e hierárquica
- Espaçamento generoso

---

*Este documento é a fonte de verdade para todo o design da plataforma LIA.*
*Última atualização: 5 de Dezembro de 2025*
