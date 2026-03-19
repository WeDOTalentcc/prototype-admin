# Guia de Desenvolvimento - Sistema de Automação LIA

## Objetivo

Este documento fornece especificações técnicas detalhadas para o time de desenvolvimento implementar o Sistema de Automação LIA em diferentes stacks e plataformas.

---

## Arquitetura de Componentes

### Visão Geral

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│  │ SmartTransition  │  │ BulkActions      │  │ QuickActions     │          │
│  │ Modal            │  │ Modal            │  │ Dropdown         │          │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘          │
│           │                     │                      │                     │
│           └─────────────────────┼──────────────────────┘                     │
│                                 ▼                                            │
│  ┌──────────────────────────────────────────────────────────────────┐       │
│  │                    TransitionContext Hook                         │       │
│  │  - collectCandidateContext()                                      │       │
│  │  - getAvailableActions()                                          │       │
│  │  - getSuggestedSubStatus()                                        │       │
│  └──────────────────────────────────────────────────────────────────┘       │
│                                 │                                            │
└─────────────────────────────────┼────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              BACKEND API                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│  │ /api/automation/ │  │ /api/lia/        │  │ /api/templates/  │          │
│  │ transitions      │  │ generate-message │  │ by-situation     │          │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘          │
│           │                     │                      │                     │
│           └─────────────────────┼──────────────────────┘                     │
│                                 ▼                                            │
│  ┌──────────────────────────────────────────────────────────────────┐       │
│  │                    LIA Agent Service                              │       │
│  │  - generatePersonalizedMessage()                                  │       │
│  │  - predictSubStatus()                                             │       │
│  │  - adjustMessageForSubStatus()                                    │       │
│  └──────────────────────────────────────────────────────────────────┘       │
│                                 │                                            │
└─────────────────────────────────┼────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              LLM (Claude/Gemini)                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Componentes Frontend

### 1. SmartTransitionModal

Modal principal que aparece ao mover candidato(s) de etapa.

#### Props Interface

```typescript
interface SmartTransitionModalProps {
  isOpen: boolean
  onClose: () => void
  
  // Candidato(s) sendo movido(s)
  candidates: CandidateForTransition[]
  
  // Transição
  fromStage: string
  toStage: string
  
  // Contexto
  jobVacancy: JobVacancy
  companyId: string
  
  // Callbacks
  onConfirm: (result: TransitionResult) => Promise<void>
  onCancel: () => void
}

interface CandidateForTransition {
  id: string
  name: string
  email?: string
  phone?: string
  avatar?: string
  current_title?: string
  
  // Contexto para personalização
  context: CandidateContext
}

interface TransitionResult {
  candidates: {
    candidateId: string
    action: TransitionAction
    subStatus: string
    channel?: 'email' | 'whatsapp'
    message?: {
      subject?: string
      body: string
    }
  }[]
}
```

#### Estados do Componente

```typescript
interface SmartTransitionModalState {
  // Modo de operação
  mode: 'single' | 'bulk'
  
  // Escolha de personalização (bulk only)
  personalizationType: 'template' | 'lia_personalized'
  
  // Ação selecionada
  selectedAction: TransitionAction | null
  
  // Sub-status (pode ser diferente por candidato em bulk)
  subStatusByCandidate: Record<string, string>
  
  // Mensagens geradas
  messagesByCandidate: Record<string, GeneratedMessage>
  
  // Estado de edição
  editingCandidateId: string | null
  
  // Loading states
  isGenerating: boolean
  isSubmitting: boolean
  
  // Canal de envio
  channel: 'email' | 'whatsapp'
}

interface GeneratedMessage {
  subject?: string
  body: string
  isEdited: boolean
  originalBody: string
}
```

#### Fluxo de Renderização

```tsx
function SmartTransitionModal(props: SmartTransitionModalProps) {
  const [state, setState] = useState<SmartTransitionModalState>(initialState)
  
  // 1. Ao abrir, determinar ações disponíveis
  const availableActions = useMemo(() => 
    getAvailableActions(props.fromStage, props.toStage),
    [props.fromStage, props.toStage]
  )
  
  // 2. Ao abrir, prever sub-status para cada candidato
  useEffect(() => {
    if (props.isOpen) {
      predictSubStatusForAll()
    }
  }, [props.isOpen])
  
  // 3. Quando sub-status muda, regenerar mensagem
  const handleSubStatusChange = async (candidateId: string, newSubStatus: string) => {
    setState(prev => ({
      ...prev,
      subStatusByCandidate: {
        ...prev.subStatusByCandidate,
        [candidateId]: newSubStatus
      }
    }))
    
    // Regenerar mensagem para este candidato
    await regenerateMessage(candidateId, newSubStatus)
  }
  
  return (
    <Modal isOpen={props.isOpen} onClose={props.onClose}>
      {/* Header com info da transição */}
      <TransitionHeader 
        from={props.fromStage} 
        to={props.toStage}
        candidateCount={props.candidates.length}
      />
      
      {/* Seleção de ação */}
      <ActionSelector
        actions={availableActions}
        selected={state.selectedAction}
        onSelect={handleActionSelect}
      />
      
      {/* Se bulk, opção de personalização */}
      {state.mode === 'bulk' && (
        <PersonalizationToggle
          value={state.personalizationType}
          onChange={handlePersonalizationChange}
        />
      )}
      
      {/* Lista de candidatos com preview */}
      <CandidateMessageList
        candidates={props.candidates}
        messages={state.messagesByCandidate}
        subStatuses={state.subStatusByCandidate}
        onSubStatusChange={handleSubStatusChange}
        onMessageEdit={handleMessageEdit}
        isGenerating={state.isGenerating}
      />
      
      {/* Seleção de canal */}
      <ChannelSelector
        value={state.channel}
        onChange={setChannel}
        emailAvailable={hasEmail}
        whatsappAvailable={hasPhone}
      />
      
      {/* Footer com ações */}
      <ModalFooter>
        <Button variant="outline" onClick={props.onCancel}>
          Cancelar
        </Button>
        <Button 
          onClick={handleConfirm}
          disabled={!canConfirm}
          loading={state.isSubmitting}
        >
          {getConfirmButtonText()}
        </Button>
      </ModalFooter>
    </Modal>
  )
}
```

### 2. CandidateMessagePreview

Componente que exibe preview da mensagem de um candidato.

```tsx
interface CandidateMessagePreviewProps {
  candidate: CandidateForTransition
  message: GeneratedMessage
  subStatus: string
  availableSubStatuses: SubStatus[]
  onSubStatusChange: (newSubStatus: string) => void
  onMessageEdit: (newBody: string) => void
  isGenerating: boolean
}

function CandidateMessagePreview(props: CandidateMessagePreviewProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  
  return (
    <Card className="p-4">
      {/* Header com info do candidato */}
      <div className="flex items-center gap-3 mb-3">
        <Avatar src={props.candidate.avatar} />
        <div>
          <p className="font-medium">{props.candidate.name}</p>
          <p className="text-sm text-gray-500">{props.candidate.current_title}</p>
        </div>
        {props.candidate.context.wsi_score && (
          <Badge>Score: {props.candidate.context.wsi_score.overall}</Badge>
        )}
      </div>
      
      {/* Seletor de sub-status */}
      <div className="mb-3">
        <Label>Motivo</Label>
        <Select
          value={props.subStatus}
          onValueChange={props.onSubStatusChange}
        >
          {props.availableSubStatuses.map(status => (
            <SelectItem key={status.name} value={status.name}>
              {status.displayName}
            </SelectItem>
          ))}
        </Select>
        {/* Indicador que LIA sugeriu */}
        <p className="text-xs text-cyan-600 mt-1">
          <Sparkles className="inline w-3 h-3 mr-1" />
          Sugerido pela LIA
        </p>
      </div>
      
      {/* Preview da mensagem */}
      <div className="relative">
        {props.isGenerating ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="animate-spin mr-2" />
            <span>LIA está personalizando...</span>
          </div>
        ) : isEditing ? (
          <Textarea
            value={props.message.body}
            onChange={(e) => props.onMessageEdit(e.target.value)}
            rows={6}
          />
        ) : (
          <div 
            className={`bg-gray-50 rounded-lg p-3 text-sm ${
              isExpanded ? '' : 'max-h-24 overflow-hidden'
            }`}
          >
            {props.message.body}
          </div>
        )}
        
        {/* Botões de ação */}
        <div className="flex gap-2 mt-2">
          <Button 
            variant="ghost" 
            size="sm"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            {isExpanded ? 'Recolher' : 'Expandir'}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsEditing(!isEditing)}
          >
            {isEditing ? 'Salvar' : 'Editar'}
          </Button>
        </div>
        
        {/* Indicador de edição */}
        {props.message.isEdited && (
          <Badge variant="outline" className="absolute top-2 right-2">
            Editado
          </Badge>
        )}
      </div>
    </Card>
  )
}
```

---

## Hooks

### useTransitionContext

Hook que gerencia todo o contexto de transição.

```typescript
interface UseTransitionContextOptions {
  candidates: CandidateForTransition[]
  fromStage: string
  toStage: string
  jobVacancy: JobVacancy
}

interface UseTransitionContextReturn {
  // Ações disponíveis
  availableActions: TransitionAction[]
  
  // Sub-status
  predictedSubStatuses: Record<string, string>
  updateSubStatus: (candidateId: string, subStatus: string) => void
  
  // Mensagens
  messages: Record<string, GeneratedMessage>
  generateMessages: (personalized: boolean) => Promise<void>
  regenerateMessage: (candidateId: string) => Promise<void>
  updateMessage: (candidateId: string, body: string) => void
  
  // Estado
  isGenerating: boolean
  error: string | null
}

function useTransitionContext(options: UseTransitionContextOptions): UseTransitionContextReturn {
  const [predictedSubStatuses, setPredictedSubStatuses] = useState<Record<string, string>>({})
  const [messages, setMessages] = useState<Record<string, GeneratedMessage>>({})
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // Determinar ações baseado na transição
  const availableActions = useMemo(() => {
    return getAvailableActionsForTransition(options.fromStage, options.toStage)
  }, [options.fromStage, options.toStage])
  
  // Prever sub-status inicial para cada candidato
  useEffect(() => {
    async function predictAll() {
      const predictions: Record<string, string> = {}
      
      for (const candidate of options.candidates) {
        const predicted = await predictSubStatus(
          candidate.context,
          options.fromStage,
          options.toStage
        )
        predictions[candidate.id] = predicted
      }
      
      setPredictedSubStatuses(predictions)
    }
    
    predictAll()
  }, [options.candidates, options.fromStage, options.toStage])
  
  // Gerar mensagens
  const generateMessages = useCallback(async (personalized: boolean) => {
    setIsGenerating(true)
    setError(null)
    
    try {
      const generated: Record<string, GeneratedMessage> = {}
      
      // Processar em batches de 5 para performance
      const batches = chunk(options.candidates, 5)
      
      for (const batch of batches) {
        const promises = batch.map(async (candidate) => {
          const subStatus = predictedSubStatuses[candidate.id]
          
          let message: string
          if (personalized) {
            message = await generatePersonalizedMessage(
              candidate.context,
              options.toStage,
              subStatus,
              options.jobVacancy
            )
          } else {
            message = await getTemplateMessage(
              options.toStage,
              candidate,
              options.jobVacancy
            )
          }
          
          return {
            id: candidate.id,
            message: {
              body: message,
              isEdited: false,
              originalBody: message
            }
          }
        })
        
        const results = await Promise.all(promises)
        results.forEach(r => {
          generated[r.id] = r.message
        })
      }
      
      setMessages(generated)
    } catch (err) {
      setError('Erro ao gerar mensagens')
      console.error(err)
    } finally {
      setIsGenerating(false)
    }
  }, [options.candidates, predictedSubStatuses, options.toStage, options.jobVacancy])
  
  // Regenerar mensagem específica (quando sub-status muda)
  const regenerateMessage = useCallback(async (candidateId: string) => {
    const candidate = options.candidates.find(c => c.id === candidateId)
    if (!candidate) return
    
    setMessages(prev => ({
      ...prev,
      [candidateId]: {
        ...prev[candidateId],
        isEdited: false // Reset edit flag
      }
    }))
    
    setIsGenerating(true)
    
    try {
      const subStatus = predictedSubStatuses[candidateId]
      const newMessage = await generatePersonalizedMessage(
        candidate.context,
        options.toStage,
        subStatus,
        options.jobVacancy
      )
      
      setMessages(prev => ({
        ...prev,
        [candidateId]: {
          body: newMessage,
          isEdited: false,
          originalBody: newMessage
        }
      }))
    } catch (err) {
      console.error(err)
    } finally {
      setIsGenerating(false)
    }
  }, [options.candidates, predictedSubStatuses, options.toStage, options.jobVacancy])
  
  // Atualizar sub-status
  const updateSubStatus = useCallback((candidateId: string, subStatus: string) => {
    setPredictedSubStatuses(prev => ({
      ...prev,
      [candidateId]: subStatus
    }))
    
    // Auto-regenerar mensagem
    regenerateMessage(candidateId)
  }, [regenerateMessage])
  
  // Atualizar mensagem manualmente
  const updateMessage = useCallback((candidateId: string, body: string) => {
    setMessages(prev => ({
      ...prev,
      [candidateId]: {
        ...prev[candidateId],
        body,
        isEdited: body !== prev[candidateId]?.originalBody
      }
    }))
  }, [])
  
  return {
    availableActions,
    predictedSubStatuses,
    updateSubStatus,
    messages,
    generateMessages,
    regenerateMessage,
    updateMessage,
    isGenerating,
    error
  }
}
```

---

## Backend API Endpoints

### POST /api/automation/predict-substatus

Prever sub-status baseado no contexto do candidato.

```python
# Request
{
  "candidate_context": {
    "id": "cand_123",
    "current_stage": "interview_technical",
    "target_stage": "rejected",
    "wsi_score": {
      "overall": 65,
      "technical": 55,
      "behavioral": 75,
      "cultural": 70
    },
    "interview_notes": [
      {
        "stage": "interview_technical",
        "rating": 3,
        "gaps": ["cloud architecture", "system design"],
        "strengths": ["python", "communication"]
      }
    ],
    "lia_parecer": {
      "summary": "Candidato junior com bom potencial...",
      "development_areas": ["cloud", "arquitetura"]
    }
  },
  "job_context": {
    "title": "Senior Backend Developer",
    "seniority": "senior",
    "requirements": ["python", "aws", "microservices"]
  }
}

# Response
{
  "predicted_substatus": "insufficient_technical_skills",
  "confidence": 0.85,
  "reasoning": "Candidato possui gaps em cloud e arquitetura, requisitos críticos para a senioridade da vaga",
  "alternatives": [
    {
      "substatus": "profile_not_aligned",
      "confidence": 0.12
    }
  ]
}
```

### POST /api/automation/generate-message

Gerar mensagem personalizada.

```python
# Request
{
  "candidate_context": { ... },
  "job_context": { ... },
  "message_type": "feedback_construtivo",
  "substatus": "insufficient_technical_skills",
  "channel": "email",
  "template_id": "default-feedback-email"  # opcional, usa como base
}

# Response
{
  "subject": "Retorno sobre sua candidatura - Senior Backend Developer",
  "body": "Olá João,\n\nAgradecemos muito sua participação em nosso processo seletivo...",
  "metadata": {
    "personalization_points": [
      "Mencionou experiência com Python",
      "Sugeriu desenvolvimento em cloud/arquitetura",
      "Tom encorajador mantido"
    ],
    "tokens_used": 450
  }
}
```

### POST /api/automation/regenerate-for-substatus

Regenerar mensagem quando sub-status muda.

```python
# Request
{
  "original_message": "Olá João, agradecemos sua participação...",
  "new_substatus": "another_candidate_selected",
  "candidate_context": { ... },
  "job_context": { ... }
}

# Response
{
  "body": "Olá João,\n\nAgradecemos muito sua participação... Após análise cuidadosa, decidimos avançar com outro candidato...",
  "changes_made": [
    "Alterado motivo de 'gaps técnicos' para 'outro candidato selecionado'",
    "Mantido reconhecimento de pontos fortes",
    "Ajustado tom para mais positivo"
  ]
}
```

### POST /api/automation/execute-transition

Executar transição com todas as ações.

```python
# Request
{
  "transitions": [
    {
      "candidate_id": "cand_123",
      "from_stage": "interview_technical",
      "to_stage": "rejected",
      "substatus": "insufficient_technical_skills",
      "action": "email",
      "message": {
        "subject": "Retorno sobre sua candidatura",
        "body": "Olá João..."
      }
    },
    {
      "candidate_id": "cand_456",
      "from_stage": "interview_technical",
      "to_stage": "rejected",
      "substatus": "another_candidate_selected",
      "action": "whatsapp",
      "message": {
        "body": "Olá Maria..."
      }
    }
  ],
  "job_vacancy_id": "job_789"
}

# Response
{
  "success": true,
  "results": [
    {
      "candidate_id": "cand_123",
      "stage_updated": true,
      "message_sent": true,
      "message_id": "msg_abc"
    },
    {
      "candidate_id": "cand_456",
      "stage_updated": true,
      "message_sent": true,
      "message_id": "msg_def"
    }
  ],
  "alerts_triggered": [
    {
      "type": "bell",
      "recipient": "recruiter@company.com",
      "message": "2 candidatos movidos para Reprovado"
    }
  ]
}
```

---

## LIA Agent Service

### Prompts de Sistema

#### Prompt para Predição de Sub-Status

```python
SUBSTATUS_PREDICTION_PROMPT = """
Você é um especialista em recrutamento analisando o contexto de um candidato 
para determinar o motivo mais apropriado para a transição de etapa.

CANDIDATO:
- Nome: {candidate_name}
- Etapa Atual: {current_stage}
- Nova Etapa: {target_stage}

AVALIAÇÕES:
{evaluations}

NOTAS DE ENTREVISTA:
{interview_notes}

PARECER LIA:
{lia_parecer}

VAGA:
- Título: {job_title}
- Senioridade: {seniority}
- Requisitos: {requirements}

SUB-STATUS DISPONÍVEIS PARA {target_stage}:
{available_substatuses}

TAREFA:
Analise o contexto e escolha o sub-status mais apropriado. Considere:
1. Os dados objetivos (scores, notas)
2. O feedback dos entrevistadores
3. O alinhamento com os requisitos da vaga
4. O contexto geral do processo

Responda em JSON:
{
  "predicted_substatus": "codigo_do_substatus",
  "confidence": 0.0-1.0,
  "reasoning": "Explicação breve do motivo da escolha"
}
"""
```

#### Prompt para Geração de Mensagem

```python
MESSAGE_GENERATION_PROMPT = """
Você é LIA, assistente de recrutamento da WeDoTalent. Gere uma mensagem 
personalizada para o candidato.

CANDIDATO:
- Nome: {candidate_name}
- Email: {email}
- Cargo Atual: {current_title}

PROCESSO:
- Vaga: {job_title}
- De: {from_stage} → Para: {to_stage}
- Motivo: {substatus_display_name}

DADOS PARA PERSONALIZAÇÃO:
{personalization_data}

TIPO DE MENSAGEM: {message_type}
CANAL: {channel}

TEMPLATE BASE (use como estrutura):
{template_base}

REGRAS:
1. Mantenha tom profissional mas acolhedor
2. Personalize com os dados reais do candidato
3. {channel_specific_rules}
4. Máximo {max_words} palavras
5. Siga as diretrizes de Do's and Don'ts

DO's:
- Usar nome do candidato
- Mencionar pontos fortes observados
- Ser construtivo em feedback negativo
- Incluir próximos passos quando aplicável

DON'Ts:
- Não inventar dados
- Não expor scores numéricos
- Não comparar com outros candidatos
- Não usar clichês vazios

Gere a mensagem:
"""
```

#### Prompt para Ajuste de Mensagem

```python
MESSAGE_ADJUSTMENT_PROMPT = """
A mensagem abaixo precisa ser ajustada porque o motivo da transição mudou.

MENSAGEM ORIGINAL:
{original_message}

MUDANÇA:
- Motivo anterior: {old_substatus}
- Novo motivo: {new_substatus}

CONTEXTO DO CANDIDATO:
{candidate_context}

TAREFA:
Ajuste a mensagem para refletir o novo motivo. Mantenha:
- Estrutura geral
- Tom
- Personalizações existentes

Altere apenas os trechos que mencionam o motivo específico.

Mensagem ajustada:
"""
```

---

## Regras de Negócio

### Mapeamento Ação → Situação de Template

```typescript
const ACTION_TO_TEMPLATE_SITUATION: Record<string, TemplateSituation> = {
  // Ações de avanço
  'triagem_wsi': 'triagem',
  'agendar_entrevista': 'agendamento',
  'enviar_proposta': 'proposta',
  'boas_vindas': 'proposta_aceita',
  
  // Ações de comunicação geral
  'email_aprovacao': 'feedback_positivo',
  'whatsapp_aprovacao': 'feedback_positivo',
  
  // Ações de rejeição
  'email_feedback': 'feedback_construtivo',
  'whatsapp_feedback': 'feedback_construtivo',
  
  // Follow-up
  'email_followup': 'follow_up',
  'whatsapp_followup': 'follow_up',
  
  // Contato inicial
  'primeiro_contato': 'contato_inicial',
}
```

### Regras de Canal

```typescript
const CHANNEL_RULES = {
  email: {
    maxLength: 2000,
    requireSubject: true,
    allowFormatting: true,
    emojiLimit: 0,
    formalityLevel: 'formal',
  },
  whatsapp: {
    maxLength: 500,
    requireSubject: false,
    allowFormatting: false,
    emojiLimit: 3,
    formalityLevel: 'semi_formal',
  }
}
```

### Regras de Automação por Transição

```typescript
const TRANSITION_AUTOMATION_RULES: Record<string, AutomationRule> = {
  'sourcing_to_screening': {
    defaultAction: 'triagem_wsi',
    autoSend: true,
    requireConfirmation: true,
    suggestChannel: 'email',
    allowSkip: false,
  },
  'screening_to_interview': {
    defaultAction: 'agendar_entrevista',
    autoSend: true,
    requireConfirmation: true,
    suggestChannel: 'email',
    allowSkip: false,
  },
  'any_to_rejected': {
    defaultAction: 'email_feedback',
    autoSend: false,
    requireConfirmation: true,
    suggestChannel: 'email',
    allowSkip: true,
    requireReview: true, // Recrutador deve revisar
  },
  'interview_to_offer': {
    defaultAction: 'enviar_proposta',
    autoSend: false,
    requireConfirmation: true,
    suggestChannel: 'email',
    allowSkip: false,
    requireReview: true,
  },
  'offer_to_hired': {
    defaultAction: 'boas_vindas',
    autoSend: false,
    requireConfirmation: true,
    suggestChannel: 'email',
    allowSkip: true,
    triggerAlerts: ['bell', 'teams'],
  },
  // Transições silenciosas
  'long_list_to_short_list': {
    defaultAction: 'apenas_mover',
    autoSend: false,
    requireConfirmation: false,
    allowSkip: true,
    silent: true,
  },
}
```

---

## Testes

### Cenários de Teste

```typescript
describe('SmartTransitionModal', () => {
  describe('Sub-status prediction', () => {
    it('should predict "insufficient_technical_skills" for low technical score', async () => {
      const context = {
        wsi_score: { overall: 55, technical: 40, behavioral: 70, cultural: 60 },
        target_stage: 'rejected'
      }
      
      const predicted = await predictSubStatus(context)
      expect(predicted).toBe('insufficient_technical_skills')
    })
    
    it('should predict "another_candidate_selected" when job has hired candidate', async () => {
      const context = {
        wsi_score: { overall: 80, technical: 85, behavioral: 75, cultural: 80 },
        target_stage: 'rejected',
        job: { has_hired_candidate: true }
      }
      
      const predicted = await predictSubStatus(context)
      expect(predicted).toBe('another_candidate_selected')
    })
  })
  
  describe('Message regeneration on substatus change', () => {
    it('should regenerate message when substatus changes', async () => {
      const initialMessage = 'Você possui gaps em cloud...'
      const newSubstatus = 'another_candidate_selected'
      
      const regenerated = await regenerateMessage(initialMessage, newSubstatus, context)
      
      expect(regenerated).not.toContain('gaps em cloud')
      expect(regenerated).toContain('outro candidato')
    })
  })
  
  describe('Bulk actions', () => {
    it('should generate unique messages for each candidate', async () => {
      const candidates = [
        { id: '1', name: 'João', context: { wsi_score: { overall: 65 } } },
        { id: '2', name: 'Maria', context: { wsi_score: { overall: 80 } } }
      ]
      
      const messages = await generateBulkMessages(candidates, 'rejected')
      
      expect(messages['1']).toContain('João')
      expect(messages['2']).toContain('Maria')
      expect(messages['1']).not.toBe(messages['2'])
    })
  })
})
```

---

## Migração e Rollout

### Fase 1: MVP Individual
1. Implementar SmartTransitionModal
2. Integrar no Kanban (handleDrop)
3. Integrar na Tabela (InteractiveStageCell)
4. Testes com equipe interna

### Fase 2: Bulk Actions
1. Expandir modal para múltiplos candidatos
2. Implementar geração em paralelo
3. UI de preview em lista

### Fase 3: Automação Avançada
1. Alertas Bell e Teams
2. Configurações por empresa
3. Analytics de uso

### Feature Flags

```typescript
const AUTOMATION_FEATURE_FLAGS = {
  smart_transition_modal: true,          // MVP
  lia_substatus_prediction: true,        // MVP
  lia_message_personalization: true,     // MVP
  substatus_dynamic_adjustment: true,    // MVP
  bulk_actions: false,                   // Fase 2
  teams_integration: false,              // Fase 3
  automation_analytics: false,           // Fase 3
}
```

---

## Considerações de Performance

1. **Cache de Contexto**: Cachear contexto de candidatos por 5 minutos
2. **Batch Processing**: Processar mensagens em lotes de 5
3. **Lazy Loading**: Carregar preview de mensagens sob demanda em bulk
4. **Debounce**: Debounce de 300ms na mudança de sub-status antes de regenerar

---

*Documento criado em: Janeiro 2026*
*Versão: 1.0*
*Para: Time de Desenvolvimento WeDoTalent*
