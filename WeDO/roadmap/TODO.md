# TODO - Plataforma LIA WedoTalent

> Documento de referência para pendências e melhorias futuras

---

## 1. Análise de Melhores Práticas de IA

### ✅ O que já fizemos bem

#### Arquitetura Multi-Agente
- [x] Orquestrador central com 11 agentes especializados (LangGraph + Claude Sonnet 4.5)
- [x] Separação clara de responsabilidades entre agentes
- [x] Estado persistente entre interações (workflow_data)
- [x] Loop detection para evitar repetição infinita de perguntas

#### Governança e Ética de IA
- [x] Framework de governança com níveis de autonomia configuráveis por vaga
- [x] Regras anti-viés implementadas no sistema de scoring
- [x] Audit logs para rastreabilidade de decisões de IA
- [x] Human-in-the-loop para decisões críticas (aprovação de vagas, movimentação de candidatos)

#### Conformidade LGPD
- [x] Opt-out tracking para candidatos
- [x] Quarentena de 90 dias após rejeição
- [x] Respeito a horários de envio de comunicação
- [x] Rate limiting por candidato
- [x] Consentimento explícito para processamento de dados

#### Scoring e Avaliação
- [x] Sistema WSI (Work Sample Interview) com metodologia científica
- [x] Integração de Bloom's Taxonomy, Dreyfus Model, Big Five
- [x] Pesos universais para garantir fairness entre candidatos
- [x] Nota LIA Geral como score composto transparente

#### Explicabilidade
- [x] Reasoning armazenado em audit_logs com critérios usados/ignorados
- [x] Confidence score em cada decisão de IA
- [x] Context pills e quick actions explicando ações da IA

#### Proatividade Inteligente
- [x] Sistema de alertas proativos multi-canal (CHAT, BELL, TEAMS, EMAIL, WHATSAPP)
- [x] Daily briefings configuráveis
- [x] Notificações de SLA e candidatos parados

### ❌ O que falta implementar

#### Explicabilidade Avançada
- [ ] Dashboard de explicabilidade para recrutadores (por que a LIA tomou cada decisão)
- [ ] Visualização gráfica de pesos do scoring
- [ ] Comparativo visual de candidatos com destaque nos diferenciais
- [ ] "Why this score?" button em cada nota de candidato

#### Fairness e Anti-Bias
- [ ] Relatório de diversidade por vaga (gênero, idade, região)
- [ ] Alertas automáticos de possível viés em funis
- [ ] A/B testing de critérios para validar neutralidade
- [ ] Anonymized screening mode (ocultar nome, foto, idade)

#### Feedback Loop
- [ ] Captura sistemática de feedback dos recrutadores sobre recomendações
- [ ] Re-treinamento de prompts baseado em decisões aceitas/rejeitadas
- [ ] Métricas de precisão da IA (recomendações aceitas vs rejeitadas)
- [ ] Correlation analysis: score LIA vs contratação real

#### Segurança de IA
- [ ] Rate limiting por API key de IA (evitar custos explosivos)
- [ ] Fallback automático para modelo secundário (Gemini) quando Claude falhar
- [ ] Guardrails para respostas (filtro de conteúdo inapropriado)
- [ ] Prompt injection protection

#### Otimizações de Performance
- [ ] Cache de embeddings para busca semântica
- [ ] Batch processing para triagem em massa
- [ ] Async processing para operações pesadas (CV parsing, scoring)
- [ ] Queue system para alta demanda

#### Monitoramento e Observabilidade
- [ ] Dashboard de uso de tokens e custos
- [ ] Alertas de latência de resposta da IA
- [ ] Logs estruturados para debugging de conversas
- [ ] Métricas de qualidade de resposta (user satisfaction)

#### Calibração Contínua
- [ ] Sistema de calibração periódica por recrutador
- [ ] Ajuste automático de pesos baseado em histórico
- [ ] Benchmarking de vagas similares
- [ ] Sugestões proativas de ajuste de critérios

#### Model Routing (Roteamento Inteligente de Modelos)
- [ ] Implementar seleção automática de modelo baseado na tarefa
- [ ] Configuração de modelo padrão por cliente (na Plataforma de Gestão)
- [ ] Fallback automático quando modelo principal falhar
- [ ] Monitoramento de custos por modelo/cliente

**Como deve funcionar:**

| Critério | Modelo Rápido/Barato | Modelo Avançado |
|----------|---------------------|-----------------|
| Complexidade | Perguntas simples, triagem básica | Análise profunda, geração de JD |
| Custo | Gemini Flash, Claude Haiku | Claude Sonnet/Opus |
| Velocidade | Respostas instantâneas | Pode demorar mais |
| Qualidade | Boa o suficiente | Máxima precisão |

**Decisão de Arquitetura (Recomendada):**

1. **Backend (Automático)**: Sistema escolhe modelo baseado na tarefa
   - Chat simples → Modelo rápido
   - Scoring/Análise → Modelo avançado
   - CV Parsing → Modelo com boa extração

2. **Plataforma de Gestão (Configurável por CS/Comercial)**:
   - Modelo padrão por cliente
   - Limite mensal de tokens
   - Alertas de custo (ex: 80% do limite)
   - Override para casos especiais

3. **Interface do Recrutador (Transparente)**:
   - Não mostra qual modelo está sendo usado
   - Zero fricção - recrutador só quer resultados
   - Opcionalmente: toggle "Análise Profunda" para forçar modelo avançado

**Exemplo de configuração por cliente:**
```
Empresa: XPTO Ltda
├── Plano: Profissional
├── Modelo padrão: Claude Sonnet
├── Modelo fallback: Gemini Pro
├── Limite mensal: 500.000 tokens
├── Alertas de custo: Sim (80%)
└── Modelo para scoring: Claude Opus (override)
```

---

## 2. Plataforma de Gestão de Clientes (Interno)

### Objetivo
Criar uma plataforma interna para os times de Desenvolvimento, Comercial e CS gerenciarem:

### Funcionalidades Necessárias

#### Gestão de Empresas/Clientes
- [ ] CRUD completo de empresas clientes
- [ ] Histórico de interações e suporte
- [ ] Status do cliente (prospect, trial, ativo, churn)
- [ ] Notas e observações por cliente

#### Gestão de Licenças
- [ ] Tipos de licença (trial, básico, profissional, enterprise)
- [ ] Controle de validade e renovação
- [ ] Limites por plano (vagas, usuários, candidatos)
- [ ] Alertas de expiração

#### Gestão de Usuários por Cliente
- [ ] CRUD de usuários por empresa
- [ ] Roles e permissões (admin, recrutador, gestor, viewer)
- [ ] Ativação/desativação de acessos
- [ ] Logs de acesso

#### Gestão de Implementações
- [ ] Checklist de onboarding por cliente
- [ ] Status de integração ATS
- [ ] Configurações específicas do cliente
- [ ] Timeline de implementação

#### Dashboards Internos
- [ ] Métricas de uso por cliente
- [ ] Health score de clientes
- [ ] Funil de vendas (para comercial)
- [ ] Tickets de suporte (para CS)

### Considerações Técnicas
- Autenticação separada (usuários internos WedoTalent)
- Acesso restrito por role interno
- Auditoria de ações (quem fez o quê)
- Possível integração com CRM existente

---

## 3. Bugs e Correções Pendentes

### Página de Favoritos (Funil de Talentos)
- [ ] **Ícone de Visualizar**: Não funciona ou está com comportamento incorreto
- [ ] **Ícone LIA**: Ação de LIA não está funcionando nos favoritos
- [ ] Verificar se a rota de favoritos está carregando os dados corretos

### Preview de Vaga (Roteiro e Visão Geral)

#### Tab: Roteiro de Triagem
- [ ] **Canais de Comunicação**: Dados hardcoded (WhatsApp ON, Chat Web ON, Email OFF) - integrar com backend
- [ ] **Configurações do Fluxo**: Dados hardcoded (Triagem em 5 min, Scoring por IA, etc.) - integrar com governance_rules
- [ ] **Métricas de Performance**: Dados hardcoded (89% taxa resposta, 4.8 NPS, etc.) - integrar com analytics real
- [ ] **Agendamento Automático**: Dados hardcoded (Microsoft Teams, slots, etc.) - integrar com calendar_config
- [ ] Verificar se todas as ações dos botões estão funcionando (Configurar, Ver Template, etc.)

#### Tab: Visão Geral
- [ ] **Próximas Ações/Timeline**: Dados podem estar incompletos ou hardcoded
- [ ] **Insights da LIA**: Cálculos baseados em dados reais vs estimativas genéricas
- [ ] **Métricas do Funil**: Verificar se os percentuais e tendências estão calculados corretamente
- [ ] **Orçamento**: Confirmar que budget e budget_used vêm do backend

#### Geral
- [ ] **Componente job-preview.tsx**: Arquivo de 1025 linhas existe mas NÃO está sendo usado - avaliar remoção ou refatoração
- [ ] **Refatoração jobs-page.tsx**: Arquivo com 5500+ linhas precisa ser modularizado
- [ ] Unificar tipos entre frontend (Job interface) e backend (JobVacancy interface)

---

## 4. Melhorias de UX/UI Pendentes

- [ ] Loading states mais informativos durante processamento de IA
- [ ] Skeleton loaders em todas as tabelas
- [ ] Feedback visual de ações em progresso
- [ ] Toasts de confirmação de ações

---

## 5. Integrações Pendentes

### ATS
- [ ] Testar sincronização bidirecional com Gupy
- [ ] Implementar webhook handlers para atualizações
- [ ] Mapear todos os campos entre sistemas

### Comunicação
- [ ] Templates de WhatsApp aprovados
- [ ] Integração com provedor de SMS
- [ ] Email transacional configurado

### Calendário
- [ ] Microsoft Graph para agendamento de entrevistas
- [ ] Google Calendar como alternativa

---

## Priorização Sugerida

### Alta Prioridade (Próximo Sprint)
1. Correções de bugs (Favoritos + Preview de Triagem)
2. Explicabilidade básica (Why this score?)
3. Dashboard de custos de IA

### Média Prioridade (Próximos 2 Sprints)
1. Plataforma de Gestão de Clientes (MVP)
2. Feedback loop básico
3. Relatório de diversidade

### Baixa Prioridade (Backlog)
1. A/B testing de critérios
2. Anonymized screening
3. Cache de embeddings

---

*Última atualização: 02/12/2025*
