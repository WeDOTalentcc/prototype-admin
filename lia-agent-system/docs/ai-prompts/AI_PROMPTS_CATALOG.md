# Catálogo de Prompts LIA

Este documento lista todos os prompts do sistema LIA com suas versões, descrições e exemplos de uso.

## Visão Geral

O sistema LIA utiliza uma arquitetura multi-agente com prompts especializados para cada função do processo de recrutamento.

| # | Prompt | Versão | Última Atualização | Agente |
|---|--------|--------|-------------------|--------|
| 1 | ORCHESTRATOR_PROMPT | 2.0.0 | 2026-01-30 | Orquestrador Central |
| 2 | JOB_PLANNER_PROMPT | 2.0.0 | 2026-01-30 | Planejador de Vagas |
| 3 | SOURCING_PROMPT | 2.0.0 | 2026-01-30 | Especialista em Sourcing |
| 4 | CV_SCREENING_PROMPT | 2.0.0 | 2026-01-30 | Triagem Curricular |
| 5 | INTERVIEWER_PROMPT | 2.0.0 | 2026-01-30 | Entrevistador WSI |
| 6 | WSI_EVALUATOR_PROMPT | 2.0.0 | 2026-01-30 | Avaliador WSI |
| 7 | SCHEDULING_PROMPT | 2.0.0 | 2026-01-30 | Agendamento |
| 8 | ANALYST_FEEDBACK_PROMPT | 2.0.0 | 2026-01-30 | Analista & Feedback |
| 9 | ATS_INTEGRATOR_PROMPT | 2.0.0 | 2026-01-30 | Integrador ATS |
| 10 | RECRUITER_ASSISTANT_PROMPT | 2.0.0 | 2026-01-30 | Assistente do Recrutador |
| 11 | PROACTIVE_INSIGHTS_PROMPT | 2.0.0 | 2026-01-30 | Insights Proativos |

---

## Componentes Compartilhados

Antes dos prompts individuais, o sistema define componentes reutilizáveis:

### LIA_PERSONA
**Versão**: 2.0.0 | **Última Atualização**: 2026-01-30

Define a identidade unificada da LIA usada em todos os agentes.

**Conteúdo**:
- Identidade: LIA (Learning Intelligence Assistant)
- Tom: Profissional, empático, direto e proativo
- Linguagem: Formal mas acessível
- Evitar: Gírias, emojis excessivos, abreviações

### HR_VOCABULARY
**Versão**: 2.0.0 | **Última Atualização**: 2026-01-30

Vocabulário técnico de RH brasileiro padronizado.

**Categorias**:
- Processo Seletivo
- Avaliação de Candidatos
- Níveis de Senioridade
- Tipos de Contratação
- Remuneração e Benefícios
- Etapas do Processo

### DATA_PERSISTENCE_GUIDELINES
**Versão**: 2.0.0 | **Última Atualização**: 2026-01-30

Diretrizes obrigatórias para persistência de dados e sincronização com ATS.

### ETHICAL_GUIDELINES
**Versão**: 2.0.0 | **Última Atualização**: 2026-01-30

Diretrizes éticas obrigatórias para avaliação sem viés.

---

## Prompts dos Agentes

### 1. ORCHESTRATOR_PROMPT

**Nome**: Orquestrador Central
**Versão**: 2.0.0
**Última Atualização**: 2026-01-30
**Autor**: WeDOTalent Team

**Descrição**:
Coordenadora central do sistema de recrutamento. Responsável por entender requisições dos recrutadores, direcionar tarefas aos agentes especializados e garantir a qualidade das respostas.

**Responsabilidades**:
- Entender requisições dos recrutadores
- Delegar tarefas aos agentes especializados
- Manter contexto entre conversas
- Garantir persistência de dados
- Coordenar sincronização com ATS

**Variáveis Disponíveis**:
| Variável | Tipo | Descrição |
|----------|------|-----------|
| `{context}` | string | Contexto atual da conversa |

**Exemplo de Uso**:
```python
from app.agents.prompts import get_agent_prompt

prompt = get_agent_prompt("orchestrator", context="Vaga: Desenvolvedor Python Sênior")
```

**Formato de Resposta**:
- Respostas Informativas: Resumo, Detalhes, Próximos Passos
- Confirmação de Ações: Ação Realizada, Dados Atualizados, Sincronização

---

### 2. JOB_PLANNER_PROMPT

**Nome**: Planejador de Vagas
**Versão**: 2.0.0
**Última Atualização**: 2026-01-30
**Autor**: WeDOTalent Team

**Descrição**:
Especialista em definição e estruturação de vagas. Cria job descriptions, extrai requisitos e gera perguntas WSI para entrevistas.

**Responsabilidades**:
- Criar e editar vagas de emprego
- Extrair requisitos de JDs
- Gerar perguntas WSI (Bloom + Dreyfus + Big Five)
- Definir perfil ideal do candidato
- Mapear competências técnicas e comportamentais

**Metodologia**:
- Bloom's Taxonomy: Classificação cognitiva
- Dreyfus Model: Níveis de expertise (1-5)
- Big Five: Traços de personalidade

**Variáveis Disponíveis**:
| Variável | Tipo | Descrição |
|----------|------|-----------|
| `{context}` | string | Contexto da vaga sendo criada/editada |

**Exemplo de Uso**:
```python
prompt = get_agent_prompt("job_planner", context="Criando vaga para Tech Lead")
```

**Campos Persistidos**:
- Título, Requisitos técnicos, Senioridade, Modalidade → WedoTalent + ATS
- Requisitos comportamentais, Perguntas WSI → Apenas WedoTalent

---

### 3. SOURCING_PROMPT

**Nome**: Especialista em Sourcing
**Versão**: 2.0.0
**Última Atualização**: 2026-01-30
**Autor**: WeDOTalent Team

**Descrição**:
Especialista em busca e captação de candidatos. Realiza buscas no banco de talentos local e no Pearch AI, gera boolean strings e executa outreach.

**Responsabilidades**:
- Buscar candidatos (banco local + Pearch AI)
- Gerar strings booleanas avançadas
- Outreach via WhatsApp e LinkedIn
- Enriquecer perfis de candidatos
- Criar longlist inicial

**Fluxo de Busca**:
1. Busca no banco local (gratuito)
2. Busca no Pearch AI (se necessário)
3. Unificação e remoção de duplicatas
4. Ranking por relevância

**Variáveis Disponíveis**:
| Variável | Tipo | Descrição |
|----------|------|-----------|
| `{context}` | string | Critérios de busca e vaga alvo |

**Exemplo de Uso**:
```python
prompt = get_agent_prompt("sourcing", context="Buscar desenvolvedores Python com 5+ anos")
```

---

### 4. CV_SCREENING_PROMPT

**Nome**: Triagem Curricular
**Versão**: 2.0.0
**Última Atualização**: 2026-01-30
**Autor**: WeDOTalent Team

**Descrição**:
Especialista em análise de CVs e screening inicial. Parseia currículos, calcula scores e detecta red flags.

**Responsabilidades**:
- Parsear CVs (PDF, DOCX)
- Triagem automática contra requisitos
- Calcular score WSI inicial (70% técnico, 30% comportamental)
- Rankear candidatos para shortlist
- Detectar red flags

**Metodologia de Scoring**:
- Score Técnico (70%): Hard skills, experiência, formação
- Score Comportamental (30%): Indicadores do CV
- Dynamic Cutoff: Recalculo após 30-50 candidatos
- Smart Saturation: Pausa se >20 aprovados

**Variáveis Disponíveis**:
| Variável | Tipo | Descrição |
|----------|------|-----------|
| `{context}` | string | Informações da vaga e candidato |

**Exemplo de Uso**:
```python
prompt = get_agent_prompt("cv_screening", context="Analisando CV para vaga de Data Scientist")
```

---

### 5. INTERVIEWER_PROMPT

**Nome**: Entrevistador WSI
**Versão**: 2.0.0
**Última Atualização**: 2026-01-30
**Autor**: WeDOTalent Team

**Descrição**:
Especialista em entrevistas estruturadas WSI. Conduz entrevistas via WhatsApp/Voz, faz perguntas adaptativas e valida respostas com técnica CBI.

**Responsabilidades**:
- Conduzir entrevistas WSI
- Fazer perguntas adaptativas
- Transcrever e analisar entrevistas
- Validar respostas usando STAR

**Metodologia CBI (STAR)**:
- **S**ituation: Contexto claro?
- **T**ask: Tarefa definida?
- **A**ction: Ações específicas?
- **R**esult: Resultados mensuráveis?

**Fluxo de Entrevista**:
1. Apresentação e rapport
2. Perguntas técnicas (Bloom)
3. Perguntas comportamentais (Big Five)
4. Sondagem Dreyfus
5. Perguntas do candidato
6. Alinhamento de expectativas

**Variáveis Disponíveis**:
| Variável | Tipo | Descrição |
|----------|------|-----------|
| `{context}` | string | Informações do candidato e vaga |

**Exemplo de Uso**:
```python
prompt = get_agent_prompt("interviewer", context="Entrevista técnica - Backend Developer")
```

---

### 6. WSI_EVALUATOR_PROMPT

**Nome**: Avaliador WSI
**Versão**: 2.0.0
**Última Atualização**: 2026-01-30
**Autor**: WeDOTalent Team

**Descrição**:
Especialista em avaliação científica de candidatos. Aplica metodologia WSI completa: Bloom's Taxonomy, Dreyfus Model e Big Five.

**Responsabilidades**:
- Avaliar transcrições de entrevistas
- Aplicar scoring Bloom + Dreyfus + Big Five
- Gerar pareceres estruturados
- Comparar candidatos (side-by-side)
- Calibrar modelo com feedback

**Metodologia WSI**:

**Bloom's Taxonomy (1-6)**:
| Nível | Descrição | Score |
|-------|-----------|-------|
| Lembrar | Recorda fatos básicos | 1 |
| Compreender | Explica conceitos | 2 |
| Aplicar | Usa conhecimento | 3 |
| Analisar | Decompõe problemas | 4 |
| Avaliar | Julga criticamente | 5 |
| Criar | Inova e propõe | 6 |

**Dreyfus Model (1-5)**:
| Nível | Descrição | Score |
|-------|-----------|-------|
| Novato | Segue regras básicas | 1 |
| Iniciante Avançado | Reconhece padrões | 2 |
| Competente | Planeja e prioriza | 3 |
| Proficiente | Visão holística | 4 |
| Expert | Intuição e improviso | 5 |

**Big Five**:
- Abertura (O), Conscienciosidade (C), Extroversão (E), Amabilidade (A), Neuroticismo (N)

**Variáveis Disponíveis**:
| Variável | Tipo | Descrição |
|----------|------|-----------|
| `{context}` | string | Transcrição e dados do candidato |

**Exemplo de Uso**:
```python
prompt = get_agent_prompt("wsi_evaluator", context="Avaliar entrevista do candidato João")
```

---

### 7. SCHEDULING_PROMPT

**Nome**: Especialista em Agendamento
**Versão**: 2.0.0
**Última Atualização**: 2026-01-30
**Autor**: WeDOTalent Team

**Descrição**:
Especialista em agendamento de entrevistas. Integra com Microsoft Graph para gerenciar calendários e enviar convites.

**Responsabilidades**:
- Agendar entrevistas via Microsoft Graph
- Coordenar disponibilidade de entrevistadores
- Enviar convites e lembretes
- Gerenciar reagendamentos
- Self-scheduling para candidatos

**Integração Microsoft Graph**:
- Acesso a calendários
- Criação de eventos com Teams/Meet
- Detecção de conflitos
- Envio de convites automáticos

**Variáveis Disponíveis**:
| Variável | Tipo | Descrição |
|----------|------|-----------|
| `{context}` | string | Detalhes do agendamento |

**Exemplo de Uso**:
```python
prompt = get_agent_prompt("scheduling", context="Agendar entrevista técnica para amanhã")
```

---

### 8. ANALYST_FEEDBACK_PROMPT

**Nome**: Analista & Feedback
**Versão**: 2.0.0
**Última Atualização**: 2026-01-30
**Autor**: WeDOTalent Team

**Descrição**:
Especialista em KPIs, relatórios e comunicação. Gera dashboards, análise de funil e feedback para candidatos.

**Responsabilidades**:
- Gerar KPIs e dashboards
- Análise de funil de recrutamento
- Feedback para candidatos
- Comunicação em massa
- Relatórios para gestores

**KPIs Principais**:
- Time-to-fill: Dias desde abertura até contratação
- Time-to-hire: Dias desde candidatura até contratação
- Quality-of-hire: Performance pós-contratação
- Pipeline velocity: Candidatos por etapa
- Taxa de conversão: Percentual entre etapas

**Tipos de Relatórios**:
- Daily briefing
- Weekly summary
- Job health report
- Candidate comparison
- Funil de recrutamento

**Variáveis Disponíveis**:
| Variável | Tipo | Descrição |
|----------|------|-----------|
| `{context}` | string | Dados para análise/relatório |

**Exemplo de Uso**:
```python
prompt = get_agent_prompt("analyst_feedback", context="Relatório semanal da vaga X")
```

---

### 9. ATS_INTEGRATOR_PROMPT

**Nome**: Integrador ATS
**Versão**: 2.0.0
**Última Atualização**: 2026-01-30
**Autor**: WeDOTalent Team

**Descrição**:
Especialista em integração com sistemas ATS. Garante sincronização, conformidade LGPD e audit logging.

**Responsabilidades**:
- Sincronizar candidatos com ATS externos
- Garantir conformidade LGPD
- Audit logging de operações
- Mapeamento de campos entre sistemas

**Integrações Suportadas**:
- Gupy: ATS líder no Brasil
- Pandapé: Solução integrada de RH
- Merge.dev: API unificada (40+ sistemas)

**Mapeamento de Campos**:
| LIA | Gupy | Pandapé |
|-----|------|---------|
| candidate_id | application_id | candidato_id |
| name | nome | nome_completo |
| status | fase | situacao |

**Variáveis Disponíveis**:
| Variável | Tipo | Descrição |
|----------|------|-----------|
| `{context}` | string | Operação de sincronização |

**Exemplo de Uso**:
```python
prompt = get_agent_prompt("ats_integrator", context="Sincronizar candidato com Gupy")
```

---

### 10. RECRUITER_ASSISTANT_PROMPT

**Nome**: Assistente Pessoal do Recrutador
**Versão**: 2.0.0
**Última Atualização**: 2026-01-30
**Autor**: WeDOTalent Team

**Descrição**:
Ajudante geral para tarefas do dia-a-dia do recrutador. Solícito, organizado e proativo.

**Responsabilidades**:
- Daily briefing matinal
- Gerenciamento de tarefas pessoais
- Responder perguntas gerais
- Sugestões proativas
- Calibração de perfil com feedback
- Acompanhamento de metas

**Tipos de Ajuda**:
- "O que tenho para fazer hoje?" → Lista de tarefas
- "Como funciona X?" → Explicação do recurso
- "Me ajude com Y" → Assistência contextual

**Variáveis Disponíveis**:
| Variável | Tipo | Descrição |
|----------|------|-----------|
| `{context}` | string | Contexto do recrutador |

**Exemplo de Uso**:
```python
prompt = get_agent_prompt("recruiter_assistant", context="Briefing do dia")
```

---

### 11. PROACTIVE_INSIGHTS_PROMPT

**Nome**: Gerador de Insights Proativos
**Versão**: 2.0.0
**Última Atualização**: 2026-01-30
**Autor**: WeDOTalent Team

**Descrição**:
Analisa métricas de busca e gera insights estratégicos com recomendações de ações.

**Estrutura de Resposta**:
1. Narrativa Principal (2-3 frases)
2. Destaques (max 5 pontos positivos)
3. Preocupações (max 5 pontos de atenção)
4. Recomendações (max 4 ações)
5. Pergunta Proativa

**Regras de Análise**:
- Score >= 80%: Excelente
- Score >= 60%: Bom
- Score < 60%: Sugerir refinamento
- Pool < 30: Sugerir expansão
- Pool >= 50: Saudável

**Variáveis Disponíveis**:
| Variável | Tipo | Descrição |
|----------|------|-----------|
| `{context}` | string | Métricas de busca |

**Exemplo de Uso**:
```python
prompt = get_agent_prompt("proactive_insights", context="Análise do pipeline da vaga X")
```

---

## Histórico de Versões

### v2.0.0 (2026-01-30)
- Adicionada persona LIA unificada
- Adicionado vocabulário técnico de RH brasileiro
- Adicionadas diretrizes de persistência de dados
- Adicionadas diretrizes éticas obrigatórias
- Expandidos formatos de resposta estruturada
- Adicionados detalhes de sincronização com ATS

### v1.0.0 (2025-12-01)
- Versão inicial dos prompts
- 8 agentes básicos

---

## Como Usar

### Importar e Usar Prompts

```python
from app.agents.prompts import get_agent_prompt

# Obter prompt de um agente
prompt = get_agent_prompt("orchestrator", context="Meu contexto")

# Obter componentes compartilhados
from app.agents.prompts.agent_prompts import (
    get_lia_persona,
    get_hr_vocabulary,
    get_data_persistence_guidelines,
    get_ethical_guidelines
)

persona = get_lia_persona()
vocabulary = get_hr_vocabulary()
```

### Usando o Registry (Novo)

```python
from app.agents.prompts.prompt_registry import prompt_registry, init_prompts

# Inicializar todos os prompts
init_prompts()

# Obter prompt específico
content = prompt_registry.get_prompt("orchestrator", version="2.0.0")

# Obter versão mais recente
content = prompt_registry.get_prompt("orchestrator", version="latest")

# Listar todas as versões
versions = prompt_registry.get_all_versions("orchestrator")

# Obter catálogo completo
catalog = prompt_registry.get_catalog()
```

---

## Manutenção

Para informações sobre como criar, atualizar e revisar prompts, consulte:
- [README de Prompts](../app/agents/prompts/README.md)
