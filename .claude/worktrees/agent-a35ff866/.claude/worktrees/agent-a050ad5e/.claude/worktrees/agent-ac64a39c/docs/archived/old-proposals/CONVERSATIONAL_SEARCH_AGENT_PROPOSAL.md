# Proposta: Agente de Busca Conversacional para Funil de Talentos

**Data**: 2026-01-20  
**Status**: Em Avaliação  
**Autor**: Equipe LIA  
**Versão**: 1.0

---

## 1. Resumo Executivo

Esta proposta descreve a implementação de uma experiência de busca conversacional no Funil de Talentos da Plataforma LIA, permitindo que recrutadores encontrem candidatos através de linguagem natural em uma interface de chat. A solução combina busca na base interna (candidatos já cadastrados) com integração opcional da Pearch AI para sourcing global.

---

## 2. Contexto e Motivação

### 2.1 Estado Atual
- O Funil de Talentos possui um prompt de busca em linguagem natural
- Existe Semantic Search implementado com Gemini
- Sourcing Agent possui 12 actions funcionais
- A experiência é single-query (uma busca, um resultado)

### 2.2 Oportunidade
- Concorrentes (Paradox, HireEZ, Humanly) oferecem experiências conversacionais
- Pearch AI lançou Chat Completions API compatível com formato OpenAI
- Recrutadores preferem refinamento iterativo vs. refazer buscas
- Diferencial competitivo no mercado brasileiro (Gupy, Kenoby ainda usam filtros tradicionais)

### 2.3 Benchmark de Mercado

| Plataforma | Tipo | Preço | Conversacional |
|------------|------|-------|----------------|
| Paradox (Olivia) | High-volume hiring | ~$6K+/ano | Lider em IA conversacional |
| HireEZ | Sourcing | $169-450/user/mes | EZ Agent (Agentic AI) |
| Humanly | Mid-market | $1K/mes | Chat screening |
| Pearch AI | API | $600/10k creditos | Chat Completions API |
| SeekOut | Enterprise | Custom | NLP Search |
| Eightfold | Enterprise | Custom | Deep learning matching |

---

## 3. Solucao Proposta

### 3.1 Visao Geral

Criar um **Search Conversation Agent** que atua como wrapper conversacional sobre a infraestrutura existente, oferecendo:

1. **Busca na Base Interna**: Candidatos ja cadastrados na LIA
2. **Busca Global (Pearch)**: Sourcing de candidatos externos
3. **Modo Hibrido**: Busca unificada em ambas as fontes

### 3.2 Arquitetura

```
+-------------------------------------------------------------+
|                    FUNIL DE TALENTOS                        |
+-------------------------------------------------------------+
|                                                             |
|  +-----------------------------------------------------+   |
|  |  Chat Interface                                      |   |
|  |  +-----------------------------------------------+  |   |
|  |  | "Preciso de devs React em SP ate R$20k"       |  |   |
|  |  +-----------------------------------------------+  |   |
|  |                                                     |   |
|  |  [Minha Base]  [Mercado (Pearch)]  [Ambos]         |   |
|  +-----------------------------------------------------+   |
|                           |                                 |
|                           v                                 |
|  +-----------------------------------------------------+   |
|  |           Search Conversation Agent                  |   |
|  |  +-----------+  +-----------+  +------------+       |   |
|  |  | Memoria   |  | Intencao  |  | Orquestracao|      |   |
|  |  | Conversa  |  | Parser    |  | de Fontes   |      |   |
|  |  +-----------+  +-----------+  +------------+       |   |
|  +------------------------+----------------------------+   |
|                           |                                 |
|         +-----------------+------------------+              |
|         v                 v                  v              |
|  +------------+    +------------+    +----------------+    |
|  | PostgreSQL |    |  Sourcing  |    |   Pearch AI    |    |
|  | (Internos) |    |   Agent    |    |   (Externos)   |    |
|  +------------+    +------------+    +----------------+    |
|                                                             |
+-------------------------------------------------------------+
```

### 3.3 Fluxo de Conversa

```
+-------------------------------------------------------------+
| EXEMPLO DE CONVERSA                                         |
+-------------------------------------------------------------+
|                                                             |
| Recrutador: "React seniors em SP ate R$20k"                 |
|                                                             |
| LIA: Encontrei 23 candidatos na sua base e 47 no           |
|      mercado. Aqui estao os destaques:                      |
|                                                             |
|      Sua Base (23):                                         |
|      - 8 com 5+ anos de experiencia                         |
|      - 5 ja entrevistados anteriormente                     |
|      - 3 marcados como favoritos                            |
|                                                             |
|      Mercado (47):                                          |
|      - 12 disponiveis imediatamente                         |
|      - 8 com experiencia em fintech                         |
|                                                             |
|      [Ver Sua Base] [Ver Mercado] [Filtrar mais]            |
|                                                             |
| Recrutador: "Filtre so os que falam ingles fluente"         |
|                                                             |
| LIA: Reduzi para 12 da sua base e 28 do mercado.           |
|      Notei que 4 candidatos da sua base trabalharam         |
|      em empresas americanas. Quer priorizar eles?           |
|                                                             |
|      [Sim, priorizar] [Mostrar todos]                       |
|                                                             |
| Recrutador: "Sim, e mostre so os de fintech"                |
|                                                             |
| LIA: Perfeito! Aqui estao os 6 candidatos:                  |
|      [Tabela com candidatos rankeados]                      |
|                                                             |
+-------------------------------------------------------------+
```

---

## 4. Componentes Tecnicos

### 4.1 Backend - Search Conversation Agent

**Localizacao**: `lia-agent-system/app/agents/specialized/search_conversation_agent.py`

```python
class SearchConversationAgent:
    """
    Agente de busca conversacional para o Funil de Talentos.
    Combina busca interna (PostgreSQL) com busca externa (Pearch AI).
    """
    
    actions = [
        "chat_search",           # Busca conversacional principal
        "refine_search",         # Refinamento iterativo
        "switch_source",         # Alternar entre fontes
        "explain_results",       # Explicar criterios de ranking
        "suggest_filters",       # Sugerir filtros proativamente
        "compare_candidates",    # Comparar candidatos selecionados
        "save_search",           # Salvar busca como template
        "export_results"         # Exportar resultados
    ]
    
    def __init__(self):
        self.sourcing_agent = SourcingAgent()  # Reutiliza agente existente
        self.pearch_client = PearchClient()    # Novo cliente Pearch
        self.conversation_memory = []          # Historico da conversa
```

### 4.2 Integracao Pearch AI

**Localizacao**: `lia-agent-system/app/services/pearch_service.py`

```python
class PearchService:
    """
    Servico de integracao com Pearch AI Chat Completions API.
    Documentacao: https://apidocs.pearch.ai/reference/post_chat-completions
    """
    
    BASE_URL = "https://api.pearch.ai/chat/completions"
    
    async def search_candidates(
        self,
        query: str,
        limit: int = 10,
        search_type: str = "pro",  # "fast" ou "pro"
        insights: bool = True,
        reveal_emails: bool = False,
        conversation_id: Optional[str] = None
    ) -> AsyncGenerator[dict, None]:
        """
        Busca candidatos via API conversacional da Pearch.
        Retorna stream de resultados (SSE format).
        
        Parametros extra_body disponiveis:
        - limit: numero de candidatos
        - type: "fast" (3-40s) ou "pro" (30-300s, mais preciso)
        - insights: notas de alinhamento por candidato
        - profile_scoring: ranking de relevancia
        - high_freshness: perfis em tempo real (mais caro)
        - reveal_emails/reveal_phones: dados de contato
        """
        payload = {
            "messages": [{"role": "user", "content": query}],
            "stream": True,
            "extra_body": {
                "limit": limit,
                "type": search_type,
                "insights": insights,
                "profile_scoring": True,
                "reveal_emails": reveal_emails,
                "filter_out_no_emails": reveal_emails
            }
        }
        
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                self.BASE_URL,
                json=payload,
                headers={
                    "Authorization": f"Bearer {PEARCH_API_KEY}",
                    "Accept": "text/event-stream"
                }
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        yield json.loads(line[6:])
```

### 4.3 Frontend - Chat Interface

**Localizacao**: `plataforma-lia/src/components/talent-funnel/ConversationalSearch.tsx`

```tsx
interface ConversationalSearchProps {
  onResultsChange: (candidates: Candidate[]) => void
  defaultSource: 'internal' | 'pearch' | 'both'
}

export function ConversationalSearch({ 
  onResultsChange, 
  defaultSource 
}: ConversationalSearchProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [source, setSource] = useState(defaultSource)
  
  const handleSendMessage = async (content: string) => {
    // Adiciona mensagem do usuario
    setMessages(prev => [...prev, { role: 'user', content }])
    setIsStreaming(true)
    
    // Chama API com streaming
    const response = await fetch('/api/v1/search/conversational', {
      method: 'POST',
      body: JSON.stringify({
        message: content,
        source,
        conversation_id: conversationId
      })
    })
    
    // Processa SSE stream
    const reader = response.body.getReader()
    // ... streaming logic
  }
  
  return (
    <div className="flex flex-col h-full">
      {/* Source selector */}
      <div className="flex gap-2 p-2 border-b">
        <Button 
          variant={source === 'internal' ? 'default' : 'outline'}
          onClick={() => setSource('internal')}
        >
          Minha Base
        </Button>
        <Button 
          variant={source === 'pearch' ? 'default' : 'outline'}
          onClick={() => setSource('pearch')}
        >
          Mercado
        </Button>
        <Button 
          variant={source === 'both' ? 'default' : 'outline'}
          onClick={() => setSource('both')}
        >
          Ambos
        </Button>
      </div>
      
      {/* Messages */}
      <ScrollArea className="flex-1 p-4">
        {messages.map((msg, i) => (
          <ChatMessage key={i} message={msg} />
        ))}
      </ScrollArea>
      
      {/* Input */}
      <ChatInput 
        onSend={handleSendMessage} 
        disabled={isStreaming}
        placeholder="Descreva o candidato ideal..."
      />
    </div>
  )
}
```

### 4.4 Estrutura de Dados

```typescript
interface ConversationMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  metadata?: {
    search_params?: SearchParams
    results_count?: number
    sources_used?: ('internal' | 'pearch')[]
    suggested_actions?: SuggestedAction[]
  }
}

interface SearchContext {
  conversation_id: string
  messages: ConversationMessage[]
  current_filters: SearchFilters
  cached_results: {
    internal: Candidate[]
    pearch: Candidate[]
  }
  user_preferences: {
    preferred_source: string
    show_suggestions: boolean
  }
}

interface SuggestedAction {
  label: string
  action: string
  params: Record<string, any>
}
```

---

## 5. Interface do Usuario

### 5.1 Layout Proposto - Modo Expandido

```
+------------------------------------------------------------------+
| FUNIL DE TALENTOS                                    [+ Novo] [S] |
+------------------------------------------------------------------+
|                                                                  |
|  +------------------------------------------------------------+ |
|  | Buscar candidatos...                              [Chat]   | |
|  |                                                             | |
|  | [Minha Base] [Mercado] [Ambos]                             | |
|  +------------------------------------------------------------+ |
|                                                                  |
|  +-----------------------------+--------------------------------+ |
|  |                             |                                | |
|  |    TABELA DE CANDIDATOS     |     CHAT COM LIA              | |
|  |                             |                                | |
|  |  [ ] Nome        Score  Exp |  LIA: Encontrei 23...         | |
|  |  ----------------------------  |                              | |
|  |  [ ] Maria       92%    5a  |  Voce: Filtre ingles          | |
|  |  [ ] Joao        88%    4a  |                                | |
|  |  [ ] Ana         85%    6a  |  LIA: Reduzi para 12...       | |
|  |                             |                                | |
|  |  [< 1 2 3 ... >]            |  [Digite sua mensagem...]     | |
|  |                             |                                | |
|  +-----------------------------+--------------------------------+ |
|                                                                  |
+------------------------------------------------------------------+
```

### 5.2 Modos de Visualizacao

| Modo | Descricao | Quando usar |
|------|-----------|-------------|
| **Compacto** | So prompt de busca, chat oculto | Buscas rapidas |
| **Expandido** | Chat ao lado da tabela (50/50) | Refinamento iterativo |
| **Super Expandido** | Chat fullscreen | Sourcing complexo |

### 5.3 Quick Actions (Chips)

```
[Mostrar analytics] [Refinar busca] [Salvar busca]
[Exportar] [Criar shortlist] [Contatar selecionados]
```

### 5.4 Sugestoes Proativas

A LIA sugere acoes baseadas no contexto:

```
LIA: Encontrei 23 candidatos React em SP.

[Filtrar por ingles] [Ver so seniors] [Incluir remoto]
[Comparar top 3] [Ver perfis completos]
```

---

## 6. Fluxos de Uso

### 6.1 Busca Simples (Minha Base)

```
Recrutador                   Interface                 Search Agent              Sourcing Agent            PostgreSQL
    |                           |                           |                         |                        |
    |-- "Devs React em SP" ---->|                           |                         |                        |
    |                           |-- chat_search() --------->|                         |                        |
    |                           |                           |-- search_candidates() ->|                        |
    |                           |                           |                         |-- SELECT with filters ->|
    |                           |                           |                         |<-- Candidates[] --------|
    |                           |                           |<-- Results with scores --|                        |
    |                           |<-- Streaming response ----|                         |                        |
    |<-- Chat + tabela ---------|                           |                         |                        |
```

### 6.2 Busca Global (Pearch)

```
Recrutador                   Interface              Search Agent              Pearch Service            Pearch API
    |                           |                        |                         |                        |
    |-- "Devs React" [Mercado]->|                        |                         |                        |
    |                           |-- chat_search() ------>|                         |                        |
    |                           |                        |-- search_candidates() ->|                        |
    |                           |                        |                         |-- POST /chat/completions|
    |                           |                        |                         |<-- SSE stream ---------|
    |                           |                        |<-- Parsed candidates ---|                        |
    |                           |<-- Streaming response -|                         |                        |
    |<-- Chat + candidatos -----|                        |                         |                        |
```

### 6.3 Busca Hibrida (Ambos)

```
Recrutador                   Search Agent              Sourcing Agent            Pearch Service
    |                           |                           |                         |
    |-- chat_search(both) ----->|                           |                         |
    |                           |                           |                         |
    |                           |== PARALELO ===============|=========================|
    |                           |-- search_internal() ----->|                         |
    |                           |-- search_external() ----------------------------->  |
    |                           |                           |                         |
    |                           |<-- Internal results ------|                         |
    |                           |<-- External results --------------------------------|
    |                           |                           |                         |
    |                           |-- merge + dedupe + rank --|                         |
    |                           |                           |                         |
    |<-- Unified results -------|                           |                         |
```

---

## 7. Integracoes

### 7.1 Environment Variables Necessarias

```env
# Pearch AI (NOVO)
PEARCH_API_KEY=pearch_xxx

# Ja existentes (Claude/Gemini)
ANTHROPIC_API_KEY=xxx
GEMINI_API_KEY=xxx
```

### 7.2 Integracoes Existentes Utilizadas

| Componente | Uso |
|------------|-----|
| **Sourcing Agent** | Reutiliza 12 actions existentes |
| **Semantic Search** | Gemini para interpretacao de linguagem natural |
| **Candidate API** | Endpoints existentes de candidatos |
| **PostgreSQL** | Base de candidatos internos |

### 7.3 Nova Integracao: Pearch AI

| Endpoint | Metodo | Descricao |
|----------|--------|-----------|
| `/chat/completions` | POST | Busca conversacional (SSE stream) |
| Parametros `extra_body` | | `limit`, `type`, `insights`, `reveal_emails` |

**Preco**: $600 por 10.000 creditos (~$0.06/candidato)

---

## 8. Custos

### 8.1 Custos Operacionais Mensais

| Componente | Volume Estimado | Custo |
|------------|-----------------|-------|
| Pearch API | 2.000 candidatos/mes | ~$120/mes |
| Claude API | 5.000 msgs/mes | ~$50/mes |
| Infraestrutura | Incluido (Replit) | $0 |
| **Total** | | **~$170/mes** |

### 8.2 Custo por Busca

| Fonte | Custo por Candidato |
|-------|---------------------|
| Base Interna | ~$0.01 (Claude) |
| Pearch | ~$0.06 (credito) |
| Hibrido | ~$0.035 (media) |

### 8.3 Comparativo com Concorrentes

| Solucao | Custo Anual | Observacao |
|---------|-------------|------------|
| **LIA + Pearch** | ~$2.000 | API-first, conversacional |
| HireEZ Starter | ~$2.000/user | Interface completa |
| Humanly | ~$12.000 | Chat + sourcing |
| LinkedIn Recruiter | ~$10.000+ | Acesso direto LinkedIn |
| SeekOut | Custom | Enterprise only |

### 8.4 ROI Esperado

- **Tempo economizado**: ~30% menos tempo por busca (refinamento vs. refazer)
- **Qualidade**: Candidatos mais relevantes pelo contexto conversacional
- **Satisfacao**: UX moderna comparavel a concorrentes premium
- **Diferencial**: Unico no mercado brasileiro com busca conversacional

---

## 9. Cronograma de Implementacao

### Fase 1: Base Interna Conversacional (Semana 1-2)

| Tarefa | Responsavel | Tempo |
|--------|-------------|-------|
| Criar SearchConversationAgent | Backend | 8h |
| Adaptar UI com chat expandido | Frontend | 6h |
| Implementar streaming SSE | Backend | 4h |
| Integrar com Sourcing Agent | Backend | 2h |
| Testes e ajustes | QA | 4h |
| **Subtotal** | | **24h** |

### Fase 2: Integracao Pearch (Semana 3)

| Tarefa | Responsavel | Tempo |
|--------|-------------|-------|
| Criar PearchService | Backend | 4h |
| Implementar autenticacao e streaming | Backend | 2h |
| Adicionar seletor de fonte | Frontend | 2h |
| Merge e deduplicacao de resultados | Backend | 2h |
| Testes com API real | QA | 2h |
| **Subtotal** | | **12h** |

### Fase 3: Experiencia Completa (Semana 4)

| Tarefa | Responsavel | Tempo |
|--------|-------------|-------|
| Modo Super Expandido (fullscreen) | Frontend | 4h |
| Quick Actions e sugestoes proativas | Frontend | 4h |
| Salvar buscas como templates | Full-stack | 3h |
| Analytics de uso | Backend | 2h |
| Documentacao e treinamento | Todos | 3h |
| **Subtotal** | | **16h** |

### Resumo de Esforco

| Fase | Backend | Frontend | Total |
|------|---------|----------|-------|
| Fase 1 | 14h | 6h | 20h + 4h QA |
| Fase 2 | 8h | 2h | 10h + 2h QA |
| Fase 3 | 5h | 8h | 13h + 3h doc |
| **Total** | **27h** | **16h** | **~52h** |

---

## 10. Riscos e Mitigacoes

### 10.1 Riscos Tecnicos

| Risco | Probabilidade | Impacto | Mitigacao |
|-------|---------------|---------|-----------|
| Latencia Pearch API (30-300s modo pro) | Media | Medio | Cache de resultados, mostrar progresso, usar modo "fast" para preview |
| Custo exceder orcamento | Baixa | Medio | Limites por usuario, alertas de uso, quotas mensais |
| Qualidade das respostas conversacionais | Baixa | Alto | Prompt engineering robusto, fallback para busca tradicional |
| Integracao complexa com streaming | Baixa | Medio | Fases incrementais, rollback facil, testes extensivos |
| Concorrencia de requests | Media | Baixo | Rate limiting, queue de requests |
| Indisponibilidade Pearch API | Baixa | Alto | Fallback automatico para busca interna, modo degradado |

### 10.2 Riscos de Compliance e LGPD

| Risco | Probabilidade | Impacto | Mitigacao |
|-------|---------------|---------|-----------|
| Transferencia internacional de dados | Alta | Alto | Ver secao 10.3 Compliance LGPD |
| Falta de base legal para sourcing externo | Media | Alto | Interesse legitimo + transparencia |
| Retencao de dados por terceiros (Pearch) | Media | Medio | Contrato DPA, auditoria de compliance |
| Falta de consentimento para contato | Media | Alto | Verificacao de opt-in antes de contato |

### 10.3 Compliance LGPD - Analise Detalhada

**Contexto Legal:**
A integracao com Pearch AI envolve busca de candidatos em bases publicas (LinkedIn, GitHub, etc.), o que requer analise cuidadosa da base legal.

**Base Legal Aplicavel:**
- **Interesse Legitimo (Art. 7, IX LGPD)**: Recrutamento e selecao constitui interesse legitimo do controlador
- **Dados Publicos (Art. 7, §4 LGPD)**: Dados manifestamente publicos podem ser tratados sem consentimento

**Requisitos para Conformidade:**

| Requisito | Implementacao |
|-----------|---------------|
| **Transparencia** | Informar candidato sobre origem dos dados no primeiro contato |
| **Finalidade** | Limitar uso a recrutamento especifico, nao marketing |
| **Necessidade** | Buscar apenas dados relevantes para a vaga |
| **Retencao** | Politica clara de exclusao apos processo seletivo |
| **Direitos do Titular** | Mecanismo de opt-out e exclusao sob demanda |

**Modelo de Consentimento para Primeiro Contato:**
```
Ola [Nome], encontramos seu perfil atraves de busca publica para a vaga de [Cargo].
Gostaríamos de conversar sobre a oportunidade.

Este contato esta em conformidade com a LGPD (interesse legitimo).
Caso nao deseje receber contatos, responda PARAR.
```

**Contrato com Pearch (DPA - Data Processing Agreement):**
- Verificar se Pearch possui DPA padrao
- Definir Pearch como Operador, LIA como Controlador
- Clausulas de transferencia internacional (SCCs)
- Direito de auditoria

**Transferencia Internacional:**
- Pearch provavelmente hospeda dados nos EUA
- Necessario: Standard Contractual Clauses (SCCs) ou certificacao adequada
- Documentar transferencia no ROPA (Record of Processing Activities)

### 10.4 Premissas Financeiras

**Volume Estimado por Cliente:**

| Perfil de Cliente | Vagas/mes | Buscas/vaga | Candidatos/busca | Total candidatos/mes |
|-------------------|-----------|-------------|------------------|---------------------|
| Pequeno (1-5 recrutadores) | 5 | 3 | 20 | 300 |
| Medio (6-15 recrutadores) | 20 | 4 | 25 | 2.000 |
| Grande (16+ recrutadores) | 50 | 5 | 30 | 7.500 |

**Custo por Perfil de Cliente:**

| Perfil | Candidatos/mes | Custo Pearch | Custo Claude | Total |
|--------|----------------|--------------|--------------|-------|
| Pequeno | 300 | $18 | $5 | $23/mes |
| Medio | 2.000 | $120 | $30 | $150/mes |
| Grande | 7.500 | $450 | $100 | $550/mes |

**Limites por Usuario (Controle de Custos):**

| Limite | Valor | Justificativa |
|--------|-------|---------------|
| Buscas Pearch/dia/usuario | 10 | Evitar abuso, incentivar refinamento |
| Candidatos Pearch/mes/empresa | 5.000 | Limite orçamentário |
| Alertas de uso | 70%, 90%, 100% | Notificacao preventiva |

**Modelo de Repasse (Opcional):**
- Incluir X creditos Pearch no plano base
- Creditos adicionais: $0.10/candidato (margem 67%)

### 10.5 Criterios de Go/No-Go (Fase Piloto)

**Criterios de Sucesso (GO):**

| Criterio | Meta | Prazo |
|----------|------|-------|
| Adocao | >40% dos recrutadores piloto usando chat | 30 dias |
| Satisfacao | NPS >30 | 30 dias |
| Custo por busca | <$0.15 medio | 30 dias |
| Taxa de erro | <2% | 30 dias |
| Qualidade de candidatos | >70% relevancia percebida | 30 dias |

**Criterios de Falha (NO-GO):**

| Criterio | Limite | Acao |
|----------|--------|------|
| Custo excedendo 2x orcamento | >$340/mes piloto | Pausar Pearch, manter interno |
| Latencia media >60s | Modo pro | Migrar para modo fast apenas |
| Taxa de erro >5% | Qualquer fonte | Rollback para busca tradicional |
| Reclamacoes de privacidade | Qualquer | Revisar fluxo de consentimento |
| Indisponibilidade Pearch >2h | Em horario comercial | Ativar fallback permanente |

**Plano de Fallback:**

1. **Modo Degradado**: Desabilitar Pearch, manter chat conversacional apenas para base interna
2. **Rollback Completo**: Voltar para prompt de busca tradicional (codigo preservado)
3. **Limite Emergencial**: Desabilitar novos requests Pearch via flag de configuracao

---

## 11. Metricas de Sucesso

### 11.1 KPIs Principais

| Metrica | Meta | Como medir |
|---------|------|------------|
| Adocao do chat | 60% dos recrutadores em 3 meses | Analytics de uso |
| Tempo medio por busca | -30% vs. busca tradicional | Comparacao antes/depois |
| Satisfacao (NPS) | +20 pontos | Survey pos-uso |
| Conversoes (contatos enviados) | +15% | Tracking de acoes |
| Candidatos encontrados/busca | +40% | Metricas de resultado |

### 11.2 Metricas Tecnicas

| Metrica | Meta |
|---------|------|
| Latencia media de resposta (interno) | < 2s |
| Latencia media de resposta (Pearch) | < 45s (modo pro) |
| Taxa de erro | < 1% |
| Uptime | 99.5% |

### 11.3 Metricas de Custo

| Metrica | Meta |
|---------|------|
| Custo por busca | < $0.10 |
| Custo mensal total | < $200 |
| ROI (tempo economizado) | > 200% |

---

## 12. Proximos Passos

1. **Aprovacao**: Revisar proposta com stakeholders
2. **Trial Pearch**: Solicitar creditos de teste para validar integracao
3. **Prototipacao**: Criar MVP da Fase 1 (busca interna conversacional)
4. **Validacao**: Teste com 5-10 recrutadores selecionados
5. **Ajustes**: Refinar baseado em feedback
6. **Fase 2**: Implementar integracao Pearch
7. **Rollout**: Lancamento gradual para todos usuarios

---

## 13. Anexos

### A. Prompt do Search Conversation Agent

```python
SEARCH_CONVERSATION_SYSTEM_PROMPT = """
Voce e a LIA, assistente de recrutamento da plataforma WeDoTalent.

Seu papel e ajudar recrutadores a encontrar candidatos ideais atraves de 
conversas naturais. Voce tem acesso a duas fontes:

1. Base Interna: Candidatos ja cadastrados no sistema
2. Mercado (Pearch): Candidatos do LinkedIn, GitHub e outras plataformas

CAPACIDADES:
- Interpretar requisitos em linguagem natural
- Executar buscas semanticas e por filtros
- Refinar resultados iterativamente
- Sugerir filtros e acoes uteis
- Comparar candidatos
- Explicar criterios de ranking

AO RECEBER UMA BUSCA:
1. Interprete a intencao do recrutador
2. Execute a busca na fonte apropriada
3. Apresente resultados de forma conversacional
4. Sugira refinamentos baseados nos resultados
5. Mantenha contexto para buscas iterativas

FORMATO DE RESPOSTA:
- Seja proativo: sugira filtros e acoes uteis
- Seja conciso: respostas diretas, sem rodeios
- Seja util: explique o raciocinio quando relevante
- Use emojis com moderacao para indicar categorias
- Inclua quick actions como sugestoes clicaveis

EXEMPLO:
Usuario: "preciso de devs python senior em SP"

Resposta:
Encontrei 18 candidatos Python Senior em Sao Paulo na sua base:

**Destaques:**
- 7 com 5+ anos de experiencia
- 4 com background em Data Science
- 3 ja entrevistados para outras vagas

Quer que eu filtre por algum criterio especifico?

[Machine Learning] [Django/FastAPI] [Ingles fluente] [Disponiveis agora]
"""
```

### B. Estrutura de Resposta Pearch API

```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion.chunk",
  "choices": [{
    "delta": {
      "content": "Encontrei 23 candidatos...",
      "candidates": [
        {
          "id": "uuid",
          "name": "Maria Silva",
          "title": "Senior React Developer",
          "location": "Sao Paulo, SP",
          "experience_years": 5,
          "skills": ["React", "TypeScript", "Node.js"],
          "match_score": 0.92,
          "insights": "Experiencia relevante em fintech, liderou equipe de 5 devs...",
          "linkedin_url": "https://linkedin.com/in/...",
          "email": "maria@...",  // se reveal_emails=true
          "current_company": "Nubank"
        }
      ]
    }
  }]
}
```

### C. API Endpoints Novos

```
POST /api/v1/search/conversational
- Inicia ou continua conversa de busca
- Body: { message, source, conversation_id? }
- Response: SSE stream

GET /api/v1/search/conversations/{id}
- Recupera historico de conversa
- Response: { messages[], cached_results }

POST /api/v1/search/conversations/{id}/save
- Salva busca como template
- Body: { name, description }

DELETE /api/v1/search/conversations/{id}
- Remove conversa

GET /api/v1/search/templates
- Lista templates salvos
```

### D. Configuracoes do Usuario

```typescript
interface UserSearchPreferences {
  default_source: 'internal' | 'pearch' | 'both'
  show_suggestions: boolean
  auto_expand_chat: boolean
  pearch_search_type: 'fast' | 'pro'
  reveal_contact_info: boolean
  max_results_per_search: number
}
```

---

**Documento criado em**: 2026-01-20  
**Ultima atualizacao**: 2026-01-20  
**Responsavel**: Equipe de Produto LIA

---

## Aprovacoes

| Stakeholder | Status | Data |
|-------------|--------|------|
| Produto | Pendente | - |
| Engenharia | Pendente | - |
| Design | Pendente | - |
| Financeiro | Pendente | - |
