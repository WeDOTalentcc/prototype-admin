# Spec: Políticas de Contratação — Configuração Assistida por LIA

**Versão:** 1.0  
**Data:** 21/02/2026  
**Status:** Planejamento  
**Autor:** Equipe de Produto WeDoTalent

---

## 1. Visão Geral

A funcionalidade **Políticas de Contratação** permite que empresas configurem como o processo de recrutamento funciona através de uma conversa assistida pela LIA. As regras definidas alimentam toda a inteligência da plataforma — a LIA passa a operar como uma recrutadora interna que conhece os processos, prazos e preferências da empresa.

### 1.1 Princípios

1. **Não é obrigatório** — A empresa usa a plataforma normalmente sem configurar. A LIA opera no modo genérico até que as regras sejam definidas
2. **Progressivo** — Não precisa responder tudo de uma vez. Pode voltar e complementar
3. **Reconfigurável** — O recrutador volta a qualquer momento e muda via chat ou edição direta no painel
4. **Aprendizado contínuo** — Além das regras explícitas, a LIA observa padrões e calibra automaticamente
5. **Customer Success** — O momento ideal é quando o time de CS está junto com o cliente

### 1.2 Fluxo do Usuário

```
Dia 1:   Cliente entra → usa a plataforma normalmente → LIA opera no genérico
Dia 15:  CS agenda sessão → abre Configurações → Políticas → LIA faz perguntas → regras salvas
Dia 30:  Recrutador percebe que quer mudar algo → volta lá → ajusta via chat ou painel
Dia 60+: LIA já aprendeu padrões → sugere ajustes nas regras → recrutador confirma
```

---

## 2. Layout da Tela

**Localização:** Menu Configurações → Tab "Políticas de Contratação"

**Diagramas no FigJam:**
- Layout da tela: [Layout - Políticas de Contratação](https://www.figma.com/online-whiteboard/create-diagram/804303f5-3a26-417b-8465-731a8dbd4a50?utm_source=other&utm_content=edit_in_figjam)
- Fluxo de onboarding: [Fluxo Onboarding - 19 Perguntas LIA](https://www.figma.com/online-whiteboard/create-diagram/b9190356-1ea6-4902-ad00-adf832672f81?utm_source=other&utm_content=edit_in_figjam)
- Arquitetura de automação: [Arquitetura Automação Progressiva - 5 Níveis](https://www.figma.com/online-whiteboard/create-diagram/b8f7d8b3-2dd5-4222-9de1-1ac20537b0e2?utm_source=other&utm_content=edit_in_figjam)

### 2.1 Wireframe Detalhado

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  ⚙ Configurações                                                           │
│  ─────────────────────────────────────────────────────────────────────────── │
│  [Empresa] [Equipe] [Integrações] [●Políticas de Contratação] [Billing]    │
│                                          ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔          │
│                                          (underline cyan #60BED1)           │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────┐    ┌───────────────────────────────────────┐   │
│  │  CHAT LIA (~420px)      │    │  PAINEL DE POLÍTICAS (flex-1)        │   │
│  │  bg: #141414            │    │  bg: transparent                     │   │
│  │  border: 1px #1E1E1E    │    │                                      │   │
│  │  rounded-md (8px)       │    │  ── Progresso ──────────────────────  │   │
│  │                         │    │  ▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░░░  │   │
│  │  ┌─────────────────┐   │    │  5 de 19 regras configuradas          │   │
│  │  │ 🤖 LIA • online │   │    │  Última atualização: 15/03/2026      │   │
│  │  │ (cyan dot)       │   │    │                                      │   │
│  │  └─────────────────┘   │    │  ┌─────────────────────────────────┐  │   │
│  │                         │    │  │  📋 Pipeline e Processo         │  │   │
│  │  ┌─────────────────┐   │    │  │  bg: #141414                    │  │   │
│  │  │ Bot msg (#1A1A1A)│   │    │  │  border: 1px #1E1E1E           │  │   │
│  │  │ Olá! Vou te     │   │    │  │  rounded-md (8px)               │  │   │
│  │  │ ajudar a config..│   │    │  │                                 │  │   │
│  │  └─────────────────┘   │    │  │  Mín. entrevistas: 2        ✓   │  │   │
│  │                         │    │  │  Aprovação gestor: Sim      ✓   │  │   │
│  │     ┌──────────────┐   │    │  │  SLA por etapa: —               │  │   │
│  │     │ User msg     │   │    │  │  Templates: —                   │  │   │
│  │     │ (cyan tint)  │   │    │  │                       [Editar]  │  │   │
│  │     └──────────────┘   │    │  └─────────────────────────────────┘  │   │
│  │                         │    │                                      │   │
│  │  ┌─────────────────┐   │    │  ┌─────────────────────────────────┐  │   │
│  │  │ Bot msg         │   │    │  │  📅 Agendamento                 │  │   │
│  │  │ Quantas entre.. │   │    │  │                                 │  │   │
│  │  └─────────────────┘   │    │  │  Dias: —                        │  │   │
│  │                         │    │  │  Horários: —                    │  │   │
│  │     ┌──────────────┐   │    │  │  Duração: —                     │  │   │
│  │     │ User resp    │   │    │  │  Auto-agendamento: —            │  │   │
│  │     └──────────────┘   │    │  │                       [Editar]  │  │   │
│  │                         │    │  └─────────────────────────────────┘  │   │
│  │  ┌─────────────────┐   │    │                                      │   │
│  │  │ Bot msg         │   │    │  ┌─────────────────────────────────┐  │   │
│  │  │ Entendido!...   │   │    │  │  💬 Comunicação                 │  │   │
│  │  └─────────────────┘   │    │  │                                 │  │   │
│  │                         │    │  │  Feedback reprovação: —         │  │   │
│  │  ┌─────────────────┐   │    │  │  Prazo feedback: —              │  │   │
│  │  │ [Digite...]  [➤]│   │    │  │  Canal preferido: —             │  │   │
│  │  │ (input field)    │   │    │  │  Tom da LIA: —                 │  │   │
│  │  └─────────────────┘   │    │  │                       [Editar]  │  │   │
│  └─────────────────────────┘    │  └─────────────────────────────────┘  │   │
│                                  │                                      │   │
│                                  │  ┌─────────────────────────────────┐  │   │
│                                  │  │  🔍 Triagem                    │  │   │
│                                  │  │                                 │  │   │
│                                  │  │  Filtro salarial: —            │  │   │
│                                  │  │  Experiência: —                │  │   │
│                                  │  │  Perguntas padrão: —           │  │   │
│                                  │  │                       [Editar]  │  │   │
│                                  │  └─────────────────────────────────┘  │   │
│                                  │                                      │   │
│                                  │  ┌─────────────────────────────────┐  │   │
│                                  │  │  🤖 Autonomia da LIA           │  │   │
│                                  │  │                                 │  │   │
│                                  │  │  Triagem automática: —         │  │   │
│                                  │  │  Agendamento automático: —     │  │   │
│                                  │  │  Mover etapa automático: —     │  │   │
│                                  │  │  Nível autonomia: —            │  │   │
│                                  │  │                       [Editar]  │  │   │
│                                  │  └─────────────────────────────────┘  │   │
│                                  └───────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Especificações Visuais (DS v4.1)

| Elemento | Token | Valor |
|----------|-------|-------|
| Background página | `--bg-primary` | #0A0A0A |
| Background cards | `--bg-card` | #141414 |
| Border cards | `--border-subtle` | #1E1E1E |
| Border radius cards | `rounded-md` | 8px |
| Accent (LIA) | `--accent-cyan` | #60BED1 |
| Texto primário | `--text-primary` | #FFFFFF |
| Texto secundário | `--text-secondary` | #9CA3AF |
| Texto desabilitado | `--text-disabled` | #4B5563 |
| Chat bot msg bg | `--bg-chat-bot` | #1A1A1A |
| Chat user msg bg | `--bg-chat-user` | rgba(96,190,209,0.08) |
| Checkmark configurado | `--accent-cyan` | #60BED1 |
| Progress bar | `--accent-cyan` | #60BED1 |
| Font títulos cards | Inter | 14px semibold |
| Font valores | Open Sans | 13px regular |
| Font labels | Open Sans | 12px regular, text-secondary |

### 2.3 Comportamento Interativo

1. **Estado vazio:** Todos os cards mostram "—" em cinza com texto "Converse com a LIA para configurar" na parte superior do painel
2. **Preenchimento em tempo real:** Conforme a LIA recebe respostas, os valores aparecem nos cards com animação fade-in
3. **Checkmarks:** Valores configurados mostram ✓ em cyan; não configurados mostram "—" em cinza
4. **Botão [Editar]:** Abre o card em modo edição inline (campos editáveis diretamente)
5. **Barra de progresso:** Atualiza automaticamente conforme regras são salvas (X de 19)
6. **Scroll:** O painel direito faz scroll independente; o chat tem scroll próprio
7. **Responsividade:** Em telas < 1024px, os painéis empilham verticalmente (chat em cima, cards embaixo)

---

## 3. Modelo de Dados

### 3.1 Tabela: `company_hiring_policies`

```python
class CompanyHiringPolicy(Base):
    __tablename__ = "company_hiring_policies"
    
    id = Column(UUID, primary_key=True, default=uuid4)
    company_id = Column(String(255), nullable=False, unique=True, index=True)
    
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    updated_by = Column(String(255), nullable=True)
    setup_progress = Column(Integer, default=0)  # 0-100%
    setup_completed_at = Column(DateTime, nullable=True)
    
    # Bloco 1: Pipeline e Processo
    pipeline_rules = Column(JSON, default=lambda: {
        "min_interviews_before_offer": None,
        "manager_approval_for_offer": None,
        "max_days_in_stage": {},
        "pipeline_templates": []
    })
    
    # Bloco 2: Agendamento
    scheduling_rules = Column(JSON, default=lambda: {
        "allowed_days": None,
        "allowed_hours": None,
        "default_duration_minutes": None,
        "self_scheduling_enabled": None
    })
    
    # Bloco 3: Comunicação
    communication_rules = Column(JSON, default=lambda: {
        "auto_rejection_feedback": None,
        "rejection_feedback_deadline_hours": None,
        "preferred_channel": None,
        "lia_tone": None
    })
    
    # Bloco 4: Triagem
    screening_rules = Column(JSON, default=lambda: {
        "salary_expectation_filter": None,
        "salary_tolerance_percent": None,
        "experience_policy": None,
        "default_screening_questions": []
    })
    
    # Bloco 5: Autonomia da LIA
    automation_rules = Column(JSON, default=lambda: {
        "auto_screening": None,
        "auto_scheduling": None,
        "auto_stage_advance": None,
        "autonomy_level": None
    })
    
    # Padrões aprendidos (preenchido automaticamente pela LIA)
    learned_patterns = Column(JSON, default=lambda: [])
    
    __table_args__ = (
        Index('ix_hiring_policy_company', 'company_id'),
    )
```

### 3.2 Integração com Modelos Existentes

| Modelo existente | Campo relevante | Como se conecta | Mapeamento de dados |
|---|---|---|---|
| `RecruitmentStage` | `sla_hours` | `pipeline_rules.max_days_in_stage` alimenta o SLA | Chave: `stage_id` (UUID). Valor em dias, convertido para horas (`dias * 24`) ao gravar em `sla_hours`. Ex: `{"stage_abc": 5}` → `sla_hours = 120` |
| `RecruitmentStage` | `auto_advance_rules` | `automation_rules.auto_stage_advance` é um toggle global que habilita/desabilita as regras per-stage | Se `auto_stage_advance = false`, todas as `auto_advance_rules` das stages da empresa são ignoradas. Se `true`, cada stage mantém suas regras individuais. |
| `RecruitmentStage` | `action_behavior` | Informa o tipo de ação esperada na etapa | Leitura apenas — não é modificado pela policy |
| `RecruitmentSubStatus` | `auto_actions` | Conecta com regras de automação | Leitura apenas |
| `ScreeningQuestion` | company-scoped | `screening_rules.default_screening_questions` referencia IDs | Array de `question_id` (UUID). Essas questions são adicionadas automaticamente a toda nova vaga |
| Feature Flags | `ENABLE_*` | `automation_rules` mapeia para feature flags por empresa | `auto_screening` → `ENABLE_AUTO_SCREENING_{company_id}`, `auto_scheduling` → `ENABLE_AUTO_SCHEDULING_{company_id}` |

> **Nota sobre unidades:** `max_days_in_stage` usa dias (inteiro) como unidade no JSON da policy. A conversão para `sla_hours` no `RecruitmentStage` é feita automaticamente pelo serviço de sincronização (`PolicySyncService`).

### 3.3 Acesso pelos Agentes

Cada agente/serviço acessa as políticas via `context.tenant_id`:

```python
async def get_company_policy(company_id: str) -> CompanyHiringPolicy:
    """Retorna as políticas da empresa ou defaults se não configurado."""
    policy = await db.query(CompanyHiringPolicy).filter_by(company_id=company_id).first()
    if not policy:
        return CompanyHiringPolicy(company_id=company_id)  # defaults
    return policy
```

---

## 4. Roteiro de Perguntas da LIA

### 4.1 Regras de Condução

- A LIA **não faz todas as perguntas de uma vez** — agrupa por bloco
- Após cada bloco: "Salvei as configurações de [bloco]. Quer continuar ou prefere parar por aqui?"
- Entende respostas naturais: "Terça a quinta" → `["tue","wed","thu"]`
- Permite pular: "Pula essa" / "Não sei ainda" → mantém null (default genérico)
- Valores preenchidos aparecem no painel direito em tempo real
- Recrutador pode voltar a qualquer momento e recomeçar ou ajustar

### 4.2 Bloco 1: Pipeline e Processo (4 perguntas)

| # | Pergunta da LIA | Campo | Default | Conexão na plataforma | Implementação |
|---|---|---|---|---|---|
| 1 | "Quantas entrevistas mínimas vocês fazem antes de enviar uma proposta ao candidato?" | `pipeline_rules.min_interviews_before_offer` | null (sem limite) | Validação no modal de transição para etapa Proposta | **NOVO** — Requer validação no `UniversalTransitionModal` ao mover para Proposta: contar stages do tipo "interview" completadas |
| 2 | "A proposta salarial precisa de aprovação do gestor da área?" | `pipeline_rules.manager_approval_for_offer` | null | `batch-approval-modal.tsx`, workflow de aprovação | **NOVO** — Requer workflow de aprovação com notificação ao gestor |
| 3 | "Qual o tempo máximo que um candidato pode ficar em cada etapa sem nenhuma ação? Por exemplo, 5 dias na triagem, 10 dias na entrevista." | `pipeline_rules.max_days_in_stage` | null | Campo `sla_hours` no `RecruitmentStage` | **EXISTENTE** — `RecruitmentStage.sla_hours` já existe. Necessário: `PolicySyncService` para converter dias→horas e popular |
| 4 | "Vocês têm tipos de vagas com processos diferentes? Por exemplo, operacional com menos etapas, técnica com mais etapas?" | `pipeline_rules.pipeline_templates` | [] | `RecruitmentStage` per-company, `Jornada de Recrutamento` | **EXISTENTE** — Templates de jornada já suportados. Armazena labels como referência informativa |

**Resumo do bloco:**
> "Entendido! Salvei: [valores]. Essas regras vão ajudar a LIA a monitorar prazos e alertar quando algum candidato ficar parado. Quer continuar para as configurações de agendamento?"

### 4.3 Bloco 2: Agendamento (4 perguntas)

| # | Pergunta da LIA | Campo | Default | Conexão na plataforma | Implementação |
|---|---|---|---|---|---|
| 5 | "Quais dias da semana são permitidos para entrevistas?" | `scheduling_rules.allowed_days` | null (todos) | `scheduling_service.py`, `calendar_service.py` | **PARCIAL** — Serviço de agendamento existe, mas não consulta policy. Necessário: injetar filtro de dias |
| 6 | "Qual o horário permitido? Por exemplo, das 9h às 18h." | `scheduling_rules.allowed_hours` | null | `scheduling_service.py` | **PARCIAL** — Mesmo caso acima |
| 7 | "Qual a duração padrão de uma entrevista?" | `scheduling_rules.default_duration_minutes` | null (60min) | `scheduling_service.py` | **PARCIAL** — Serviço aceita duração, mas sem default de policy |
| 8 | "Candidatos podem escolher o horário da entrevista sozinhos, com base na agenda disponível?" | `scheduling_rules.self_scheduling_enabled` | null (false) | `ScreeningSchedulingModal.tsx` | **NOVO** — Auto-agendamento é funcionalidade futura |

**Resumo do bloco:**
> "Configurações de agendamento salvas! Quando a LIA sugerir horários de entrevista, vai respeitar essas regras. Quer configurar como a comunicação com candidatos funciona?"

### 4.4 Bloco 3: Comunicação (4 perguntas)

| # | Pergunta da LIA | Campo | Default | Conexão na plataforma | Implementação |
|---|---|---|---|---|---|
| 9 | "Candidatos reprovados devem receber uma mensagem de feedback automática?" | `communication_rules.auto_rejection_feedback` | null (false) | `CommunicationDispatcher`, `transition_dispatch_service.py` | **PARCIAL** — `CommunicationDispatcher` envia, mas não dispara automaticamente após reprovação. Necessário: hook no `transition_dispatch_service` |
| 10 | "Em quanto tempo após a reprovação o feedback deve ser enviado? Por exemplo, 24h, 48h." | `communication_rules.rejection_feedback_deadline_hours` | null (48h) | SLA de comunicação | **NOVO** — Requer scheduler para despacho atrasado (delayed job) |
| 11 | "Qual o canal preferido para falar com candidatos: WhatsApp, email ou ambos?" | `communication_rules.preferred_channel` | null | `whatsapp_service.py`, `email_service.py`, `ScreeningChannelsModal.tsx` | **EXISTENTE** — Canais já existem. Necessário: consultar policy como fallback quando recrutador não especifica |
| 12 | "Qual o tom que a LIA deve usar ao falar com candidatos? Profissional, amigável ou mais formal?" | `communication_rules.lia_tone` | null ("professional") | System prompts da LIA, `lia_persona` | **NOVO** — Requer template de system prompt parametrizável por tom. Valor injetado no prompt da LIA: `{tone: "professional" | "friendly" | "formal"}` |

**Resumo do bloco:**
> "Comunicação configurada! A LIA vai usar [canal] como canal preferido e tom [tom]. Quer definir como a triagem de candidatos funciona?"

### 4.5 Bloco 4: Triagem (3 perguntas)

| # | Pergunta da LIA | Campo | Default | Conexão na plataforma | Implementação |
|---|---|---|---|---|---|
| 13 | "Vocês filtram candidatos por pretensão salarial? Se sim, com qual tolerância? Por exemplo, até 15% acima do orçamento." | `screening_rules.salary_expectation_filter` + `salary_tolerance_percent` | null (false) | Campo de pretensão salarial na vaga | **NOVO** — Requer comparação pretensão vs. orçamento da vaga na triagem automática. Fase 2+ |
| 14 | "A experiência mínima é definida por cada vaga individualmente ou vocês têm um padrão geral da empresa?" | `screening_rules.experience_policy` | null ("per_job") | Campo de experiência na vaga | **INFORMATIVO** — Armazena a preferência, mas enforcement é per-job. Não requer lógica nova imediata |
| 15 | "Existem perguntas de triagem que valem para todas as vagas da empresa? Perguntas que todo candidato deveria responder, independente da vaga." | `screening_rules.default_screening_questions` | [] | `CompanyBankQuestions`, `ScreeningQuestion` (company-scoped), `company-screening-settings.tsx` | **EXISTENTE** — `CompanyBankQuestions` já suporta perguntas company-scoped. Necessário: auto-adicionar ao criar vaga |

**Resumo do bloco:**
> "Triagem configurada! Essas regras vão ser aplicadas em todas as vagas novas. Última parte: quer definir o nível de autonomia da LIA?"

### 4.6 Bloco 5: Autonomia da LIA (4 perguntas)

| # | Pergunta da LIA | Campo | Default | Conexão na plataforma | Implementação |
|---|---|---|---|---|---|
| 16 | "A LIA pode triar candidatos automaticamente ou prefere que ela apresente os resultados e aguarde sua confirmação?" | `automation_rules.auto_screening` | null (false) | `StageAutomationEngine`, feature flags | **PARCIAL** — `StageAutomationEngine` existe. Necessário: consultar policy e feature flag `ENABLE_AUTO_SCREENING_{company_id}` |
| 17 | "A LIA pode agendar entrevistas automaticamente com base nas regras que acabamos de definir?" | `automation_rules.auto_scheduling` | null (false) | `scheduling_service.py`, feature flags | **PARCIAL** — Serviço existe. Necessário: trigger automático pós-triagem aprovada + feature flag |
| 18 | "A LIA pode mover candidatos de etapa automaticamente quando todos os critérios são atendidos? Por exemplo, triagem completa com score bom → mover para entrevista." | `automation_rules.auto_stage_advance` | null (false) | `auto_advance_rules` no `RecruitmentStage` | **EXISTENTE** — `auto_advance_rules` é per-stage. Este toggle habilita/desabilita globalmente. Se `false`, todas as regras per-stage são ignoradas |
| 19 | "De forma geral, qual nível de autonomia quer dar à LIA? Baixo — sempre confirma com você antes de agir. Médio — confirma apenas ações de alto impacto como propostas e reprovações. Alto — age sozinha e notifica você depois." | `automation_rules.autonomy_level` | null ("low") | Feature flags, `PolicyEngine` | **NOVO** — Ver seção 5.4 para mapeamento detalhado de cada nível |

**Resumo final:**
> "Configuração completa! A LIA agora conhece as regras da sua empresa. Você pode voltar aqui a qualquer momento para ajustar. Conforme você usar a plataforma, a LIA também vai aprendendo suas preferências e sugerindo melhorias."

---

## 5. Visão de Automação Progressiva

### 5.1 Os 5 Níveis

| Nível | Nome | Descrição | O que precisa |
|---|---|---|---|
| 1 | Auto-Transition Rules | Regras configuráveis: "Quando [evento], mover para [etapa]" | `CompanyHiringPolicy` + `StageAutomationEngine` |
| 2 | Smart Suggestions | LIA monitora pipeline e sugere ações proativas no chat | Monitor contínuo + `ProactiveAlertService` |
| 3 | Batch Intelligence | LIA agrupa candidatos similares e propõe ações em lote | `CandidateContextAggregator` + clustering |
| 4 | Predictive Pipeline | ML prediz outcomes e sugere pular/acelerar etapas | `OutcomePredictor` + `PredictiveAnalytics` |
| 5 | Autonomous Pipeline | LIA opera sozinha nas etapas configuradas, recrutador só decide no final | Nível de autonomia "high" + todas as camadas |

### 5.2 O que já existe na plataforma para cada nível

| Nível | Componente existente | Status | Gap |
|---|---|---|---|
| 1 | `StageAutomationEngine`, `auto_advance_rules`, `AutomationTrigger` | Estrutura existe | Falta conectar com `CompanyHiringPolicy` |
| 2 | `ProactiveAlertService`, `AutonomousAgentService`, `IntelligenceNotifications` | Serviços existem | Falta loop de monitoramento ativo |
| 3 | `CandidateContextAggregator`, bulk actions | Parcial | Falta clustering por similaridade |
| 4 | `OutcomePredictor`, `FeatureEngineering`, `PredictiveAnalytics` | Calculam mas não acionam | Falta predição → sugestão → ação |
| 5 | Feature flags, `PolicyEngine` | Controle granular existe | Falta orquestração de piloto automático |

### 5.3 Arquitetura de Aprendizado

```
┌──────────────────────────────────────────────────────┐
│                 FONTES DE DADOS                       │
│                                                       │
│  Regras explícitas        Observação de padrões       │
│  (CompanyHiringPolicy)    (learned_patterns)          │
│         │                        │                    │
│         ▼                        ▼                    │
│  ┌─────────────────────────────────────┐              │
│  │     MOTOR DE DECISÃO DA LIA         │              │
│  │                                     │              │
│  │  Regras explícitas (peso 1.0)       │              │
│  │  + Padrões aprendidos (peso 0.7)    │              │
│  │  + Defaults genéricos (peso 0.3)    │              │
│  │                                     │              │
│  │  → Decisão com confiança calculada  │              │
│  └─────────────────────────────────────┘              │
│         │                                             │
│         ▼                                             │
│  ┌─────────────────────────────────────┐              │
│  │     AÇÃO                            │              │
│  │                                     │              │
│  │  Confiança > 0.9 + autonomia high   │              │
│  │  → Executa e notifica               │              │
│  │                                     │              │
│  │  Confiança > 0.7 + autonomia medium │              │
│  │  → Sugere e pede confirmação        │              │
│  │                                     │              │
│  │  Confiança < 0.7 OU autonomia low   │              │
│  │  → Apenas informa, recrutador age   │              │
│  └─────────────────────────────────────┘              │
│         │                                             │
│         ▼                                             │
│  ┌─────────────────────────────────────┐              │
│  │     FEEDBACK LOOP                   │              │
│  │                                     │              │
│  │  Recrutador aceitou sugestão?       │              │
│  │  → Sim: reforça padrão (+0.05)      │              │
│  │  → Não: reduz peso (-0.1)           │              │
│  │  → Alterou: aprende variação        │              │
│  └─────────────────────────────────────┘              │
└──────────────────────────────────────────────────────┘
```

### 5.4 Mapeamento Detalhado dos Níveis de Autonomia (Pergunta 19)

O campo `autonomy_level` traduz-se em comportamentos concretos via feature flags existentes:

| Nível | Valor | Triagem | Agendamento | Mover etapa | Feedback reprovação | Propostas/Ofertas |
|---|---|---|---|---|---|---|
| **Baixo** | `"low"` | LIA apresenta ranking → recrutador decide | LIA sugere horários → recrutador confirma | Nunca automático | LIA prepara texto → recrutador envia | Sempre manual |
| **Médio** | `"medium"` | Auto se `auto_screening=true` | Auto se `auto_scheduling=true` | Auto em etapas de baixo impacto (triagem→entrevista) | Auto se `auto_rejection_feedback=true` | Requer confirmação |
| **Alto** | `"high"` | Sempre automático | Sempre automático | Automático em todas as etapas exceto proposta | Sempre automático | Requer confirmação (nunca 100% automático) |

**Regra de segurança:** Propostas salariais e contratações **nunca** são 100% automáticas, independente do nível. A LIA sempre pede confirmação para ações de alto impacto financeiro.

**Mapeamento para feature flags existentes:**

```
autonomy_level = "low" →
  ENABLE_AUTO_SCREENING_{company_id} = false
  ENABLE_AUTO_SCHEDULING_{company_id} = false
  ENABLE_AUTO_STAGE_ADVANCE_{company_id} = false
  ENABLE_AUTO_REJECTION_FEEDBACK_{company_id} = false

autonomy_level = "medium" →
  Usa os toggles individuais (perguntas 16-18 + 9)
  Sem override — cada toggle mantém seu valor

autonomy_level = "high" →
  ENABLE_AUTO_SCREENING_{company_id} = true (override)
  ENABLE_AUTO_SCHEDULING_{company_id} = true (override)
  ENABLE_AUTO_STAGE_ADVANCE_{company_id} = true (override)
  ENABLE_AUTO_REJECTION_FEEDBACK_{company_id} = true (override)
  ENABLE_AUTO_OFFER_{company_id} = false (nunca auto)
```

### 5.5 Resumo de Status de Implementação

| Status | Contagem | Perguntas |
|---|---|---|
| **EXISTENTE** (lógica backend já existe) | 5 | #3, #4, #11, #15, #18 |
| **PARCIAL** (serviço existe, falta conectar com policy) | 5 | #5, #6, #7, #9, #16, #17 |
| **NOVO** (requer desenvolvimento) | 5 | #1, #2, #8, #10, #12 |
| **INFORMATIVO** (armazena preferência, sem enforcement imediato) | 2 | #14, #19 |

> **Nota:** Pergunta #19 é "informativa" no sentido de que o nível de autonomia é um **atalho** que configura os toggles individuais. A implementação real são os toggles (perguntas 16-18).

---

## 6. Prioridade de Implementação

| Fase | Escopo | Esforço | Impacto |
|---|---|---|---|
| Fase 1 | Modelo de dados `CompanyHiringPolicy` + API CRUD + tela em Configurações com chat LIA | Médio | Base para tudo |
| Fase 2 | Roteiro de 19 perguntas funcionando no chat + preenchimento do painel em tempo real | Médio | Onboarding assistido |
| Fase 3 | Agentes consultam `CompanyHiringPolicy` antes de agir (scheduling, communication, screening) | Alto | LIA personalizada |
| Fase 4 | Monitor contínuo + sugestões proativas baseadas nas regras | Alto | Automação nível 2 |
| Fase 5 | Aprendizado contínuo (`learned_patterns`) + recalibração | Alto | Automação nível 4-5 |

---

## 7. Dependências Técnicas

| Componente | Status | Ação necessária |
|---|---|---|
| Tab "Políticas de Contratação" em Configurações | Nova | Criar no frontend |
| Chat LIA no contexto de configuração | Adaptar | Reutilizar componente de chat existente com novo contexto |
| API `/api/v1/company-hiring-policy` | Nova | CRUD endpoints |
| Modelo `CompanyHiringPolicy` | Novo | Migration + model |
| Consulta de policies nos agentes | Novo | `get_company_policy()` helper |
| Integração com `RecruitmentStage.sla_hours` | Existente | Conectar campos |
| Integração com feature flags | Existente | Mapear `automation_rules` |

---

---

## 8. Plano de Implementação Completo

Ver documento detalhado: `plataforma-lia/docs/specs/plano-evolucao-lia.md`

O plano completo cobre 4 fases (~18-23 semanas) desde a fundação (modelo + settings page) até aprendizado contínuo (feedback loop + consultoria estratégica). Este documento (hiring-policies-spec.md) detalha as Fases 1 e 2; o plano de evolução cobre também as Fases 3 (proatividade) e 4 (aprendizado).

---

*Documento de especificação v1.0 — 21/02/2026*
