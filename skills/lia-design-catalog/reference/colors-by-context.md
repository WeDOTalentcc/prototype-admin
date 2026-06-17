# Colors by Context Reference - Design System LIA v4.1

## Job Status Colors
| Status | Badge BG | Badge Text | Border | Quando Mostrar |
|--------|----------|------------|--------|----------------|
| **Aberta** | `bg-green-50` | `text-green-700` | `border-green-200` | Vaga publicada e recebendo |
| **Pausada** | `bg-amber-50` | `text-amber-700` | `border-amber-200` | Temporariamente suspensa |
| **Fechada** | `bg-gray-100` | `text-gray-700` | `border-gray-200` | Vaga preenchida |
| **Rascunho** | `bg-blue-50` | `text-blue-700` | `border-blue-200` | Em criação |

## Candidate Status Colors
| Status | Badge BG | Badge Text | Border | Ícone |
|--------|----------|------------|--------|-------|
| **Novo** | `bg-blue-50` | `text-blue-700` | `border-blue-200` | Plus |
| **Em Triagem** | `bg-amber-50` | `text-amber-700` | `border-amber-200` | Clock |
| **Aprovado** | `bg-green-50` | `text-green-700` | `border-green-200` | CheckCircle |
| **Rejeitado** | `bg-red-50` | `text-red-700` | `border-red-200` | XCircle |
| **Contratado** | `bg-green-100` | `text-green-800` | `border-green-300` | Check |

## WeDo Accent Contexts (10% Accent)
| Contexto | Cor Base | Badge BG | Quando Usar |
|----------|----------|----------|-------------|
| **LIA / Automação** | Cyan #60BED1 | `rgba(96,190,209,0.1)` | Features IA, brain icon |
| **Candidatos** | Green #5DA47A | `rgba(93,164,122,0.1)` | Perfis, talentos |
| **Tempo / Prazo** | Orange #D19960 | `rgba(209,153,96,0.1)` | Urgência, deadlines |
| **Insights / IA** | Purple #9860D1 | `rgba(152,96,209,0.1)` | Análises, sugestões |
| **Crítico** | Magenta #D160AB | `rgba(209,96,171,0.1)` | Alta prioridade |

## Badge Implementation
```html
<!-- Job Status -->
<span class="inline-flex items-center px-2 py-1 rounded-sm text-[10px] font-medium bg-green-50 text-green-700 border border-green-200">Aberta</span>
<span class="inline-flex items-center px-2 py-1 rounded-sm text-[10px] font-medium bg-amber-50 text-amber-700 border border-amber-200">Pausada</span>
<span class="inline-flex items-center px-2 py-1 rounded-sm text-[10px] font-medium bg-gray-100 text-gray-700 border border-gray-200">Fechada</span>
<span class="inline-flex items-center px-2 py-1 rounded-sm text-[10px] font-medium bg-blue-50 text-blue-700 border border-blue-200">Rascunho</span>

<!-- WeDo Accent -->
<span class="inline-flex items-center px-2 py-1 rounded-sm text-[10px] font-medium text-[#60BED1] border border-[#60BED1]/20" style="background: rgba(96,190,209,0.1);">LIA</span>
<span class="inline-flex items-center px-2 py-1 rounded-sm text-[10px] font-medium text-[#5DA47A] border border-[#5DA47A]/20" style="background: rgba(93,164,122,0.1);">Candidato</span>
<span class="inline-flex items-center px-2 py-1 rounded-sm text-[10px] font-medium text-[#D19960] border border-[#D19960]/20" style="background: rgba(209,153,96,0.1);">Urgente</span>
<span class="inline-flex items-center px-2 py-1 rounded-sm text-[10px] font-medium text-[#9860D1] border border-[#9860D1]/20" style="background: rgba(152,96,209,0.1);">Insight</span>
<span class="inline-flex items-center px-2 py-1 rounded-sm text-[10px] font-medium text-[#D160AB] border border-[#D160AB]/20" style="background: rgba(209,96,171,0.1);">Crítico</span>
```
