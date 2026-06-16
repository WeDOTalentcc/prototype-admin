# Fluxo Completo de Criação de Vagas com IA

## Visão Geral

O sistema de criação de vagas da Plataforma LIA utiliza um **modelo de detecção automática de critérios** onde a LIA (Learning Intelligence Assistant) identifica informações importantes enquanto o usuário descreve a vaga de forma natural. Este documento detalha todo o fluxo de 8 etapas, os agentes de IA envolvidos, os painéis da interface e o fluxo pós-publicação.

---

## Arquitetura Multi-Agent

### Orquestrador Principal

O **Orchestrator v2.2** é o cérebro do sistema, responsável por:
- Roteamento inteligente de intenções (IntentRouter)
- Coordenação de 9 agentes especializados
- Gestão de contexto e memória de sessão
- Delegação de tarefas entre agentes

### Agentes Envolvidos na Criação de Vagas

| Agente | Responsabilidade | Momento de Ação |
|--------|-----------------|-----------------|
| **JobIntakeAgent** | Conduz todo o wizard de 8 etapas, detecta critérios, gera perguntas WSI | Etapas 1-8 |
| **ScreeningAgent** | Avalia CVs contra rubricas da vaga, gera scores | Pós-publicação |
| **SourcingPipelineAgent** | Busca candidatos local/global, popula pipeline | Pós-publicação |
| **CommunicationAgent** | Envia notificações Teams/Bell para aprovações | Pós-publicação |
| **TaskPlannerAgent** | Decomposição de tarefas, priorização | Suporte contínuo |

---

## Fluxo de 8 Etapas

### Etapa 1: Detecção de Critérios
**Painel:** Critérios Detectados (0/9)

**Mensagem LIA:**
> "Detalhe o máximo que puder sobre a vaga para otimizar o processo de construção.
>
> Exemplo: 'Preciso de um Desenvolvedor Backend Sênior para a área de Engenharia, reportando ao Tech Lead João Silva. Deve ter experiência com Python, FastAPI e AWS. Modelo híbrido em São Paulo, CLT, faixa de 15-20k.'
>
> Campos detectáveis automaticamente:
> • Cargo e área
> • Gestor responsável
> • Competências técnicas e comportamentais
> • Senioridade e modelo de trabalho
> • Localização e tipo de contrato
> • Faixa salarial"

**Funcionamento:**
- Usuário descreve a vaga em linguagem natural
- LIA detecta automaticamente 9 tipos de critérios:
  1. Cargo (título da posição)
  2. Gestor/Área (departamento, equipe)
  3. Competências Técnicas (skills, linguagens, ferramentas)
  4. Competências Comportamentais (soft skills)
  5. Senioridade (Júnior, Pleno, Sênior, Especialista)
  6. Modelo de Trabalho (Presencial, Híbrido, Remoto)
  7. Localização (cidade, estado, país)
  8. Tipo de Contrato (CLT, PJ, Temporário)
  9. Faixa Salarial (mínimo, máximo, moeda)

**Painel Lateral:**
- Mostra progresso em tempo real (ex: 5/9 detectados)
- Indicadores de confiança (Alta, Média, Baixa)
- Cada critério detectado aparece com tag colorida

**Requisito Mínimo:** 2 critérios detectados para avançar

**Prompt de Detecção:**
```
Analise a descrição da vaga e extraia os seguintes critérios:
- cargo: título da posição
- gestor_area: departamento ou área responsável
- competencias_tecnicas: lista de skills técnicas
- competencias_comportamentais: lista de soft skills
- senioridade: nível de experiência
- modelo_trabalho: presencial/híbrido/remoto
- localizacao: cidade/estado/país
- tipo_contrato: CLT/PJ/Temporário
- faixa_salarial: {min, max, moeda}

Retorne JSON estruturado com confiança para cada campo.
```

---

### Etapa 2: Informações Básicas
**Painel:** Informações Básicas

**Mensagem LIA:**
> "Preenchi com base na sua descrição e no setup da empresa.
>
> Revise e ajuste os campos ao lado. Se precisar alterar algo, é só me dizer ou editar diretamente no painel!"

**Campos do Painel:**
- Título da Vaga
- Departamento/Área
- Gestor Responsável (dropdown com gestores da empresa)
- Localidade
- Modelo de Trabalho (Presencial/Híbrido/Remoto)
- Tipo de Contrato (CLT/PJ/Temporário)
- Nível de Senioridade
- Data de Abertura
- Prazo para Preenchimento

**Integração:**
- Dados pré-preenchidos com base na detecção da Etapa 1
- Validação em tempo real
- Sugestões baseadas em vagas anteriores similares

---

### Etapa 3: Requisitos Técnicos
**Painel:** Requisitos Técnicos

**Mensagem LIA:**
> "Agora vamos definir as competências técnicas!
>
> Detectei algumas skills com base na sua descrição. Você pode:
> • Adicionar novas linguagens, frameworks ou ferramentas
> • Ajustar o nível de proficiência (Básico, Intermediário, Avançado)
> • Marcar como obrigatório ou desejável
>
> Edite diretamente no painel ao lado."

**Campos do Painel:**
- **Linguagens de Programação** (com nível: Básico/Intermediário/Avançado)
- **Frameworks e Bibliotecas**
- **Bancos de Dados**
- **Ferramentas e Plataformas**
- **Certificações Desejadas**
- **Idiomas** (com nível de proficiência)

**Funcionalidades:**
- Autocomplete com sugestões baseadas no mercado
- Tags coloridas por categoria
- Ordenação por prioridade (arrastar e soltar)
- Indicador de skills detectadas automaticamente vs. adicionadas manualmente

---

### Etapa 4: Competências Comportamentais
**Painel:** Competências Comportamentais

**Mensagem LIA:**
> "Vamos definir as competências comportamentais!
>
> Baseado no perfil da vaga e na cultura da sua empresa, sugeri algumas competências.
>
> Para cada uma, você pode:
> • Ajustar o peso (1-5) conforme a importância
> • Editar a justificativa para a avaliação
> • Adicionar ou remover competências
>
> O peso define quanto essa competência impacta na Nota LIA do candidato."

**Sistema de Pesos (1-5):**
| Peso | Significado | Impacto no LIA Score |
|------|-------------|---------------------|
| 1 | Desejável | +5% |
| 2 | Importante | +10% |
| 3 | Muito Importante | +15% |
| 4 | Essencial | +20% |
| 5 | Crítico | +25% |

**Competências Sugeridas:**
- Comunicação Eficaz
- Resolução de Problemas
- Trabalho em Equipe
- Adaptabilidade
- Liderança
- Pensamento Analítico
- Orientação a Resultados
- Criatividade e Inovação

**Campos por Competência:**
- Nome da Competência
- Peso (slider 1-5)
- Justificativa (texto curto)

---

### Etapa 5: Salário e Benefícios
**Painel:** Salário e Benefícios

**Mensagem LIA:**
> "Ótimo progresso! Agora vamos para remuneração e benefícios.
>
> Com base nas informações previamente cadastradas pela empresa e conforme nível e área/departamento da posição, os benefícios e faixas salariais foram sugeridos.
>
> Defina:
> • Faixa salarial (mínimo e máximo)
> • Bônus anual e critérios
> • Benefícios oferecidos
>
> Esses dados ajudam a atrair candidatos qualificados."

**Campos de Remuneração:**
- Faixa Salarial (Mínimo - Máximo)
- Moeda (BRL, USD, EUR)
- Tipo (CLT, PJ, Misto)
- Bônus/Variável (%)
- PLR/PPR

**Painel de Benefícios:**
Carregados do setup da empresa com toggle para ativar/desativar:
- Vale Refeição/Alimentação
- Vale Transporte
- Plano de Saúde
- Plano Odontológico
- Seguro de Vida
- Auxílio Home Office
- Auxílio Educação
- Gympass/Wellhub
- Day Off Aniversário
- Previdência Privada

**Benefícios Customizáveis:**
- Adicionar benefício específico para a vaga
- Descrever detalhes (valor, condições)

---

### Etapa 6: Perguntas de Triagem WSI
**Painel:** Perguntas de Triagem Rápida

**Mensagem LIA:**
> "Quase lá! Agora vamos configurar as perguntas de triagem rápida.
>
> Essas perguntas serão enviadas automaticamente via WhatsApp para uma pré-qualificação dos candidatos.
>
> A triagem incluirá:
> • Perguntas padrão da empresa (setup)
> • Perguntas específicas para esta vaga
>
> Gerei 7 perguntas de triagem baseadas na **metodologia WSI** e no perfil da vaga.
>
> Frameworks científicos usados:
> • **CBI** (Competency-Based Interviewing)
> • **Dreyfus Model** (Avaliação de Expertise)
> • **Bloom's Taxonomy** (Níveis de Conhecimento)
>
> Selecione **5 perguntas** que melhor se adequam ao processo seletivo."

**Metodologia WSI (Work Sample Interview):**

O sistema gera perguntas usando três frameworks científicos:

#### 1. CBI - Competency-Based Interviewing
Perguntas baseadas em competências que exploram comportamentos passados:
- "Conte sobre uma situação em que você..."
- "Descreva um momento em que precisou..."
- "Como você lidou com..."

#### 2. Modelo Dreyfus (5 Níveis de Expertise)
| Nível | Descrição | Tipo de Pergunta |
|-------|-----------|------------------|
| 1 - Novato | Segue regras e instruções | Conhecimento básico |
| 2 - Iniciante Avançado | Reconhece padrões | Situações similares |
| 3 - Competente | Planeja e prioriza | Tomada de decisão |
| 4 - Proficiente | Visão holística | Análise complexa |
| 5 - Especialista | Intuição expert | Inovação e liderança |

#### 3. Taxonomia de Bloom (6 Níveis Cognitivos)
| Nível | Verbo | Exemplo de Pergunta |
|-------|-------|---------------------|
| Lembrar | Definir, Listar | "O que é...?" |
| Entender | Explicar, Descrever | "Por que...?" |
| Aplicar | Implementar, Usar | "Como você aplicaria...?" |
| Analisar | Comparar, Diferenciar | "Qual a diferença entre...?" |
| Avaliar | Julgar, Criticar | "O que você mudaria...?" |
| Criar | Desenvolver, Projetar | "Como você criaria...?" |

**Interface do Painel:**
- 7 perguntas geradas com preview
- Checkbox para selecionar (máximo 5)
- Botão para regenerar pergunta individual
- Indicador do framework usado (CBI/Dreyfus/Bloom)
- Tempo estimado de resposta por pergunta

**Prompt de Geração WSI:**
```
Com base no perfil da vaga, gere 7 perguntas de triagem usando:

1. CBI (Competency-Based Interviewing):
   - Perguntas situacionais baseadas em comportamentos passados
   - Estrutura STAR (Situação, Tarefa, Ação, Resultado)

2. Modelo Dreyfus:
   - Calibrar nível de acordo com senioridade da vaga
   - Júnior: níveis 1-2, Pleno: níveis 2-3, Sênior: níveis 3-4, Especialista: níveis 4-5

3. Taxonomia de Bloom:
   - Variar níveis cognitivos nas perguntas
   - Incluir pelo menos uma pergunta de cada nível superior (Analisar, Avaliar, Criar)

Retorne JSON com:
- pergunta: texto da pergunta
- framework: CBI|Dreyfus|Bloom
- nivel_dreyfus: 1-5
- nivel_bloom: lembrar|entender|aplicar|analisar|avaliar|criar
- competencia_avaliada: competência que a pergunta avalia
- tempo_estimado_segundos: tempo esperado de resposta
```

---

### Etapa 7: Configuração do Pipeline
**Painel:** Configuração do Pipeline

**Mensagem LIA:**
> "Vamos configurar o pipeline de recrutamento!
>
> Defina as etapas do processo seletivo, responsáveis e prazos estimados para cada fase.
>
> Sugestão de etapas:
> 1. Triagem Curricular (LIA)
> 2. Screening Rápido (WhatsApp)
> 3. Entrevista Técnica
> 4. Entrevista Comportamental
> 5. Proposta
>
> Você pode adicionar, remover ou reordenar as etapas conforme seu processo."

**Etapas Padrão do Pipeline:**
1. **Triagem Curricular** (Automática - LIA)
2. **Screening Rápido** (5 perguntas WSI)
3. **Entrevista Técnica**
4. **Entrevista Comportamental**
5. **Case/Desafio Técnico**
6. **Entrevista Final**
7. **Proposta**
8. **Contratação**

**Configurações por Etapa:**
- Nome da Etapa
- Responsável (Gestor/Recrutador/LIA)
- SLA (dias para completar)
- Tipo de Avaliação (Automática/Manual/Híbrida)
- Critérios de Aprovação

**Funcionalidades:**
- Arrastar para reordenar etapas
- Adicionar/remover etapas
- Templates de pipeline por tipo de vaga

---

### Etapa 7.5: Configuração de Governança (GovernanceRules)
**Painel:** Regras de Autonomia da LIA

**Mensagem LIA:**
> "Agora vamos definir até onde posso agir automaticamente nesta vaga.
>
> Configure o nível de autonomia que você quer me dar. Para ações mais sensíveis, 
> posso apenas sugerir e você confirma."

**Campos do Painel:**

| Configuração | Descrição | Padrão |
|--------------|-----------|--------|
| **auto_schedule_interviews** | Agendar entrevistas sem aprovação | ❌ Não |
| **auto_send_negative_feedback** | Enviar rejeição sem aprovação | ❌ Não |
| **requires_validation_before_shortlist** | Aprovar shortlist antes de avançar | ✅ Sim |
| **max_auto_sourcing_per_day** | Limite de sourcing automático/dia | 50 |
| **allow_ai_first_contact** | LIA pode fazer primeiro contato | ❌ Não |
| **saturation_threshold** | Pausar triagem após N aprovados | 20 |

**Modelo de Dados:**
```python
class GovernanceRules:
    auto_schedule_interviews: bool = False
    auto_send_negative_feedback: bool = False
    requires_validation_before_shortlist: bool = True
    max_auto_sourcing_per_day: int = 50
    allow_ai_first_contact: bool = False
    saturation_threshold: int = 20
```

**Explicação para o Recrutador:**
- **Autonomia Total**: LIA age automaticamente e notifica depois
- **Supervisão**: LIA sugere e espera aprovação
- **Híbrido**: Ações menores automáticas, decisões críticas precisam aprovação

**Funcionalidades:**
- Presets de autonomia (Conservador, Moderado, Agressivo)
- Alerta visual sobre implicações de cada configuração
- Histórico de ações automáticas por vaga

---

### Etapa 8: Revisão e Publicação
**Painel:** Resumo da Vaga

**Mensagem LIA:**
> "Excelente! Aqui está o resumo completo da vaga.
>
> O resumo inclui automaticamente:
> • Apresentação da empresa (sobre, missão)
> • EVP (Employee Value Proposition)
> • Valores e cultura da organização
> • Desafios da posição
>
> Revise todos os detalhes antes de publicar. Você pode clicar em qualquer seção para voltar e editar.
>
> Quando estiver tudo certo, clique em **Publicar Vaga** para ativar o recrutamento!"

**Cards de Resumo:**

1. **Card Informações Básicas**
   - Título, Departamento, Localidade
   - Modelo de Trabalho, Contrato, Senioridade

2. **Card Requisitos Técnicos**
   - Skills com níveis
   - Certificações, Idiomas

3. **Card Competências Comportamentais**
   - Lista com pesos visuais (barras)

4. **Card Remuneração e Benefícios**
   - Faixa salarial formatada
   - Lista de benefícios selecionados

5. **Card Perguntas de Triagem**
   - 5 perguntas selecionadas em preview

6. **Card Pipeline**
   - Visualização em fluxo das etapas

**Ações Disponíveis:**
- **Salvar Rascunho**: Salva sem publicar
- **Visualizar Preview**: Como aparecerá para candidatos
- **Publicar Vaga**: Ativa a vaga e inicia sourcing

---

## Fluxo Pós-Publicação

### Diagrama de Fluxo

```
┌─────────────────────────────────────────────────────────────────┐
│                    PUBLICAÇÃO DA VAGA                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. BUSCA LOCAL AUTOMÁTICA                                      │
│  ─────────────────────────                                      │
│  • SourcingPipelineService.run_post_publish_sourcing()          │
│  • Busca na base de talentos interna                            │
│  • Matching por skills, localização, senioridade                │
│  • Sem consumo de créditos                                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. RESULTADOS DA BUSCA LOCAL                                   │
│  ───────────────────────────                                    │
│  • Modal com candidatos encontrados                             │
│  • Cards com LIA Score, match %, skills                         │
│  • Quick actions: Ver Perfil, Adicionar ao Pipeline             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. SUGESTÃO DE BUSCA GLOBAL                                    │
│  ───────────────────────────                                    │
│  LIA: "Encontrei X candidatos na sua base. Quer expandir a     │
│        busca para candidatos externos? (consome Y créditos)"    │
│                                                                 │
│  [Sim, expandir busca]     [Não, continuar com estes]          │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────┐
│  4A. BUSCA GLOBAL       │     │  4B. PULAR BUSCA GLOBAL │
│  ───────────────────    │     │  ─────────────────────  │
│  • Pearch AI (800M+)    │     │  • Usar apenas base     │
│  • Deduz créditos       │     │    local                │
│  • confirm_global_search│     │  • Ir para pipeline     │
└─────────────────────────┘     └─────────────────────────┘
              │                               │
              └───────────────┬───────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. POPULAÇÃO DO PIPELINE                                       │
│  ─────────────────────────                                      │
│  • Candidatos adicionados automaticamente                       │
│  • Status inicial: "Novo" ou "Triagem"                         │
│  • LIA Score calculado para cada um                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  6. NOTIFICAÇÕES                                                │
│  ──────────────                                                 │
│  • Bell: "LIA adicionou X candidatos ao pipeline"               │
│  • Teams: Card com ação "Aprovar para triagem"                  │
│  • Email: Resumo diário (opcional)                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  7. TRIAGEM AUTOMÁTICA (ScreeningAgent)                         │
│  ──────────────────────────────────────                         │
│  • CV vs Rubricas da Vaga                                       │
│  • LIA Score atualizado                                         │
│  • Red Flags detectados                                         │
│  • Ranking de candidatos                                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  8. SATURAÇÃO INTELIGENTE (Smart Saturation)                    │
│  ──────────────────────────────────────────                     │
│  CONDIÇÃO: approved_count >= saturation_threshold (default: 20) │
│                                                                 │
│  SE saturado:                                                   │
│  • Pausar triagem automática                                    │
│  • Notificar recrutador                                         │
│  • Sugerir: "Agendar entrevistas" ou "Desbloquear pipeline"    │
│                                                                 │
│  SE não saturado:                                               │
│  • Continuar triagem normalmente                                │
│  • Informar vagas restantes até saturação                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  9. CALIBRAÇÃO CONTÍNUA (Calibration Loop)                      │
│  ─────────────────────────────────────────                      │
│  • Captura feedback implícito (ações do recrutador)             │
│  • Captura feedback explícito (thumbs up/down)                  │
│  • Ajusta pesos e thresholds para próximas triagens             │
│  • Gera sugestões de recalibração para aprovação                │
└─────────────────────────────────────────────────────────────────┘
```

### APIs do Fluxo Pós-Publicação

#### POST /api/v1/job-vacancies/{job_id}/publish

Publica a vaga e inicia sourcing automático.

**Request:**
```json
{
  "trigger_sourcing": true
}
```

**Response:**
```json
{
  "success": true,
  "job_id": "uuid",
  "status": "Ativa",
  "message": "Vaga 'Desenvolvedor Senior' publicada com sucesso!",
  "sourcing_result": {
    "local_candidates_found": 15,
    "local_candidates_added": 12,
    "global_search_available": true,
    "credits_required": 20,
    "awaiting_global_confirmation": true
  }
}
```

#### POST /api/v1/job-vacancies/{job_id}/confirm-global-search

Confirma busca global e deduz créditos.

**Request:**
```json
{
  "credits_to_use": 20
}
```

**Response:**
```json
{
  "success": true,
  "candidates_found": 45,
  "candidates_added": 38,
  "credits_used": 20,
  "message": "Busca global concluída! 38 candidatos adicionados ao pipeline."
}
```

#### GET /api/v1/job-vacancies/{job_id}/sourcing-status

Retorna status atual do sourcing.

**Response:**
```json
{
  "job_id": "uuid",
  "total_candidates": 50,
  "qualified_candidates": 35,
  "pipeline_status": "active",
  "recommended_action": "Revisar candidatos qualificados"
}
```

---

### APIs de Saturação e Governança

#### GET /api/v1/job-vacancies/{job_id}/saturation-status

Retorna status de saturação do pipeline.

**Response:**
```json
{
  "job_id": "uuid",
  "approved_count": 18,
  "saturation_threshold": 20,
  "is_saturated": false,
  "slots_remaining": 2,
  "recommendation": "continue_screening"
}
```

#### POST /api/v1/job-vacancies/{job_id}/unlock-pipeline

Desbloqueia pipeline saturado (override manual).

**Response:**
```json
{
  "success": true,
  "message": "Pipeline desbloqueado. Triagem retomada.",
  "new_threshold": 30
}
```

#### PUT /api/v1/job-vacancies/{job_id}/governance-rules

Atualiza regras de governança da vaga.

**Request:**
```json
{
  "auto_schedule_interviews": false,
  "auto_send_negative_feedback": false,
  "saturation_threshold": 25,
  "allow_ai_first_contact": true
}
```

---

### APIs de Calibração

#### POST /api/v1/calibration/feedback

Registra feedback explícito do recrutador.

**Request:**
```json
{
  "candidate_id": "uuid",
  "job_id": "uuid",
  "agrees_with_lia": false,
  "lia_score": 85,
  "feedback_reason": "Candidato não demonstrou experiência prática"
}
```

#### GET /api/v1/calibration/divergences

Retorna divergências entre LIA e recrutador (últimos 30 dias).

**Response:**
```json
{
  "divergences": [
    {
      "candidate_id": "uuid",
      "lia_score": 82,
      "recruiter_action": "reject",
      "score_delta": -5,
      "reason": "Experiência não compatível"
    }
  ],
  "total_divergences": 12,
  "agreement_rate": 78.5
}
```

---

## Notificações do Sistema

### Tipos de Notificação

| Evento | Canal | Mensagem |
|--------|-------|----------|
| Vaga Publicada | Bell, Teams | "Vaga [Título] publicada com sucesso" |
| Candidatos Encontrados | Bell, Teams | "LIA adicionou X candidatos ao pipeline de [Vaga]" |
| Triagem Concluída | Bell, Teams | "Triagem automática concluída. Y candidatos qualificados" |
| Aprovação Pendente | Teams | "Aprove para iniciar triagem de [Vaga]" |
| Candidato Destacado | Bell | "Candidato com 95% de match para [Vaga]" |

### Formato Notificação Teams

```
📋 **Nova Atividade - Vaga: [Título]**

LIA adicionou **X candidatos** ao pipeline.

**Destaques:**
• Y candidatos com match > 80%
• Z candidatos com experiência relevante

[Ver Pipeline] [Aprovar Triagem]
```

---

## Painéis da Interface

### Layout Geral do Wizard

```
┌──────────────────────────────────────────────────────────────────────┐
│  Header: Criar Nova Vaga                                    [X]      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────┐  ┌────────────────────────────┐ │
│  │                                 │  │   PAINEL LATERAL           │ │
│  │   ÁREA DO CHAT LIA              │  │   ────────────────         │ │
│  │                                 │  │                            │ │
│  │   [Avatar LIA]                  │  │   Etapa 1 de 8            │ │
│  │   Olá! Vou te ajudar...        │  │   ████████░░ 12%          │ │
│  │                                 │  │                            │ │
│  │   [Input do usuário]            │  │   Critérios Detectados:    │ │
│  │   _________________________     │  │   ✓ Cargo                  │ │
│  │                                 │  │   ✓ Área                   │ │
│  │                                 │  │   ○ Competências           │ │
│  │                                 │  │   ○ Senioridade            │ │
│  │                                 │  │   ...                      │ │
│  │                                 │  │                            │ │
│  │                                 │  │   [Campos Editáveis]       │ │
│  │                                 │  │                            │ │
│  └─────────────────────────────────┘  └────────────────────────────┘ │
│                                                                      │
│  [← Voltar]                                            [Avançar →]   │
└──────────────────────────────────────────────────────────────────────┘
```

### Painéis por Etapa

| Etapa | Painel Esquerdo | Painel Direito |
|-------|-----------------|----------------|
| 1 | Chat com LIA | Critérios Detectados (0/9) |
| 2 | Chat com LIA | Formulário: Info Básicas |
| 3 | Chat com LIA | Lista: Skills Técnicas |
| 4 | Chat com LIA | Cards: Competências + Pesos |
| 5 | Chat com LIA | Formulário: Salário + Benefícios |
| 6 | Chat com LIA | Cards: Perguntas WSI (selecionar 5) |
| 7 | Chat com LIA | Fluxo: Etapas do Pipeline |
| 7.5 | Chat com LIA | Formulário: Regras de Autonomia |
| 8 | Cards de Resumo | Ações: Salvar/Publicar |

---

## Integração com Outros Sistemas

### Pearch AI (Busca Global)
- 800M+ perfis profissionais
- Busca por skills, experiência, localização
- Enriquecimento de dados de contato
- Consumo de créditos por busca

### Microsoft Teams
- Notificações via webhook
- Cards interativos com ações
- Integração com Calendar para agendamentos

### ATSs Integrados
- Gupy
- Pandapé
- StackOne (40+ sistemas)
- Sincronização bidirecional de candidatos

---

## Métricas e Analytics

### KPIs do Wizard
- Taxa de conclusão por etapa
- Tempo médio por etapa
- Critérios mais detectados automaticamente
- Taxa de uso de busca global

### KPIs Pós-Publicação
- Candidatos encontrados (local vs global)
- Taxa de qualificação automática
- Tempo até primeiro candidato qualificado
- Custo por candidato (créditos)

---

## Considerações de Segurança

### Multi-Tenancy
- Todas as operações filtradas por `company_id`
- Isolamento completo entre empresas
- Tokens JWT com claims de empresa

### LGPD
- Consentimento para processamento de dados
- Direito ao esquecimento implementado
- Logs de auditoria para todas as ações

### Dados Sensíveis
- Faixas salariais com controle de visibilidade
- Vagas confidenciais com acesso restrito
- Mascaramento de empresa para publicação anônima

---

## Glossário

| Termo | Definição |
|-------|-----------|
| **LIA** | Learning Intelligence Assistant - IA conversacional do sistema |
| **WSI** | Work Sample Interview - Metodologia de entrevista baseada em amostras de trabalho |
| **CBI** | Competency-Based Interviewing - Entrevista baseada em competências |
| **LIA Score** | Pontuação calculada pela IA indicando adequação do candidato |
| **Rubrica** | Conjunto de critérios usados para avaliar candidatos |
| **Pipeline** | Sequência de etapas do processo seletivo |
| **Sourcing** | Processo de busca e identificação de candidatos |
| **Pearch** | Serviço de busca global de candidatos (800M+ perfis) |

---

*Documento atualizado em Janeiro 2026 - Plataforma LIA v2.3*
*Adicionado: Etapa 7.5 (GovernanceRules), Saturação Inteligente, Calibração Contínua, APIs de Governança*
