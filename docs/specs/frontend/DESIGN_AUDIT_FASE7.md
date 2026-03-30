# Design Audit — Fase 7 (Notion/ElevenLabs Pattern)
**Data:** 2026-03-30

## Achados de Espaçamento

### Padding/Spacing Arbitrário (produção)
| Ocorrência | Arquivo | Resolução |
|---|---|---|
|  |  | Corrigido para  |
|  |  | Corrigido para  |
|  (×2) |  | Corrigido para  |

### Width/Height Arbitrário (backlog — valores contextuais)
Os valores , , ,  etc. são contextuais
(viewports, responsividade, proporções de charts). Catalogados para revisão futura.

Top 5 mais frequentes:
-  — 55 ocorrências (modais, painéis laterais)
-  — 28 ocorrências (mensagens de chat, bubbles)
-  — 24 ocorrências (sidebars, dropdowns)
-  — 21 ocorrências (charts, listas)
-  — 22 ocorrências (avatares, thumbnails)

## Achados de Tipografia

### Tamanhos Arbitrários (produção)
| Ocorrência | Arquivo | Resolução |
|---|---|---|
|  |  | Corrigido para  |
|  |  | Corrigido para  |
|  | componente de badge | Uso de CSS var — aceitável |

### Escala Semântica nos Componentes UI
O sistema de tipografia em  usa escala semântica correta:
-  para captions, labels, badges
-  para corpo de texto secundário
-  para títulos de seção
-  para headings principais
- Sem mistura de escalas arbitrárias nos componentes de sistema

## Achados de Dark Mode

### Tokens Incorretos Encontrados (antes da correção)
Total: **162 ocorrências** de  ou  em arquivos de produção.

Distribuição por tipo:
-  (91) — Padrão intencional para botões CTA invertidos. Mapeado em . NÃO corrigido (correto).
-  (16) — Variante hover de botões CTA. NÃO corrigido (correto).
-  (22) — Progress bars / fill de charts. Corrigido para 
-  (3) — Progress fill médio. Corrigido para 
-  (3+) — Badges de status. Corrigido para 
-  (2) — Non-standard Tailwind (não existe). Corrigido para 
-  (1) — Non-standard Tailwind (não existe). Corrigido para 
-  (2) — Texto primário invertido. Corrigido para 
-  (18) — Apenas em arquivos . Ignorado.
-  (2) — Apenas em arquivos . Ignorado.

## Consistência de Cards

### Componente Base ()
O card base está bem implementado:
-  para modo claro
-  para dark — tokens corretos
- CardHeader:  — padding consistente
- CardContent:  — consistente com header
- CardFooter:  — consistente
- CardTitle: 
- CardDescription: 

Ponto de atenção:  usa  — pode ser subescalado. Considerar  em revisão futura.

### Shadow e Border
As shadows estão configuradas via CSS variables (,  etc.)
definidas em  e não via classes Tailwind arbitrárias — correto.

## Correções Aplicadas

### Espaçamentos Arbitrários (5 tokens fixados)
1.  ->  em 
2.  ->  em 
3.  ->  (x2) em 
4.  ->  em 
5.  ->  em 

### Dark Mode Tokens (33+ tokens fixados em 12 arquivos)
| Antes | Depois | Arquivos Afetados |
|---|---|---|
|  |  | onboarding-page, onboarding-premium-page, real-time-dashboard-page, add-candidate-modal, executive-dashboard-page, DiversidadeInclusaoDashboard, JobPreviewPanel, StrategicTab, WorkModelsTab, RecruitersTab, work-model-analytics-page |
|  |  | add-list-to-vacancies-modal, TestPreviewModal, JobPreviewPanel |
|  |  | LIAQuestionsPanel, TestHistoryModal, jobs-page, TestLibraryModal |
|  |  | JobPreviewPanel |
|  |  | dashboards-page |
|  |  | job-insights-modal |
|  |  | job-insights-modal |

## Backlog (próximo sprint)

### Alta Prioridade
- [ ] Criar token  para substituir  em botões CTA (91 ocorrências) — tornando a intenção semântica explícita
- [ ] CardTitle usa  — avaliar se  seria mais adequado para acessibilidade
- [ ] Verificar se  (176px) é visual/funcionalmente equivalente ao  original nos inputs do EAP

### Média Prioridade
- [ ] Revisar , ,  em modais — criar utilitários ,  no design system
- [ ] Catalogar todos  para sidebars e criar tokens semânticos (ex: , )
- [ ] Mover arquivos  para fora do  para evitar falsos positivos em auditorias futuras

### Baixa Prioridade
- [ ] Documentar classe  no design system
- [ ] Alinhar  nos archived com tokens LIA antes de possível restauração
