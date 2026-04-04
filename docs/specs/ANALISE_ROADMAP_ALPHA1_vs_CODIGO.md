# Análise Profunda: Roadmap Alpha 1 vs. Código Existente

**Data:** 31/03/2026  
**Versão:** 6.3 — Verificação profunda: status per-etapa validados contra código real (Fact-Checker ATIVO, A/B Testing ATIVO, Semantic Search ATIVO, Predictive Analytics ATIVO, Long-Term Memory ATIVO, Embedding auto-trigger ATIVO, LGPD consent ATIVO, Rate Limiter ATIVO, Data Minimization ATIVO)  
**Escopo:** Cruzamento do Fluxo Alpha 1 (v2) com a implementação real no Replit  
**Objetivo:** Listar APENAS componentes onde IA está envolvida (agente consome/produz algo via LLM, modelo, embedding ou heurística inteligente). Cada item explica concretamente a relação: qual agente consome o quê, produz o quê, e por quê.

---

## FLUXO ALPHA 1 — VISÃO DIDÁTICA COMPLETA

```
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│                          FLUXO ALPHA 1 — TESTE INTERNO WEDOTALENT (v2)                         │
│                                                                                                │
│  PREMISSAS: ATS integrado | Vagas importadas | Login email/senha                              │
└────────────────────────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────────┐                                              ┌──────────────────┐
    │    CONSULTOR      │                                              │       LIA         │
    └────────┬─────────┘                                              └────────┬─────────┘
             │                                                                  │
             │  1. LOGIN                                                         │
             │  ──────────────────────────────────────────────────────────────► │
             │  • Login com email/senha                                         │
             │  • Acessa dashboard de vagas                                     │
             │                                                                  │
             ├──────────────────────────────────────────────────────────────────┤
             │                                                                  │
             │  2. EDITAR VAGA (importada do ATS)                                │
             │  ──────────────────────────────────────────────────────────────► │
             │  • Acessa página de vagas WeDo, seleciona vaga existente        │
             │  • NÃO cria vaga na WeDo — edita dados importados              │
             │  • Define requisitos, benefícios, faixa salarial, modelo        │
             │  • 🤖 Ag.8 ATSIntegrationReActAgent [ats_integration]              │
             │    (sync dados do ATS) ⚠ PÓS-MVP                               │
             │                                                                  │
             │                              2B. VAGA CRIADA WeDO (agora possível)
             │  ──────────────────────────────────────────────────────────────► │
             │  • Clicar em "Criar Vaga" no botão Criar Vaga                   │
             │  • Seleciona "Criar Manualmente"                                │
             │  • Preenche campos da vaga manualmente                          │
             │                                                                  │
             ├──────────────────────────────────────────────────────────────────┤
             │                                                                  │
             │  3. CONFIGURAR ROTEIRO WSI                                        │
             │  ──────────────────────────────────────────────────────────────► │
             │  • A partir do JD da vaga (importado do ATS ou gerado na        │
             │    TAB CONFIGURAÇÕES DA VAGA)                                   │
             │  • Via TAB: CONFIGURAÇÕES Vaga → Revisar/Ajustar JD             │
             │  • TAB CONFIGURAÇÕES, SEÇÃO: PERGUNTAS Triagem →                │
             │    Criar (completo/compacto) ou Editar roteiro existente        │
             │  • Selecionar/ajustar perguntas de triagem                      │
             │  • 🤖 JDGeneratorService [job_management] (LLM) gera/ajusta JD  │
             │  • 🤖 WSIQuestionGeneratorService [cv_screening] (Gemini LLM)   │
             │    gera perguntas WSI                                            │
             │                                                                  │
             │                              3B. GERAR PERGUNTAS WSI             │
             │  ◄────────────────────────────────────────────────────────────── │
             │  • LIA analisa JD/requisitos → gera perguntas WSI (Blocos 2-5)  │
             │  • Consultor edita/ajusta via TAB CONFIGURAÇÕES                 │
             │                                                                  │
             ├──────────────────────────────────────────────────────────────────┤
             │                                                                  │
             │  4. BUSCAR CANDIDATOS (Funil de Talentos)                          │
             │  ──────────────────────────────────────────────────────────────► │
             │  • Busca no Funil de Talentos: banco interno + Pearch           │
             │  • Gera prompt no campo de busca do Funil de Talentos           │
             │  • Metodologias de busca:                                        │
             │    - Elasticsearch + PGVector + WRF (Weighted Rank Fusion)      │
             │    - ES Score Drop Analyzer + PGV Gap Analyzer (pré-WRF)        │
             │    - WRF Dynamic K (ajuste por nível de qualificação)           │
             │    - LLM Job Classification para otimização de K values         │
             │  • Modos de busca:                                              │
             │    - IA Natural (linguagem livre)                               │
             │    - Boolean (operadores AND/OR/NOT)                            │
             │    - Perfil Similar (a partir de candidato referência)          │
             │    - Job Description (busca por JD colada/importada)            │
             │    - Archetypes (perfis pré-configurados por área)              │
             │  • Filtros Avançados (MAP-003):                                 │
             │    - Cargo: títulos, senioridade, tempo no cargo                │
             │    - Empresa: nome, indústria, porte, funding, HQ              │
             │    - Skills: técnicas + nível de expertise                      │
             │    - Educação: universidade, grau, área, ano graduação          │
             │    - Idiomas: idioma + nível proficiência                       │
             │    - Geral: experiência mín/máx, ocultar perfis já vistos      │
             │    - Perfil: decision maker, top universities, startup          │
             │    - Pearch: fast/pro, exigir email/telefone, open to work     │
             │  • Tabela de candidatos: 10 por vez, botão "Carregar +10"       │
             │  • Preview do candidato inline na tabela (4 tabs):               │
             │    - Perfil Completo: dados, experiência, skills, educação     │
             │    - Atividades: timeline (triagens WSI, emails, entrevistas,  │
             │      candidaturas, testes, ofertas + eventos do ATS)           │
             │    - Arquivos: CVs e documentos anexados                       │
             │    - Pareceres e Análises: análises LIA salvas + opiniões      │
             │  • Like/Dislike feedback por candidato (otimiza busca)           │
             │  • Prompt expandido da LIA (lado esquerdo da tabela):           │
             │    - Análise de perfil, comparação, ranking, skills             │
             │    - 🤖 Ag.2 SourcingReActAgent [sourcing]                        │
             │      (busca/perfis similares)                                    │
             │    - 🤖 WSIScreeningPipeline [cv_screening] (triagem/screening) │
             │    - 🤖 WSIService [cv_screening] (análise/comparação/ranking)  │
             │  • Pearch + Apify (captura emails + enriquecimento)             │
             │  • Email OBRIGATÓRIO | Telefone opcional                         │
             │                                                                  │
             ├──────────────────────────────────────────────────────────────────┤
             │                                                                  │
             │  5. APROVAR MAPEADOS (Gate 1)                                     │
             │  ──────────────────────────────────────────────────────────────► │
             │  • Candidatos vão para coluna FUNIL no Kanban ou Tabela         │
             │  • Card do candidato no Kanban — ícones de score com modais:    │
             │    - 🧠 Triagem (BrainCircuit) → Modal detalhes triagem WSI     │
             │    - 🎯 CV (Target) → Modal análise de CV                       │
             │    - ⚙️ Geral (Gauge) → Modal nota média geral                  │
             │    - 👁️ Preview (Eye) → Abre preview do candidato (4 tabs)      │
             │  • Aprovação INDIVIDUAL (card a card) ou EM MASSA (max 100)     │
             │  • Drag-and-drop manual para qualquer coluna (incl. Reprovado) │
             │  • Etapas críticas → SmartTransitionModal pede confirmação      │
             │  • Aprovados → LIA inicia contato | Reprovados → Feedback       │
             │  ⚡ Inscritos via web BYPASS Gate 1 → triagem automática          │
             │  • 🤖 Ag.0 MainOrchestrator [orchestrator]                        │
             │  • 🤖 Ag.7 CommunicationReActAgent [communication] (feedback)   │
             │  • 🤖 Ag.8 ATSIntegrationReActAgent [ats_integration]           │
             │    (sync status) ⚠ PÓS-MVP                                     │
             │                                                                  │
             ├──────────────────────────────────────────────────────────────────┤
             │                                                                  │
             │                              6. CONTATO VIA EMAIL                 │
             │  ◄────────────────────────────────────────────────────────────── │
             │  • Contato primário: SEMPRE email                                │
             │  • Email com 2 opções:                                           │
             │    A) Link para triagem via CHAT WEB (canal principal)           │
             │    B) Solicita nº celular → WhatsApp (canal secundário)         │
             │  • 🤖 Ag.0 MainOrchestrator [orchestrator] dispara contato        │
             │  • 🤖 Ag.7 CommunicationReActAgent [communication]              │
             │    (executa send_email/send_whatsapp)                            │
             │                                                                  │
             ├──────────────────────────────────────────────────────────────────┤
             │                                                                  │
             │                              6B. FOLLOW-UP AUTOMÁTICO (7 DIAS)   │
             │  ◄────────────────────────────────────────────────────────────── │
             │  • Se candidato NÃO abre/clica email                             │
             │  • Re-envio automático a cada 24h por 7 dias consecutivos       │
             │  • Após 7 dias sem resposta → status "sem_resposta"             │
             │  • Consultor notificado                                          │
             │                                                                  │
             ├──────────────────────────────────────────────────────────────────┤
             │                                                                  │
             │                              7. TRIAGEM WSI                       │
             │  ◄────────────────────────────────────────────────────────────── │
             │  • Canais disponíveis:                                           │
             │    - Chat web (link do email) — canal principal                 │
             │    - WhatsApp (se forneceu nº)                                  │
             │    - Ligação telefone (Twilio/OpenMic.ai)                       │
             │    - Ligação web (voice screening)                              │
             │  • LIA aplica perguntas WSI com agentes coordenados:            │
             │    🤖 Ag.0 Orchestrator [orchestrator] (coordenação geral)       │
             │    🤖 Ag.4 WSIInterviewGraph [cv_screening] (conduz chat,        │
             │       aplica perguntas)                                          │
             │    🤖 Ag.5 WSIService [cv_screening] (analisa respostas,         │
             │       calcula score)                                             │
             │    🤖 WSIVoiceOrchestrator [cv_screening] (triagem por voz)      │
             │  • Score WSI calculado ao final | Parecer textual gerado        │
             │                                                                  │
             ├──────────────────────────────────────────────────────────────────┤
             │                                                                  │
             │                              7A. TRIAGEM ABANDONADA              │
             │  ◄────────────────────────────────────────────────────────────── │
             │  • Candidato inicia mas para de responder                        │
             │  • Timeout: 48h sem atividade → 1º lembrete automático          │
             │  • +48h sem retorno → 2º lembrete                               │
             │  • Após 2º lembrete sem retorno → alerta ao consultor           │
             │  • Progresso parcial SALVO                                       │
             │                                                                  │
             ├──────────────────────────────────────────────────────────────────┤
             │                                                                  │
             │                              7B. FEEDBACK PÓS-TRIAGEM           │
             │  ◄────────────────────────────────────────────────────────────── │
             │  • 🤖 Ag.4 WSIInterviewGraph [cv_screening] agradece,           │
             │    dá feedback, informa próximos passos                         │
             │  • Canal: mesmo da triagem (chat web, WhatsApp ou voz)          │
             │                                                                  │
             ├──────────────────────────────────────────────────────────────────┤
             │                                                                  │
             │  8. APROVAR/REPROVAR TRIADOS (Gate 2)                             │
             │  ──────────────────────────────────────────────────────────────► │
             │  • Consultor recebeu alerta Teams (7B)                           │
             │  • Revisa score WSI + parecer LIA na plataforma                 │
             │  • Aprova → SHORT LIST | Reprova → FEEDBACK                     │
             │  • 🤖 Ag.7 PersonalizedFeedbackService [cv_screening]           │
             │    (gera parecer/feedback)                                       │
             │  • 🤖 Ag.8 ATSIntegrationReActAgent [ats_integration]           │
             │    (sync status) ⚠ PÓS-MVP                                     │
             │                                                                  │
             ├──────────────────────────────────────────────────────────────────┤
             │                                                                  │
             │                              9A. AGENDAR ENTREVISTA              │
             │  ◄────────────────────────────────────────────────────────────── │
             │  (Se APROVADO) LIA agenda entrevista                             │
             │  • Email + WhatsApp ao candidato (data/hora + link reunião)      │
             │  • 🤖 Ag.6 InterviewGraph [interview_scheduling]                  │
             │  • Se NÃO encontra horário → alerta ao consultor via Teams      │
             │                                                                  │
             │                              9B. ENVIAR FEEDBACK                 │
             │  ◄────────────────────────────────────────────────────────────── │
             │  (Se REPROVADO) LIA envia feedback via email e/ou WhatsApp      │
             │  • 🤖 Ag.7 PersonalizedFeedbackService [cv_screening]           │
             │  • 🤖 CommunicationReActAgent [communication] (envia)           │
             │                                                                  │
             ▼                                                                  ▼
    ┌────────────────────────────────────────────────────────────────────────────────────────┐
    │                               FIM DO ESCOPO ALPHA 1                                    │
    └────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 0. MAPA IA — FLUXO ALPHA 1 (somente onde IA atua)

**Regra:** Um componente só aparece se IA está envolvida. "IA" = LLM, embedding, modelo ML, heurística adaptativa, ou agente autônomo.

**Convenção de nomes:** Os rótulos Ag.0–Ag.8 vêm do Fluxo Alpha 1 v2 (source of truth do MVP). No código, os agentes estão registrados em `agents_registry.yaml` com nomes de domínio (pipeline, sourcing, wizard, talent, kanban, policy, jobs_management). Correspondência:

| Rótulo | Classe no código | Domínio |
|--------|-----------------|---------|
| Ag.0 | MainOrchestrator | orchestrator |
| Ag.2 | SourcingReActAgent | sourcing |
| Ag.4 | WSIInterviewGraph | cv_screening |
| Ag.5 | WSIService (scoring) | cv_screening |
| Ag.6 | InterviewGraph | interview_scheduling |
| Ag.7 | CommunicationReActAgent (envio) / PersonalizedFeedbackService (feedback) | communication / cv_screening |
| Ag.8 | ATSIntegrationReActAgent ⚠ PÓS-MVP | ats_integration |
| — | WSIQuestionGeneratorService (gera perguntas WSI, E3) | cv_screening |
| — | WSIScreeningPipeline (triagem/screening, E4) | cv_screening |
| — | WSIVoiceOrchestrator (triagem por voz, E7) | cv_screening |
| — | JDGeneratorService (gera/ajusta JD, E2/E3) | job_management |

**Legenda:** ● Ativo | ◐ Disponível (precisa ativar) | ○ A implementar | ⚠ Gap bloqueante

---


### ETAPA 1 — LOGIN

**Nenhuma IA envolvida.** Login é email/senha via AuthService (JWT). Pré-requisito de infraestrutura.

---

### ETAPA 2 — EDITAR VAGA (importada do ATS)

**Ação humana:** Consultor acessa página `/jobs`, seleciona vaga importada do ATS, edita manualmente requisitos/benefícios/faixa salarial/modelo de trabalho. Essa edição manual não envolve IA.

**Ação IA (condicional):** Se o consultor abre o modal "Gerar JD" a partir dos dados preenchidos, a IA entra:

| Componente IA | O que faz | Por quê | Status |
|--------------|----------|---------|--------|
| **JDGeneratorService** (Claude) | Recebe dados da vaga (título, skills, benefícios, responsabilidades) → gera JD estruturada em markdown (seções: Sobre, Responsabilidades, Requisitos, Benefícios, Diversidade) + SEO title + tags | Porque o consultor precisa de um JD profissional a partir de dados brutos; Claude redige e estrutura sem inventar conteúdo | ● |
| **FairnessGuard L1/L2** | Pre-check no texto do JD gerado: L1 bloqueia requisitos discriminatórios (13 categorias: gênero, idade, etnia...); L2 alerta termos proxy enviesados (log only) | Porque o JD gerado por LLM pode conter viés inadvertido; FG filtra antes de salvar | ● |

> **Nota MVP:** Ag.8 ATSIntegrationReActAgent [ats_integration] atua nas etapas de Gate (E5, E8) para sync de status de volta ao ATS. ⚠ PÓS-MVP.

---

### ETAPA 3 — CONFIGURAR ROTEIRO WSI

**Ação humana:** Consultor acessa modal "Roteiro de Triagem", escolhe criar (completo/compacto) ou editar roteiro existente, revisa/ajusta perguntas geradas.

**Ação IA:**

| Componente IA | O que faz | Por quê | Status |
|--------------|----------|---------|--------|
| **JDGeneratorService** (Claude) | Se o JD ainda não existe ou precisa ajuste, gera/melhora o JD a partir dos dados da vaga (mesmo serviço da E2) | Porque o roteiro WSI parte do JD — se não há JD, precisa gerar antes | ● |
| **WSI Question Generator** (Gemini) | Recebe JD + competências técnicas + comportamentais + senioridade → gera perguntas WSI organizadas em Blocos 2 (elegibilidade), 3 (técnico), 4 (comportamental) via `POST /api/v1/wsi/generate-questions`. Há também o pipeline unificado `POST /api/v1/wsi/screening-pipeline` (`WSIScreeningPipeline`) que orquestra geração + calibração + scoring em fluxo único | Porque as perguntas de triagem precisam ser calibradas por senioridade (Dreyfus), complexidade cognitiva (Bloom), traços de personalidade (Big Five) e competência (CBI) | ● |
| **WSIScreeningQuestionGenerator** (heurístico + calibração) | Gera perguntas via templates Big5/CBI/Bloom/Dreyfus quando o LLM não está disponível; aplica `SeniorityContextCalibrator` para ajustar Dreyfus target e Bloom levels por área/indústria | Porque o fallback garante geração mesmo sem LLM, e a calibração contextual adapta a dificuldade ao perfil real da vaga | ● |
| **FairnessGuard L1/L2** | Pre-check nas perguntas geradas: L1 bloqueia perguntas com padrões discriminatórios; L2 alerta proxy terms | Porque perguntas de triagem discriminatórias invalidam o processo seletivo inteiro | ● |

> **Serviços envolvidos:** **WSIQuestionGeneratorService** (`WSIScreeningQuestionGenerator`) gera as perguntas WSI. **JDGeneratorService** (`jd_generator_service.py`) gera/ajusta o JD quando o consultor usa a TAB Configurações. **Ag.4 WSIInterviewGraph** (`wsi_interview_graph.py`) conduz a entrevista na E7, aplicando as perguntas sequencialmente, coletando respostas e gerando feedback.

---

### ETAPA 4 — BUSCAR CANDIDATOS (Funil de Talentos)

**Ação humana:** Consultor gera prompt de busca no campo de busca do Funil de Talentos, aplica filtros avançados, avalia candidatos na tabela (like/dislike), usa prompt expandido da LIA.

**Ação IA:**

| Componente IA | O que faz | Por quê | Status |
|--------------|----------|---------|--------|
| **CascadedRouter** (6 tiers) | Recebe mensagem do consultor → resolve intent via memory → Redis → pgvector → regex → LLM cascade (Haiku→Sonnet→Opus) → clarification | Porque o texto livre do consultor precisa ser roteado ao agente correto (sourcing, triagem, análise); o cascade otimiza custo (tiers baratos primeiro) | ● |
| **Ag.2 SourcingAgent** (LangGraph) | Recebe intent de busca → executa search via Elasticsearch + PGVector + WRF Dynamic K → retorna candidatos ranqueados | Porque a busca híbrida (keyword + semântica) com fusão de rank ponderada encontra candidatos que busca simples perderia | ● |
| **Ag.3 TriagemCurricular** (LangGraph) | Recebe perfil de candidato → analisa CV via LLM → gera score de aderência + parecer textual | Porque a triagem manual de CVs é o gargalo #1 do recrutador; o LLM compara skills/experiência contra os requisitos da vaga | ● |
| **Ag.5 AvaliadorWSI** (LangGraph) | Recebe perfil + dados de triagem → calcula score WSI composto → gera ranking comparativo | Porque o ranking por score WSI padronizado permite comparação objetiva entre candidatos | ● |
| **Semantic Search** (Gemini 768-dim) | Expande semanticamente skills/títulos/indústrias do prompt → busca por similaridade vetorial no PGVector | Porque "React developer" deve encontrar "frontend engineer com React" — a expansão semântica cobre sinônimos e variações | ● |
| **FairnessGuard L1** | Bloqueia buscas com padrões discriminatórios explícitos (ex: "só homens", "menos de 30 anos") — pre-check no MainOrchestrator antes de rotear ao agente | Porque buscas discriminatórias violam legislação trabalhista e valores WeDO | ● |
| **FairnessGuard L2** | Alerta (soft warning, log only) termos proxy que podem indicar viés indireto (ex: "boa aparência", "escola de primeira linha") | Porque viés indireto é sutil e precisa ser rastreado para auditoria | ● |
| **Learning Loop** | Captura accept/modify/reject de candidatos avaliados → alimenta `RoutingFeedback` + score calibration | Porque o feedback do consultor melhora a precisão do scoring e do roteamento ao longo do tempo | ● |
| **Routing Adaptativo** (E9) | `_apply_adaptive_adjustments` no CascadedRouter: ajusta confidence de roteamento com factor 0.8x-1.2x baseado em histórico de correções | Porque se o consultor corrige frequentemente o domínio roteado, o sistema aprende a ajustar | ● |
| **Score Normalization** | Normaliza scores por `difficulty_coefficient` da vaga para comparação justa entre vagas de dificuldades diferentes | Porque uma vaga "Senior ML Engineer" tem baseline diferente de "Junior Admin" | ● |
| **Model Drift** | Monitora `score_drift` + `approval_drift` — alerta quando distribuição de scores muda significativamente | Porque drift indica que o modelo ou o comportamento do consultor mudou, exigindo recalibração | ● |

---

### ETAPA 5 — APROVAR MAPEADOS (Gate 1)

**Ação humana:** Consultor revisa candidatos no Kanban/Tabela, aprova individualmente ou em massa (max 100), arrasta cards entre colunas, confirma via SmartTransitionModal.

**Ação IA:**

| Componente IA | O que faz | Por quê | Status |
|--------------|----------|---------|--------|
| **Ag.0 Orchestrator** (LangGraph) | Coordena pós-aprovação: dispara contato para aprovados, feedback para reprovados, delega a Ag.7 e Ag.8 | Porque a ação de aprovar/reprovar desencadeia múltiplos fluxos paralelos que precisam de coordenação | ● |
| **Ag.7 AnalistaFeedback** (LangGraph) | Gera parecer textual de feedback para candidatos reprovados baseado nos dados de triagem/score | Porque feedback personalizado e construtivo melhora employer branding e é requisito WeDO Talent Guide | ● |
| **Ag.8 IntegradorATS** (LangGraph) | Sincroniza status de aprovação/reprovação de volta ao ATS (Gupy/Pandape) via `sync_candidate_to_ats` | Porque o ATS externo precisa refletir a decisão tomada na plataforma LIA para manter consistência | ● |
| **Policy Engine** *(governa IA)* | Aplica `ALPHA1_SECTOR_RULES`: autonomy levels + HITL thresholds por setor determinam se a IA pode agir sozinha ou precisa confirmação humana. Regra determinística que controla o comportamento dos agentes IA | Porque em setores regulados (saúde, finanças) a IA precisa de HITL | ● |
| **FairnessGuard L1** | `check_rejection_fairness` como tool: valida se motivo de rejeição contém padrão discriminatório | Porque rejeições discriminatórias são risco legal e reputacional | ● |
| **Learning Loop** | Captura decisões consultor vs. sugestão IA (aceitar/rejeitar/modificar) → alimenta routing adjustments + score calibration | Porque o delta entre sugestão IA e decisão humana é o sinal mais forte para melhorar o modelo | ● |
| **Calibration** | Implicit feedback: consultor avança candidato com low-score = sinal de que o score está subestimando | Porque calibração contínua corrige systematic bias nos scores | ● |
| **Model Drift** | Trigger se `approval_drift` > 10 p.p. entre períodos → alerta para recalibração | Porque mudança brusca na taxa de aprovação indica problema no scoring ou mudança de critérios | ● |

---

### ETAPA 6 — CONTATO VIA EMAIL + FOLLOW-UP

**Ação humana:** Consultor acompanha status de envios. Follow-up é automático.

**Ação IA:**

| Componente IA | O que faz | Por quê | Status |
|--------------|----------|---------|--------|
| **Ag.0 Orchestrator** (LangGraph) | Orquestra o fluxo de contato: recebe decisão de Gate 1, delega envio ao Ag.7 ou ao domínio communication. Follow-ups via Celery Beat (`followup-check-hourly`) | Porque a coordenação pós-aprovação precisa disparar múltiplos canais de forma orquestrada | ● (contato) / ● (follow-up) |
| **Ag.7 CommunicationReActAgent** [communication] | Executa as tools de comunicação (`send_email`, `send_whatsapp`) registradas em `communication_tool_registry.py`. Personaliza template com dados do candidato/vaga | Porque as tools de envio estão no domínio communication, orquestradas pelo CommunicationReActAgent | ● |
| **Template Learning** | Aprende quais templates de email têm melhor taxa de abertura/resposta → prioriza em envios futuros | Porque otimizar o template por performance reduz "sem_resposta" | ● |
| **A/B Testing** | Variantes de template de email testadas por cohort para medir taxa de abertura/clique | Porque decisões de template devem ser data-driven, não por opinião | ● |

---

### ETAPA 7 — TRIAGEM WSI (Chat Web / WhatsApp)

**Ação humana:** Candidato responde perguntas WSI via chat web (link do email) ou WhatsApp. Consultor revisa resultado.

**Ação IA:**

| Componente IA | O que faz | Por quê | Status |
|--------------|----------|---------|--------|
| **Ag.0 Orchestrator** (LangGraph) | Coordena o fluxo de triagem: recebe mensagem do candidato → FairnessGuard pre-check → roteia para Ag.4 | Porque cada mensagem do candidato passa por compliance antes de ser processada | ● |
| **Ag.4 EntrevistadorWSI** (LangGraph) | Conduz o chat de triagem: aplica perguntas WSI sequencialmente, faz follow-up contextual, encerra com feedback | Porque a triagem precisa ser conduzida de forma natural (conversacional) e seguindo a metodologia WSI | ● |
| **Ag.5 AvaliadorWSI** (LangGraph) | Analisa cada resposta do candidato → calcula score por competência (0-100) → gera score WSI composto + parecer textual | Porque a avaliação objetiva por competência com scoring padronizado é o core da metodologia WSI | ● |
| **FairnessGuard L1/L2** | Pre-check em CADA mensagem do candidato no MainOrchestrator: L1 bloqueia; L2 alerta. Aplicado nas respostas antes de enviar ao LLM avaliador. Também ativo no `rubric_evaluation.py` (reasoning check) | Porque respostas do candidato podem conter informações protegidas que não devem influenciar o scoring | ● |
| **CascadedRouter** (6 tiers) | Roteia mensagens do candidato durante triagem para o domínio correto (cv_screening) | Porque mesmo dentro da triagem, o candidato pode fazer perguntas fora de escopo que precisam de roteamento | ● |
| **Calibration** | Calibração de scores WSI usando `SeniorityContextCalibrator`: ajusta Dreyfus target + Bloom levels por área/indústria/senioridade | Porque "senior em fintech" tem baseline diferente de "senior em agro" | ● |
| **Score Normalization** | Normaliza scores por versão do roteiro para comparação justa entre candidatos avaliados com roteiros diferentes | Porque se o roteiro mudou entre candidatos, scores brutos não são comparáveis | ● |
| **Model Drift** | Monitora drift em scores WSI entre períodos → alerta se distribuição muda | Porque drift indica mudança no modelo de avaliação ou nos prompts | ● |
| **Voice Analysis** | STT (Deepgram) + TTS (OpenAI): transcreve áudio do candidato → texto para avaliação; gera áudio da pergunta | Porque candidatos podem preferir responder por voz, e a plataforma precisa suportar multimodal | ● |
| **Policy Engine** *(governa IA)* | Autonomy level por setor: define se Ag.5 pode auto-aprovar candidatos high-score ou precisa HITL (regra determinística, não IA) | Porque em setores regulados a decisão final não pode ser 100% automática | ● |

---

### ETAPA 8 — APROVAR TRIADOS (Gate 2)

**Ação humana:** Consultor revisa score WSI + parecer LIA, aprova → Short List ou reprova → Feedback.

**Ação IA:**

| Componente IA | O que faz | Por quê | Status |
|--------------|----------|---------|--------|
| **Ag.7 AnalistaFeedback** (LangGraph) | Gera feedback personalizado para reprovados com base no score WSI + parecer + motivo de rejeição | Porque feedback genérico prejudica employer branding; o LLM personaliza por competência | ● |
| **Ag.8 IntegradorATS** (LangGraph) | Sincroniza decisão Gate 2 (aprovado/reprovado + motivo) de volta ao ATS | Porque o ATS precisa refletir o status pós-triagem para o workflow do cliente | ● |
| **Policy Engine** *(governa IA)* | HITL thresholds por setor: define se candidatos acima de threshold X podem ser auto-aprovados (regra determinística, não IA) | Porque Gate 2 é decisão crítica e setores regulados exigem aprovação humana explícita | ● |
| **FairnessGuard L1** | Valida motivo de rejeição: bloqueia se contém padrão discriminatório | Porque rejeição pós-triagem com motivo discriminatório é risco legal máximo | ● |
| **Learning Loop** | Captura decisões Gate 2 vs. recomendação IA → alimenta calibration | Porque o delta Gate 2 é o sinal mais maduro (pós-triagem completa) para calibrar scoring | ● |
| **Calibration** | Implicit feedback: consultor aprova candidato com low-WSI ou reprova high-WSI = sinal forte | Porque a calibração pós-WSI é mais precisa que a pós-sourcing (E5) | ● |
| **Model Drift** | Monitora `approval_drift` Gate 2 separadamente do Gate 1 | Porque os dois gates têm dinâmicas diferentes e drift em um não implica drift no outro | ● |
| **Routing Adaptativo** | Correções de rota entre domínios alimentam `RoutingFeedback` → ajustes de confidence futuros | Porque erros de roteamento no Gate 2 (ex: rota errada para feedback vs. agendamento) precisam ser corrigidos | ● |

---

### ETAPA 9 — AGENDAR ENTREVISTA + FEEDBACK

**Ação humana:** Consultor confirma short list. Para reprovados, feedback é automático.

**Ação IA:**

| Componente IA | O que faz | Por quê | Status |
|--------------|----------|---------|--------|
| **Ag.6 SchedulingAgent** (LangGraph) | Recebe candidato aprovado → busca slots disponíveis → gera convite (ICS + link reunião) → envia via email + WhatsApp | Porque agendamento manual de entrevistas é trabalho repetitivo que a IA elimina | ● |
| **Ag.7 AnalistaFeedback** (LangGraph) | Gera texto de feedback para reprovados: estrutura motivo + pontos fortes + sugestões de desenvolvimento | Porque feedback construtivo é valor diferencial WeDO e o LLM personaliza por candidato | ● |
| **FairnessGuard L1/L2** | Valida texto de feedback gerado: L1 bloqueia linguagem discriminatória; L2 alerta proxy terms. Ativo no `rubric_evaluation.py` (reasoning check antes de persistir) | Porque feedback com viés prejudica o candidato e a marca do cliente | ● |
| **Template Learning** | Aprende quais templates de feedback têm melhor recepção (NPS/reação) → prioriza variantes melhores | Porque feedback que o candidato valoriza melhora employer branding measurably | ● |
| **Embedding Service** (Gemini 768-dim) | Gera embedding do perfil completo do candidato para matching futuro em outras vagas. Auto-trigger em `reject_candidate` para re-discovery | Porque o candidato reprovado nesta vaga pode ser ideal para outra — o embedding permite re-discovery | ● |

---

### MATRIZ DE RESUMO — Componentes IA por Etapa

| Etapa | Agentes IA | LLM/Modelo | Serviço IA principal | Status |
|-------|-----------|-----------|---------------------|--------|
| E1 Login | — | — | — | sem IA |
| E2 Editar Vaga | — | Claude (JDGenerator) | JDGeneratorService | ● (condicional) |
| E3 Roteiro WSI | — (serviços, não agentes) | Claude + Gemini | JDGeneratorService + WSIQuestionGeneratorService | ● |
| E4 Buscar Candidatos | Ag.2, Ag.3, Ag.5 | LLM cascade + Gemini embeddings | CascadedRouter + SourcingPipeline + CVScoring | ● |
| E5 Gate 1 | Ag.0, Ag.7, Ag.8 | LLM (feedback) | PolicyEngine + LearningLoop | ● |
| E6 Contato Email | Ag.0, Ag.7 | LLM (template personalization) | EmailService + TemplateLearning | ● |
| E7 Triagem WSI | Ag.0, Ag.4, Ag.5 | LLM (avaliação) + Deepgram + OpenAI TTS | WSIService + VoiceService | ● |
| E8 Gate 2 | Ag.7, Ag.8 | LLM (feedback) | PolicyEngine + LearningLoop | ● |
| E9 Agendar + Feedback | Ag.6, Ag.7 | LLM (feedback) + Gemini (embedding) | SchedulingService + EmbeddingService | ● |

**FairnessGuard por etapa (somente onde IA gera conteúdo):**

| Etapa | FG L1 (block) | FG L2 (warn) | Onde atua |
|-------|:------------:|:------------:|----------|
| E2 Editar Vaga | ● | ● | No JD gerado por Claude — `check_fairness` em input+output no `jd_generation.py` |
| E3 Roteiro WSI | ● | ● | Nas perguntas geradas por Gemini — filtro pós-geração no `wsi_questions.py` |
| E4 Buscar Candidatos | ● | ● | No texto de busca do consultor (pre-check no Orchestrator) |
| E5 Gate 1 | ● | ● | No motivo de rejeição (`check_rejection_reason` em `candidates.py`) |
| E7 Triagem WSI | ● | ● | Nas respostas do candidato antes do LLM avaliador; reasoning check em `rubric_evaluation.py` |
| E8 Gate 2 | ● | ● | No motivo de rejeição Gate 2 |
| E9 Feedback | ● | ● | No texto de feedback/reasoning gerado — `fairness_guard.check` em `rubric_evaluation.py` |

**Inteligência adaptativa por etapa (somente onde há loop de aprendizado):**

| Etapa | Learning Loop | Routing Adaptativo | Calibration | Score Norm | Model Drift |
|-------|:------------:|:-----------------:|:-----------:|:----------:|:-----------:|
| E4 Buscar | ● | ● | ● | ● | ● |
| E5 Gate 1 | ● | ● | ● | — | ● |
| E7 Triagem | ● | — | ● | ● | ● |
| E8 Gate 2 | ● | ● | ● | — | ● |

**Comunicação por etapa (somente etapas com canais ativos):**

| Etapa | Email | WhatsApp | Chat Web | Teams | VoIP |
|-------|:-----:|:--------:|:--------:|:-----:|:----:|
| E6 Contato + Follow-up | ● | ● | — | ● | — |
| E7 Triagem WSI | ● | ● | ● | — | ● |
| E9 Agendar + Feedback | ● | ● | — | ● | — |

> **Legenda:** ● Ativo | ◐ Disponível (precisa ativar) | ○ A implementar | ⚠ Gap bloqueante

---

### LISTA CONSOLIDADA — O que precisa ativar, implementar ou conectar

#### ◐ PRECISA ATIVAR (código existe, precisa ligar)

> Todos os itens desta seção foram resolvidos. Embedding auto-trigger Gate 2 confirmado ATIVO via `_generate_rediscovery_embedding` em `reject_candidate`.

#### ⚠ GAPS BLOQUEANTES POR ETAPA

| # | O quê | Etapa | Impacto se não resolver |
|---|-------|-------|------------------------|
| G5 | ~~**Apify API keys**~~ | E4 | **RESOLVIDO** — `APIFY_API_KEY` configurada como secret no Replit |

#### PRIORIDADE SUGERIDA

| Prioridade | Itens | Justificativa |
|-----------|-------|---------------|
| **P0 — Bloqueante MVP** | **100% COMPLETO** | Todos os itens resolvidos |
| **P1 — Compliance** | **100% COMPLETO** | Todos os itens resolvidos |
| **P2 — Integração** | **100% COMPLETO** | G5 Apify API key configurada |
| **P3 — Otimização** | **100% COMPLETO** | Embedding auto-trigger Gate 2 confirmado ATIVO |

---

### NOTA: Agentes no `AgentType` que participam fora do fluxo Alpha 1

| Agente (enum) | Papel | Motivo de exclusão do fluxo |
|---------------|-------|-----------------------------|
| **RECRUITER_ASSISTANT** | Assistente pessoal do recrutador | Funciona como **fallback geral** quando o CascadedRouter não identifica um domínio específico. Não é acionado diretamente por nenhuma etapa E1–E9; responde a perguntas genéricas do consultor fora do fluxo de recrutamento. |
| **TASK_PLANNER** | Planejador de tarefas | Existe no enum `AgentType` (Agente 9) mas **não possui implementação de agente dedicado** — sem arquivo de agente, sem tools registradas, sem system prompt. Reservado para uso futuro. |

> **Referência:** `lia-agent-system/app/shared/agents/agent_types.py` linhas 53-57.

### NOTA: Domínios implementados FORA do escopo Alpha 1

| Domínio | Descrição | Por que não aparece no fluxo |
|---------|-----------|------------------------------|
| `automation` | Automação de workflows internos | Infraestrutura para automações futuras; nenhuma etapa Alpha 1 depende dele |
| `hiring_policy` | Políticas de contratação por empresa/setor | Consumido internamente pelo PolicyEngine, mas não exposto como agente no fluxo |
| `pipeline` | Gestão de pipeline de candidatos (Kanban backend) | Backend do Kanban que é usado pelas etapas E5/E8, mas como infraestrutura, não como agente autônomo |
| `policy` | Motor de regras e sector rules | Suporte ao PolicyEngine e ALPHA1_SECTOR_RULES; opera como serviço interno, não como agente |
| `recruiter_assistant` | Domínio do assistente pessoal do recrutador | Agente de fallback (ver nota acima); fora do fluxo linear E1-E9 |

> Estes domínios existem no código (`lia-agent-system/app/domains/`) mas não são acionados diretamente como agentes no fluxo de 9 etapas do Alpha 1.

---

## 1. VISÃO GERAL — O QUE EXISTE vs. O QUE FALTA

### 1.1 Resumo Executivo

O backend (`lia-agent-system`) possui uma arquitetura robusta com 10+ domínios, 30+ tools registradas, 6+ agentes ReAct migrados para LangGraph, 6 camadas de compliance (FairnessGuard 3 camadas, PII Masking, Fact-Checker, Audit, Policy Engine, LGPD) e **11 camadas de inteligência** (Learning Loop, A/B Testing, Routing Adaptativo, Template Learning, Calibration, Score Normalization, Predictive Analytics, Model Drift, Conversation Memory, Semantic Search, Voice Analysis) implementadas. O frontend (`plataforma-lia`) tem integração real via proxy Next.js → FastAPI, incluindo **chat web público de triagem** (`/triagem/[token]`).

**A distância para MVP funcional reduziu drasticamente:**

1. **Integração ponta-a-ponta** — WRF Dynamic K, LLM Job Classification, A/B Testing, Template Learning e FairnessGuard L3 estão **integrados e ativos** no RAG pipeline e communication services
2. **Compliance ativo nos endpoints** — FairnessGuard L1/L2 wired em `jd_generation.py`, `wsi_questions.py`, `rubric_evaluation.py`, `candidates.py`. Opt-out LGPD com HMAC tokens. PII Masking global. Audit logging ativo em JD generation e WSI questions. FairnessGuard auto-check em rejeições ativo em `reject_candidate`. Consentimento LGPD explícito com checkbox obrigatório em WelcomeCard
3. **Scheduler completo** — Celery Beat com 13 tasks agendadas: follow-up horário, abandono WSI 4h, feedback 2h, drift diário, LGPD cleanup, RAGAS eval, LTM compression diária
4. **Integrações externas** — Voice STT/TTS (Deepgram+OpenAI), Teams (Graph API), Apify (5 actors), Embedding (cache Redis), A/B Testing com 3 experimentos seed
5. **Chat web público** — **IMPLEMENTADO** com 10 componentes React, voice mode, progress tracking, consentimento LGPD explícito
6. **Infraestrutura externa restante** — ATS real (Gupy/Pandapé), Twilio WhatsApp, Resend/SendGrid, Apify, Microsoft Teams dependem de credenciais e configuração de produção

---

## 2. TABELA MESTRE: ETAPAS × AGENTES × COMPLIANCE × INTELIGÊNCIA

### ETAPA 1: LOGIN

| Dimensão | Componente | Status | Arquivo Replit |
|----------|-----------|--------|----------------|
| **Domínio** | Auth | Implementado | `app/api/v1/auth.py` |
| **Serviço** | AuthService (JWT + WorkOS SSO) | Implementado | `app/services/auth_service.py` |
| **Tool** | — (não é agente) | N/A | — |
| **Frontend** | Login page + auth hooks | Implementado | `src/app/(auth)/login/` |
| **COMPLIANCE** | | | |
| ↳ FairnessGuard | N/A nesta etapa | — | — |
| ↳ PII Masking | Logs de login mascarados | ATIVO | `PIIMaskingFilter` global |
| ↳ Fact-Checker | N/A nesta etapa | — | — |
| ↳ Audit Trail | Login events | PRECISA ATIVAR | `audit_service.py` existe mas NÃO está integrado em `auth.py` |
| ↳ Policy Engine | Rate limiting de tentativas | ATIVO | `RateLimitMiddleware` em `main.py` — Redis-backed sliding window, fallback in-memory |
| ↳ LGPD | Cookie consent | N/A | Autenticação via JWT, sem cookies de sessão |
| **INTELIGÊNCIA** | | | |
| ↳ Learning Loop | N/A | — | — |
| ↳ A/B Testing | N/A | — | — |
| ↳ Routing Adaptativo | N/A | — | — |
| ↳ Template Learning | N/A | — | — |
| ↳ Calibration | N/A | — | — |
| ↳ Score Normalization | N/A | — | — |
| ↳ Predictive Analytics | N/A | — | — |
| ↳ Model Drift | N/A | — | — |
| ↳ Conv. Memory | N/A | — | — |
| ↳ Semantic Search | N/A | — | — |
| ↳ Voice Analysis | N/A | — | — |

**Pendente:** Audit trail de autenticação precisa ser ativado em `auth.py`.

---

### ETAPA 2: EDITAR VAGA (importada do ATS)

| Dimensão | Componente | Status | Arquivo Replit |
|----------|-----------|--------|----------------|
| **Agente** | Ag.8 IntegradorATS | Implementado | `app/domains/ats_integration/` |
| **Domínio** | `ats_integration` + `job_management` | Implementado | `app/domains/` |
| **Serviços** | ATSSyncService, GupyClient, PandapeClient | Implementado | `app/services/ats_sync_service.py` |
| **Tools** | `sync_candidate_to_ats`, `fetch_candidate_from_ats`, `validate_ats_fields` | Registradas | `ats_integration_tool_registry.py` |
| **Frontend** | Página de vagas + edição | Implementado | `src/app/(dashboard)/jobs/` |
| **COMPLIANCE** | | | |
| ↳ FairnessGuard L1 | Bloquear requisitos discriminatórios no JD | ATIVO | `check_fairness` em `jd_generation.py` — input+output |
| ↳ FairnessGuard L2 | Alertar termos proxy enviesados | ATIVO | `check_fairness` em `jd_generation.py` — warnings em output |
| ↳ PII Masking | Strip PII antes de enviar ao LLM | ATIVO (global) | `strip_pii_for_llm_prompt` |
| ↳ Fact-Checker | N/A (não há claims numéricas) | — | — |
| ↳ Audit Trail | Log de geração de JD | PARCIAL | `audit_service.log_decision` ativo em `jd_generation.py`. Edições manuais de vaga ainda sem audit |
| ↳ Policy Engine | N/A nesta etapa | — | — |
| ↳ LGPD | Dados do ATS com consentimento | PARCIAL | ATSSyncService filtra dados sensíveis (salário) com `"Dado sensível - não sincronizar"`. Consent explícito do candidato no ATS de origem (bypass Gate 1 COMP-8) |
| **INTELIGÊNCIA** | | | |
| ↳ Learning Loop | Captura edições do wizard (salary, skills, benefits) | ATIVO | `learning_loop_service.py` via `capture_from_wizard_update` |
| ↳ A/B Testing | Variantes de prompt para JD generation | ATIVO | `ab_testing_service.py` — `seed_email_ab_tests` cria 3 experimentos na startup. Testes de prompt JD-specific ainda precisam ser criados |
| ↳ Routing Adaptativo | N/A (domínio fixo: job_management) | — | — |
| ↳ Template Learning | Aprende templates após 3 vagas similares | ATIVO | `template_learning_service.py` |
| ↳ Calibration | N/A (sem scoring nesta etapa) | — | — |
| ↳ Score Normalization | N/A | — | — |
| ↳ Predictive Analytics | `predict_time_to_fill`, `predict_optimal_salary` | ATIVO | `predictive_analytics_service.py` — endpoints expostos via `api/v1/predictive_analytics.py`, usado por `predictive_tools.py` nos agentes |
| ↳ Model Drift | N/A | — | — |
| ↳ Conv. Memory | Entity tracking (vaga mencionada) | ATIVO | `conversation_state.py` |
| ↳ Semantic Search | Expansão de skills para JD | ATIVO | `semantic_search_service.py` — endpoints expostos via `api/v1/semantic_search.py`, expansão de skills/cargos/indústrias |
| ↳ Voice Analysis | N/A | — | — |

**Pendente:** Sync com ATS real depende de credenciais de produção (API keys Gupy/Pandapé).

---

### ETAPA 3: CONFIGURAR ROTEIRO WSI

| Dimensão | Componente | Status | Arquivo Replit |
|----------|-----------|--------|----------------|
| **Serviço** | WSIQuestionGeneratorService (gera perguntas WSI) | Implementado | `app/domains/cv_screening/services/wsi_question_generator.py` |
| **Serviço** | JDGeneratorService (gera/ajusta JD) | Implementado | `app/domains/job_management/services/jd_generator_service.py` |
| **Agente** | Ag.4 EntrevistadorWSI (conduz a entrevista, não gera perguntas) | Implementado | `app/domains/cv_screening/agents/wsi_interview_graph.py` |
| **Domínio** | `cv_screening` (WSI) + `job_management` + `wizard` | Implementado | `app/domains/` |
| **Serviços** | WSIService, WSIScreeningPipeline | Implementado | `wsi_service.py`, `wsi_screening_pipeline.py` |
| **Tools** | `generate_screening_questions`, `analyze_jd_and_suggest_competencies` | Registradas | WSI domain tools |
| **Frontend** | Modal WSI + Preview Vaga | Implementado | `src/components/modals/` |
| **COMPLIANCE** | | | |
| ↳ FairnessGuard L1-L2 | Perguntas geradas sem viés | ATIVO | `check_fairness` per-question em `wsi_questions.py` |
| ↳ PII Masking | Strip antes de enviar JD ao LLM | ATIVO | `strip_pii_for_llm_prompt` |
| ↳ Fact-Checker | Validar claims nas perguntas | ATIVO | `fact_checker.py` integrado no `DomainWorkflow._post_check` — `enable_fact_checker=True` por default. Valida claims contra dados de contexto (salários, contagens) |
| ↳ Audit Trail | Log de geração de roteiro WSI | ATIVO | `audit_service.log_decision` em `wsi_questions.py` |
| ↳ Policy Engine | N/A | — | — |
| ↳ LGPD | N/A (dados internos) | — | — |
| **INTELIGÊNCIA** | | | |
| ↳ Learning Loop | Captura edições nas perguntas geradas | ATIVO | `learning_loop_service.py` |
| ↳ A/B Testing | Variantes de prompt para geração de perguntas | DISPONÍVEL | `ab_testing_service.py` |
| ↳ Routing Adaptativo | N/A (domínio fixo) | — | — |
| ↳ Template Learning | N/A (roteiro é por vaga) | — | — |
| ↳ Calibration | N/A | — | — |
| ↳ Score Normalization | N/A | — | — |
| ↳ Predictive Analytics | N/A | — | — |
| ↳ Model Drift | N/A | — | — |
| ↳ Conv. Memory | Tracking da vaga ativa na sessão | ATIVO | `conversation_state.py` |
| ↳ Semantic Search | Expansão de competências sugeridas | ATIVO | `semantic_search_service.py` — endpoints expostos via `api/v1/semantic_search.py` |
| ↳ Voice Analysis | N/A | — | — |

**Status:** Compliance completo para esta etapa.

---

### ETAPA 4: BUSCAR CANDIDATOS (Funil de Talentos)

| Dimensão | Componente | Status | Arquivo Replit |
|----------|-----------|--------|----------------|
| **Agente** | Ag.2 SourcingAgent | Implementado | `app/domains/sourcing/` |
| **Agente** | Ag.3 TriagemCurricular | Implementado | `app/domains/cv_screening/` |
| **Agente** | Ag.5 AvaliadorWSI | Implementado | `app/domains/cv_screening/` (WSI Evaluator) |
| **Domínio** | `sourcing` + `pipeline` | Implementado | `app/domains/` |
| **Serviços** | SourcingPipelineService, CandidateEnrichmentService, CVScoringService | Implementados | `app/services/` |
| **Tools** | `search_candidates`, `analyze_profile`, `score_candidate`, `enrich_profile` | Registradas | `sourcing_tool_registry.py` |
| **Frontend** | Funil de Talentos (tabela + filtros + sidebar LIA) | Implementado | `src/app/(dashboard)/candidates/` |
| **Busca** | Elasticsearch + PGVector + WRF | ATIVO | ES + PGVector + WRF Dynamic K ativo; LLM Classification + FG L3 sector acessíveis via RAG |
| **COMPLIANCE** | | | |
| ↳ FairnessGuard L1 | Bloquear buscas discriminatórias | ATIVO | `MainOrchestrator` L35-47 |
| ↳ FairnessGuard L2 | Alertar proxy terms na busca | ATIVO | `MainOrchestrator` L48-62 |
| ↳ FairnessGuard L3 | Análise semântica nas respostas do LLM | ATIVO | `check_with_sector()` ativo em pipeline_transition, rubric_evaluation, communication_tools, sourcing_agent, RAG pipeline |
| ↳ PII Masking | Strip PII de candidatos antes do LLM | ATIVO | `strip_pii_for_llm_prompt` |
| ↳ Fact-Checker | Validar claims nas análises LIA | ATIVO | `fact_checker.py` integrado no `DomainWorkflow._post_check` — `enable_fact_checker=True` por default |
| ↳ Audit Trail | Log de buscas + scores | PRECISA ATIVAR | `audit_service.py` não integrado em `candidates.py` |
| ↳ Policy Engine | N/A | — | — |
| ↳ LGPD | Modo anônimo no Toon | IMPLEMENTADO | `ToonService` `anonymize=True` |
| ↳ Bias Detection | `_LEARNING_PROTECTED_FIELDS` | ATIVO | Bloqueia learning de campos protegidos |
| **INTELIGÊNCIA** | | | |
| ↳ Learning Loop | Captura accept/modify/reject de candidatos avaliados | ATIVO | `learning_loop_service.py` |
| ↳ A/B Testing | Variantes de prompt para scoring | ATIVO | `ab_testing_service.py` — endpoints expostos via `api/v1/ab_testing.py` (GET/POST testes, GET variant) |
| ↳ Routing Adaptativo | Ajuste de confiança sourcing vs screening | ATIVO | `routing_learning_service.py` (0.8x-1.2x) |
| ↳ Template Learning | N/A (não é criação de vaga) | — | — |
| ↳ Calibration | Feedback explícito/implícito sobre scores | ATIVO | `calibration_service.py` |
| ↳ Score Normalization | Normaliza scores por difficulty_coefficient | ATIVO | `score_normalization_service.py` |
| ↳ Predictive Analytics | `predict_skill_success` | ATIVO | `predictive_analytics_service.py` — endpoints expostos, integrado em agentes via `predictive_tools.py` |
| ↳ Model Drift | Monitora score_drift + approval_drift | ATIVO | `model_drift_service.py` — trigger automático |
| ↳ Conv. Memory | Tracking de candidatos mencionados + filtros | ATIVO | `conversation_state.py` |
| ↳ Semantic Search | Expansão semântica de skills/títulos/indústrias | ATIVO | `semantic_search_service.py` (Gemini 768-dim) |
| ↳ Voice Analysis | N/A (busca não é por voz) | — | — |

**Pendente:** Audit Trail precisa ativação para buscas em `candidates.py`. Apify depende de API keys de produção.

---

### ETAPA 5: APROVAR MAPEADOS (Gate 1)

| Dimensão | Componente | Status | Arquivo Replit |
|----------|-----------|--------|----------------|
| **Agente** | Ag.0 Orchestrator | Implementado | `main_orchestrator.py` |
| **Agente** | Ag.7 AnalistaFeedback | Implementado | `app/domains/analytics/` |
| **Agente** | Ag.8 IntegradorATS | Implementado | `app/domains/ats_integration/` |
| **Domínio** | `pipeline` + `kanban` | Implementado | `app/domains/` |
| **Serviços** | KanbanService, PipelineTransitionService | Implementados | `app/services/` |
| **Tools** | `suggest_movements`, `check_rejection_fairness`, `identify_bottlenecks` | Registradas | `kanban_tool_registry.py` |
| **Frontend** | Kanban board + SmartTransitionModal | Implementado | `src/app/(dashboard)/job-kanban/` |
| **COMPLIANCE** | | | |
| ↳ FairnessGuard | `check_rejection_fairness` auto-check | ATIVO | Auto-check em `reject_candidate` (`candidate_tools.py`) + FG L3 pré-check no Pipeline Transition Agent |
| ↳ PII Masking | Ativo globalmente | ATIVO | — |
| ↳ Fact-Checker | N/A (decisão binária) | — | — |
| ↳ Audit Trail | Log de aprovações/rejeições + overrides | PRECISA ATIVAR | `audit_service.py` — `record_human_review` |
| ↳ Policy Engine | Autonomy levels + HITL thresholds por setor | IMPLEMENTADO | `ALPHA1_SECTOR_RULES` em `policy_engine_service.py` |
| ↳ Escalation | Trigger quando AI confidence < threshold | IMPLEMENTADO | `trigger_escalation` |
| ↳ LGPD | Consentimento antes de contato | ATIVO | `CandidateChannelSelector.select_channels` verifica `LGPDConsent` + `CandidateOptOut` por canal. WhatsApp inclui estado `AWAITING_CONSENT` com mensagem explícita |
| **INTELIGÊNCIA** | | | |
| ↳ Learning Loop | Captura decisões: aceitar/rejeitar/modificar AI suggestion | ATIVO | `learning_loop_service.py` |
| ↳ A/B Testing | N/A (decisão humana) | — | — |
| ↳ Routing Adaptativo | Correções de rota alimentam ajustes | ATIVO | `routing_learning_service.py` |
| ↳ Template Learning | N/A | — | — |
| ↳ Calibration | Implicit feedback: avançar candidato low-score = sinal | ATIVO | `calibration_service.py` → `record_implicit_feedback` |
| ↳ Score Normalization | N/A (scores já normalizados) | — | — |
| ↳ Predictive Analytics | N/A | — | — |
| ↳ Model Drift | Trigger se approval_drift > 10 p.p. | ATIVO | `model_drift_service.py` |
| ↳ Conv. Memory | Tracking de ações no kanban | ATIVO | `conversation_state.py` |
| ↳ Semantic Search | N/A | — | — |
| ↳ Voice Analysis | N/A | — | — |

**Pendente:** Audit de overrides humanos precisa ativação (`audit_service.py` — `record_human_review`).

---

### ETAPA 6: CONTATO VIA EMAIL + FOLLOW-UP

| Dimensão | Componente | Status | Arquivo Replit |
|----------|-----------|--------|----------------|
| **Agente** | Ag.0 Orchestrator | Implementado | `main_orchestrator.py` |
| **Agente** | Ag.7 AnalistaFeedback (via CommunicationReActAgent) | Implementado | `app/domains/communication/agents/communication_react_agent.py` |
| **Domínio** | `communication` | Implementado | `app/domains/communication/` |
| **Serviços** | EmailService (Resend/SendGrid), WhatsAppService (Twilio) | Implementados | `email_service.py`, `whatsapp_service.py` |
| **Tools (ReAct)** | `send_email`, `send_whatsapp`, `get_communication_history`, `schedule_message`, `check_rate_limit` | Registradas | `communication_tool_registry.py` (canonical ReAct registry). Nota: `communication_tools.py` (legacy) também registra `send_feedback` e `send_bulk_email` |
| **Frontend** | Templates de email | Implementado | `src/components/` |
| **COMPLIANCE** | | | |
| ↳ FairnessGuard | N/A (email é template) | — | — |
| ↳ PII Masking | Emails não logam dados pessoais | ATIVO | `PIIMaskingFilter` |
| ↳ Fact-Checker | N/A | — | — |
| ↳ Audit Trail | Log de envios + opens + clicks | PRECISA ATIVAR | `audit_service.py` |
| ↳ Policy Engine / Rate Limiting | Limite de envio por empresa/dia | IMPLEMENTADO | `RateLimitRule` sliding window |
| ↳ LGPD | Opt-out link no email | ATIVO | `communication_optout.py` — HMAC-signed tokens, ConsentEvent auditável |
| **INTELIGÊNCIA** | | | |
| ↳ Learning Loop | N/A (email é ação, não sugestão) | — | — |
| ↳ A/B Testing | Variantes de template de email | ATIVO | `seed_email_ab_tests` cria 3 experimentos no startup (Fase 5) |
| ↳ Routing Adaptativo | N/A | — | — |
| ↳ Template Learning | Templates de email aprendidos | ATIVO | `TemplateLearningService` com UNION de fontes corrigida |
| ↳ Calibration | N/A | — | — |
| ↳ Score Normalization | N/A | — | — |
| ↳ Predictive Analytics | N/A | — | — |
| ↳ Model Drift | N/A | — | — |
| ↳ Conv. Memory | Tracking de candidatos contatados | ATIVO | `conversation_state.py` |
| ↳ Semantic Search | N/A | — | — |
| ↳ Voice Analysis | N/A | — | — |

**Pendente:** Nenhum gap nesta etapa. Tracking de opens/clicks depende de configuração no provedor de email de produção.

---

### ETAPA 7: TRIAGEM WSI (Chat Web / WhatsApp)

| Dimensão | Componente | Status | Arquivo Replit |
|----------|-----------|--------|----------------|
| **Agente** | Ag.0 Orchestrator | Implementado | `main_orchestrator.py` |
| **Agente** | Ag.4 EntrevistadorWSI | Implementado | `app/domains/cv_screening/` |
| **Agente** | Ag.5 AvaliadorWSI | Implementado | `app/domains/cv_screening/` |
| **Domínio** | `cv_screening` + `communication` | Implementado | `app/domains/` |
| **Serviços** | WSIService, WhatsAppService, VoiceService | Implementados | `app/services/` |
| **Tools** | `generate_screening_questions`, `analyze_response`, `calculate_wsi` | Registradas | WSI tools |
| **Frontend Chat Web** | Chat page para candidato | **IMPLEMENTADO** | `src/app/triagem/[token]/page.tsx` (Fase 2) |
| **COMPLIANCE** | | | |
| ↳ FairnessGuard L1-L2 | Perguntas e análises sem viés | ATIVO | Reasoning check em `rubric_evaluation.py` |
| ↳ FairnessGuard L3 | Análise semântica das respostas | ATIVO | `check_with_sector()` acessível via RAG pipeline |
| ↳ PII Masking | Strip PII nas respostas antes do LLM | ATIVO | `strip_pii_for_llm_prompt` |
| ↳ Fact-Checker | Validar scores e claims do WSI | ATIVO | `fact_checker.py` integrado no `DomainWorkflow._post_check` — `enable_fact_checker=True` por default |
| ↳ Audit Trail | Log completo: cada pergunta/resposta/score | PRECISA ATIVAR | `audit_service.py` não integrado em `rubric_evaluation.py` |
| ↳ Policy Engine | Autonomy level por setor | IMPLEMENTADO | `ALPHA1_SECTOR_RULES` |
| ↳ LGPD | Consentimento antes da triagem | ATIVO | WelcomeCard com checkbox explícito obrigatório — botões desabilitados até aceite LGPD |
| ↳ Timeout/Abandono | Lembretes 48h + 48h | ATIVO | Celery Beat `wsi-abandoned-check` a cada 4h |
| **INTELIGÊNCIA** | | | |
| ↳ Learning Loop | Captura padrões de resposta por competência | ATIVO | `learning_loop_service.py` |
| ↳ A/B Testing | Variantes de prompt para análise de respostas | ATIVO | `ab_testing_service.py` — endpoints expostos via `api/v1/ab_testing.py` |
| ↳ Routing Adaptativo | N/A (domínio fixo: cv_screening) | — | — |
| ↳ Template Learning | N/A | — | — |
| ↳ Calibration | Calibração de scores WSI | ATIVO | `calibration_service.py` |
| ↳ Score Normalization | Normalização por versão do roteiro | ATIVO | `score_normalization_service.py` |
| ↳ Predictive Analytics | N/A | — | — |
| ↳ Model Drift | Monitora drift em scores WSI | ATIVO | `model_drift_service.py` |
| ↳ Conv. Memory | Estado da triagem por candidato | ATIVO | `conversation_state.py` |
| ↳ Semantic Search | N/A (perguntas já definidas) | — | — |
| ↳ Voice Analysis | STT/TTS para triagem por voz | ATIVO | `voice_service.py` — Deepgram (primário) + OpenAI Whisper (fallback) para STT; OpenAI TTS para síntese |

**Pendente:** Audit Trail precisa ativação em `rubric_evaluation.py` para log de cada pergunta/resposta/score.

---

### ETAPA 8: APROVAR TRIADOS (Gate 2)

| Dimensão | Componente | Status | Arquivo Replit |
|----------|-----------|--------|----------------|
| **Agente** | Ag.7 AnalistaFeedback | Implementado | `app/domains/analytics/` |
| **Agente** | Ag.8 IntegradorATS | Implementado | `app/domains/ats_integration/` |
| **Domínio** | `pipeline` + `kanban` + `analytics` | Implementado | `app/domains/` |
| **Tools** | `suggest_movements`, `check_rejection_fairness` | Registradas | `kanban_tool_registry.py` |
| **Frontend** | Kanban board (mesmo de Gate 1) | Implementado | `src/app/(dashboard)/job-kanban/` |
| **COMPLIANCE** | | | |
| ↳ FairnessGuard | Validação de rejeição (motivo) | ATIVO | Auto-check em `reject_candidate` (`candidate_tools.py`) + FG L3 pré-check no Pipeline Transition Agent |
| ↳ PII Masking | Ativo | ATIVO | — |
| ↳ Audit Trail | Log de aprovação/rejeição Gate 2 | PRECISA ATIVAR | `audit_service.py` |
| ↳ Policy Engine | HITL thresholds por setor | IMPLEMENTADO | `ALPHA1_SECTOR_RULES` |
| ↳ LGPD | Dados compartilhados com próxima etapa | ATIVO | `PipelineFeedbackTool._remove_score_references` strip scores numéricos; `FairnessGuard` sanitiza feedback; `ats_integration_stage_context.py` define campos internos vs ATS |
| **INTELIGÊNCIA** | | | |
| ↳ Learning Loop | Feedback sobre decisões Gate 2 | ATIVO | `learning_loop_service.py` |
| ↳ Calibration | Implicit feedback: avançar candidato low-WSI | ATIVO | `calibration_service.py` |
| ↳ Model Drift | Monitora approval_drift Gate 2 | ATIVO | `model_drift_service.py` |
| ↳ Routing Adaptativo | Correções de rota entre domínios | ATIVO | `routing_learning_service.py` |
| ↳ (demais) | N/A nesta etapa | — | — |

**Pendente:** Audit Trail de aprovação/rejeição Gate 2 precisa ativação em `candidates.py` / pipeline tools.

---

### ETAPA 9: AGENDAR ENTREVISTA + FEEDBACK

| Dimensão | Componente | Status | Arquivo Replit |
|----------|-----------|--------|----------------|
| **Agente** | Ag.6 SchedulingAgent | Implementado | `app/domains/interview_scheduling/` |
| **Agente** | Ag.7 AnalistaFeedback | Implementado | `app/domains/analytics/` |
| **Domínio** | `scheduling` + `analytics` + `communication` | Implementados | `app/domains/` |
| **Serviços** | SchedulingService (ICS + Teams), EmailService, WhatsAppService | Implementados | `app/services/` |
| **Tools** | `schedule_interview`, `send_feedback` | Registradas | `communication_tools.py` |
| **Frontend** | Scheduling UI | Implementado | `src/app/(dashboard)/` |
| **COMPLIANCE** | | | |
| ↳ FairnessGuard | Feedback sem viés | ATIVO | `fairness_guard.check` em `rubric_evaluation.py` |
| ↳ PII Masking | Ativo | ATIVO | — |
| ↳ Fact-Checker | N/A | — | — |
| ↳ Audit Trail | Log de aprovação/rejeição + feedback enviado | PRECISA ATIVAR | `audit_service.py` |
| ↳ Policy Engine | N/A | — | — |
| ↳ LGPD | Dados compartilhados com calendário | ATIVO | `SchedulingService.generate_ics_content` — data minimization: apenas dtstart/dtend/summary/location/attendee, sem dados sensíveis do candidato |
| **INTELIGÊNCIA** | | | |
| ↳ Learning Loop | Feedback sobre qualidade do feedback gerado | ATIVO | `learning_loop_service.py` — feedback loop no fluxo de avaliação |
| ↳ A/B Testing | Variantes de template de feedback | ATIVO | `ab_testing_service.py` — endpoints expostos via `api/v1/ab_testing.py`. Falta criar experimentos de feedback-specific |
| ↳ Template Learning | Templates de feedback aprendidos | ATIVO | `template_learning_service.py` com UNION de fontes corrigida |
| ↳ Embedding Service | Embedding do perfil para matching futuro | ATIVO | `embedding_service.py` (Gemini 768-dim) com cache via `embedding_cache_service.py`. Auto-trigger em `reject_candidate` → `_generate_rediscovery_embedding` gera embedding para re-discovery futuro |
| ↳ Long-Term Memory | Armazena episódios da vaga para referência | ATIVO | `long_term_memory.py` — integrado no `EnhancedAgentMixin._post_loop_learning` (episódios salvos após cada ReAct loop) + `_get_memory_context` para enriquecer prompts |
| ↳ (demais) | N/A nesta etapa | — | — |

**Pendente:** Teams/Google Calendar depende de configuração de tenant do cliente para produção. Audit Trail precisa ativação.

---

## 3. MATRIZ CONSOLIDADA: COMPLIANCE POR AGENTE

| Agente | Domínio | FG L1 | FG L2 | FG L3 | PII | LGPD | Fact-Check | Audit | Policy | Bias Det. |
|--------|---------|:-----:|:-----:|:-----:|:---:|:----:|:----------:|:-----:|:------:|:---------:|
| Ag.0 Orchestrator | orchestration | ATIVO | ATIVO | — | ATIVO | — | ATIVO | Parcial | ATIVO | Via FG |
| Ag.2 Sourcing | sourcing | ATIVO | ATIVO | ATIVO | ATIVO | Anonymize | ATIVO | A ativar | — | Via FG |
| Ag.3 TriagemCurr. | cv_screening | ATIVO | ATIVO | ATIVO | ATIVO | ATIVO | ATIVO | A ativar | — | Via FG |
| Ag.4 Entrev.WSI | cv_screening | ATIVO | ATIVO | ATIVO | ATIVO | ATIVO | ATIVO | A ativar | — | Via FG |
| Ag.5 Avaliador WSI | cv_screening | ATIVO | ATIVO | ATIVO | ATIVO | ATIVO | ATIVO | A ativar | — | Via FG |
| Ag.6 Scheduling | scheduling | — | — | — | ATIVO | ATIVO | — | A ativar | — | — |
| Ag.7 Feedback | analytics | ATIVO | ATIVO | — | ATIVO | — | ATIVO | A ativar | — | Via FG |
| Ag.8 ATS Integr. | ats_integration | — | — | — | ATIVO | PARCIAL | — | A ativar | — | — |

**Legenda:** ATIVO = funcionando | A ativar = código existe, precisa ligar | A impl. = código não existe | A verificar = precisa checagem

---

## 4. MATRIZ CONSOLIDADA: INTELIGÊNCIA POR ETAPA

| Etapa | Learning Loop | A/B Test | Routing | Template | Calibr. | Score Norm. | Predict. | Drift | Conv. Mem. | Semantic | Voice |
|-------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1. Login | — | — | — | — | — | — | — | — | — | — | — |
| 2. Editar Vaga | ATIVO | ATIVO | — | ATIVO | — | — | ATIVO | — | ATIVO | ATIVO | — |
| 3. Roteiro WSI | ATIVO | ATIVO | — | — | — | — | — | — | ATIVO | ATIVO | — |
| 4. Buscar Cand. | ATIVO | ATIVO | ATIVO | — | ATIVO | ATIVO | ATIVO | ATIVO | ATIVO | ATIVO | — |
| 5. Gate 1 | ATIVO | — | ATIVO | — | ATIVO | — | — | ATIVO | ATIVO | — | — |
| 6. Email/Follow | — | ATIVO | — | ATIVO | — | — | — | — | ATIVO | — | — |
| 7. Triagem WSI | ATIVO | ATIVO | — | — | ATIVO | ATIVO | — | ATIVO | ATIVO | — | ATIVO |
| 8. Gate 2 | ATIVO | — | ATIVO | — | ATIVO | — | — | ATIVO | — | — | — |
| 9. Agendar/Feed. | ATIVO | ATIVO | — | ATIVO | — | — | — | — | — | — | — |

**Legenda:** ATIVO = integrado e funcionando | — = N/A

---

## 5. DETALHAMENTO DAS 11 CAMADAS DE INTELIGÊNCIA

### 5.1 Learning Loop (Captura Silenciosa)
- **Arquivo:** `app/shared/learning/learning_loop_service.py` (1137 linhas)
- **Mecanismo:** Observa o que o recrutador aceita, modifica ou rejeita sem pedir feedback explícito
- **Outcomes:** `accepted` | `modified` | `rejected` | `ignored`
- **Pattern Types:** salary_preference, skill_preference, benefit_preference, work_model_preference, screening_preference, jd_style_preference, source_trust
- **Confidence:** Baseada em sample size (≥20 = high, ≥10 = medium, ≥5 = low)
- **FairnessGuard Integration:** `validate_learning_batch()` bloqueia padrões discriminatórios ANTES de persistir (F1-02)
- **Model Drift Integration:** Trigger automático via `asyncio.create_task` quando feedback é `rejected` ou `ignored`
- **Snapshot Integration:** `learning_snapshot_service` salva snapshot ANTES de aplicar patterns (rollback Z2-01)

### 5.2 A/B Testing
- **Arquivo:** `app/shared/learning/ab_testing_service.py` (307 linhas)
- **Mecanismo:** Hash-based traffic splitting (MD5 → bucket 0-9999)
- **Estatísticas:** z-score, p-value (erfc), 95% CI, improvement percentage
- **Significância:** p < 0.05 AND |improvement| > 5%
- **Modelo:** `PromptVariant` (test_name, variant_name, traffic_percentage) + `ABTestResult` (metric_name, metric_value)

### 5.3 Routing Adaptativo
- **Arquivo:** `app/services/routing_learning_service.py`
- **Mecanismo:** Quando usuário corrige roteamento (mensagem foi pro domínio errado), ajusta multiplicadores de confiança por domínio
- **Range:** 0.8x (muitos erros) a 1.2x (alta precisão)
- **Método:** `compute_domain_confidence_adjustments(company_id, db)` → Dict[str, float]

### 5.4 Template Learning
- **Arquivo:** `app/shared/learning/template_learning_service.py`
- **Mecanismo:** Após 3 vagas similares (mesmo setor/seniority), gera template automaticamente
- **Métodos:** `learn_from_job_creation()`, `suggest_templates_for_improvement()`

### 5.5 Calibration
- **Arquivo:** `app/services/calibration_service.py`
- **Mecanismo:** Dual feedback — explícito (thumbs up/down) + implícito (avançar candidato low-score)
- **Output:** `CalibrationSuggestion` (ex: "Reduzir peso de skill técnica em 15%")
- **Métodos:** `record_explicit_feedback()`, `record_implicit_feedback()`, `generate_suggestions()`

### 5.6 Score Normalization
- **Arquivo:** `app/domains/cv_screening/services/score_normalization_service.py`
- **Mecanismo:** Ajusta scores baseado no `difficulty_coefficient` da versão do questionário
- **Objetivo:** Candidatos que responderam versões mais difíceis não são penalizados

### 5.7 Predictive Analytics
- **Arquivo:** `app/domains/analytics/services/predictive_analytics_service.py` (+ `app/services/ml/outcome_predictor.py`)
- **API:** `app/api/v1/predictive_analytics.py` (endpoints expostos)
- **Agent Tools:** `predictive_tools.py` — integrado em agentes analytics/sourcing
- **Métodos:**
  - `predict_time_to_fill(db, job_data, company_id)` → dias estimados + confidence
  - `predict_optimal_salary(db, job_data, company_id)` → faixa salarial competitiva
  - `predict_skill_success(db, skill_name, company_id)` → probabilidade de sucesso

### 5.8 Model Drift
- **Arquivo:** `app/services/model_drift_service.py`
- **4 Dimensões monitoradas:**
  - Score Drift: variação > 0.5 pts na janela de 7 dias
  - Approval Drift: variação > 10 pontos percentuais
  - Cost Drift: aumento significativo de custo LLM
  - Latency Drift: degradação de tempo de resposta
- **Trigger:** Chamado automaticamente pelo Learning Loop quando feedback negativo acumula

### 5.9 Conversation Memory
- **Arquivo:** `app/shared/memory/conversation_state.py`
- **Mecanismo:** Estado efêmero da sessão de chat
- **Recursos:**
  - Entity tracking (última vaga, último candidato mencionado)
  - Pronoun resolution ("conte mais sobre **ele**" → resolve para último candidato)
  - Active filters tracking (filtros de busca persistem na sessão)
- **Long-Term Memory:** `libs/agents-core/lia_agents_core/long_term_memory.py` — episódios + compressão LLM após 30 dias. Integrado ativamente via `EnhancedAgentMixin._post_loop_learning` (salva learnings após cada ReAct loop) + `_get_memory_context` (enriquece system prompt com memórias históricas). Background processing via Celery tasks

### 5.10 Semantic Search
- **Arquivo:** `app/shared/intelligence/semantic_search_service.py`
- **Provider:** Gemini `text-embedding-004` (768 dimensões)
- **Cache:** Redis para evitar re-embedding
- **Domínios:** Skills, Job Titles, Industries, Locations
- **Métodos:** `expand_query(domain, query)`, `expand_skills()`, `expand_job_titles()`
- **Embedding Service:** `app/shared/intelligence/embedding_service.py` — wrapper para geração de vetores

### 5.11 Voice Analysis
- **Arquivo:** `app/services/voice_service.py`
- **STT Providers:** Deepgram (primário), Whisper (fallback)
- **TTS Provider:** OpenAI (`voice="nova"`)
- **Uso:** Triagem WSI por voz (candidato pode responder por áudio)

---

## 6. GAPS IDENTIFICADOS

### 6.1 Gaps Estruturais (faltam no fluxo)

| # | Gap | Impacto | Prioridade |
|---|-----|---------|-----------|
| G7 | **Configuração de Infra Externa** — API keys: Twilio, Resend/SendGrid, ATS | Sem credenciais, tudo roda em "dev mode" (Apify já configurado) | PÓS MVP |

### 6.2 Gaps de Compliance

| # | Gap | O que existe | O que falta | Prioridade |
|---|-----|-------------|-------------|-----------|
| C3 | **Audit Trail completo** | `AuditService` com 8 decision types; ativo em `jd_generation.py` e `wsi_questions.py` | Ativar em: `auth.py` (login), `candidates.py` (busca), pipeline tools (aprovação/rejeição), `rubric_evaluation.py` (triagem), communication (contato) | MVP |
| C6 | **Bias Audit Report** | FairnessGuard coleta dados | Falta dashboard/relatório periódico de Four-Fifths Rule | PÓS MVP |
| C7 | **EU AI Act Compliance** | Mencionado nos docs | Falta classificação de risco por agente e disclosure obrigatório | PÓS MVP |

### 6.3 Gaps de Inteligência

| # | Gap | Status | O que falta |
|---|-----|--------|-------------|
| I2 | **Predictive Analytics UI** | Backend ATIVO — endpoints expostos, integrado em agentes | Falta UI de Predictive Analytics na página de vagas (mostrar predict_time_to_fill, predict_optimal_salary ao recrutador) |

---

## 7. MAPA DE PRIORIDADES DE CONSTRUÇÃO

### Fase 0: INFRAESTRUTURA

| # | Item | Tipo | Status |
|---|------|------|--------|
| P0.1 | Configurar credenciais de produção (Twilio, Resend, ATS) | Config | **PÓS MVP** — Apify já configurado; demais dependem de contas de produção |
| P0.3 | Configurar Elasticsearch + PGVector em produção | Infra | **PÓS MVP** — config de produção |
| P0.4 | Ativar Audit Trail em todos os endpoints | Backend | **PENDENTE** — ativo em JD/WSI, falta ativar nos demais touchpoints |

> Fases 1 (Fluxo Core), 2 (Triagem + Automação) e 3 (Gates + Scheduling) — **100% completas**. Único item parcial: P3.4 Bell notification pendente.

### Fase 4: COMPLIANCE + INTELIGÊNCIA PROFUNDA

| # | Item | Tipo | Status |
|---|------|------|--------|
| P3.4 | Bell notification (notificações in-app) | Frontend | **PENDENTE** — Teams e Email ativos; falta bell |
| P4.1 | Bias Audit Dashboard (Four-Fifths Rule) | Frontend + Backend | **PENDENTE** |
| P4.2 | EU AI Act Risk Classification por agente | Docs + Backend | **PENDENTE** |
| P4.3 | LGPD DSR (Data Subject Requests) — export/delete | Backend | **PENDENTE** |
| P4.4 | Criar A/B Tests de prompt JD/scoring | Backend | **PARCIAL** — infraestrutura ATIVA (endpoints + seed email templates); falta criar testes de prompt JD-specific e scoring-specific |
| P4.5 | Integrar Predictive Analytics na UI de vagas | Frontend + Backend | **PENDENTE** |
| P4.7 | SOX Audit Export (para auditoria externa) | Backend | **PENDENTE** |

---

## 8. GRAFO DE DEPENDÊNCIAS DOS AGENTES

```
                    ┌──────────────┐
                    │  Ag.0        │
                    │ Orchestrator │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────▼────┐ ┌────▼─────┐ ┌────▼─────┐
        │  Ag.2    │ │  Ag.4   │ │  Ag.8   │
        │ Sourcing │ │Entrev.  │ │ ATS Int.│
        └─────┬────┘ │  WSI    │ └────┬────┘
              │      └────┬────┘      │
              │           │           │
        ┌─────▼────┐ ┌────▼─────┐    │
        │  Ag.3    │ │  Ag.5   │    │
        │ Triagem  │ │Avaliador│    │
        │Curricular│ │  WSI    │    │
        └──────────┘ └────┬────┘    │
                          │         │
                    ┌─────▼────┐    │
                    │  Ag.7    │◄───┘
                    │Analista  │
                    │Feedback  │
                    └─────┬────┘
                          │
                    ┌─────▼────┐
                    │  Ag.6    │
                    │Scheduling│
                    └──────────┘
```

---

## 9. DETALHAMENTO FairnessGuard — ARQUITETURA 3 CAMADAS

### Layer 1: Explicit Bias Block (350+ patterns, 13 categorias)
- **Categorias:** gender, age, ethnicity, religion, disability, marital_status, sexual_orientation, pregnancy, appearance, social_class, political, nationality, health
- **Ação:** BLOCK — impede processamento
- **Integração ativa:** MainOrchestrator (pré-roteamento)
- **Protected fields:** `_LEARNING_PROTECTED_FIELDS` = {gender, age, ethnicity, marital_status, photo, institution, address, religion, disability, cv_gaps}

### Layer 2: Implicit Bias Soft Warning (proxy terms)
- **Exemplos:** "dinâmico" → proxy para age, "boa aparência" → proxy para appearance
- **Ação:** WARN — permite com alerta
- **Integração ativa:** MainOrchestrator (pré-roteamento)

### Layer 3: Semantic Analysis (LLM-based)
- **Provider:** Gemini (análise semântica profunda)
- **Ação:** WARN ou BLOCK dependendo da severidade
- **Integração:** Condicionada por setor via `ALPHA1_SECTOR_RULES[sector].fairness_layer3_enabled`
- **Setores com L3 ativo:** tech, financeiro, saude, rpo
- **Setores sem L3:** varejo, logistica

### FairnessGuard no Learning Loop (F1-02)
- `validate_learning_batch()` — chamado ANTES de persistir patterns aprendidos
- Bloqueia patterns que correlacionam com campos protegidos
- Audit trail automático quando pattern é bloqueado

---

## 10. ARQUIVOS-CHAVE DO CÓDIGO REFERENCIADOS

### Backend Core
| Arquivo | Responsabilidade |
|---------|-----------------|
| `app/orchestrator/main_orchestrator.py` | Orquestração central (3 fases) + FairnessGuard L1-L2 |
| `app/orchestrator/intent_router.py` | Roteamento de intents por cascata de modelos |
| `libs/agents-core/lia_agents_core/react_agent_registry.py` | Registry de agentes ReAct |
| `libs/agents-core/lia_agents_core/langgraph_base.py` | Base LangGraph com checkpointer |

### Compliance (6 camadas)
| Arquivo | Responsabilidade |
|---------|-----------------|
| `app/shared/compliance/fairness_guard.py` | FairnessGuard (3 camadas, ~350 patterns, 13 categorias) |
| `app/shared/pii_masking.py` | PII Masking (4 camadas, Presidio opt-in) |
| `app/shared/compliance/audit_service.py` | Audit Trail (SOX-compliant, 730-1825d retention, human override) |
| `app/shared/compliance/fact_checker.py` | Fact-Checker (salary, count, %, date + V5 granulares) |
| `app/services/policy_engine_service.py` | Policy Engine + Rate Limiting + Escalation + Sector Rules |
| `app/api/v1/lgpd.py` | LGPD endpoints (consent, DSR, anonymize) |

### Inteligência (11 camadas)
| Arquivo | Responsabilidade |
|---------|-----------------|
| `app/shared/learning/learning_loop_service.py` | Learning Loop (silent capture + FairnessGuard F1-02) |
| `app/shared/learning/ab_testing_service.py` | A/B Testing (z-score, p-value, 95% CI) |
| `app/services/routing_learning_service.py` | Routing Adaptativo (0.8x-1.2x confidence multipliers) |
| `app/shared/learning/template_learning_service.py` | Template Learning (auto after 3 similar jobs) |
| `app/services/calibration_service.py` | Calibration (explicit + implicit feedback → weight suggestions) |
| `app/domains/cv_screening/services/score_normalization_service.py` | Score Normalization (difficulty coefficient) |
| `app/services/ml/outcome_predictor.py` | Predictive Analytics (time-to-fill, optimal salary, skill success) |
| `app/services/model_drift_service.py` | Model Drift (4 dimensions: score, approval, cost, latency) |
| `app/shared/memory/conversation_state.py` | Conversation Memory (entity tracking, pronoun resolution) |
| `app/shared/intelligence/semantic_search_service.py` | Semantic Search (Gemini 768-dim, Redis cache, domain expansion) |
| `app/services/voice_service.py` | Voice Analysis (STT: Deepgram/Whisper, TTS: OpenAI) |
| `app/shared/intelligence/embedding_service.py` | Embedding Service (Gemini text-embedding-004, 768-dim) |
| `libs/agents-core/lia_agents_core/long_term_memory.py` | Long-Term Memory (episodes + LLM compression after 30d) |
| `app/shared/learning/learning_snapshot_service.py` | Learning Snapshot (pre-learning rollback points, Z2-01) |

### Communication
| Arquivo | Responsabilidade |
|---------|-----------------|
| `app/domains/communication/services/email_service.py` | Email (Resend/SendGrid) |
| `app/domains/communication/services/whatsapp_service.py` | WhatsApp (Twilio) |
| `app/domains/cv_screening/services/wsi_service.py` | WSI (CBI/Bloom/Dreyfus/Big Five) |
| `app/domains/ats_integration/` | ATS (Gupy/Pandapé/Merge.dev) |
| `app/domains/interview_scheduling/services/scheduling_service.py` | Scheduling (ICS + Teams) |

