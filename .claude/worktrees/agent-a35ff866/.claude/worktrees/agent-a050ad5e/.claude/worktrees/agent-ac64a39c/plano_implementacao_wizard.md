# Plano de Implementação - Job Creation Wizard (Fast Track)

## Objetivo
Transformar o wizard de criação de vagas em um sistema Fast Track inteligente onde a 10ª vaga é criada 80% mais rápido que a 1ª (15 min → 3 min).

---

## Status Geral de Implementação

| Fase | Status | Progresso |
|------|--------|-----------|
| Fase 1: Templates Curados | ✅ Parcial | 50/480 templates (10.4%) |
| Fase 2: Learning Loop Backend | ✅ Concluído | 100% |
| Fase 3: Fast Track UX | ✅ Concluído | 100% |
| Fase 4: Learning Loop Inteligente | ✅ Concluído | 100% |
| **Fase 5: Polimento Final** | ✅ Concluído | 100% (core) |

---

## Fase 5: Polimento Final ✅ CONCLUÍDO

### 5.1 Tarefas Implementadas

#### ALTA PRIORIDADE - Funcionalidades Core ✅

| # | Tarefa | Descrição | Status | Localização |
|---|--------|-----------|--------|-------------|
| 1 | Confirmação de Campos Sensíveis | Após Fast Track, LIA pergunta: gestor, localização, vaga afirmativa | ✅ | `expanded-chat-modal.tsx:5195-5350` |
| 2 | Regeneração WSI Frontend | Detecta mudanças em competências e oferece regenerar perguntas | ✅ | `expanded-chat-modal.tsx:1240-1286, 5105-5190` |
| 3 | Pré-qualificação Global | Busca perguntas globais das Configurações via `useCompanyEligibilityQuestions` | ✅ | `expanded-chat-modal.tsx:684, 2174-2186, 3878` |

#### MÉDIA PRIORIDADE - Analytics & Tracking ✅

| # | Tarefa | Descrição | Status | Localização |
|---|--------|-----------|--------|-------------|
| 4 | Evento `fast_track_suggestion_shown` | Dispara quando sugestões são exibidas | ✅ | `expanded-chat-modal.tsx:1205` |
| 5 | Evento `fast_track_accepted` | Dispara quando usuário aceita sugestão | ✅ | `expanded-chat-modal.tsx:5480` |
| 6 | Evento `fast_track_rejected` | Dispara em 3 pontos: negativa explícita, from_scratch, UI dismiss | ✅ | `expanded-chat-modal.tsx:5518, 5556, 5586, 7657` |
| 7 | Evento `fast_track_wsi_regenerated` | Dispara quando WSI é regenerado após mudança de competências | ✅ | `expanded-chat-modal.tsx:5153` |

#### BAIXA PRIORIDADE - Expansão de Templates ⏳

| # | Tarefa | Descrição | Status |
|---|--------|-----------|--------|
| 8 | Templates Operações/Supply Chain | 35 templates | ⏳ Pendente |
| 9 | Templates Engenharia | 50 templates | ⏳ Pendente |
| 10 | Templates Jurídico/Compliance | 25 templates | ⏳ Pendente |
| 11 | Templates demais áreas | 320 templates restantes | ⏳ Pendente |

### 5.2 Fluxo Completo Fast Track (Implementado)

```
┌─────────────────────────────────────────────────────────────────────┐
│ ETAPA 1: DETECÇÃO (✅ IMPLEMENTADO)                                 │
│ Usuário digita título da vaga                                       │
│ Sistema busca vagas similares (>70% match semântico)               │
└───────────────────────────────┬─────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ ETAPA 2: SUGESTÃO CONVERSACIONAL (✅ IMPLEMENTADO)                  │
│ LIA mostra sugestões no chat + painel lateral                       │
│ Usuário responde em linguagem natural ("sim", "a 2", "não")         │
│ Analytics: fast_track_suggestion_shown                              │
└───────────────────────────────┬─────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ ETAPA 3: CÓPIA COMPLETA (✅ IMPLEMENTADO)                           │
│ Copia: título, descrição, skills, salário, WSI, etc.               │
│ Preenche todos os campos automaticamente                            │
│ Analytics: fast_track_accepted                                      │
└───────────────────────────────┬─────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ ETAPA 4: CAMPOS SENSÍVEIS (✅ IMPLEMENTADO)                         │
│                                                                     │
│ LIA: "Copiei tudo! Só preciso confirmar alguns detalhes:            │
│ - Quem é o gestor desta vaga?                                       │
│ - A localização continua [cidade anterior]?                         │
│ - Essa vaga é afirmativa para algum grupo?"                         │
│                                                                     │
│ Usuário responde em linguagem natural                               │
│ LIA interpreta via NLU e preenche campos                            │
└───────────────────────────────┬─────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ ETAPA 5: REVISÃO (✅ IMPLEMENTADO - FastTrackReviewPanel)           │
│ Painel lateral com seções colapsáveis para edição                   │
│ LIA: "Quer ajustar algo ou posso publicar?"                         │
└───────────────────────────────┬─────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ ETAPA 6: REGENERAÇÃO WSI (✅ IMPLEMENTADO)                          │
│                                                                     │
│ SE usuário editou competências:                                     │
│ LIA: "Percebi que você alterou competências (+React, -Angular).     │
│ Quer que eu atualize as perguntas WSI?"                             │
│                                                                     │
│ Usuário: "sim" → Chama /wsi/regenerate-questions                    │
│ Usuário: "não" → Mantém perguntas originais                         │
│ Analytics: fast_track_wsi_regenerated                               │
└───────────────────────────────┬─────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ ETAPA 7: PUBLICAÇÃO (✅ IMPLEMENTADO)                               │
│ Botão "Publicar Vaga" no painel                                     │
│ Registra Fast Track usage + gera embedding                          │
│ Inclui eligibility_questions da pré-qualificação global             │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.3 Campos Sensíveis - Implementação

**Filosofia:** LIA interpreta respostas em linguagem natural (sem dropdowns)

| Campo | Pergunta LIA | Padrões Reconhecidos | Status |
|-------|--------------|----------------------|--------|
| Gestor | "Quem é o gestor desta vaga?" | Nome completo, regex extração | ✅ |
| Localização | "A localização continua [cidade]?" | "sim", "não, [cidade]", "remoto" | ✅ |
| Vaga Afirmativa | "Essa vaga é afirmativa?" | "não", "sim, para [grupo]", grupos específicos | ✅ |

**Estados de controle:**
- `awaitingSensitiveFieldsConfirmation`: Gates resposta do usuário
- `fastTrackAppliedData`: Armazena dados para referência na pergunta

### 5.4 Regeneração WSI - Implementação

**Trigger:** Usuário edita competências técnicas ou comportamentais no painel

**Estados de controle:**
- `fastTrackOriginalCompetencies`: Salva skills originais do Fast Track
- `wsiRegenerationPrompted`: Previne prompts duplicados
- `awaitingWSIRegenerationConfirmation`: Gates resposta do usuário

**Fluxo implementado:**
1. Fast Track aplicado → salva competências originais
2. useEffect monitora mudanças em `technicalSkills` / `behavioralCompetencies`
3. Se mudança detectada durante stage 'competencies':
   - Gera summary de mudanças (+skill, -skill)
   - LIA pergunta conversacionalmente
4. Usuário responde "sim" → chama API regenerateWSIQuestions
5. Novas perguntas substituem as anteriores
6. Analytics: `fast_track_wsi_regenerated` disparado

### 5.5 Pré-qualificação Global - Implementação

**Hook utilizado:** `useCompanyEligibilityQuestions()`

**Fluxo:**
1. Hook carrega perguntas da empresa automaticamente (linha 684)
2. Perguntas sincronizadas para `companyDefaultQuestions` (linha 2174)
3. Mantidas separadas dos dados Fast Track (não sobrescritas)
4. Incluídas no payload final como `eligibility_questions` (linha 3878)

### 5.6 Analytics Events - Implementação

| Evento | Payload | Pontos de Disparo |
|--------|---------|-------------------|
| `fast_track_suggestion_shown` | `{ accepted: false }` | Quando sugestões aparecem (1205) |
| `fast_track_accepted` | `{ accepted: true }` | Quando usuário aceita (5480) |
| `fast_track_rejected` | `{ accepted: false }` | 3 pontos: explícito (5518), from_scratch (5556, 5586), UI dismiss (7657) |
| `fast_track_wsi_regenerated` | `{ accepted: true }` | Após regeneração bem-sucedida (5153) |

**Prevenção de duplicatas:**
- `fastTrackSuggestionsShownTracked`: Previne múltiplos `suggestion_shown`
- Estados de awaiting previnem eventos durante confirmações

---

## Fases Anteriores (Referência)

### Fase 1: Biblioteca de Templates ✅ PARCIAL

| Categoria | Templates Base | Expandidos | Status |
|-----------|---------------|------------|--------|
| Tecnologia | 15 | 64 | ✅ |
| Vendas | 10 | 30 | ✅ |
| RH | 8 | 24 | ✅ |
| Finanças | 9 | 30 | ✅ |
| Marketing | 8 | 24 | ✅ |
| **Total Implementado** | **50** | **172** | **10.4%** |

### Fase 2: Learning Loop Backend ✅ CONCLUÍDO

- [x] Endpoint `/api/v1/job-templates/learning/learn-from-job`
- [x] Endpoint `/api/v1/job-embeddings/fast-track`
- [x] Endpoint `/api/v1/job-embeddings/record-usage`
- [x] Endpoint `/api/v1/job-embeddings/update-outcome`
- [x] `JobEmbeddingService` com OpenAI embeddings
- [x] Busca semântica por similaridade coseno (>70%)
- [x] Ponderação por `success_weight`

### Fase 3: Fast Track UX ✅ CONCLUÍDO

- [x] Hook `useFastTrack` com detecção automática
- [x] Componente `FastTrackSuggestions` (cards informativos)
- [x] Componente `FastTrackReviewPanel` (seções colapsáveis)
- [x] Fluxo conversacional (1 sugestão → aplica direto; N sugestões → pede número)
- [x] Tratamento de erros robusto
- [x] Reset automático de estado
- [x] Endpoint `/wsi/regenerate-questions` (backend pronto)
- [x] Confirmação de campos sensíveis pós-Fast Track
- [x] Detecção de mudança de competências + regeneração WSI

### Fase 4: Learning Loop Inteligente ✅ CONCLUÍDO

- [x] Success weights (hired→1.2, cancelled→0.8)
- [x] Tracking automático de outcomes
- [x] Multi-tenant support via `company_id`
- [x] Wrapper `updateJobVacancyStatusWithOutcome()`

---

## Pendências Restantes

### Prioridade Baixa (Expansão de Templates)

| Categoria | Templates Necessários | Estimativa |
|-----------|----------------------|------------|
| Operações/Supply Chain | 35 | 2-3 dias |
| Engenharia | 50 | 3-4 dias |
| Jurídico/Compliance | 25 | 2 dias |
| Demais áreas | 320 | 8-10 dias |
| **Total** | **430** | **~15-20 dias** |

### Próximos Passos Sugeridos

1. **Medição de métricas** - Coletar dados reais de uso para validar objetivo 80% saving
2. **Expansão de templates** - Priorizar áreas com maior volume de vagas
3. **Refinamento NLU** - Melhorar padrões de reconhecimento de campos sensíveis
4. **A/B testing** - Comparar fluxo Fast Track vs tradicional

---

## Métricas de Sucesso

| Métrica | Baseline | Target | Status |
|---------|----------|--------|--------|
| Tempo 1ª vaga | 15 min | 15 min | ⏳ Medir |
| Tempo 10ª vaga | 15 min | 3 min | ⏳ Medir |
| Taxa de reuso Fast Track | 0% | 60%+ | ⏳ Medir |
| Cobertura templates | 172 | 480+ | 📊 10.4% |

---

## Arquivos Principais

### Backend (lia-agent-system)
| Arquivo | Descrição |
|---------|-----------|
| `app/services/job_embedding_service.py` | Embeddings e busca semântica |
| `app/api/v1/job_embeddings.py` | Endpoints Fast Track |
| `app/api/v1/wsi_questions.py` | Regeneração WSI |
| `app/services/pre_qualification_service.py` | Pré-qualificação |

### Frontend (plataforma-lia)
| Arquivo | Descrição |
|---------|-----------|
| `src/hooks/useFastTrack.ts` | Hook principal Fast Track |
| `src/hooks/use-company-eligibility-questions.ts` | Pré-qualificação global |
| `src/hooks/useWizardAnalytics.ts` | Analytics tracking |
| `src/components/job-wizard/FastTrackSuggestions.tsx` | Cards de sugestões |
| `src/components/job-wizard/FastTrackReviewPanel.tsx` | Painel de revisão |
| `src/components/expanded-chat-modal.tsx` | Modal do wizard (~9800 linhas) |
| `src/services/lia-api.ts` | Funções de API |

---

## Histórico de Atualizações

| Data | Atualização |
|------|-------------|
| 2026-02-01 | Criação do plano com 50 templates |
| 2026-02-01 | Fase 2 concluída: Learning Loop backend |
| 2026-02-01 | Fase 4 concluída: Learning Loop Inteligente |
| 2026-02-01 | Fase 3 concluída: Fast Track UX core |
| 2026-02-01 | Fase 5 iniciada: Polimento final |
| 2026-02-01 | Removido: Dropdowns de gestores/localizações (substituído por NLU conversacional) |
| 2026-02-01 | ✅ Campos sensíveis implementados (gestor, localização, vaga afirmativa) |
| 2026-02-01 | ✅ Regeneração WSI implementada (detecção de mudanças + prompt conversacional) |
| 2026-02-01 | ✅ Pré-qualificação global integrada (useCompanyEligibilityQuestions) |
| 2026-02-01 | ✅ Analytics completo (4 eventos com prevenção de duplicatas) |
| 2026-02-01 | **Fase 5 concluída** (funcionalidades core 100%, templates pendentes) |
