# Comparação de Vagas - Implementação LIA

## Visão Geral

Sistema de comparação de vagas com análise inteligente pela LIA (Learning Intelligence Assistant).

## Componentes

### Frontend

#### JobCompareModal (`plataforma-lia/src/components/modals/job-compare-modal.tsx`)

Modal rico para comparação visual de vagas incluindo:

1. **Cards Resumo**
   - Total Candidatos
   - Performance Média
   - Taxa Conversão
   - Em Triagem

2. **Tabela Comparativa**
   - Candidatos (com indicador "Melhor")
   - Aprovados
   - Triagem
   - Salário
   - Local
   - Performance
   - Requisitos Técnicos
   - Competências Comportamentais
   - Benefícios

3. **Funil de Candidatos** (novo)
   - Barras horizontais com percentuais
   - Candidatos (100%)
   - Em Triagem (%)
   - Aprovados (%)
   - Cores distintas por vaga (cyan, purple, emerald, orange)

4. **Análise LIA**
   - Resumo textual comparativo
   - Indicadores-Chave (métricas principais)
   - Insights categorizados por tipo:
     - **Ação Recomendada** (amarelo) - Ações urgentes
     - **Análise** (roxo) - Observações analíticas
     - **Comparativo** (azul) - Diferenças entre vagas
     - **Atenção** (vermelho) - Alertas importantes
   - Recomendações com bullets

5. **Exportação**
   - Exportar PDF
   - Compartilhar (Web Share API)

#### Hook useJobAnalytics (`plataforma-lia/src/hooks/use-job-analytics.ts`)

```typescript
const { compareJobs, loading, error, result } = useJobAnalytics()

// Comparar vagas
await compareJobs(['job-id-1', 'job-id-2'])
```

### Backend

#### JobAnalyticsPromptService (`lia-agent-system/app/services/job_analytics_prompt_service.py`)

Serviço que roteia queries de comparação para agentes especializados.

**Command Template:**
```python
"comparative_analysis": {
    "name": "Análise Comparativa",
    "description": "Compara métricas entre vagas",
    "prompt_template": "Compare as vagas selecionadas: {job_titles}...",
    "agent": "AnalistaFeedbackAgent",
    "agent_type": AgentType.ANALYST_FEEDBACK,
    "required_context": ["job_ids"],
    "intent": "comparar_vagas"
}
```

**Padrões de Query (NLP):**
- "comparar vagas"
- "diferença entre as vagas"
- "qual vaga está melhor"

#### API Endpoint (`plataforma-lia/src/lib/api/job-analytics.ts`)

```typescript
POST /api/backend-proxy/job-analytics?action=compare
Body: { job_ids: string[] }
Response: AnalyticsResponse
```

## Uso no Chat LIA

Quando o recrutador perguntar:
- "Compare minhas vagas ativas"
- "Qual vaga tem melhor performance?"
- "Compare a vaga de Analista com a de Product Manager"

O sistema detecta a intent `comparar_vagas` e executa o `comparative_analysis` command.

## Fluxo de Integração

```
┌─────────────────┐    ┌──────────────────────┐    ┌───────────────────┐
│   Chat LIA      │───>│ JobAnalyticsPrompt   │───>│ AnalistaFeedback  │
│   (Frontend)    │    │ Service              │    │ Agent             │
└─────────────────┘    └──────────────────────┘    └───────────────────┘
                              │
                              v
                       ┌──────────────────────┐
                       │ AnalyticsResponse    │
                       │ - response           │
                       │ - data               │
                       │ - charts             │
                       │ - suggestions        │
                       └──────────────────────┘
                              │
                              v
                       ┌──────────────────────┐
                       │ JobCompareModal      │
                       │ (Visualização Rica)  │
                       └──────────────────────┘
```

## Tipos de Insight

| Tipo | Cor | Ícone | Exemplo |
|------|-----|-------|---------|
| `action_recommended` | Amarelo | Zap | "Alto volume em triagem - priorize avaliações" |
| `analysis` | Roxo | Search | "Taxa de conversão média abaixo de 10%" |
| `comparative` | Azul | ArrowRightLeft | "Vaga A tem 49% mais candidatos que Vaga B" |
| `attention` | Vermelho | XCircle | "Vaga está há 15 dias sem aprovações" |

## Melhorias Implementadas (Janeiro 2026)

1. **Funil Visual de Candidatos** - Barras horizontais com progressão visual
2. **Insights Categorizados** - Sistema de cores e badges por tipo de insight
3. **Cores por Vaga** - Identificação visual distinta para cada vaga comparada

## Arquivos Relacionados

- `plataforma-lia/src/components/modals/job-compare-modal.tsx` - Modal principal
- `plataforma-lia/src/hooks/use-job-analytics.ts` - Hook React
- `plataforma-lia/src/lib/api/job-analytics.ts` - API client
- `lia-agent-system/app/services/job_analytics_prompt_service.py` - Serviço backend
- `lia-agent-system/app/agents/specialized/analista_feedback_agent.py` - Agente de análise
