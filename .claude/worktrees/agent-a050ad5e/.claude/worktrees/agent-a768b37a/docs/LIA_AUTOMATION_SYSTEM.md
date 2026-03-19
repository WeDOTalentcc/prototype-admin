# Sistema de Automação LIA - Especificação Completa

## Visão Geral

O Sistema de Automação LIA é um conjunto de funcionalidades que automatizam e personalizam a comunicação com candidatos ao longo do processo de recrutamento, reduzindo o trabalho manual do recrutador enquanto melhora significativamente a experiência do candidato.

### Princípios Fundamentais

1. **LIA Sugere, Recrutador Confirma**: A LIA sempre gera sugestões inteligentes, mas o recrutador tem controle final
2. **Personalização Baseada em Dados**: Toda comunicação usa dados reais do candidato (scores, notas, pareceres)
3. **Ajuste Dinâmico**: Quando o recrutador altera um parâmetro (ex: sub-status), a LIA reajusta automaticamente o texto
4. **Templates Editáveis Apenas no CommunicationHub**: Os templates base são gerenciados centralmente; modais de envio fazem ajustes temporários

---

## Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                    CAMADA DE APRESENTAÇÃO                        │
├─────────────────────────────────────────────────────────────────┤
│  StageTransitionModal  │  BulkActionsModal  │  QuickActionsMenu │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MOTOR DE AUTOMAÇÃO LIA                        │
├─────────────────────────────────────────────────────────────────┤
│  ContextCollector  │  MessageGenerator  │  SubStatusPredictor   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CAMADA DE DADOS                               │
├─────────────────────────────────────────────────────────────────┤
│  CandidateContext  │  Templates  │  InterviewNotes  │  Scores   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Fluxo de Transição de Etapa

### 1. Trigger de Transição

O sistema é acionado quando:
- Candidato é arrastado no Kanban (drag and drop)
- Candidato é movido via tabela (InteractiveStageCell)
- Ação em lote é executada (bulk action)

### 2. Coleta de Contexto do Candidato

```typescript
interface CandidateContext {
  // Dados básicos
  id: string
  name: string
  email: string
  phone?: string
  
  // Histórico no processo
  current_stage: string
  target_stage: string
  days_in_process: number
  stages_completed: string[]
  
  // Avaliações
  wsi_score?: {
    overall: number
    technical: number
    behavioral: number
    cultural: number
  }
  
  // Notas e pareceres
  interview_notes?: {
    stage: string
    interviewer: string
    rating: number
    strengths: string[]
    gaps: string[]
    recommendation: 'advance' | 'reject' | 'hold'
    notes: string
  }[]
  
  lia_parecer?: {
    summary: string
    strengths: string[]
    development_areas: string[]
    cultural_fit: number
    recommendation: string
  }
  
  // Contexto da vaga
  job: {
    id: string
    title: string
    department: string
    seniority: string
    requirements: string[]
  }
}
```

### 3. Geração de Sugestões pela LIA

A LIA analisa o contexto e gera:
- **Sub-status sugerido**: Baseado na etapa e dados disponíveis
- **Mensagem personalizada**: Usando template base + personalização
- **Canal recomendado**: Email ou WhatsApp baseado em urgência/contexto

### 4. Apresentação ao Recrutador

Modal exibe:
- Candidato(s) sendo movido(s)
- Sub-status sugerido (editável)
- Preview da mensagem (editável)
- Opções de canal

### 5. Ajuste Dinâmico

Quando recrutador altera sub-status:
```
Sub-status alterado → LIA regenera mensagem → Preview atualizado
```

---

## Tipos de Transição e Comportamento

### Matriz de Transições

| De | Para | Automação | Comunicação | Sub-status LIA |
|----|------|-----------|-------------|----------------|
| Funil | Triagem | Auto | Convite WSI | `awaiting_screening_schedule` |
| Funil | Reprovado | Manual | Feedback | Analisa CV |
| Triagem | Long List | Semi | Aprovação (opcional) | `added_to_long_list` |
| Triagem | Short List | Semi | Aprovação | `added_to_short_list` |
| Triagem | Entrevista | Auto | Agendamento | `awaiting_*_schedule` |
| Triagem | Reprovado | Manual | Feedback | Analisa triagem |
| Long List | Short List | Silencioso | Nenhuma | `added_to_short_list` |
| Long List | Reprovado | Manual | Feedback | Analisa contexto |
| Short List | Entrevista | Auto | Agendamento | `awaiting_*_schedule` |
| Short List | Reprovado | Manual | Feedback | Analisa contexto |
| Entrevista* | Próxima Entrevista | Auto | Agendamento | `awaiting_*_schedule` |
| Entrevista* | Proposta | Semi | Proposta | `preparing_offer` |
| Entrevista* | Reprovado | Manual | Feedback | Analisa entrevista |
| Proposta | Contratado | Semi | Boas-vindas | `onboarding_scheduled` |
| Proposta | Recusada | Silencioso | Nenhuma | `accepted_other_offer` |
| Proposta | Reprovado | Manual | Feedback | `another_candidate_selected` |

### Níveis de Automação

#### 🟢 Auto (Automático)
- LIA executa imediatamente após confirmação rápida
- Recrutador vê preview mas não precisa editar
- Exemplo: Convite para triagem, agendamento de entrevista

#### 🟡 Semi (Semi-automático)
- LIA sugere ação e mensagem
- Recrutador pode aceitar, editar ou pular
- Exemplo: Email de aprovação, proposta

#### 🔴 Manual
- LIA gera sugestão completa
- Recrutador deve revisar antes de enviar
- Exemplo: Feedback de reprovação (requer revisão cuidadosa)

#### ⚪ Silencioso
- Move sem comunicação externa
- Apenas registra no sistema
- Exemplo: Long List → Short List (movimentação interna)

---

## Sistema de Templates

### Categorias de Templates

#### 1. Contato Inicial (`contato_inicial`)
- **Uso**: Primeiro contato com candidato prospectado
- **Gatilho**: Funil → qualquer etapa ativa
- **Tom**: Profissional, entusiasmado, personalizado

#### 2. Convite Triagem (`triagem`)
- **Uso**: Convidar para avaliação WSI com LIA
- **Gatilho**: Funil → Triagem
- **Tom**: Acolhedor, explicativo, motivacional
- **Elementos obrigatórios**:
  - Explicação do que é a triagem
  - Duração estimada (15-20 min)
  - Links de acesso (Web/WhatsApp)
  - Menção à LGPD

#### 3. Follow-up (`follow_up`)
- **Uso**: Acompanhamento de candidatos
- **Gatilho**: Candidato sem resposta há X dias
- **Tom**: Cordial, não invasivo

#### 4. Aprovação/Avanço (`feedback_positivo`)
- **Uso**: Comunicar que candidato avançou
- **Gatilho**: Qualquer etapa → próxima etapa ativa
- **Tom**: Celebratório, encorajador
- **Personalização**: Mencionar pontos fortes observados

#### 5. Agendamento (`agendamento`)
- **Uso**: Convidar para entrevista
- **Gatilho**: Qualquer etapa → Entrevista*
- **Tom**: Profissional, prático
- **Elementos obrigatórios**:
  - Tipo de entrevista
  - Link de agendamento ou horários
  - Informações sobre entrevistador(es)
  - Dicas de preparação (opcional)

#### 6. Proposta (`proposta`)
- **Uso**: Enviar oferta de contratação
- **Gatilho**: Qualquer etapa → Proposta/Contratado
- **Tom**: Celebratório, formal, claro
- **Elementos obrigatórios**:
  - Cargo e departamento
  - Informações de remuneração (se aplicável)
  - Próximos passos
  - Prazo para resposta

#### 7. Proposta Aceita (`proposta_aceita`)
- **Uso**: Confirmar contratação e boas-vindas
- **Gatilho**: Proposta → Contratado
- **Tom**: Muito celebratório, acolhedor
- **Elementos**:
  - Boas-vindas à equipe
  - Informações de onboarding
  - Contatos importantes

#### 8. Feedback Construtivo (`feedback_construtivo`)
- **Uso**: Comunicar reprovação de forma construtiva
- **Gatilho**: Qualquer etapa → Reprovado
- **Tom**: Respeitoso, construtivo, encorajador
- **Personalização obrigatória**:
  - Agradecer participação
  - Mencionar pontos fortes
  - Oferecer orientação construtiva
  - Manter porta aberta

#### 9. Vaga Fechada (`vaga_fechada`)
- **Uso**: Quando vaga é preenchida/cancelada
- **Gatilho**: Bulk action ou fechamento de vaga
- **Tom**: Respeitoso, breve

---

## Geração de Mensagens pela LIA

### Prompt Base para Geração

```
Você é LIA, assistente de recrutamento da WeDoTalent. Sua tarefa é gerar 
uma mensagem personalizada para o candidato baseada no contexto fornecido.

CONTEXTO DO CANDIDATO:
- Nome: {{candidato_nome}}
- Vaga: {{vaga}}
- Etapa atual: {{etapa_origem}}
- Nova etapa: {{etapa_destino}}
- Motivo/Sub-status: {{substatus}}

DADOS DISPONÍVEIS:
{{dados_candidato}}

TIPO DE MENSAGEM: {{tipo_template}}

REGRAS:
1. Use tom profissional mas acolhedor
2. Personalize baseado nos dados reais
3. Seja conciso (máximo 200 palavras para email, 100 para WhatsApp)
4. Siga as diretrizes de Do's and Don'ts abaixo
```

### Do's and Don'ts para Mensagens LIA

#### ✅ DO's (Fazer)

**Tom e Linguagem:**
- Usar nome do candidato (primeiro nome para WhatsApp, nome completo para email formal)
- Manter tom respeitoso e profissional
- Ser conciso e direto ao ponto
- Usar linguagem positiva mesmo em rejeições
- Personalizar com dados específicos do candidato

**Conteúdo:**
- Mencionar a vaga/posição específica
- Agradecer a participação do candidato
- Em aprovações: destacar 1-2 pontos fortes observados
- Em rejeições: oferecer feedback construtivo específico
- Incluir próximos passos claros quando aplicável
- Em agendamentos: fornecer todas informações necessárias

**Estrutura:**
- Começar com saudação apropriada ao canal
- Ir direto ao ponto principal
- Terminar com call-to-action claro ou despedida cordial
- Para email: usar formatação com parágrafos curtos
- Para WhatsApp: usar emojis com moderação (máximo 2-3)

**Personalização baseada em dados:**
- Usar notas de entrevista para contextualizar feedback
- Mencionar competências observadas na triagem WSI
- Referenciar experiências do CV quando relevante
- Adaptar mensagem ao senioridade da vaga

#### ❌ DON'Ts (Não Fazer)

**Tom e Linguagem:**
- NÃO usar linguagem excessivamente formal ou burocrática
- NÃO ser vago ou genérico demais
- NÃO usar clichês corporativos vazios
- NÃO ser condescendente ou paternalista
- NÃO usar humor ou sarcasmo
- NÃO usar gírias ou linguagem muito informal

**Conteúdo:**
- NÃO revelar informações confidenciais da empresa
- NÃO comparar candidato com outros diretamente
- NÃO mencionar nomes de outros candidatos
- NÃO prometer futuras oportunidades que não existem
- NÃO dar feedback médico, psicológico ou pessoal
- NÃO criticar empregadores anteriores do candidato
- NÃO incluir informações incorretas ou inventadas

**Em Rejeições Especificamente:**
- NÃO usar frases como "infelizmente" no início
- NÃO ser excessivamente apologético
- NÃO mentir sobre o motivo da rejeição
- NÃO deixar a porta "muito aberta" se não houver intenção real
- NÃO ser brutalmente honesto sobre gaps (ser construtivo)
- NÃO enviar feedback de entrevista técnica sem validação do entrevistador

**Estrutura:**
- NÃO escrever parágrafos longos (máximo 3-4 linhas)
- NÃO usar múltiplas fontes ou formatações excessivas
- NÃO incluir anexos sem necessidade clara
- NÃO usar muitos emojis (especialmente em email)

**Dados:**
- NÃO inventar dados que não existem no contexto
- NÃO assumir informações não fornecidas
- NÃO expor scores numéricos diretamente ao candidato
- NÃO citar verbatim notas internas de entrevistadores

---

## Sub-Status e Seleção Automática

### Lógica de Predição de Sub-Status

A LIA analisa o contexto para sugerir o sub-status mais apropriado:

#### Para Reprovação (`rejected`)

```typescript
function predictRejectionSubStatus(context: CandidateContext): string {
  const { wsi_score, interview_notes, current_stage, lia_parecer } = context
  
  // Se há outro candidato sendo contratado para a mesma vaga
  if (context.job.has_hired_candidate) {
    return 'another_candidate_selected'
  }
  
  // Se score WSI baixo
  if (wsi_score && wsi_score.overall < 50) {
    if (wsi_score.technical < 40) return 'insufficient_technical_skills'
    if (wsi_score.behavioral < 40) return 'behavioral_concerns'
    if (wsi_score.cultural < 40) return 'cultural_fit'
  }
  
  // Se rejeitado em entrevista técnica
  if (current_stage === 'interview_technical') {
    const techNotes = interview_notes?.find(n => n.stage === 'interview_technical')
    if (techNotes?.gaps?.length > 2) return 'insufficient_technical_skills'
  }
  
  // Se rejeitado em entrevista com gestor
  if (current_stage.includes('manager')) {
    return 'manager_decision'
  }
  
  // Se candidato demonstrou falta de interesse
  if (context.response_time_days > 7) {
    return 'lack_of_interest'
  }
  
  // Se expectativa salarial incompatível (se dado disponível)
  if (context.salary_expectation > context.job.salary_max * 1.2) {
    return 'salary_expectation'
  }
  
  // Default
  return 'profile_not_aligned'
}
```

#### Mapeamento Sub-Status → Mensagem

| Sub-Status | Foco da Mensagem |
|------------|------------------|
| `another_candidate_selected` | Agradecer, mencionar competição forte, manter banco |
| `insufficient_technical_skills` | Agradecer, sugerir áreas de desenvolvimento técnico |
| `behavioral_concerns` | Agradecer, ser muito diplomático, focar em fit |
| `cultural_fit` | Agradecer, mencionar diferença de momento/estilo |
| `manager_decision` | Agradecer, mencionar decisão final do gestor |
| `salary_expectation` | Agradecer, mencionar incompatibilidade (sem valores) |
| `overqualified` | Agradecer muito, reconhecer qualificações, manter contato |
| `underqualified` | Agradecer, encorajar desenvolvimento, sugerir áreas |
| `location_incompatibility` | Agradecer, mencionar questão logística |
| `lack_of_interest` | Tom neutro, desejar sucesso |

---

## Ajuste Dinâmico de Mensagem

### Fluxo de Reajuste

```
1. Recrutador altera sub-status no dropdown
2. Sistema detecta mudança
3. LIA é chamada com novo contexto:
   - Mesmo candidato
   - Mesmo tipo de template
   - NOVO sub-status
4. LIA regenera apenas os trechos afetados
5. Preview é atualizado em tempo real
```

### Implementação

```typescript
async function regenerateMessageOnSubStatusChange(
  currentMessage: string,
  newSubStatus: string,
  context: CandidateContext
): Promise<string> {
  const prompt = `
    Você tem uma mensagem de feedback que precisa ser ajustada porque 
    o motivo da reprovação mudou.
    
    MENSAGEM ATUAL:
    ${currentMessage}
    
    NOVO MOTIVO: ${getSubStatusDisplayName(newSubStatus)}
    
    CONTEXTO DO CANDIDATO:
    ${JSON.stringify(context)}
    
    TAREFA:
    Ajuste a mensagem para refletir o novo motivo, mantendo:
    - Tom geral
    - Estrutura
    - Personalização existente
    
    Altere apenas os trechos que mencionam o motivo ou feedback específico.
  `
  
  return await liaApi.generateText(prompt)
}
```

---

## Ações em Lote (Bulk Actions)

### Fluxo de Bulk

```
1. Recrutador seleciona múltiplos candidatos
2. Escolhe ação (ex: mover para Reprovado)
3. Modal abre com:
   - Lista de candidatos
   - Opção: Template padrão vs Personalizado pela LIA
4. Se "Personalizado":
   - LIA gera mensagem única para cada candidato
   - Preview de cada mensagem é exibido
   - Recrutador pode editar individualmente
5. Confirmação envia todas as mensagens
```

### Otimização de Performance

Para bulk com muitos candidatos:
- Gerar mensagens em paralelo (batch de 5)
- Mostrar loading progressivo
- Permitir edição enquanto outras geram
- Cache de contexto de candidatos

---

## Alertas Internos

### Bell (Notificações Internas)

| Evento | Destinatário | Prioridade |
|--------|--------------|------------|
| Triagem WSI concluída | Recrutador responsável | Alta |
| Candidato avançou de etapa | Próximo entrevistador | Média |
| Entrevista agendada | Entrevistador | Alta |
| Prazo de resposta expirando | Recrutador | Alta |
| Proposta aceita | Gestor + RH | Alta |
| Candidato contratado | Time inteiro | Baixa |

### Microsoft Teams Integration

| Evento | Canal/Pessoa | Formato |
|--------|--------------|---------|
| Entrevista técnica agendada | Canal do time técnico | Card com detalhes |
| Proposta aprovada | Canal de Recrutamento | Anúncio |
| Contratação concluída | Canal geral do time | Celebração |
| Candidato finalista | Gestor direto (DM) | Card resumo |

---

## Configurações por Empresa

### Níveis de Configuração

```typescript
interface CompanyAutomationConfig {
  // Níveis de automação por tipo de transição
  automation_levels: {
    sourcing_to_screening: 'auto' | 'semi' | 'manual'
    screening_to_interview: 'auto' | 'semi' | 'manual'
    any_to_rejected: 'auto' | 'semi' | 'manual'
    // ...
  }
  
  // Canais habilitados
  channels: {
    email: boolean
    whatsapp: boolean
    teams: boolean
    bell: boolean
  }
  
  // Preferências de comunicação
  communication: {
    default_channel: 'email' | 'whatsapp'
    require_review_for_rejection: boolean
    auto_send_interview_invites: boolean
    include_salary_in_offer: boolean
  }
  
  // Templates personalizados
  custom_templates: {
    rejection_footer?: string
    company_signature?: string
    // ...
  }
}
```

---

## Métricas e Analytics

### KPIs do Sistema de Automação

| Métrica | Descrição |
|---------|-----------|
| Tempo médio por transição | Segundos gastos pelo recrutador por movimentação |
| Taxa de aceitação LIA | % de sugestões aceitas sem edição |
| Taxa de edição | % de mensagens editadas antes do envio |
| NPS do candidato | Satisfação do candidato com comunicação |
| Volume de mensagens/dia | Throughput do sistema |
| Erros de envio | Taxa de falhas |

---

## Próximas Evoluções

### Fase 1 (MVP)
- Modal de transição inteligente (individual)
- Sub-status automático
- Mensagem personalizada com preview
- Ajuste dinâmico ao mudar sub-status

### Fase 2
- Ações em lote com personalização individual
- Integração Teams para alertas
- Analytics de uso

### Fase 3
- Aprendizado: LIA melhora baseada em edições
- Sugestão proativa: LIA sugere ações baseada em padrões
- Automação condicional: regras customizáveis

---

*Documento criado em: Janeiro 2026*
*Versão: 1.0*
*Autor: WeDoTalent AI Team*
