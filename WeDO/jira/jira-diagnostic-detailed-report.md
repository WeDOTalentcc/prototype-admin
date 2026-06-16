# DIAGNÓSTICO JIRA DETALHADO - PLATAFORMA LIA MVP

**Data:** 02 de Fevereiro de 2026  
**Projeto:** WT (wedotalent tasks 2026)

---

# ÍNDICE

1. [130 Cards para Exclusão](#1-130-cards-para-exclusão)
2. [100 Cards Sincronizados (OK)](#2-100-cards-sincronizados-ok)
3. [51 Cards Novos para Criar](#3-51-cards-novos-para-criar)

---

# 1. 130 CARDS PARA EXCLUSÃO

Estes cards existem no Jira mas **não fazem parte** do documento `lia-mvp-cards-jira.md` atualizado. Foram identificados como cards de versões anteriores do projeto ou funcionalidades que foram removidas/consolidadas do escopo MVP.

## 1.1 Cards DEV Antigos (5 cards)

**O que são:** Tarefas de desenvolvimento de sprints anteriores, provavelmente de uma fase inicial do projeto.

**Por que excluir:** São tarefas genéricas de desenvolvimento que não se alinham com a nova estrutura de cards do MVP.

| Jira Key | Título | Motivo Exclusão |
|----------|--------|-----------------|
| WT-47 | [DEV-S1-005] Configurar Sidekiq para Background Jobs | Infraestrutura antiga, não faz parte do MVP atual |
| WT-52 | [DEV-S2-005] Testar Fluxo SSO Completo | Consolidado em AUTH-002 e INT-WOS-xxx |
| WT-57 | [DEV-S3-005] Testar Fluxo de Checkout End-to-End | Funcionalidade de billing não está no MVP |
| WT-62 | [DEV-S4-005] Implementar Webhooks HubSpot (Opcional) | Integração HubSpot removida do MVP |
| WT-66 | [DEV-S5-004] Testes Finais e Documentação da API | Card genérico, será substituído por testes específicos |

---

## 1.2 Cards VAG Expandidos (67 cards)

**O que são:** Cards de funcionalidades de vagas que foram criados em uma versão anterior com escopo mais amplo. O MVP atual simplificou para 8 cards de vagas (VAG-001 a VAG-008).

**Por que excluir:** O escopo do MVP foi reduzido. Funcionalidades como filtros avançados, níveis de chat LIA, wizards expandidos, e configurações complexas foram movidas para pós-MVP.

### VAG-009 a VAG-027: Funcionalidades de Filtro e LIA (19 cards)

| Jira Key | Título | Motivo Exclusão |
|----------|--------|-----------------|
| WT-291 | [VAG-009] Filtro Vagas Urgentes | Consolidado em filtros básicos KAN-007 |
| WT-292 | [VAG-010] Filtro Vagas Paralisadas | Pós-MVP |
| WT-293 | [VAG-011] Filtro Concluidas e Canceladas | Pós-MVP |
| WT-294 | [VAG-012] Container LIA Centralizado | Consolidado no wizard conversacional |
| WT-295 | [VAG-013] Titulo Contextual Dinamico | Pós-MVP |
| WT-296 | [VAG-014] Input de Chat LIA | Consolidado em WIZ-001 |
| WT-297 | [VAG-015] Icones Microfone e Busca | Pós-MVP |
| WT-298 | [VAG-016] Sugestoes Contextuais | Consolidado em WIZ-006 |
| WT-299 | [VAG-017] Integracao Backend LIA | Consolidado nos cards de integração LLM |
| WT-300 | [VAG-018] Acao Criar Nova Vaga | Consolidado em WIZ-001 |
| WT-301 | [VAG-019] Acao Ver Minhas Vagas | Consolidado em VAG-001 |
| WT-302 | [VAG-020] Acao Ver Todas as Vagas | Consolidado em VAG-001 |
| WT-303 | [VAG-021] Acao Resumo das Vagas | Pós-MVP |
| WT-304 | [VAG-022] Acao Mais Ideias (AI) | Pós-MVP |
| WT-305 | [VAG-023] Empty State Design | Design básico no MVP |
| WT-306 | [VAG-024] Mensagem Boas-Vindas LIA | Consolidado em WIZ-001 |

### VAG-028 a VAG-047: Tabela de Vagas Avançada (20 cards)

| Jira Key | Título | Motivo Exclusão |
|----------|--------|-----------------|
| WT-307 | [VAG-028] Tabela de Vagas - Estrutura Base | Consolidado em VAG-001 |
| WT-308 | [VAG-029] Colunas Configuraveis Toggle/Order | Pós-MVP |
| WT-309 | [VAG-030] Ordenacao Multi-Coluna Sort | Pós-MVP |
| WT-310 | [VAG-031] Redimensionamento de Colunas | Pós-MVP |
| WT-311 | [VAG-032] Selecao em Lote Checkbox | Consolidado em TAB-003 |
| WT-312 | [VAG-033] Persistencia de Config localStorage | Pós-MVP |
| WT-313 | [VAG-034] Coluna Performance LIA Triagens | Pós-MVP |
| WT-314 | [VAG-035] Coluna Roteiro de Triagem | Consolidado em WSI-003 |
| WT-315 | [VAG-036] Acoes por Linha Menu Dropdown | Consolidado em VAG-003 |
| WT-316 | [VAG-037] Preview Panel - Estrutura Base | Consolidado em PRV-001 |
| WT-317 | [VAG-038] Tab Visao Geral - Funil Rapido | Pós-MVP |
| WT-318 | [VAG-039] Tab Visao Geral - Metricas LIA | Pós-MVP |
| WT-319 | [VAG-040] Tab Visao Geral - Responsaveis | Pós-MVP |
| WT-320 | [VAG-041] Tab Visao Geral - Datas Criticas | Pós-MVP |
| WT-321 | [VAG-042] Tab Roteiro de Triagem - WSI Blocks | Consolidado em WSI-002 |
| WT-322 | [VAG-043] WSI Blocks - Accordion Expansivel | Consolidado em WSI-003 |
| WT-323 | [VAG-044] WSI Blocks - Editor de Perguntas | Consolidado em WSI-004 |
| WT-324 | [VAG-045] Configuracao de Canais de Triagem | Consolidado em TRI-001 |
| WT-325 | [VAG-046] Processo Seletivo Inline Breadcrumb | Pós-MVP |
| WT-326 | [VAG-047] Resize do Painel de Preview | Pós-MVP |

### VAG-048 a VAG-078: Modals e Chat Avançado (28 cards)

| Jira Key | Título | Motivo Exclusão |
|----------|--------|-----------------|
| WT-327 | [VAG-048] JobActionsBar - Barra de Acoes | Consolidado em VAG-003 |
| WT-328 | [VAG-049] JobPublishModal - Publicar em Canais | Pós-MVP |
| WT-329 | [VAG-050] JobInsightsModal - Metricas Expandidas | Pós-MVP |
| WT-330 | [VAG-051] JobDuplicateModal - Duplicar Vaga | Consolidado em VAG-005 |
| WT-331 | [VAG-052] JobStatusModal - Pausar/Ativar Vaga | Consolidado em VAG-004 |
| WT-332 | [VAG-053] JobAssignRecruiterModal - Atribuir Recrutador | Pós-MVP |
| WT-333 | [VAG-054] JobUnpublishModal - Despublicar Vaga | Pós-MVP |
| WT-334 | [VAG-055] JobCompareModal - Comparar Vagas | Pós-MVP |
| WT-335 | [VAG-056] EditJobModal - Edicao Completa | Consolidado em WIZ-008 |
| WT-336 | [VAG-057] JobFiltersPanel - Painel Lateral | Consolidado em KAN-007 |
| WT-337 | [VAG-058] Filtros Rapidos Ativas/Urgentes/Remotas | Pós-MVP |
| WT-338 | [VAG-059] Filtro por Status da Vaga | Consolidado em VAG-002 |
| WT-339 | [VAG-060] Filtro por Etapa do Processo | Pós-MVP |
| WT-340 | [VAG-061] Filtro por Modelo de Trabalho | Pós-MVP |
| WT-341 | [VAG-062] Filtro por Recrutador/Gestor | Pós-MVP |
| WT-342 | [VAG-063] Busca Booleana AND/OR/NOT | Pós-MVP |
| WT-343 | [VAG-064] Pesquisas Salvas Templates | Pós-MVP |
| WT-344 | [VAG-065] Persistencia de Filtros Hook | Pós-MVP |
| WT-345 | [VAG-066] Nivel 1 Mini Prompt Inline | Consolidado em WIZ-001 |
| WT-346 | [VAG-067] Nivel 2 Chat Expandido Lateral | Consolidado em WIZ-001 |
| WT-347 | [VAG-068] Nivel 3 Super Chat Criacao de Vaga | Consolidado em WIZ-001 |
| WT-348 | [VAG-069] Deteccao de Intent de Criacao | Consolidado em WIZ-002 |
| WT-349 | [VAG-070] Auto-Expand LIA ao Selecionar Vagas | Pós-MVP |
| WT-350 | [VAG-071] Historico de Mensagens Inline | Pós-MVP |
| WT-351 | [VAG-072] AudioRecordButton Gravacao de Voz | Pós-MVP |
| WT-352 | [VAG-073] LiaVacancyQueriesGuide Popover | Pós-MVP |
| WT-353 | [VAG-074] ExpandedChatModal Modal Full | Consolidado em WIZ-001 |
| WT-354 | [VAG-075] Botao Nova Vaga Header | Design básico no MVP |
| WT-355 | [VAG-076] Super Chat Modal Container | Consolidado em WIZ-001 |
| WT-356 | [VAG-077] Wizard Step 1 Descricao Inicial | Consolidado em novos cards WIZ-009 a WIZ-013 |
| WT-357 | [VAG-078] Wizard Step 2 Informacoes Basicas | Consolidado em novos cards WIZ-009 a WIZ-013 |

---

## 1.3 Cards CONFIG Antigos (58 cards)

**O que são:** Cards de configuração administrativa que foram criados com uma estrutura diferente. O novo documento `configuracoes-admin-cards-jira.md` define 58 cards com nova nomenclatura.

**Por que excluir:** Foram substituídos pelos novos cards de configuração. A estrutura mudou de prefixos SET/EMP/REC/COM/MET/BGL/INT/VOZ para os novos épicos do MVP.

### SET - Estrutura de Configurações (1 card)

| Jira Key | Título | Motivo Exclusão |
|----------|--------|-----------------|
| WT-1037 | [SET-001] Estrutura do Menu de Configurações Admin | Substituído por nova estrutura de navegação |

### EMP - Configurações da Empresa (17 cards)

| Jira Key | Título | Motivo Exclusão |
|----------|--------|-----------------|
| WT-1038 | [EMP-001] Formulario de Dados Institucionais | Substituído por CFG-005 (Dados da Empresa para LIA) |
| WT-1039 | [EMP-002] Upload de Logo da Empresa | Pós-MVP |
| WT-1040 | [EMP-003] Selecao de Industria e Tamanho | Pós-MVP |
| WT-1041 | [EMP-004] Formulario de Cultura Organizacional | Pós-MVP |
| WT-1042 | [EMP-005] Configuracao de Tech Stack | Pós-MVP |
| WT-1043 | [EMP-006] Radar de Cultura Big Five | Pós-MVP |
| WT-1044 | [EMP-008] Gestao de Departamentos | Pós-MVP |
| WT-1045 | [EMP-009] Gestao de Membros por Departamento | Pós-MVP |
| WT-1046 | [EMP-010] Gestao de Beneficios | Pós-MVP |
| WT-1047 | [EMP-011] Regras de Elegibilidade | Pós-MVP |
| WT-1048 | [EMP-012] Gestao de Usuarios do Sistema | Substituído por INT-WOS-005 (User Management SDK) |
| WT-1049 | [EMP-013] Implementar Sistema de Roles | Substituído por INT-WOS-003 |
| WT-1050 | [EMP-014] Permissoes Granulares por Modulo | Pós-MVP |
| WT-1051 | [EMP-015] Gestao de Aprovadores | Pós-MVP |
| WT-1052 | [EMP-016] Configurar Fluxo Multi-nivel | Pós-MVP |
| WT-1053 | [EMP-017] Importacao Inteligente de Dados | Substituído por IMP-001 |

### REC - Configurações de Recrutamento (12 cards)

| Jira Key | Título | Motivo Exclusão |
|----------|--------|-----------------|
| WT-1054 | [REC-001] Visualizacao do Pipeline de Recrutamento | Consolidado em KAN-001 |
| WT-1055 | [REC-002] Edicao de Pipeline (Customer Success) | Pós-MVP |
| WT-1056 | [REC-003] Drag & Drop de Etapas do Pipeline | Consolidado em KAN-003 |
| WT-1057 | [REC-004] Gestao de Perguntas Screening WhatsApp | Consolidado em WSI-004 |
| WT-1058 | [REC-005] Suporte a Tipos de Pergunta | Consolidado em WSI-002 |
| WT-1059 | [REC-006] Toggle de Pergunta Obrigatoria | Consolidado em WSI-004 |
| WT-1060 | [REC-007] Drag & Drop de Perguntas | Consolidado em WSI-004 |
| WT-1061 | [REC-008] Botao Restaurar Perguntas Padrao | Pós-MVP |
| WT-1062 | [REC-009] Configuracao de Status de Candidatos | Pós-MVP |
| WT-1063 | [REC-010] Configuracao de Solicitacao de Dados | Substituído por DAT-001 |
| WT-1064 | [REC-011] Configuracao de Instrucoes LIA por Campo | Substituído por CFG-001 |
| WT-1065 | [REC-012] Regras de Governanca LIA | Pós-MVP |

### COM - Comunicação (10 cards)

| Jira Key | Título | Motivo Exclusão |
|----------|--------|-----------------|
| WT-1066 | [COM-001] Listagem de Templates de Email | Consolidado em TPL-001 a TPL-007 |
| WT-1067 | [COM-002] Criar Template de Email | Consolidado em TPL-005 |
| WT-1068 | [COM-003] Editar Template Existente | Consolidado em TPL-005 |
| WT-1069 | [COM-004] Sistema de Variaveis Dinamicas | Consolidado em TPL-006 |
| WT-1070 | [COM-005] Preview de Template com Dados | Consolidado em TPL-007 |
| WT-1071 | [COM-006] Duplicar Template Existente | Pós-MVP |
| WT-1072 | [COM-007] Excluir Template Custom | Pós-MVP |
| WT-1073 | [COM-008] Configuracao de Assinatura de Email | Pós-MVP |
| WT-1074 | [COM-009] Configuracao de Janela de Envio LGPD | Pós-MVP |
| WT-1075 | [COM-010] Configuracao de Alertas e Briefings | Substituído por NOT-003 |

### MET - Metas e Headcount (7 cards)

| Jira Key | Título | Motivo Exclusão |
|----------|--------|-----------------|
| WT-1076 | [MET-001] Definir Metas por Recrutador | Pós-MVP (módulo de analytics) |
| WT-1077 | [MET-002] Definir Metas Agregadas de Equipe | Pós-MVP |
| WT-1078 | [MET-003] Configurar KPIs Padrao | Pós-MVP |
| WT-1079 | [MET-004] Configurar Periodos de Metas | Pós-MVP |
| WT-1080 | [MET-005] Dashboard de Acompanhamento de Metas | Pós-MVP |
| WT-1081 | [MET-006] Planejamento de Headcount | Pós-MVP |
| WT-1082 | [MET-007] Visualizacao de Headcount Atual | Pós-MVP |

### BGL - Busca Global e Créditos (5 cards)

| Jira Key | Título | Motivo Exclusão |
|----------|--------|-----------------|
| WT-1083 | [BGL-001] Configurar Limite de Candidatos | Pós-MVP (billing) |
| WT-1084 | [BGL-002] Habilitar/Desabilitar Busca Global | Pós-MVP |
| WT-1085 | [BGL-003] Exibir Saldo de Creditos | Pós-MVP (billing) |
| WT-1086 | [BGL-004] Exibir Tabela de Custos por Acao | Pós-MVP (billing) |
| WT-1087 | [BGL-005] Historico de Consumo de Creditos | Pós-MVP (billing) |

### INT - Integrações Genéricas (6 cards)

| Jira Key | Título | Motivo Exclusão |
|----------|--------|-----------------|
| WT-1088 | [INT-001] Integração Stripe para Billing | Pós-MVP (billing não está no escopo) |
| WT-1089 | [INT-002] Integração HubSpot + Arrows | Pós-MVP |
| WT-1090 | [INT-003] Integração WorkOS | Substituído por INT-WOS-001 a INT-WOS-007 (mais detalhado) |
| WT-1091 | [INT-004] Integração Microsoft Graph | Substituído por INT-MSG-002 a INT-MSG-006 (mais detalhado) |
| WT-1092 | [INT-005] Integração ATS via Merge | Pós-MVP |
| WT-1093 | [INT-006] Integração Comunicação (Mailgun, WhatsApp) | Substituído por INT-TWI-001 a INT-TWI-007 |

### VOZ - Integração de Voz (1 card)

| Jira Key | Título | Motivo Exclusão |
|----------|--------|-----------------|
| WT-1094 | [VOZ-001] Integração Deepgram (Speech-to-Text) | Pós-MVP |

---

## 1.4 Resumo das Exclusões

| Categoria | Quantidade | Motivo Principal |
|-----------|------------|------------------|
| DEV Antigos | 5 | Tarefas genéricas de sprints anteriores |
| VAG Expandidos | 67 | Escopo reduzido para MVP, consolidados ou pós-MVP |
| CONFIG Antigos | 58 | Substituídos por nova estrutura de cards |
| **TOTAL** | **130** | - |

---

# 2. 100 CARDS SINCRONIZADOS (OK)

Estes cards já existem no Jira e correspondem ao documento atualizado. **Não precisam de exclusão**, mas podem precisar de **atualização de descrição** para alinhar com as especificações detalhadas do documento.

## 2.1 ÉPICO 1: Autenticação (4 cards)

| Jira Key | Código | Título | Tipo |
|----------|--------|--------|------|
| WT-893 | AUTH-001 | Tela de Login | Frontend |
| WT-894 | AUTH-002 | Integração WorkOS SSO | Integração |
| WT-895 | AUTH-003 | Middleware de Autenticação | Backend |
| WT-896 | AUTH-004 | Gestão de Sessão JWT | Backend |

## 2.2 ÉPICO 2: Wizard Conversacional (8 cards)

| Jira Key | Código | Título | Tipo |
|----------|--------|--------|------|
| WT-897 | WIZ-001 | Interface Chat Conversacional | Frontend |
| WT-898 | WIZ-002 | Orquestrador de Intenções | AI |
| WT-899 | WIZ-003 | Serviço de Insights de Mercado | Backend |
| WT-900 | WIZ-004 | Gerador de Job Description | AI |
| WT-901 | WIZ-005 | Salvamento de Rascunho | Backend |
| WT-902 | WIZ-006 | Sugestões Clicáveis | Frontend |
| WT-903 | WIZ-007 | Preview da Vaga (Live) | Full-Stack |
| WT-904 | WIZ-008 | Formulário de Edição Completa | Full-Stack |

> **Nota:** WIZ-009 a WIZ-013 são cards **novos** a serem criados.

## 2.3 ÉPICO 3: Busca e Mapeamento (6 cards)

| Jira Key | Código | Título | Tipo |
|----------|--------|--------|------|
| WT-905 | MAP-001 | Lista de Candidatos da Base | Frontend |
| WT-906 | MAP-002 | Busca Semântica com Gemini | Backend |
| WT-907 | MAP-003 | Filtros Avançados | Full-Stack |
| WT-908 | MAP-004 | Adicionar Candidato à Vaga | Full-Stack |
| WT-909 | MAP-005 | Matching Score IA | AI |
| WT-910 | MAP-006 | Sugestões Proativas LIA | AI |

## 2.4 ÉPICO 4: Geração de Perguntas WSI (5 cards)

| Jira Key | Código | Título | Tipo |
|----------|--------|--------|------|
| WT-911 | WSI-001 | Motor de Geração de Perguntas | AI |
| WT-912 | WSI-002 | Blocos de Metodologia WSI | Backend |
| WT-913 | WSI-003 | Preview de Perguntas | Frontend |
| WT-914 | WSI-004 | Edição Manual de Perguntas | Full-Stack |
| WT-915 | WSI-005 | Aprovação de Perguntas | Full-Stack |

## 2.5 ÉPICO 5: Triagem WhatsApp (11 cards)

| Jira Key | Código | Título | Tipo |
|----------|--------|--------|------|
| WT-916 | TRI-001 | Configuração Twilio WhatsApp | Integração |
| WT-917 | TRI-002 | Envio de Mensagem Inicial | Backend |
| WT-918 | TRI-003 | Webhook de Recebimento | Backend |
| WT-919 | TRI-004 | Fluxo Conversacional LIA | AI |
| WT-920 | TRI-005 | Persistência de Conversa | Backend |
| WT-921 | TRI-006 | Tela de Monitoramento | Frontend |
| WT-922 | TRI-007 | Timeout e Retentativas | Backend |
| WT-923 | TRI-008 | Opt-out e Consentimento | Backend |
| WT-924 | TRI-009 | Templates de Mensagem | Full-Stack |
| WT-925 | TRI-010 | Envio em Massa (Bulk) | Full-Stack |
| WT-926 | TRI-011 | Pré-Qualificação Automatizada | Backend |

> **Nota:** TRI-012 é um card **novo** a ser criado.

## 2.6 ÉPICO 6: Score WSI (8 cards)

| Jira Key | Código | Título | Tipo |
|----------|--------|--------|------|
| WT-927 | SCO-001 | Cálculo de Score WSI | AI |
| WT-928 | SCO-002 | Modelo Big Five Comportamental | AI |
| WT-929 | SCO-003 | Avaliação Bloom/Dreyfus | AI |
| WT-930 | SCO-004 | Parecer Textual LIA | AI |
| WT-931 | SCO-005 | Visualização de Score | Frontend |
| WT-932 | SCO-006 | Breakdown de Dimensões | Frontend |
| WT-933 | SCO-007 | Comparação entre Candidatos | Full-Stack |
| WT-934 | SCO-008 | Histórico de Scores | Backend |

## 2.7 ÉPICO 7: Gates de Aprovação (7 cards)

| Jira Key | Código | Título | Tipo |
|----------|--------|--------|------|
| WT-935 | GAT-001 | Gate 1: Aprovar Mapeados | Full-Stack |
| WT-936 | GAT-002 | Gate 2: Aprovar Triados | Full-Stack |
| WT-937 | GAT-003 | Modal de Reprovação | Frontend |
| WT-938 | GAT-004 | Geração de Feedback LIA | AI |
| WT-939 | GAT-005 | Envio de Feedback | Backend |
| WT-940 | GAT-006 | Aprovação em Massa | Full-Stack |
| WT-941 | GAT-007 | Histórico de Decisões | Backend |

## 2.8 ÉPICO 8: Templates de Comunicação (7 cards)

| Jira Key | Código | Título | Tipo |
|----------|--------|--------|------|
| WT-942 | TPL-001 | Template de Abordagem Inicial | Full-Stack |
| WT-943 | TPL-002 | Template de Agendamento | Full-Stack |
| WT-944 | TPL-003 | Template de Confirmação | Full-Stack |
| WT-945 | TPL-004 | Template Pós-Entrevista | Full-Stack |
| WT-946 | TPL-005 | Editor de Templates | Frontend |
| WT-947 | TPL-006 | Variáveis Dinâmicas | Backend |
| WT-948 | TPL-007 | Preview de Template | Frontend |

## 2.9 ÉPICO 9: Agendamento Automático (8 cards)

| Jira Key | Código | Título | Tipo |
|----------|--------|--------|------|
| WT-949 | AGE-001 | Integração Microsoft Graph | Integração |
| WT-950 | AGE-002 | Consulta de Disponibilidade | Backend |
| WT-951 | AGE-003 | Sugestão de Horários | AI |
| WT-952 | AGE-004 | Criação de Evento Teams | Backend |
| WT-953 | AGE-005 | Confirmação do Candidato | Full-Stack |
| WT-954 | AGE-006 | Reagendamento | Full-Stack |
| WT-955 | AGE-007 | Lembretes Automáticos | Backend |
| WT-956 | AGE-008 | Cancelamento | Full-Stack |

## 2.10 ÉPICO 10: Notificações (6 cards)

| Jira Key | Código | Título | Tipo |
|----------|--------|--------|------|
| WT-957 | NOT-001 | Sistema de Notificações Bell | Full-Stack |
| WT-958 | NOT-002 | Notificações em Tempo Real | Backend |
| WT-959 | NOT-003 | Preferências de Notificação | Full-Stack |
| WT-960 | NOT-004 | Notificações Push | Backend |
| WT-961 | NOT-005 | Histórico de Notificações | Full-Stack |
| WT-962 | NOT-006 | Badge de Não Lidas | Frontend |

## 2.11 ÉPICO 11: Kanban e Tabela (18 cards)

| Jira Key | Código | Título | Tipo |
|----------|--------|--------|------|
| WT-963 | KAN-001 | Estrutura do Kanban 4 Colunas | Frontend |
| WT-964 | KAN-002 | Card de Candidato | Frontend |
| WT-965 | KAN-003 | Drag-and-Drop entre Colunas | Frontend |
| WT-966 | KAN-004 | Menu de Ações do Card | Frontend |
| WT-967 | KAN-005 | Ícones de Ação Rápida | Frontend ⚠️ **OBSOLETO** |
| WT-968 | KAN-006 | Badge de Score WSI | Frontend |
| WT-969 | KAN-007 | Filtro por Status | Frontend |
| WT-970 | KAN-008 | Busca de Candidato | Frontend |
| WT-971 | TAB-001 | Tabela de Candidatos | Frontend |
| WT-972 | TAB-002 | Colunas Ordenáveis | Frontend |
| WT-973 | TAB-003 | Seleção Múltipla | Frontend |
| WT-974 | TAB-004 | Paginação | Frontend |
| WT-975 | TAB-005 | Ações em Massa (Barra) | Frontend |
| WT-976 | PRV-001 | Preview Lateral do Candidato | Frontend |
| WT-977 | PRV-002 | Tab Perfil | Frontend |
| WT-978 | PRV-003 | Tab Atividades | Frontend |
| WT-979 | PRV-004 | Tab Arquivos | Frontend |
| WT-980 | PRV-005 | Tab Parecer LIA | Frontend |

> **Nota:** KAN-009 e KAN-010 são cards **novos** a serem criados.

## 2.12 Vagas (8 cards)

| Jira Key | Código | Título | Tipo |
|----------|--------|--------|------|
| WT-981 | VAG-001 | Tabela de Vagas | Frontend |
| WT-982 | VAG-002 | Tabs de Status | Frontend |
| WT-983 | VAG-003 | Menu de Ações da Vaga | Frontend |
| WT-984 | VAG-004 | Pausar/Ativar Vaga | Full-Stack |
| WT-985 | VAG-005 | Duplicar Vaga | Full-Stack |
| WT-986 | VAG-006 | Arquivar Vaga | Full-Stack |
| WT-987 | VAG-007 | Contador de Candidatos | Frontend |
| WT-988 | VAG-008 | Navegação Vaga → Kanban | Frontend |

## 2.13 ÉPICO 14: Integrações Twilio (4 cards)

| Jira Key | Código | Título | Tipo |
|----------|--------|--------|------|
| WT-989 | INT-TWI-001 | Configurar Twilio Account | Integração |
| WT-990 | INT-TWI-002 | Sandbox WhatsApp | Backend |
| WT-991 | INT-TWI-003 | Número de Produção | Integração |
| WT-992 | INT-TWI-004 | Webhook de Mensagens | Backend |

> **Nota:** INT-TWI-005 a INT-TWI-007 são cards **novos** a serem criados.

---

# 3. 51 CARDS NOVOS PARA CRIAR

Estes cards estão definidos no documento `lia-mvp-cards-jira.md` mas **não existem** no Jira. Precisam ser criados.

## 3.1 ÉPICO 2: Wizard Avançado (5 cards)

| Código | Título | Tipo | Descrição |
|--------|--------|------|-----------|
| WIZ-009 | Skip Calibração Conversacional | Full-Stack | Permite pular a calibração de competências durante a criação de vaga |
| WIZ-010 | Estágio de Salário Interativo | Frontend | Interface para definir faixa salarial com análise de mercado |
| WIZ-011 | Estágio de Competências | Frontend | Seleção e priorização de competências para a vaga |
| WIZ-012 | Estágio de Perguntas WSI | Frontend | Revisão e aprovação das perguntas de triagem geradas |
| WIZ-013 | Quality Gates WSI | Backend | Validação de qualidade das perguntas e competências antes de salvar |

## 3.2 ÉPICO 5: Triagem (1 card)

| Código | Título | Tipo | Descrição |
|--------|--------|------|-----------|
| TRI-012 | Serviço de Pré-Qualificação | Backend | Serviço que faz pré-qualificação automática de candidatos antes da triagem completa |

## 3.3 ÉPICO 11: Kanban (2 cards)

| Código | Título | Tipo | Descrição |
|--------|--------|------|-----------|
| KAN-009 | Componentes Kanban Modulares | Frontend | Componentes reutilizáveis para diferentes visualizações do kanban |
| KAN-010 | Feedback Implícito em Transições | Backend | Captura feedback do recrutador quando move cards entre colunas |

## 3.4 ÉPICO 14: Integrações Twilio (3 cards)

| Código | Título | Tipo | Descrição |
|--------|--------|------|-----------|
| INT-TWI-005 | Templates Aprovados Meta | Integração | Templates de mensagem aprovados pelo Meta/WhatsApp Business |
| INT-TWI-006 | Status Delivery Reports | Backend | Relatórios de status de entrega das mensagens WhatsApp |
| INT-TWI-007 | Rate Limiting e Filas | Backend | Controle de taxa de envio e filas para mensagens em massa |

## 3.5 ÉPICO 14: Integrações Microsoft Graph (4 cards)

| Código | Título | Tipo | Descrição |
|--------|--------|------|-----------|
| INT-MSG-002 | OAuth Flow Microsoft | Backend | Fluxo OAuth para autenticação com Microsoft 365 |
| INT-MSG-003 | Calendar API | Backend | Integração com API de calendário do Microsoft 365 |
| INT-MSG-004 | Teams Meeting API | Backend | Criação de reuniões do Teams via API |
| INT-MSG-006 | Token Refresh | Backend | Renovação automática de tokens OAuth expirados |

## 3.6 ÉPICO 14: Integrações LLM (9 cards)

| Código | Título | Tipo | Descrição |
|--------|--------|------|-----------|
| INT-LLM-001 | Cliente Anthropic Claude | Backend | Cliente SDK para chamadas à API Claude (Anthropic) |
| INT-LLM-002 | Cliente Google Gemini | Backend | Cliente SDK para chamadas à API Gemini (Google) |
| INT-LLM-003 | Router de Modelos | Backend | Roteador inteligente entre diferentes modelos LLM |
| INT-LLM-004 | Fallback entre Modelos | Backend | Sistema de fallback quando um modelo falha |
| INT-LLM-005 | Gestão de Prompts | Backend | Sistema de templates e versionamento de prompts |
| INT-LLM-006 | Cache de Respostas | Backend | Cache de respostas LLM para economia de custos |
| INT-LLM-007 | Monitoramento de Custos | Backend | Dashboard de custos por modelo e por uso |
| INT-LLM-008 | Rate Limiting LLM | Backend | Controle de taxa de chamadas às APIs LLM |
| INT-LLM-009 | Logging de Conversas | Backend | Registro de todas as conversas com LLMs |

## 3.7 ÉPICO 14: Integrações WorkOS (7 cards)

| Código | Título | Tipo | Descrição |
|--------|--------|------|-----------|
| INT-WOS-001 | Configurar WorkOS Account | Integração | Setup inicial da conta WorkOS |
| INT-WOS-002 | SSO SAML/OIDC | Backend | Single Sign-On via SAML ou OIDC |
| INT-WOS-003 | Directory Sync SCIM | Backend | Sincronização de diretório de usuários |
| INT-WOS-004 | MFA Enforcement | Backend | Exigência de autenticação multifator |
| INT-WOS-005 | User Management SDK | Backend | SDK para gestão de usuários |
| INT-WOS-006 | Webhook de Eventos | Backend | Webhooks para eventos de autenticação |
| INT-WOS-007 | Admin Portal | Frontend | Portal administrativo para gestão de SSO |

## 3.8 ÉPICO 14: Integrações Apify (3 cards)

| Código | Título | Tipo | Descrição |
|--------|--------|------|-----------|
| INT-APY-001 | Configurar Apify Account | Integração | Setup inicial da conta Apify |
| INT-APY-002 | LinkedIn Scraper Actor | Backend | Actor para busca de candidatos no LinkedIn |
| INT-APY-003 | Integração com Sourcing Agent | AI | Conexão do scraper com agente de sourcing LIA |

## 3.9 ÉPICO 12: JD e Wizard Avançado (5 cards)

| Código | Título | Tipo | Descrição |
|--------|--------|------|-----------|
| JD-001 | Preview de JD com Sugestões LIA | Frontend | Preview do Job Description com sugestões da LIA |
| JD-002 | JD Completo para Publicação | Frontend | Geração do JD completo formatado para publicação |
| JDW-001 | Interação com Sugestões LIA | Backend | Backend para processar interações com sugestões |
| JDW-002 | Análise de Compensação de Mercado | Backend | Análise salarial baseada em dados de mercado |
| JDW-003 | Insights de Mercado para Vagas | Backend | Insights sobre disponibilidade de talentos |

## 3.10 ÉPICO 13: Configurações Avançadas (6 cards)

| Código | Título | Tipo | Descrição |
|--------|--------|------|-----------|
| CFG-001 | LIA Field Toggles | Frontend | Toggles para habilitar/desabilitar funcionalidades LIA por campo |
| CFG-002 | Verificação de Completude | Backend | Validação de completude de dados antes de ações LIA |
| CFG-003 | Configuração de Jornada | Frontend | Configuração do fluxo/jornada do candidato |
| CFG-004 | Hub de Comunicação | Frontend | Central de configuração de canais de comunicação |
| CFG-005 | Dados da Empresa para LIA | Frontend | Formulário de dados da empresa para contexto LIA |
| IMP-001 | Importação Inteligente | Frontend | Importação de dados via CSV/Excel com mapeamento inteligente |

## 3.11 ÉPICO 15: Agentes IA Especializados (6 cards)

| Código | Título | Tipo | Descrição |
|--------|--------|------|-----------|
| AGT-001 | Agente Avaliador WSI | AI | Agente especializado em avaliação WSI de candidatos |
| AGT-002 | Agente de Triagem Curricular | AI | Agente para análise e triagem de currículos |
| AGT-003 | Agente de Agendamento | AI | Agente para agendamento inteligente de entrevistas |
| AGT-004 | Orquestrador de Pipeline Chat | AI | Agente orquestrador do fluxo de chat com candidatos |
| DAT-001 | Sistema de Solicitação de Dados | Frontend | Interface para solicitar dados adicionais de candidatos |
| ENT-001 | Análise de Transcrição | Backend | Análise de transcrições de entrevistas/conversas |

---

# RESUMO FINAL

| Categoria | Quantidade | Ação |
|-----------|------------|------|
| Cards para EXCLUSÃO | 130 | Avaliar e excluir/arquivar no Jira |
| Cards SINCRONIZADOS | 100 | Manter (opcionalmente atualizar descrições) |
| Cards NOVOS | 51 | Criar no Jira |

---

**Documento gerado em:** 02 de Fevereiro de 2026  
**Baseado em:** `docs/lia-mvp-cards-jira.md` (versão 2.1)
