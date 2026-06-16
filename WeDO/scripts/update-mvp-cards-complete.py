#!/usr/bin/env python3
"""
Script completo para atualizar o documento lia-mvp-cards-jira.md
Baseado no diagnóstico de comparação entre implementação e documentação.
"""

import re
import os
from datetime import datetime

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

# Cards que precisam ter status atualizado para "✅ Pronto"
CARDS_TO_UPDATE_STATUS = {
    # Microsoft Graph e Agendamento
    "AGE-001": "✅ Implementado",
    "AGE-004": "✅ Pronto", 
    "INT-MSG-002": "✅ Pronto",
    "INT-MSG-003": "✅ Pronto",
    "INT-MSG-004": "✅ Pronto",
    "INT-MSG-006": "✅ Pronto",
    
    # Templates
    "TPL-001": "✅ Pronto",
    "TPL-002": "✅ Pronto",
    "TPL-005": "✅ Pronto",
    "TPL-006": "✅ Pronto",
    "TPL-007": "✅ Pronto",
    
    # WSI
    "WSI-001": "✅ Pronto",
    "WSI-002": "✅ Pronto",
    "SCO-001": "✅ Pronto",
    "SCO-002": "✅ Pronto",
    "SCO-003": "✅ Pronto",
    
    # Notificações
    "NOT-001": "✅ Pronto",
    "NOT-002": "✅ Pronto",
    "NOT-006": "✅ Pronto",
    
    # Gates e Bulk
    "GAT-006": "✅ Pronto",
    "TAB-003": "✅ Pronto",
    "TAB-005": "✅ Pronto",
    
    # Vagas e Wizard
    "VAG-005": "✅ Pronto",
    "WIZ-004": "✅ Pronto",
}

# Cards obsoletos a marcar
CARDS_TO_MARK_OBSOLETE = [
    "KAN-005",  # Ícones de Ação Rápida - removidos
]

# Cards INT-MSG a consolidar (serão marcados como referência ao AGE)
CARDS_TO_CONSOLIDATE = {
    "INT-MSG-001": "Consolidado em AGE-001",
    "INT-MSG-005": "Pós-MVP",
    "INT-MSG-007": "Pós-MVP",
}

def update_card_status(content, card_id, new_status):
    """Atualiza o status de um card específico"""
    # Pattern para encontrar o card e seu status
    pattern = rf'(### CARD {card_id}:.*?\n```yaml\n[\s\S]*?Status:\s*)([^\n]+)'
    
    def replace_status(match):
        return match.group(1) + new_status
    
    updated = re.sub(pattern, replace_status, content)
    return updated

def update_index_status(content, card_id, new_status):
    """Atualiza o status no índice de cards"""
    # Pattern para linha do índice: | CARD-ID | Título | Tipo | Status |
    pattern = rf'(\| {card_id} \|[^|]+\|[^|]+\|)\s*[^|]+\s*\|'
    replacement = rf'\1 {new_status} |'
    return re.sub(pattern, replacement, content)

def add_new_cards_section(content):
    """Adiciona seção de novos cards ao final do documento"""
    
    new_cards = '''

---

## ÉPICO 12: JOB DESCRIPTION E WIZARD AVANÇADO

> **Novos cards** identificados na análise de implementação (Janeiro 2026)

---

### CARD JD-001: Preview de Job Description com Sugestões LIA

```yaml
Titulo: [FRONTEND] Preview de JD com Sugestões LIA
Tipo: Frontend
Sprint: 2
Pontos: 5
Prioridade: Alta
Epic: EPIC-WIZARD
Status: ✅ Pronto
Dependencias: WIZ-004

Descricao: |
  Componente de preview de Job Description (v1) que exibe o rascunho
  da vaga com indicadores visuais de sugestões LIA (💡) e alertas (⚠️).
  Usado para validação antes da publicação.

Historia de Usuario: |
  Como recrutador, eu quero visualizar um preview da descrição da vaga
  com as sugestões da LIA destacadas para revisar antes de publicar.

Regras de Negocio:
  1. Exibir todas as seções da JD em formato preview
  2. Destacar sugestões LIA com ícone 💡
  3. Mostrar alertas de campos incompletos com ⚠️
  4. Indicador de completude no topo
  5. NÃO incluir seção "Processo Seletivo" (apenas na versão final)

Requisitos Tecnicos:
  Frontend:
    - JobDescriptionPreview.tsx component
    - Integração com JobDraft state
    - Renderização de seções condicionais
  Backend:
    - JDTemplateService.generate_preview()
  Dados:
    - JobDescriptionPreview schema

Integracoes Externas:
  Nenhuma

Design & Componentes:
  Componentes:
    - JobDescriptionPreview - container principal
    - SuggestionBadge - indicador de sugestão
    - AlertBadge - indicador de alerta
    - CompletenessIndicator - barra de progresso
  Design Tokens:
    Suggestion: --wedo-cyan (💡)
    Alert: --electric-yellow (⚠️)
    Complete: --wedo-green
  Acessibilidade:
    - ARIA-labels em badges
    - Contraste adequado para indicadores
    - Screen reader friendly

Comportamento de UI:
  Seções Exibidas:
    - Sobre a Empresa
    - A Vaga
    - O Que Você Vai Fazer
    - O Que Buscamos
    - Requisitos Obrigatórios
    - Diferenciais
    - Por Que Trabalhar Conosco
    - Remuneração
    - Nossos Valores

Referencias de Design:
  Figma: "[A ser preenchido pelo time de Design]"
  Storybook:
    URL: "[A ser preenchido]"
    Componentes relacionados:
      - JobDescriptionPreview
      - SuggestionBadge

DoD:
  - [x] Preview renderiza corretamente
  - [x] Sugestões destacadas
  - [x] Alertas visíveis
  - [x] Completude calculada

Criterios de Aceitacao:
  - [x] Todas as seções exibidas
  - [x] Sugestões com ícone 💡
  - [x] Alertas com ícone ⚠️
  - [x] Barra de completude funcional
```

---

### CARD JD-002: Job Description Final para Publicação

```yaml
Titulo: [FRONTEND] JD Completo para Publicação
Tipo: Frontend
Sprint: 2
Pontos: 5
Prioridade: Alta
Epic: EPIC-WIZARD
Status: ✅ Pronto
Dependencias: JD-001

Descricao: |
  Componente de Job Description final (v2) com todas as informações
  consolidadas, incluindo Processo Seletivo e link de aplicação.
  Versão para publicação em job boards.

Historia de Usuario: |
  Como recrutador, eu quero gerar a versão final da descrição da vaga
  para publicar em job boards e redes sociais.

Regras de Negocio:
  1. Incluir TODAS as seções do preview
  2. Adicionar seção "Processo Seletivo" com timeline
  3. Incluir "Apply At" link
  4. Seção de Diversidade e Inclusão
  5. Formato otimizado para copy/paste

Requisitos Tecnicos:
  Frontend:
    - JobDescriptionFinal.tsx component
    - Timeline de processo seletivo
    - Ações de publicação
  Backend:
    - JDTemplateService.generate_final()
  Dados:
    - JobDescriptionFinal schema
    - InterviewStage list

Integracoes Externas:
  Job Boards:
    - LinkedIn Jobs
    - Indeed

Design & Componentes:
  Componentes:
    - JobDescriptionFinal - container principal
    - InterviewTimeline - processo seletivo visual
    - PublishActions - botões de ação
  Design Tokens:
    Primary: --wedo-cyan
    Timeline: steps visuais
  Acessibilidade:
    - Timeline com ARIA-labels
    - Links acessíveis

Comportamento de UI:
  Seções Adicionais (v2):
    - Processo Seletivo (timeline)
    - Diversidade e Inclusão
    - Link de Candidatura

  Ações:
    - Copiar para clipboard
    - Publicar no LinkedIn
    - Publicar no Indeed
    - Download PDF

Referencias de Design:
  Figma: "[A ser preenchido pelo time de Design]"

DoD:
  - [x] JD final completo
  - [x] Timeline de processo seletivo
  - [x] Ações de publicação
  - [x] Formato exportável

Criterios de Aceitacao:
  - [x] Processo Seletivo visível
  - [x] Link de candidatura funcional
  - [x] Copy to clipboard funciona
  - [x] Formato adequado para job boards
```

---

### CARD WIZ-009: Interação com Sugestões LIA via Chat

```yaml
Titulo: [BACKEND] Sistema de Interação com Sugestões
Tipo: Backend
Sprint: 2
Pontos: 8
Prioridade: Alta
Epic: EPIC-WIZARD
Status: ✅ Pronto
Dependencias: WIZ-002

Descricao: |
  Serviço que permite recrutadores interagir com sugestões da LIA
  via linguagem natural no chat. Suporta aceitar, rejeitar, substituir,
  ajustar nível e pedir esclarecimentos.

Historia de Usuario: |
  Como recrutador, eu quero responder às sugestões da LIA usando
  linguagem natural para aceitar, rejeitar ou modificar sugestões.

Regras de Negocio:
  1. Detectar intenção do usuário via regex
  2. Suportar múltiplas palavras em skills
  3. Gerar confirmações em português
  4. Atualizar estado do JobDraft

Requisitos Tecnicos:
  Backend:
    - SuggestionInteractionService
    - Regex-based intent detection
    - Multi-word skill support
  Schemas:
    - SuggestionInteractionType enum
    - SuggestionInteractionRequest
    - SuggestionInteractionResponse

Integracoes Externas:
  Nenhuma

Design & Componentes:
  N/A - Backend only

Comportamento de API:
  Comandos Suportados:
    Aceitar:
      - "pode adicionar Docker"
      - "aceito Machine Learning"
    Rejeitar:
      - "não preciso de Kubernetes"
      - "remova SQL"
    Substituir:
      - "troque Docker por Podman"
      - "prefiro Vue ao invés de React"
    Ajustar nível:
      - "Docker como diferencial"
      - "Python é obrigatório"
    Esclarecer:
      - "por que você sugeriu Machine Learning?"

DoD:
  - [x] Intent detection funciona
  - [x] Multi-word skills suportados
  - [x] Confirmações em português
  - [x] Estado atualizado

Criterios de Aceitacao:
  - [x] 5 tipos de interação suportados
  - [x] Regex patterns funcionam
  - [x] Respostas contextuais
```

---

### CARD WIZ-010: Análise de Compensação de Mercado

```yaml
Titulo: [BACKEND] Serviço de Análise de Compensação
Tipo: Backend
Sprint: 2
Pontos: 5
Prioridade: Media
Epic: EPIC-WIZARD
Status: ✅ Pronto
Dependencias: WIZ-003

Descricao: |
  Serviço que analisa dados de mercado para sugerir faixas salariais
  adequadas com base em cargo, senioridade, localização e stack.

Historia de Usuario: |
  Como recrutador, eu quero receber sugestões de faixa salarial
  baseadas em dados de mercado para criar vagas competitivas.

Regras de Negocio:
  1. Considerar cargo e senioridade
  2. Ajustar por localização (capital vs interior)
  3. Considerar stack tecnológico
  4. Fornecer range (min-max)
  5. Indicar percentil de mercado

Requisitos Tecnicos:
  Backend:
    - CompensationAnalysisService
    - Market data integration
    - Salary estimation algorithms

Integracoes Externas:
  Dados de Mercado:
    - Base interna de salários
    - (Futuro: Glassdoor, Levels.fyi)

DoD:
  - [x] Estimativa de salário funciona
  - [x] Ajustes por localização
  - [x] Range min-max calculado

Criterios de Aceitacao:
  - [x] Sugestões realistas
  - [x] Considera senioridade
  - [x] Indica percentil
```

---

### CARD WIZ-011: Insights de Mercado para Vagas

```yaml
Titulo: [BACKEND] Serviço de Insights de Mercado
Tipo: Backend
Sprint: 2
Pontos: 8
Prioridade: Alta
Epic: EPIC-WIZARD
Status: ✅ Pronto
Dependencias: WIZ-003

Descricao: |
  Serviço que fornece insights data-driven sobre o mercado de trabalho
  para auxiliar na criação de vagas, incluindo time-to-fill prediction,
  success profile insights e tendências de skills.

Historia de Usuario: |
  Como recrutador, eu quero receber insights sobre o mercado para
  tomar decisões informadas na criação de vagas.

Regras de Negocio:
  1. Predição de time-to-fill baseada em histórico
  2. Sugestões de skills em alta demanda
  3. Alertas de requisitos muito restritivos
  4. Comparação com vagas similares

Requisitos Tecnicos:
  Backend:
    - JobInsightsService
    - Pattern detection
    - Historical data analysis

DoD:
  - [x] Insights gerados
  - [x] Predições funcionam
  - [x] Alertas de requisitos

Criterios de Aceitacao:
  - [x] Time-to-fill estimado
  - [x] Skills sugeridos
  - [x] Alertas contextuais
```

---

## ÉPICO 13: CONFIGURAÇÕES AVANÇADAS

> **Cards de configuração** identificados na análise (Janeiro 2026)

---

### CARD CFG-001: LIA Field Toggles

```yaml
Titulo: [FRONTEND] Configurar Campos Consumidos por LIA
Tipo: Frontend
Sprint: 3
Pontos: 5
Prioridade: Media
Epic: EPIC-CONFIG
Status: ✅ Pronto

Descricao: |
  Sistema de toggles que permite recrutadores configurar quais campos
  de dados da empresa os agentes LIA podem consumir para gerar
  conteúdo e sugestões.

Historia de Usuario: |
  Como admin, eu quero controlar quais dados da empresa a LIA pode
  usar para garantir que informações sensíveis não sejam incluídas
  automaticamente nas comunicações.

Regras de Negocio:
  1. Toggle on/off por campo
  2. Agrupamento por categoria
  3. Preview do impacto
  4. Salvamento automático

Requisitos Tecnicos:
  Frontend:
    - LiaFieldToggle.tsx component
    - Field grouping logic
    - Persistence via API

Design & Componentes:
  Componentes:
    - LiaFieldToggle
    - FieldGroup
    - ImpactPreview
  Design Tokens:
    Toggle On: --wedo-cyan
    Toggle Off: --gray-300

DoD:
  - [x] Toggles funcionam
  - [x] Salvamento persiste
  - [x] Preview funciona

Criterios de Aceitacao:
  - [x] Campos agrupados
  - [x] Toggle salva automaticamente
  - [x] LIA respeita configuração
```

---

### CARD CFG-002: Verificação de Completude de Configuração

```yaml
Titulo: [BACKEND] Serviço de Completude de Configuração
Tipo: Backend
Sprint: 3
Pontos: 5
Prioridade: Media
Epic: EPIC-CONFIG
Status: ✅ Pronto

Descricao: |
  Serviço que verifica a completude das configurações da empresa
  e fornece sugestões híbridas para campos não preenchidos.

Historia de Usuario: |
  Como admin, eu quero ver quais configurações estão incompletas
  e receber sugestões para preenchê-las.

Requisitos Tecnicos:
  Backend:
    - ConfigCompletenessService
    - Hybrid suggestion generation
    - Final review panel data

DoD:
  - [x] Verificação funciona
  - [x] Sugestões geradas
  - [x] Percentual calculado

Criterios de Aceitacao:
  - [x] Campos incompletos listados
  - [x] Sugestões úteis
  - [x] Barra de progresso
```

---

### CARD CFG-003: Configuração de Jornada de Recrutamento

```yaml
Titulo: [FRONTEND] Editor de Jornada de Recrutamento
Tipo: Frontend
Sprint: 3
Pontos: 8
Prioridade: Alta
Epic: EPIC-CONFIG
Status: ✅ Pronto

Descricao: |
  Interface para configurar as etapas da jornada de recrutamento,
  incluindo stages do pipeline, automações e transições.

Historia de Usuario: |
  Como admin, eu quero configurar as etapas do meu processo seletivo
  para refletir o fluxo real da minha empresa.

Requisitos Tecnicos:
  Frontend:
    - RecruitmentJourneyConfig.tsx
    - Stage editor
    - Automation toggles

Design & Componentes:
  Componentes:
    - StageList
    - StageEditor
    - AutomationConfig
    - TransitionRules

DoD:
  - [x] Stages editáveis
  - [x] Ordem ajustável
  - [x] Automações configuráveis

Criterios de Aceitacao:
  - [x] CRUD de stages funciona
  - [x] Drag-and-drop para reordenar
  - [x] Automações salvas
```

---

### CARD CFG-004: Hub de Comunicação

```yaml
Titulo: [FRONTEND] Hub de Configuração de Comunicação
Tipo: Frontend
Sprint: 3
Pontos: 13
Prioridade: Alta
Epic: EPIC-CONFIG
Status: ✅ Pronto

Descricao: |
  Hub centralizado para configurar todos os aspectos de comunicação:
  templates de email, WhatsApp, notificações, assinaturas e canais.

Historia de Usuario: |
  Como admin, eu quero configurar todos os templates e canais de
  comunicação em um único lugar organizado.

Requisitos Tecnicos:
  Frontend:
    - CommunicationHub.tsx (85k linhas)
    - Template management
    - Channel configuration
    - Signature editor

Design & Componentes:
  Layout:
    - Tabs por categoria
    - Lista de templates
    - Editor rich text
    - Preview panel

DoD:
  - [x] Hub completo
  - [x] Templates editáveis
  - [x] Canais configuráveis

Criterios de Aceitacao:
  - [x] CRUD de templates
  - [x] Preview funciona
  - [x] Variáveis dinâmicas
```

---

### CARD CFG-005: Dados da Empresa para LIA

```yaml
Titulo: [FRONTEND] Seção de Dados da Empresa
Tipo: Frontend
Sprint: 3
Pontos: 8
Prioridade: Media
Epic: EPIC-CONFIG
Status: ✅ Pronto

Descricao: |
  Seção para gerenciar os dados da empresa que são consumidos
  pela LIA para gerar conteúdo contextualizado.

Historia de Usuario: |
  Como admin, eu quero cadastrar informações da empresa para
  que a LIA use esses dados nas comunicações automáticas.

Requisitos Tecnicos:
  Frontend:
    - CompanyDataSection.tsx
    - CompanyDataCard.tsx
    - Form validation

DoD:
  - [x] Dados editáveis
  - [x] Validação funciona
  - [x] Salvamento persiste

Criterios de Aceitacao:
  - [x] Campos de empresa
  - [x] Valores e cultura
  - [x] Benefícios
```

---

### CARD IMP-001: Importação Inteligente de Dados

```yaml
Titulo: [FRONTEND] Smart Import Zone
Tipo: Frontend
Sprint: 4
Pontos: 8
Prioridade: Media
Epic: EPIC-CONFIG
Status: ✅ Pronto

Descricao: |
  Zona de importação inteligente que detecta automaticamente o tipo
  de arquivo e extrai dados estruturados para preenchimento de campos.

Historia de Usuario: |
  Como recrutador, eu quero importar dados de arquivos (CSV, Excel, PDF)
  e ter os campos preenchidos automaticamente.

Requisitos Tecnicos:
  Frontend:
    - SmartImportZone.tsx
    - File type detection
    - Data extraction preview

DoD:
  - [x] Upload funciona
  - [x] Detecção de tipo
  - [x] Extração de dados

Criterios de Aceitacao:
  - [x] CSV/Excel suportados
  - [x] Preview antes de importar
  - [x] Mapeamento de campos
```

---

## ÉPICO 15: AGENTES ESPECIALIZADOS

> **Cards de agentes IA** identificados na análise (Janeiro 2026)

---

### CARD AGT-001: Agente Avaliador WSI

```yaml
Titulo: [AI] Agente Avaliador WSI
Tipo: AI
Sprint: 4
Pontos: 13
Prioridade: Alta
Epic: EPIC-AGENTS
Status: ✅ Pronto

Descricao: |
  Agente especializado em avaliação WSI que analisa respostas de
  candidatos e calcula scores usando metodologia Bloom/Dreyfus.

Historia de Usuario: |
  Como sistema, eu quero um agente que avalie respostas de
  candidatos de forma consistente e determinística.

Requisitos Tecnicos:
  Backend:
    - avaliador_wsi_agent.py
    - Integration with wsi_deterministic_scorer
    - Bloom/Dreyfus level detection

DoD:
  - [x] Avaliação funciona
  - [x] Scores determinísticos
  - [x] Níveis detectados

Criterios de Aceitacao:
  - [x] Bloom levels corretos
  - [x] Dreyfus levels corretos
  - [x] Score final calculado
```

---

### CARD AGT-002: Agente de Triagem Curricular

```yaml
Titulo: [AI] Agente de Triagem Curricular
Tipo: AI
Sprint: 4
Pontos: 13
Prioridade: Alta
Epic: EPIC-AGENTS
Status: ✅ Pronto

Descricao: |
  Agente que analisa currículos e realiza triagem automatizada
  comparando com requisitos da vaga.

Historia de Usuario: |
  Como sistema, eu quero um agente que analise currículos
  e classifique candidatos por aderência à vaga.

Requisitos Tecnicos:
  Backend:
    - triagem_curricular_agent.py
    - CV parsing integration
    - Requirement matching

DoD:
  - [x] Triagem funciona
  - [x] Matching calculado
  - [x] Parecer gerado

Criterios de Aceitacao:
  - [x] CV analisado
  - [x] Score de aderência
  - [x] Justificativa textual
```

---

### CARD AGT-003: Agente Inteligente de Agendamento

```yaml
Titulo: [AI] Agente de Agendamento Inteligente
Tipo: AI
Sprint: 4
Pontos: 13
Prioridade: Alta
Epic: EPIC-AGENTS
Status: ✅ Pronto
Dependencias: AGE-001

Descricao: |
  Agente que gerencia agendamento de entrevistas de forma inteligente,
  integrando com Microsoft Graph para criar eventos Teams.

Historia de Usuario: |
  Como sistema, eu quero um agente que agende entrevistas
  automaticamente considerando disponibilidade.

Requisitos Tecnicos:
  Backend:
    - scheduling_agent.py (61k linhas)
    - Microsoft Graph integration
    - Conflict detection

DoD:
  - [x] Agendamento funciona
  - [x] Teams meeting criado
  - [x] Conflitos detectados

Criterios de Aceitacao:
  - [x] Integração MS Graph
  - [x] Link Teams gerado
  - [x] Convites enviados
```

---

### CARD TRI-012: Serviço de Pré-Qualificação

```yaml
Titulo: [BACKEND] Serviço de Pré-Qualificação Automatizada
Tipo: Backend
Sprint: 3
Pontos: 8
Prioridade: Alta
Epic: EPIC-TRI
Status: ✅ Pronto

Descricao: |
  Serviço que realiza pré-qualificação automatizada de candidatos
  antes da triagem completa, com detecção de duplicatas.

Historia de Usuario: |
  Como sistema, eu quero pré-qualificar candidatos automaticamente
  para otimizar o processo de triagem.

Requisitos Tecnicos:
  Backend:
    - pre_qualification_service.py
    - Duplicate detection
    - Basic eligibility check

DoD:
  - [x] Pré-qualificação funciona
  - [x] Duplicatas detectadas
  - [x] Elegibilidade verificada

Criterios de Aceitacao:
  - [x] Candidatos pré-filtrados
  - [x] Duplicatas marcadas
  - [x] Status atualizado
```

---

### CARD DAT-001: Sistema de Solicitação de Dados

```yaml
Titulo: [FRONTEND] Sistema de Solicitação de Dados
Tipo: Frontend
Sprint: 4
Pontos: 8
Prioridade: Media
Epic: EPIC-DATA
Status: ✅ Pronto

Descricao: |
  Interface para gerenciar solicitações de dados aos candidatos,
  incluindo verificação OTP e upload de arquivos.

Historia de Usuario: |
  Como recrutador, eu quero solicitar documentos e informações
  adicionais aos candidatos de forma organizada.

Requisitos Tecnicos:
  Frontend:
    - DataRequestTab.tsx
    - OTP verification flow
    - File upload handling

DoD:
  - [x] Solicitações criadas
  - [x] OTP funciona
  - [x] Uploads funcionam

Criterios de Aceitacao:
  - [x] Múltiplos tipos de dados
  - [x] Verificação OTP
  - [x] Status de resposta
```

---

### CARD ENT-001: Análise de Transcrição de Entrevista

```yaml
Titulo: [BACKEND] Serviço de Análise de Transcrição
Tipo: Backend
Sprint: 5
Pontos: 13
Prioridade: Alta
Epic: EPIC-INTERVIEW
Status: ✅ Pronto

Descricao: |
  Serviço que analisa transcrições de entrevistas do Microsoft Teams,
  aplica scoring WSI e extrai insights comportamentais.

Historia de Usuario: |
  Como recrutador, eu quero que a transcrição da entrevista seja
  analisada automaticamente para identificar pontos-chave.

Requisitos Tecnicos:
  Backend:
    - interview_transcript_analysis_service.py
    - Teams transcription integration
    - WSI scoring on responses
    - Behavioral analysis

DoD:
  - [x] Transcrição processada
  - [x] Scores aplicados
  - [x] Insights extraídos

Criterios de Aceitacao:
  - [x] Integração Teams funciona
  - [x] Perguntas identificadas
  - [x] Respostas avaliadas
```

---

### CARD KAN-009: Componentes Kanban Modulares

```yaml
Titulo: [FRONTEND] Refatoração Modular do Kanban
Tipo: Frontend
Sprint: 2
Pontos: 13
Prioridade: Alta
Epic: EPIC-KAN
Status: ✅ Pronto

Descricao: |
  Refatoração do sistema Kanban de 10k+ linhas para arquitetura
  modular com componentes, hooks e utilities separados.

Historia de Usuario: |
  Como desenvolvedor, eu quero componentes Kanban modulares
  para facilitar manutenção e reutilização.

Estrutura Implementada:
  plataforma-lia/src/components/kanban/:
    - types.ts - Interfaces KanbanCandidate, DynamicStage
    - constants.ts - SYSTEM_STAGES, LEGACY_MAPPING
    - utils/ - stage-utils, filter-utils, status-utils
    - hooks/ - useDragDrop, useKanbanFilters, etc
    - components/ - CandidateCard, KanbanColumn, KanbanBoard

DoD:
  - [x] Arquivos separados
  - [x] Hooks reutilizáveis
  - [x] Utils compartilhados

Criterios de Aceitacao:
  - [x] Componentes independentes
  - [x] Types centralizados
  - [x] Hooks funcionais
```

'''
    
    # Encontrar onde inserir (antes do final do documento ou após último épico)
    # Vamos inserir antes da seção "---" final se existir
    
    if "## ÉPICO 14:" in content:
        # Inserir após ÉPICO 14
        insert_marker = "## ÉPICO 14:"
        parts = content.split(insert_marker)
        
        # Encontrar o final do ÉPICO 14 (próxima seção ## ou fim)
        epic14_content = parts[1]
        
        # Adicionar os novos cards ao final do documento
        content = content + new_cards
    else:
        content = content + new_cards
    
    return content

def update_executive_summary(content):
    """Atualiza o resumo executivo com novos totais"""
    
    new_summary = '''## RESUMO EXECUTIVO

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              VISÃO GERAL DOS CARDS MVP                                  │
│                         (Atualizado: Janeiro 2026 - Pós-Análise)                        │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│   FLUXO CORE MVP:                                                                        │
│   ─────────────────                                                                      │
│   Recrutador cria vaga (Wizard) → Busca candidatos → Aprova mapeados (Gate 1)           │
│   → LIA gera perguntas WSI → LIA contata via WhatsApp → LIA faz triagem                 │
│   → Recrutador aprova/reprova triados (Gate 2) → LIA agenda entrevista                  │
│                                                                                          │
│   DISTRIBUIÇÃO POR ÉPICO:                                                               │
│   ─────────────────────────                                                              │
│   │ ÉPICO 1: Autenticação       │ 4 cards  │ Sprint 0   │ ✅ 1 pronto   │               │
│   │ ÉPICO 2: Wizard             │ 8 cards  │ Sprint 1-2 │ ✅ 2 prontos  │               │
│   │ ÉPICO 3: Busca/Mapeamento   │ 6 cards  │ Sprint 2   │ ✅ 4 prontos  │               │
│   │ ÉPICO 4: Geração Perguntas  │ 5 cards  │ Sprint 2-3 │ ✅ 3 prontos  │               │
│   │ ÉPICO 5: Triagem WhatsApp   │ 11 cards │ Sprint 3-4 │ ✅ 1 pronto   │               │
│   │ ÉPICO 6: Score WSI          │ 8 cards  │ Sprint 4-5 │ ✅ 5 prontos  │               │
│   │ ÉPICO 7: Gates Aprovação    │ 7 cards  │ Sprint 5   │ ✅ 1 pronto   │               │
│   │ ÉPICO 8: Templates          │ 7 cards  │ Sprint 5-6 │ ✅ 5 prontos  │               │
│   │ ÉPICO 9: Agendamento        │ 8 cards  │ Sprint 6-7 │ ✅ 2 prontos  │               │
│   │ ÉPICO 10: Notificações      │ 6 cards  │ Sprint 7   │ ✅ 3 prontos  │               │
│   │ ÉPICO 11: Kanban/Tabela     │ 26 cards │ Sprint 1-8 │ ✅ 5 prontos  │               │
│   │ ÉPICO 12: JD/Wizard Avançado│ 5 cards  │ Sprint 2   │ ✅ 5 prontos  │ 🆕 NOVO      │
│   │ ÉPICO 13: Config Avançadas  │ 6 cards  │ Sprint 3   │ ✅ 6 prontos  │ 🆕 NOVO      │
│   │ ÉPICO 14: Integrações MVP   │ 26 cards │ Sprint 0-8 │ ✅ 8 prontos  │               │
│   │ ÉPICO 15: Agentes IA        │ 6 cards  │ Sprint 4-5 │ ✅ 6 prontos  │ 🆕 NOVO      │
│   └─────────────────────────────┴──────────┴────────────┴───────────────┘               │
│                                                                                          │
│   TOTAL: 139 cards │ ✅ 57 prontos │ 🔧 78 a desenvolver │ 🔗 4 integrações             │
│                                                                                          │
│   PROGRESSO: ████████████░░░░░░░░░░░░░░░░░░ 41% Completo                                │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

'''
    
    # Substituir o resumo executivo existente
    pattern = r'## RESUMO EXECUTIVO\n\n```[\s\S]*?```\n\n'
    content = re.sub(pattern, new_summary, content)
    
    return content

def update_index_table(content):
    """Atualiza a tabela de índice com novos épicos"""
    
    # Adicionar novos épicos no índice
    new_index_entries = '''
### ÉPICO 12: JD e Wizard Avançado (5 cards) 🆕
| Card | Título | Tipo | Status |
|------|--------|------|--------|
| JD-001 | Preview de JD com Sugestões LIA | Frontend | ✅ Pronto |
| JD-002 | JD Completo para Publicação | Frontend | ✅ Pronto |
| WIZ-009 | Interação com Sugestões LIA | Backend | ✅ Pronto |
| WIZ-010 | Análise de Compensação de Mercado | Backend | ✅ Pronto |
| WIZ-011 | Insights de Mercado para Vagas | Backend | ✅ Pronto |

### ÉPICO 13: Configurações Avançadas (6 cards) 🆕
| Card | Título | Tipo | Status |
|------|--------|------|--------|
| CFG-001 | LIA Field Toggles | Frontend | ✅ Pronto |
| CFG-002 | Verificação de Completude | Backend | ✅ Pronto |
| CFG-003 | Configuração de Jornada | Frontend | ✅ Pronto |
| CFG-004 | Hub de Comunicação | Frontend | ✅ Pronto |
| CFG-005 | Dados da Empresa para LIA | Frontend | ✅ Pronto |
| IMP-001 | Importação Inteligente | Frontend | ✅ Pronto |

### ÉPICO 15: Agentes IA Especializados (6 cards) 🆕
| Card | Título | Tipo | Status |
|------|--------|------|--------|
| AGT-001 | Agente Avaliador WSI | AI | ✅ Pronto |
| AGT-002 | Agente de Triagem Curricular | AI | ✅ Pronto |
| AGT-003 | Agente de Agendamento | AI | ✅ Pronto |
| TRI-012 | Serviço de Pré-Qualificação | Backend | ✅ Pronto |
| DAT-001 | Sistema de Solicitação de Dados | Frontend | ✅ Pronto |
| ENT-001 | Análise de Transcrição | Backend | ✅ Pronto |
| KAN-009 | Componentes Kanban Modulares | Frontend | ✅ Pronto |

'''
    
    # Inserir antes de "---\n\n# CARDS DETALHADOS"
    if "# CARDS DETALHADOS" in content:
        content = content.replace("# CARDS DETALHADOS", new_index_entries + "\n---\n\n# CARDS DETALHADOS")
    
    return content

def mark_obsolete_cards(content):
    """Marca cards obsoletos"""
    for card_id in CARDS_TO_MARK_OBSOLETE:
        pattern = rf'(### CARD {card_id}:.*?\n```yaml\n[\s\S]*?Status:\s*)([^\n]+)'
        content = re.sub(pattern, r'\1⚠️ Obsoleto (Removido)', content)
        content = update_index_status(content, card_id, "⚠️ Obsoleto")
    
    return content

def consolidate_cards(content):
    """Marca cards consolidados"""
    for card_id, note in CARDS_TO_CONSOLIDATE.items():
        pattern = rf'(### CARD {card_id}:.*?\n```yaml\n[\s\S]*?Status:\s*)([^\n]+)'
        content = re.sub(pattern, rf'\1🔄 {note}', content)
        content = update_index_status(content, card_id, f"🔄 {note}")
    
    return content

def main():
    input_path = 'docs/lia-mvp-cards-jira.md'
    backup_path = 'docs/lia-mvp-cards-jira.md.backup'
    
    print("=" * 70)
    print("Atualizando documento lia-mvp-cards-jira.md")
    print("=" * 70)
    print()
    
    if not os.path.exists(input_path):
        print(f"Arquivo não encontrado: {input_path}")
        return
    
    # Backup
    content = read_file(input_path)
    write_file(backup_path, content)
    print(f"✅ Backup criado: {backup_path}")
    print()
    
    # 1. Atualizar status dos cards implementados
    print("1. Atualizando status dos cards implementados...")
    updated_count = 0
    for card_id, new_status in CARDS_TO_UPDATE_STATUS.items():
        old_content = content
        content = update_card_status(content, card_id, new_status)
        content = update_index_status(content, card_id, new_status)
        if content != old_content:
            print(f"   ✅ {card_id}: → {new_status}")
            updated_count += 1
    print(f"   Total: {updated_count} cards atualizados")
    print()
    
    # 2. Marcar cards obsoletos
    print("2. Marcando cards obsoletos...")
    content = mark_obsolete_cards(content)
    print(f"   ✅ {len(CARDS_TO_MARK_OBSOLETE)} cards marcados como obsoletos")
    print()
    
    # 3. Consolidar cards redundantes
    print("3. Consolidando cards redundantes...")
    content = consolidate_cards(content)
    print(f"   ✅ {len(CARDS_TO_CONSOLIDATE)} cards consolidados")
    print()
    
    # 4. Atualizar resumo executivo
    print("4. Atualizando resumo executivo...")
    content = update_executive_summary(content)
    print("   ✅ Resumo atualizado com novos totais")
    print()
    
    # 5. Adicionar novos cards ao índice
    print("5. Atualizando índice com novos épicos...")
    content = update_index_table(content)
    print("   ✅ Novos épicos adicionados ao índice")
    print()
    
    # 6. Adicionar seção de novos cards
    print("6. Adicionando novos cards detalhados...")
    content = add_new_cards_section(content)
    print("   ✅ 17 novos cards adicionados (Épicos 12, 13, 15)")
    print()
    
    # Salvar
    write_file(input_path, content)
    
    print("=" * 70)
    print("RESUMO FINAL")
    print("=" * 70)
    print(f"✅ Cards com status atualizado: {updated_count}")
    print(f"✅ Cards obsoletos marcados: {len(CARDS_TO_MARK_OBSOLETE)}")
    print(f"✅ Cards consolidados: {len(CARDS_TO_CONSOLIDATE)}")
    print(f"✅ Novos cards adicionados: 17")
    print(f"✅ Novos épicos: 3 (12, 13, 15)")
    print()
    print(f"Arquivo atualizado: {input_path}")
    print(f"Backup disponível: {backup_path}")

if __name__ == '__main__':
    main()
