# Backup de Tabs para Recuperação Futura - MVP Otimização

**Data de Criação:** Janeiro 2026  
**Objetivo:** Documentar tabs removidas para otimização do MVP, permitindo reconstrução futura  
**Arquivo de Origem:** `plataforma-lia/src/components/pages/jobs-page.tsx`

---

## Índice
1. [Tab Roteiro de Triagem](#1-tab-roteiro-de-triagem)
2. [Tab Métricas LIA](#2-tab-métricas-lia)
3. [Tab Pipeline/Funil & Analytics](#3-tab-pipelinefunil--analytics)
4. [Modal Tutorial WSI](#4-modal-tutorial-wsi)
5. [Modal de Edição de Roteiro](#5-modal-de-edição-de-roteiro)
6. [Constantes e Funções Auxiliares](#6-constantes-e-funções-auxiliares)
7. [States Necessários](#7-states-necessários)

---

## 1. Tab Roteiro de Triagem

### 1.1 Condição de Ativação
```tsx
{activePreviewTab === 'screening-script' && (
```

### 1.2 Estrutura Visual

#### Header
- Ícone: `ClipboardList` (cor #60BED1)
- Título: "Roteiro de Triagem Automática"
- Badge de Status: Ativo (#A8D5B7) ou Pausado (#D5BFA8)
- Botões:
  - "Como funciona?" → abre `showWSITutorialModal`
  - "Editar Roteiro" → abre `showQuestionEditModal`

#### Card Performance da Triagem
```
Linha 1 (4 colunas):
- Tempo Total: soma de (q.time_limit || 120) / 60 min
- Perguntas: screeningQuestions.length
- Reprovação Est.: ~{100 - min_score}%
- Atualizado: data da última atualização

Linha 2 (4 colunas):
- Triados: funnel.screening * 0.6
- Conclusão: (funnel.screening / funnel.total) * 100%
- Aprovação: (funnel.interview / funnel.screening) * 100%
- Nota Média: nps / 20 ou '4.2'
```

#### Card Skills WSI Avaliadas
- Ícone: `Sparkles`
- Skills vindas de `screeningConfig.wsi_skills` ou `behavioralCompetencies`
- Default: ['Comunicação', 'Resolução de Problemas', 'Adaptabilidade', 'Trabalho em Equipe']
- Nota: "Extraídas automaticamente do perfil da vaga via metodologia WSI"

#### 6 Blocos WSI (Accordion)
Usa constante `WSI_BLOCKS` com 6 blocos:

| ID | Nome | Duração | Editável | Tipo |
|----|------|---------|----------|------|
| 0 | Abordagem Inicial | < 1 min | Não | template |
| 1 | Apresentação da Oportunidade | 3 min | Não | presentation |
| 2 | Fit Básico e Elegibilidade | 2 min | Sim | eliminatory |
| 3 | Avaliação Técnica | 5 min | Sim | technical |
| 4 | Análise Situacional e Fit | 4 min | Sim | situational |
| 5 | Resultado e Encerramento | 3 min | Sim | result |

**Lógica de Classificação de Perguntas:**
```typescript
const isBlock2 = (q: any) => {
  if (typ(q) === 'eliminatory' || q.required) return true
  if (cat(q).includes('elegib') || cat(q).includes('elimin')) return true
  if (cat(q).includes('fit') && cat(q).includes('básico')) return true
  if (cat(q).includes('disponib') || cat(q).includes('eligib')) return true
  return false
}

const isBlock3 = (q: any) => {
  if (isBlock2(q)) return false
  return cat(q).includes('tecn') || cat(q).includes('tech') ||
    cat(q).includes('skill') || cat(q).includes('técnica') ||
    typ(q).includes('tech')
}

const isBlock4 = (q: any) => {
  if (isBlock2(q) || isBlock3(q)) return false
  return true // fallback
}
```

**Renderização de Blocos:**
- Blocos não editáveis (0, 1, 5): mostram `WSI_AUTOMATIC_MESSAGES` formatadas
- Blocos editáveis (2, 3, 4): mostram perguntas com badges de categoria

**Badges de Perguntas:**
- Eliminatória: `bg-red-50 text-red-600 border-red-200`
- Técnica: `bg-blue-100 text-blue-700 border-blue-200`
- Comportamental: `bg-purple-100 text-purple-700 border-purple-200`
- Geral: `bg-green-100 text-green-700 border-green-200`

#### Card Canais e Configurações
```
Canais em linha:
- WhatsApp (indicador verde)
- OpenMic.ai (indicador verde)
- Deepgram (indicador verde)

Configurações (2x2 grid):
- Idioma: Português
- Score Mínimo: min_score ?? 70%
- Timeout: 120s
- Retentativas: 3
```

#### Card Agendamento Automático
```
Status Badge: Ativo/Inativo

Configurações (2x2 grid):
- Score Mínimo: scheduling.min_score_for_auto ?? 75%
- Calendário: scheduling.calendar_provider || 'Microsoft'
- Horários: scheduling.available_hours || '9h-18h'
- Duração: scheduling.interview_duration_min ?? 45min
```

#### Card Insights LIA
```
Lista de insights:
• Triagens 6.5x mais rápidas que processo manual
• Economia estimada: R$ {horasEconomizadas * 80} em custos
• Taxa de aprovação 8% acima da média do setor
```

---

## 2. Tab Métricas LIA

### 2.1 Condição de Ativação
```tsx
{activePreviewTab === 'lia-metrics' && (
```

### 2.2 Estrutura Visual

#### Header com Resumo
- Ícone: `Sparkles`
- Título: "Performance LIA - Triagens Automatizadas"
- Descrição: "Análise detalhada do impacto da inteligência artificial no processo de triagem desta vaga"

#### Grid 2x2 de Métricas Principais

**Horas Economizadas:**
```typescript
const triagens = Math.round(previewJob.funnel.total * 0.85)
const horasEconomizadas = Math.round((triagens * 15) / 60) // 15 min por triagem
// Exibe: {horasEconomizadas}h
// Subtexto: ≈ {horasEconomizadas / 8} dias de trabalho
```

**ROI da LIA:**
```typescript
const custoHora = 80 // R$ por hora do recrutador
const economia = horasEconomizadas * custoHora
const roi = Math.round((economia / 1000) * 10) / 10
// Exibe: {roi}x
// Subtexto: R$ {economia} economizados
```

**Tempo Médio/Triagem:**
- Valor fixo: 2.3min
- Subtexto: vs 15min manual

**Taxa de Conclusão:**
```typescript
const realizadas = Math.round(funnel.screening * 0.6)
const agendadas = Math.round(funnel.screening * 0.7)
// Exibe: {(realizadas / agendadas) * 100}%
// Subtexto: {realizadas} de {agendadas} agendadas
```

#### Funil LIA Detalhado
Barras de progresso com 4 estágios:
1. **Contatados**: funnel.total * 0.85 (100%)
2. **Agendadas**: funnel.screening * 0.7
3. **Realizadas**: funnel.screening * 0.6
4. **Aprovados**: funnel.interview * 0.8

#### Média de Notas por Critério
```typescript
const criterios = [
  { criterio: 'Experiência Técnica', nota: 8.2, cor: 'bg-gray-600' },
  { criterio: 'Fit Cultural', nota: 7.8, cor: 'bg-gray-500' },
  { criterio: 'Comunicação', nota: 8.5, cor: 'bg-gray-700' },
  { criterio: 'Disponibilidade', nota: 9.1, cor: 'bg-gray-900' },
  { criterio: 'Expectativa Salarial', nota: 6.9, cor: 'bg-gray-400' }
]
```

#### Comparação com Outras Vagas
Grid 3 colunas:
- Média de Notas: 8.1 (+12% vs média)
- Taxa Aprovação: calculado (+8% vs média)
- Qualidade: A+ (Top 10%)

#### Taxa de Desistência
Grid 2 colunas:
- Não Responderam: funnel.total * 0.15 (15% do total)
- Cancelaram: funnel.screening * 0.1 (10% agendados)

#### Insights da LIA
```
• Triagens 6.5x mais rápidas que processo manual
• Economia de R$ {horasEconomizadas * 80} em custos de recrutamento
• Taxa de aprovação 8% acima da média geral
• Candidatos com fit cultural 12% superior
```

---

## 3. Tab Pipeline/Funil & Analytics

### 3.1 Condição de Ativação
```tsx
{activePreviewTab === 'pipeline' && (
```

### 3.2 Estrutura Visual

#### Grid 2x2 de Métricas Preditivas Principais

**Score de Sucesso:**
```typescript
// Lógica:
const score = funnel.total > 20 ? '85%' : funnel.total > 10 ? '60%' : '35%'
// Subtexto: Pipeline: {funnel.total} candidatos
```

**Time to Fill:**
```typescript
// Lógica:
const days = urgencyLevel > 3 ? '15' : urgencyLevel > 2 ? '25' : '35'
// Subtexto: Velocidade: {funnel.interview > 0 ? '3.2' : '1.5'} cv/dia
```

**Qualidade Pipeline:**
```typescript
// Lógica:
const grade = funnel.final > 3 ? 'A+' : funnel.interview > 5 ? 'B+' : 'C'
// Subtexto: Conversão: {(funnel.interview / funnel.total) * 100}%
```

**Risco de Recusa (card vermelho):**
```typescript
// Lógica:
const risk = level === 'Sênior' ? '45%' : level === 'Pleno' ? '25%' : '15%'
// Subtexto: Gap salarial: {level === 'Sênior' ? '±18%' : '±8%'}
```

#### Funil de Recrutamento Visual
Barras de progresso com 5 estágios:
1. **Total**: funnel.total (100%)
2. **Triagem**: funnel.screening
3. **Entrevistas**: funnel.interview
4. **Finalistas**: funnel.final
5. **Contratados**: funnel.hired

#### Métricas de Conversão
Grid 2x2:
- CV → Triagem: (funnel.screening / funnel.total) * 100%
- Triagem → Entrevista: (funnel.interview / funnel.screening) * 100%
- Entrevista → Final: (funnel.final / funnel.interview) * 100%
- Final → Contratação: (funnel.hired / funnel.final) * 100%

#### Insights da LIA (Condicionais)
```typescript
// Exibe condicionalmente:
if (funnel.total < 10) "• Pipeline baixo: Ampliar divulgação ou revisar requisitos"
if (level === 'Sênior') "• Alto risco de recusa: Prepare margem de negociação de 15-20%"
if (funnel.screening > funnel.interview * 3) "• Gargalo em entrevistas: Agilize agendamentos"
if (urgencyLevel > 3 && funnel.total < 20) "• Urgência vs Pipeline: Ative sourcing ativo e headhunting"
```

#### Comparativo com Mercado
Grid 3 colunas:
- Salário: +15% ou -5% vs mercado (baseado em salary > 'R$ 10.000')
- Candidatos: +45% ou -20% vs média (baseado em funnel.total > 30)
- Atratividade: ranking aleatório 1-10

#### KPIs e Orçamento
Grid 2x2:
- NPS: previewJob.nps
- Urgência: indicador de barras (1-5)
- Budget: R$ (budget / 1000)k
- Usado: (budgetUsed / budget) * 100%

#### Fatores de Risco
3 indicadores de barras:
- Competitividade salarial: baseado em level
- Escassez de talentos: baseado em level
- Tempo de processo: baseado em urgencyLevel

#### Canais de Divulgação
Lista de canais com status:
- LinkedIn (ícone Linkedin)
- Site (ícone Globe)
- Indeed (ícone Briefcase)

Status: "Publicado" (bg-gray-100 text-gray-800) ou "Não publicado" (bg-gray-100 text-gray-600)

---

## 4. Modal Tutorial WSI

### 5.1 State de Controle
```typescript
const [showWSITutorialModal, setShowWSITutorialModal] = useState(false)
```

### 4.2 Condição de Ativação
```tsx
{showWSITutorialModal && (
```

### 4.3 Estrutura do Modal

**Dimensões:** max-w-3xl, max-h-[85vh]

#### Header
- Ícone: `GraduationCap` em fundo #60BED1/10
- Título: "Tutorial: Metodologia WSI"
- Badge: "WeDoTalent Skill Index"
- Botão X para fechar

#### Seção 1: O que é WSI?
```
WeDoTalent Skill Index é um índice conversacional proprietário que combina 
IA com psicometria para validar competências técnicas, comportamentais e 
fit cultural em triagens de 5-10 minutos.
```

#### Seção 2: Base Teórica (4 Modelos Científicos)
Grid 2x2 com cards:

| Badge | Autor/Ano | Descrição |
|-------|-----------|-----------|
| CBI | McClelland, 1973 | Competency-Based Interviewing - perguntas situacionais baseadas em comportamentos passados |
| Bloom | Anderson et al., 2001 | Taxonomia de níveis cognitivos (Lembrar → Criar) |
| Dreyfus | 1980 | Estágios de domínio de habilidade (1-5: Novice → Expert) |
| Big Five | 1992 | Traços comportamentais para fit cultural |

#### Seção 3: Versões do WSI (Tabela)
| Modelo | Perguntas | Tempo | Indicado Para |
|--------|-----------|-------|---------------|
| WSI Compact | 6-8 | 5-7 min | Triagens rápidas, alto volume |
| WSI Compact+ | 8-10 | 7-9 min | Vagas críticas, tech leads, gestão |

#### Seção 4: 6 Blocos da Triagem
Lista com círculos numerados:
- 0: Abordagem Inicial WhatsApp (<1min) [automático]
- 1: Apresentação da Oportunidade (3min) [automático]
- 2: Fit Básico e Elegibilidade (2min) [editável]
- 3: Avaliação Técnica (5min) [editável]
- 4: Análise Situacional (4min) [editável]
- 5: Resultado e Encerramento (3min) [automático]

#### Seção 5: Tipos de Validação
Grid 2x2:
- 📝 Autodeclaração: Base inicial de domínio
- 🎯 Contexto real: Aplicação prática
- 🧪 Microteste: Raciocínio técnico
- 🎭 Situação contextual: Fit comportamental

#### Seção 6: Distribuição e Classificações
```
Distribuição de Perguntas:
- 70% técnicas (barra #60BED1)
- 30% comportamentais (barra purple-400)

Fórmula: WSI = Σ(Peso × Score) / 100

Thresholds:
- ≥ 4.2: Aprovado automático (verde)
- 3.8-4.1: Revisão humana (amarelo)
- < 3.8: Reprovado (vermelho)
```

#### Nota de Calibração
```
Calibração Dinâmica:
Após 50 triagens, a LIA recalibra os cortes por percentil histórico. 
Saturação automática ao atingir 20 aprovados por vaga.
```

#### Footer
- Texto: "Metodologia proprietária WeDoTalent • Baseada em 4 modelos científicos validados"
- Botão "Entendi" (bg-[#60BED1])

---

## 4. Modal de Edição de Roteiro

### 5.1 State de Controle
```typescript
const [showQuestionEditModal, setShowQuestionEditModal] = useState(false)
const [editingQuestion, setEditingQuestion] = useState<any>(null)
const [questionPrompt, setQuestionPrompt] = useState("")
const [suggestedQuestion, setSuggestedQuestion] = useState<any>(null)
const [selectedBlock, setSelectedBlock] = useState<number | null>(null)
```

### 5.2 Estrutura do Modal

**Dimensões:** max-w-4xl, max-h-[90vh]

#### Header
- Ícone: `ClipboardList`
- Título: "Roteiro WSI de Triagem"
- Badge de Status: Ativo/Pausado
- Botão X para fechar

#### Configurações do Roteiro
Grid 6 colunas com cards:
| Ícone | Label | Valor | Subtexto |
|-------|-------|-------|----------|
| MessageSquare | Canal | WhatsApp | mensageria |
| Clock | Duração | ~15 min | tempo total |
| RefreshCw | Tentativas | 3 | de contato |
| HelpCircle | Perguntas | {n} + 2 LIA | fixas + adaptativas |
| Mic | Formato | Texto/Áudio | resposta híbrida |
| Timer | Feedback | 24 horas | automático |

#### Aviso de Triagem em Andamento
Exibido se `funnel.screening * 0.6 > 0`:
```
⚠️ Triagem em andamento - edições estão bloqueadas para manter comparabilidade entre candidatos
```

#### Layout 2 Colunas

**Coluna Esquerda (60%):** Blocos WSI
- Accordion expandível com mesma lógica da tab
- Blocos não editáveis mostram `WSI_AUTOMATIC_MESSAGES`
- Blocos editáveis mostram perguntas com botões de edição

**Coluna Direita (40%):** Geração de Perguntas
- Textarea para prompt
- Botão de gerar pergunta
- Box "Metodologia WSI" (dica)
- Sugestões da LIA (3 exemplos fixos ou pergunta gerada)

---

## 5. Constantes e Funções Auxiliares

### 5.1 WSI_BLOCKS
```typescript
const WSI_BLOCKS = [
  { id: 0, name: 'Abordagem Inicial', description: 'Template WhatsApp pré-aprovado', duration: '< 1 min', editable: false, type: 'template' },
  { id: 1, name: 'Apresentação da Oportunidade', description: 'Pitch conversacional com detalhes da vaga', duration: '3 min', editable: false, type: 'presentation' },
  { id: 2, name: 'Fit Básico e Elegibilidade', description: 'Perguntas eliminatórias e informativas padrão', duration: '2 min', editable: true, type: 'eliminatory' },
  { id: 3, name: 'Avaliação Técnica', description: 'Skills com pesos e rubricas automáticas', duration: '5 min', editable: true, type: 'technical' },
  { id: 4, name: 'Análise Situacional e Fit', description: 'Perguntas situacionais com follow-ups', duration: '4 min', editable: true, type: 'situational' },
  { id: 5, name: 'Resultado e Encerramento', description: 'Índice WSI automático e feedback', duration: '3 min', editable: false, type: 'result' }
]
```

### 5.2 WSI_AUTOMATIC_MESSAGES
```typescript
const WSI_AUTOMATIC_MESSAGES: Record<number, { title: string; message: string; note: string }> = {
  0: {
    title: "Abordagem Inicial via WhatsApp",
    message: `Olá {candidato.nome}! 👋

Aqui é a LIA, assistente de recrutamento da {empresa.nome}.

Vi que você se candidatou para a vaga de {vaga.titulo} e gostaria de conversar sobre a oportunidade.

Podemos iniciar agora? Leva menos de 10 minutos! 🚀`,
    note: "Template pré-aprovado • Enviado automaticamente ao candidato"
  },
  1: {
    title: "Apresentação da Oportunidade",
    message: `Que ótimo ter você aqui! Deixa eu te contar um pouco sobre a vaga:

📋 **Posição:** {vaga.titulo}
🏢 **Empresa:** {empresa.nome}
📍 **Modelo:** {vaga.modelo_trabalho}
💰 **Faixa Salarial:** {vaga.faixa_salarial}

{vaga.descricao_resumida}

Agora vou fazer algumas perguntas rápidas para entender melhor seu perfil. Responda naturalmente, como se estivéssemos conversando! 💬`,
    note: "Pitch conversacional • Gerado a partir dos dados da vaga"
  },
  5: {
    title: "Resultado e Encerramento",
    message: `Muito obrigada pelas suas respostas, {candidato.nome}! 🙏

Analisei todas as informações e já encaminhei seu perfil para nossa equipe de recrutamento.

📊 **Próximos passos:**
• Você receberá um feedback em até {prazo_feedback}
• Se aprovado(a), entraremos em contato para agendar a entrevista

Qualquer dúvida, estou por aqui! Boa sorte! 🍀`,
    note: "Índice WSI calculado automaticamente • Feedback enviado conforme configuração"
  }
}
```

### 5.3 formatMessageWithVariables
```typescript
function formatMessageWithVariables(message: string): React.ReactNode[] {
  const parts = message.split(/(\{[^}]+\})/g)
  return parts.map((part, index) => {
    if (part.match(/^\{[^}]+\}$/)) {
      return (
        <span key={index} style={{ color: '#60BED1', fontWeight: 500 }}>
          {part}
        </span>
      )
    }
    if (part.includes('**')) {
      const boldParts = part.split(/(\*\*[^*]+\*\*)/g)
      return boldParts.map((bp, bpIndex) => {
        if (bp.match(/^\*\*[^*]+\*\*$/)) {
          return <strong key={`${index}-${bpIndex}`}>{bp.replace(/\*\*/g, '')}</strong>
        }
        return <span key={`${index}-${bpIndex}`}>{bp}</span>
      })
    }
    return <span key={index}>{part}</span>
  })
}
```

---

## 6. States Necessários

```typescript
// Tab de preview
const [activePreviewTab, setActivePreviewTab] = useState<string>('overview')

// Blocos expandidos
const [expandedBlocks, setExpandedBlocks] = useState<number[]>([2, 3]) // Blocos editáveis expandidos por padrão

// Modal de Tutorial WSI
const [showWSITutorialModal, setShowWSITutorialModal] = useState(false)

// Modal de Edição de Roteiro
const [showQuestionEditModal, setShowQuestionEditModal] = useState(false)
const [editingQuestion, setEditingQuestion] = useState<any>(null)
const [questionPrompt, setQuestionPrompt] = useState("")
const [suggestedQuestion, setSuggestedQuestion] = useState<{
  question: string
  type: 'eliminatory' | 'classificatory'
  options?: string[]
} | null>(null)
const [selectedBlock, setSelectedBlock] = useState<number | null>(null)
```

---

## 7. Ícones Utilizados (lucide-react)

```typescript
import {
  ClipboardList,
  BarChart3,
  Sparkles,
  Layers3,
  ChevronUp,
  ChevronDown,
  Plus,
  Edit,
  Settings,
  CalendarCheck,
  Lightbulb,
  MessageSquare,
  Clock,
  TrendingUp,
  CheckCircle,
  Star,
  AlertCircle,
  Zap,
  GraduationCap,
  BookOpen,
  Scale,
  X,
  Settings2,
  RefreshCw,
  HelpCircle,
  Mic,
  Timer,
  AlertTriangle,
  Brain,
  ArrowRight
} from 'lucide-react'
```

---

## 8. Design Tokens

```typescript
// Cor principal de destaque
const accentColor = '#60BED1'

// Cores de status
const statusActive = '#A8D5B7'  // verde menta
const statusPaused = '#D5BFA8'  // bege/sépia

// Tamanhos de fonte
// Títulos: text-[11px] ou text-[12px] font-semibold
// Corpo: text-[10px] ou text-[11px]
// Labels pequenos: text-[9px]
// Badges: text-[9px] ou text-[10px]

// Espaçamentos
// Cards: p-3 ou p-4
// Gaps: gap-2 ou gap-3
// Rounded: rounded-lg

// Fundos
// Cards: bg-white, bg-gray-50
// Hover: hover:bg-gray-100
// Destaque: bg-[#60BED1]/5, bg-[#60BED1]/10
```

---

## 9. Tipos de Dados

### 9.1 screeningConfig (do Job)
```typescript
interface ScreeningConfig {
  status?: {
    enabled: boolean
    last_updated?: string
  }
  settings?: {
    min_score?: number
  }
  wsi_skills?: string[]
  scheduling?: {
    auto_enabled?: boolean
    min_score_for_auto?: number
    calendar_provider?: string
    available_hours?: string
    interview_duration_min?: number
  }
}
```

### 9.2 screeningQuestions (do Job)
```typescript
interface ScreeningQuestion {
  id?: string
  question: string
  category?: 'technical' | 'behavioral' | 'cultural' | string
  type?: 'eliminatory' | 'classificatory'
  required?: boolean
  time_limit?: number
  options?: string[]
}
```

---

## 10. Notas de Implementação

1. **Bloqueio de edição:** Se `funnel.screening * 0.6 > 0`, desabilita edição para manter comparabilidade entre candidatos triados.

2. **Classificação automática:** Perguntas são classificadas automaticamente nos blocos 2, 3, 4 com base em `category` e `type`.

3. **Variáveis dinâmicas:** Templates usam variáveis como `{candidato.nome}`, `{vaga.titulo}` que são destacadas em #60BED1.

4. **Calibração WSI:** Após 50 triagens, cortes são recalibrados. Saturação automática ao atingir 20 aprovados.

5. **Integração com backend:** Perguntas vêm de `previewJob.screeningQuestions`, configurações de `previewJob.screeningConfig`.

---

**Documento gerado para backup de tabs removidas para otimização do MVP.**
**Use este arquivo para reconstruir as funcionalidades no futuro.**
