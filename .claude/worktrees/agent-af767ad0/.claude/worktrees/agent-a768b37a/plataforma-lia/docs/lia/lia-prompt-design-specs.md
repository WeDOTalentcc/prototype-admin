# Especificações de Design - Prompt LIA

Documento de referência para padronização do Prompt LIA em todas as páginas da plataforma.

## Visão Geral

O Prompt LIA segue o padrão visual WedoTalent ElevenLabs com paleta monocromática (90%) e accent cyan (#60BED1).

---

## 1. Prompt Compacto (Colapsado)

### Container Principal
```css
max-width: 300px;
height: 40px; /* h-10 */
border-radius: 12px; /* rounded-xl */
background: #FFFFFF;
border: 1px solid #E5E7EB;
padding-left: 16px; /* pl-4 */
padding-right: 80px; /* pr-20 */
```

### Estado Focus
```css
border-color: #60BED1;
box-shadow: 0 0 0 2px rgba(96, 190, 209, 0.12);
```

### Input
```css
font-family: "Open Sans", sans-serif;
font-size: 13px;
color: #1a1a1a;
```

### Placeholder
```css
color: #4B5563; /* text-gray-600 */
```

### Ícones (Maximize2, Send)
```css
width: 16px;
height: 16px;
color: #60BED1;
```

---

## 2. Prompt Expandido (Sidebar)

### Container Card
```css
border: 1px solid #60BED1;
background: #FFFFFF;
min-height: calc(100vh - 180px);
border-radius: 8px;
overflow: hidden;
display: flex;
flex-direction: column;
```

### Largura
- **Modo Criação de Vaga**: 60% (max 900px)
- **Modo Geral**: Variável (controlado por estado)

---

## 3. Header do Prompt Expandido

### Container
```css
padding: 12px 16px; /* px-4 py-3 */
background: #FFFFFF;
flex-shrink: 0;
```

### Ícone LIA (Brain)
```css
width: 24px;
height: 24px;
color: #60BED1;
stroke-width: 2.5;
```

### Container do Ícone
```css
width: 40px;
height: 40px;
border-radius: 8px; /* rounded-lg */
background: #FFFFFF;
display: flex;
align-items: center;
justify-content: center;
```

### Título
```css
font-family: "Open Sans", sans-serif;
font-size: 14px;
font-weight: 600; /* semibold */
color: #030712; /* text-gray-950 */
line-height: tight;
```
**Texto**: "Olá! Sou a Lia."

### Subtítulo
```css
font-family: "Open Sans", sans-serif;
font-size: 11px;
color: #6B7280; /* text-gray-500 */
line-height: tight;
margin-top: 2px;
```
**Texto**: "Como posso te ajudar hoje?"

### Botões do Header (Maximize, Close)
```css
width: 28px;
height: 28px;
border-radius: 9999px; /* rounded-full */
background: transparent;
transition: background 150ms;
```
```css
/* Hover */
background: #F3F4F6; /* hover:bg-gray-100 */
```

### Ícones dos Botões Header
```css
width: 16px;
height: 16px;
color: #6B7280; /* text-gray-500 */
```

---

## 4. Área de Mensagens do Chat

### Container
```css
flex: 1;
overflow-y: auto;
padding: 8px 12px; /* px-3 py-2 */
display: flex;
flex-direction: column;
gap: 12px; /* space-y-3 */
```

### Mensagem do Usuário

#### Layout
```css
display: flex;
justify-content: flex-end;
```

#### Container Interno
```css
display: flex;
align-items: flex-start;
gap: 8px;
max-width: 90%;
```

#### Avatar
```css
width: 24px;
height: 24px;
border-radius: 9999px;
object-fit: cover;
flex-shrink: 0;
```

#### Balão da Mensagem
```css
padding: 8px 10px; /* px-2.5 py-2 */
border-radius: 12px; /* rounded-xl */
background: #F3F4F6; /* bg-gray-100 */
font-family: "Open Sans", sans-serif;
```

#### Texto
```css
font-size: 11px;
color: #1F2937; /* text-gray-800 */
line-height: 1.625; /* leading-relaxed */
```

### Mensagem da LIA

#### Layout
```css
display: flex;
justify-content: flex-start;
```

#### Container
```css
max-width: 90%;
font-family: "Source Serif 4", Georgia, serif;
```

#### Ícone Brain
```css
width: 16px;
height: 16px;
color: #60BED1;
stroke-width: 2.5;
```

#### Container do Ícone
```css
width: 24px;
height: 24px;
border-radius: 8px;
display: flex;
align-items: center;
justify-content: center;
flex-shrink: 0;
```

#### Label "LIA"
```css
font-family: Inter, sans-serif;
font-size: 10px;
font-weight: 700; /* bold */
color: #1F2937; /* text-gray-800 */
```

#### Texto da Mensagem
```css
font-family: "Source Serif 4", Georgia, serif;
font-size: 11px;
color: #1F2937; /* text-gray-800 */
line-height: 1.625; /* leading-relaxed */
```

#### Formatação de Texto
- `**texto**` → `<strong>texto</strong>`
- Linhas com `•` → padding-left: 8px
- Linhas com `1.`, `2.` → padding-left: 8px

### Estado de Loading

#### Container
```css
display: inline-flex;
align-items: center;
gap: 8px;
padding: 8px 12px; /* px-3 py-2 */
border-radius: 12px;
background: rgba(96, 190, 209, 0.1); /* bg-[#60BED1]/10 */
```

#### Ícone Loader
```css
width: 12px;
height: 12px;
color: #60BED1;
animation: spin 1s linear infinite;
```

#### Texto
```css
font-size: 10px;
color: #6B7280; /* text-gray-500 */
```
**Texto**: "Pensando..."

---

## 5. Input Area (Inferior)

### Container
```css
flex-shrink: 0;
padding: 8px 16px 16px 16px; /* px-4 pb-4 pt-2 */
```

### Container do Input
```css
display: flex;
align-items: center;
gap: 8px;
padding: 8px;
border-radius: 8px;
background: #FFFFFF;
border: 1px solid #E4EBEF;
```

### Input de Texto
```css
flex: 1;
font-family: "Open Sans", sans-serif;
font-size: 12px; /* text-xs */
background: transparent;
color: #030712; /* text-gray-950 */
outline: none;
```

### Placeholder
```css
color: #6B7280;
```
**Texto**: "Envie mensagem para a LIA..."

### Botão de Áudio
```css
width: 28px;
height: 28px;
border-radius: 8px;
display: flex;
align-items: center;
justify-content: center;
```
```css
/* Hover */
background: #F3F4F6;
```

### Botão Enviar
```css
width: 28px;
height: 28px;
border-radius: 8px;
background: #60BED1;
display: flex;
align-items: center;
justify-content: center;
flex-shrink: 0;
```
```css
/* Disabled */
opacity: 0.5;
```

### Ícone Send
```css
width: 14px;
height: 14px;
color: #FFFFFF;
```

---

## 6. Abas (Pills)

### Container
```css
display: flex;
align-items: center;
gap: 6px; /* gap-1.5 */
margin-top: 8px;
```

### Botão Aba Ativa
```css
padding: 4px 10px; /* px-2.5 py-1 */
border-radius: 9999px; /* rounded-full */
font-family: "Open Sans", sans-serif;
font-size: 11px;
font-weight: 500; /* medium */
background: #60BED1;
color: #FFFFFF;
transition: all 150ms;
```

### Botão Aba Inativa
```css
padding: 4px 10px;
border-radius: 9999px;
font-family: "Open Sans", sans-serif;
font-size: 11px;
font-weight: 500;
background: #F3F4F6;
color: #374151;
transition: all 150ms;
```
```css
/* Hover */
background: #E5E7EB;
```

### Ícones das Abas
```css
width: 10px;
height: 10px; /* w-2.5 h-2.5 */
```

### Abas Disponíveis
1. ✨ **IA Natural** (Sparkles icon)
2. 📄 **Job Description** (FileText icon)
3. 🎯 **Templates** (Target icon)

---

## 7. Sugestões (Tags de Ação Rápida)

### Container
```css
display: flex;
align-items: center;
gap: 6px; /* gap-1.5 */
margin-top: 6px;
```

### Label "Sugestões:"
```css
font-family: "Open Sans", sans-serif;
font-size: 9px;
font-weight: 500; /* medium */
color: #6B7280;
```

### Botão Tag
```css
display: inline-flex;
align-items: center;
gap: 4px;
padding: 2px 8px; /* px-2 py-0.5 */
font-family: "Open Sans", sans-serif;
font-size: 9px;
font-weight: 500;
color: #374151;
background: #F3F4F6;
border-radius: 9999px;
transition: all 150ms;
```
```css
/* Hover */
background: #E5E7EB;
```

### Ícones das Tags
```css
width: 10px;
height: 10px;
color: #6B7280;
```

---

## 8. Indicador de Seleção

### Container
```css
padding: 8px 12px; /* px-3 py-2 */
border-radius: 8px;
background: rgba(96, 190, 209, 0.1);
border: 1px solid rgba(96, 190, 209, 0.2);
display: flex;
align-items: center;
gap: 8px;
```

### Ícone (Briefcase)
```css
width: 14px;
height: 14px;
color: #60BED1;
flex-shrink: 0;
```

### Texto
```css
font-size: 12px; /* text-xs */
font-weight: 500; /* medium */
color: #60BED1;
```
**Formato**: "{n} vaga(s) selecionada(s)"

---

## Paleta de Cores

| Uso | Cor | Tailwind |
|-----|-----|----------|
| Accent Principal | `#60BED1` | `text-[#60BED1]` |
| Accent Background 10% | `rgba(96, 190, 209, 0.1)` | `bg-[#60BED1]/10` |
| Accent Background 5% | `rgba(96, 190, 209, 0.05)` | `bg-[#60BED1]/5` |
| Accent Border 20% | `rgba(96, 190, 209, 0.2)` | `border-[#60BED1]/20` |
| Border Padrão | `#E5E7EB` | `border-gray-200` |
| Border Input | `#E4EBEF` | - |
| Background Branco | `#FFFFFF` | `bg-white` |
| Background Cinza Claro | `#F3F4F6` | `bg-gray-100` |
| Background Hover | `#E5E7EB` | `bg-gray-200` |
| Texto Principal | `#030712` | `text-gray-950` |
| Texto Secundário | `#1F2937` | `text-gray-800` |
| Texto Terciário | `#6B7280` | `text-gray-500` |
| Texto Quaternário | `#374151` | `text-gray-700` |

---

## Tipografia

| Elemento | Fonte | Tamanho | Peso |
|----------|-------|---------|------|
| Título Header | Open Sans | 14px | 600 (semibold) |
| Subtítulo Header | Open Sans | 11px | 400 (normal) |
| Texto Chat LIA | Source Serif 4 | 11px | 400 |
| Label "LIA" | Inter | 10px | 700 (bold) |
| Texto Chat Usuário | Open Sans | 11px | 400 |
| Input Compacto | Open Sans | 13px | 400 |
| Input Expandido | Open Sans | 12px | 400 |
| Botões/Tags | Open Sans | 9-11px | 500 (medium) |
| Loading | - | 10px | 400 |

---

## Comportamento

### Transições
- **Duração padrão**: 150ms / 300ms
- **Easing**: ease (default)
- **Propriedades animadas**: background, color, border-color, box-shadow, opacity

### Responsividade
- Prompt compacto: max-width 300px
- Prompt expandido: 60% width (max 900px) em modo criação
- Layout flexível com sidebar colapsável

### Persistência
- Mensagens do chat são mantidas em estado durante a sessão
- Scroll automático para última mensagem
- Estado de loading com spinner animado

### Acessibilidade
- Focus states visíveis com borda cyan
- Placeholders descritivos
- Botões com título/tooltip

---

## Classes Tailwind de Referência

```jsx
// Container Card Expandido
className="h-full flex flex-col overflow-hidden"
style={{ border: '1px solid #60BED1', backgroundColor: '#FFFFFF' }}

// Header
className="flex-shrink-0 px-4 py-3"
style={{ backgroundColor: '#FFFFFF' }}

// Ícone LIA
<Brain className="w-6 h-6" style={{ color: '#60BED1' }} strokeWidth={2.5} />

// Título
className="text-[14px] font-semibold leading-tight truncate text-gray-950"
style={{ fontFamily: 'Open Sans, sans-serif' }}

// Mensagem LIA
className="text-[11px] text-gray-800 leading-relaxed"
style={{ fontFamily: '"Source Serif 4", Georgia, serif' }}

// Input Container
className="flex items-center gap-2 p-2 rounded-lg border bg-white"
style={{ borderColor: '#E4EBEF' }}

// Botão Enviar
className="flex-shrink-0 w-7 h-7 rounded-lg flex items-center justify-center"
style={{ backgroundColor: '#60BED1' }}

// Aba Ativa
className="px-2.5 py-1 rounded-full text-[11px] font-medium text-white bg-[#60BED1]"

// Aba Inativa
className="px-2.5 py-1 rounded-full text-[11px] font-medium text-[#374151] bg-[#F3F4F6] hover:bg-[#E5E7EB]"

// Tag Sugestão
className="inline-flex items-center gap-1 px-2 py-0.5 text-[9px] font-medium text-[#374151] bg-[#F3F4F6] rounded-full hover:bg-[#E5E7EB]"
```

---

## Uso

Este documento serve como referência para implementar o Prompt LIA de forma consistente em:

1. **Página de Gestão de Vagas** (jobs-page.tsx) ✅
2. **Página Kanban da Vaga** (job-kanban-page.tsx)
3. **Página Tabela de Candidatos na Vaga** (job-kanban-page.tsx - viewMode table)
4. **Funil de Talentos** (candidates-page.tsx)
5. **Outras páginas com interação LIA**

Mantenha consistência visual seguindo estas especificações.
