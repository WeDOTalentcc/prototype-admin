# Auditoria de uso de `Sparkles` (vs cérebro da LIA)

**Versão:** 1.1 — 2026-04-21
**Tarefas:** #723 (auditoria inicial), #725 (reavaliação do estágio `enriquecida`)

## Regra geral
O ícone oficial da LIA é o **cérebro ciano** (`LIAIcon` em `src/components/ui/lia-icon.tsx`,
baseado em `Brain` do `lucide-react` com `text-wedo-cyan`). Sempre que um ícone representar
**a LIA, uma sugestão da LIA, uma ação da IA da LIA ou onboarding/personalização da LIA**,
ele deve ser o cérebro — `LIAIcon` quando o componente puder receber o wrapper completo, ou
`Brain` ciano inline quando estamos dentro de um mapa de ícones (`Record<string, LucideIcon>`)
ou em um avatar/quadrado já dimensionado.

`Sparkles` só permanece em casos **comprovadamente não-LIA**:
- Badges genéricos de "novo / experimental / beta".
- Estágios de funil/categorias do workflow rail que não são "a LIA falando".
- Mapas de ícones de backend onde `sparkles` é literalmente o nome semântico recebido.

---

## Tabela de ocorrências

Convenção da coluna **Decisão**:
- 🧠 **Substituir por LIAIcon/Brain** — representa a LIA ou IA da LIA.
- ✨ **Manter Sparkles** — não-LIA (badges, categorias, mapeamento backend).

| # | Arquivo:linha | Contexto | Decisão | Justificativa |
|---|---|---|---|---|
| 1 | `components/onboarding/SetupProgressBanner.tsx:70` | Avatar do banner "Sua configuração está X% completa". Texto adjacente: "Faltam ~X% para a LIA personalizar suas vagas". | 🧠 Brain | Representa explicitamente a LIA. |
| 2 | `components/unified-chat/SmartSuggestions.tsx:78` | Avatar circular acima do greeting "Bom dia! Eu sou a LIA". | 🧠 Brain | É a apresentação da LIA. |
| 3 | `components/unified-chat/SmartSuggestions.tsx:33` | Item de sugestão "jobAnalytics" na lista de sugestões inteligentes da LIA. | 🧠 Brain | A sugestão vem da LIA; o ícone está representando a IA, não "destaque genérico". |
| 4 | `components/unified-chat/wizard/panels/JdEnrichmentPanel.tsx:141` | Cabeçalho "Alterações realizadas pela IA" no painel de enriquecimento de JD. | 🧠 Brain | Ação da IA da LIA durante o wizard. |
| 5 | `components/chat/proactive-hints-list.tsx:158` | Marcador inline ao lado de cada hint proativo gerado pela LIA. | 🧠 Brain | Hints proativos são geração da LIA. |
| 6 | `components/settings/RecruiterPreferencesPanel.tsx:132` | Cabeçalho "Aprendido pela IA" dentro do card "Personalização da LIA". | 🧠 Brain | Card é literalmente sobre o que a LIA aprendeu. |
| 7 | `components/settings/OnboardingSettingsToggle.tsx:52` | Avatar do toggle "Onboarding com LIA". | 🧠 Brain | Toggle de feature da LIA. |
| 8 | `components/candidate-preview/PipelineDecisionBar.tsx:570` | Marcador antes do resumo de candidato gerado pela LIA (estado sem job). | 🧠 Brain | Resumo gerado pela LIA. |
| 9 | `components/candidate-preview/PipelineDecisionBar.tsx:655` | Marcador antes do resumo de candidato gerado pela LIA (estado normal). | 🧠 Brain | Idem 8. |
| 12 | `components/pages/jobs-page.tsx:131` | Botão "Prontidão" no header da página de Vagas. | 🧠 Brain | Atalho para o Hub da LIA. |
| 13 | `components/pages/modules-page.tsx:96` | Mapa `STATUS_DISPLAY` — status `experimental`. | ✨ Manter | Indicador genérico de feature experimental, sem vínculo com LIA. |
| 14 | `components/pages/modules-page.tsx:97` | Mapa `STATUS_DISPLAY` — status `beta`. | ✨ Manter | Indicador genérico de feature em beta. |
| 15 | `components/pages/modules-page.tsx:358` | Cabeçalho da seção "Disponível em Beta" (cor `text-wedo-purple`). | ✨ Manter | Seção genérica "novidades / beta", roxa, não LIA. |
| 16 | `components/pages/pipeline-overview-page.tsx:150` | Mapa `JOB_LIFECYCLE_STAGE_ICONS` — estágio `enriquecida`. | 🪄 Substituir por `Wand2` | Reavaliado na Tarefa #725. `Sparkles` destoava da rail (cujos vizinhos `Database`, `FileText`, `ListChecks`, `ShieldCheck`, `Send`, `Radio`, `Archive` são todos pictogramas semânticos neutros) — soava "celebratório/mágico" demais para um marcador de estágio. Substituído por `Wand2`, que mantém a leitura semântica de "transformação/enriquecimento de dados" sem invocar o cérebro ciano (reservado a contextos onde a LIA é a interlocutora, não onde a IA é só o motor por trás de um passo do funil). |
| 17 | `components/chat/pipeline-rail-card.tsx:13,70` | Mapa `ICON_MAP` recebe nomes de ícones do backend; `"sparkles"` mapeia para `Sparkles`. | ✨ Manter | É um mapeamento literal: se o backend pede `sparkles`, recebe `Sparkles`. Remover quebraria payloads existentes. |
| 18 | `components/ui/chat-workflow-reels.tsx:81` | Categoria utilitária `ia-automacoes` no Workflow Reels (ao lado de `analytics` e `configuracoes`). | ✨ Manter | É a "categoria" do agent-studio (automações de IA em geral, não a LIA assistente). Mantém paridade visual com as outras categorias utilitárias. |
| 19 | `components/workflow-rail/canonicalFunnelStages.ts:168` | Stage canônico `ia-automacoes` (gêmeo do item 18). | ✨ Manter | Mesmo motivo do item 18. |

### Emoji `✨`

Todas as ocorrências do emoji `✨` foram revisadas:

| Arquivo | Contexto | Decisão |
|---|---|---|
| `components/job-description/types.ts:195` (`NEW_INDICATOR`) e `field-origin-badge.tsx:117` | Indicador genérico de "campo novo / preenchido pela IA" usado em badges de origem. | ✨ Manter — funciona como um símbolo de "novo/destaque" e está fora do escopo (não é o avatar de fala da LIA). |
| `workflowRailCatalog.ts:147,234` (`generate_jd`, `lia_opinion` "next steps") | Ícones inline (string emoji) da rail de próximos passos. | ✨ Manter por ora — substituição exigiria refatoração da rail (que renderiza emoji puro). Pode ser endereçado em tarefa futura. |
| `expandable-ai-prompt/useEAPCommandCallbacks.ts:213`, `PromptSuggestionsPanel.tsx:130` | Categoria `employer_branding` em listas dinâmicas de sugestões. | ✨ Manter — é uma categoria temática, não fala da LIA. |
| `WizardAgentStep.tsx:99` | Botão "Auto" no wizard de criação de agente. | ✨ Manter — significa "automático/sugerido", não fala da LIA. |
| `PreviewSuggestionModal.tsx:203,216`, `useScreeningGuide.ts:228`, `useKanbanLIAHandlers.ts:228`, `useWSIAndCalibrationHandlers.ts:664`, `module-upsell.tsx:160`, `contact-modal.tsx:230`, `ActivityScreeningDetails.tsx:49`, `ActivityEvaluationDetails.tsx:116` | Strings de mensagens, e-mails, mocks de banner — emoji decorativo dentro de texto. | ✨ Manter — emoji em string literal, fora do escopo do avatar visual. |

A substituição de emojis dentro de strings (especialmente templates de mensagens e
mockups) está fora do escopo desta tarefa, que foca no ícone visual `Sparkles`
representando a LIA.

---

## Resumo
- **Total de ocorrências de `Sparkles` em produção:** 19 callsites únicos (12 substituições por `Brain` + 1 substituição por `Wand2` + 6 mantidos).
- **Substituídas por `Brain` ciano:** 12 (todas LIA-explícitas).
- **Substituídas por `Wand2`:** 1 (estágio `enriquecida` do funil de vagas — Tarefa #725).
- **Mantidas:** 6 (badges genéricos, mapeamento backend e categorias não-LIA).
- **Validador:** regra leve adicionada em `scripts/design-system-validator.py` (fase 7) para
  alertar quando um novo `Sparkles` aparecer próximo a textos como `LIA`, `assistente` ou
  `IA da` — evitando regressões.
