# Análise Reunião de Alinhamento — 06/02/2026

**Participantes:** Paulo Moraes + Anderson Victhor  
**Duração:** 1h32min  
**Data da Análise:** 07/02/2026  
**Documento Base:** `docs/lia-mvp-cards-jira.md` (v2.3)

---

## SUMÁRIO EXECUTIVO

| Métrica | Quantidade |
|---------|-----------|
| Cards a Ajustar | ~16 |
| Cards Novos a Criar | 13 (INT-ALT-001 consolidado com TRI-014) |
| Cards a Remover/Obsoletizar | 2 (WSI-004, KAN-005) |
| Cards a Adiar (Pós-MVP) | 3 (INT-LLM-001, INT-LLM-003, INT-LLM-004) |
| Cards a Refatorar | 1 (TRI-006) |
| Épicos Impactados | 11 de 15 |
| Épicos Adiados Inteiros | 3 (Épico 10 parcial, 12, 13) |

---

## PARTE 1: ANÁLISE POR ÉPICO — DECISÕES × CARDS × IMPACTOS

---

### ÉPICO 1: Autenticação (EPIC-AUTH) — 4→6 cards

**Status Reunião:** Em andamento, decisões importantes tomadas

#### Decisões da Reunião:
1. Adotar **subdomínio por empresa** (ex: `itau.wedotalent.cc`) — habilita white label
2. WorkOS SSO com JWT encaminhado
3. Wildcard SSL + Google Cloud necessários

#### CARD AUTH-001 — AJUSTAR
**Título Atual:** Login com WorkOS SSO  
**Ajuste:** Adicionar customização de logo/branding por tenant na tela de login

| Impacto | Detalhes |
|---------|---------|
| **UI/Frontend** | Tela de login dinâmica: campo para logo da empresa, cores customizáveis, logo carregado por subdomínio. Componente `login-page.tsx` precisa aceitar props de branding |
| **Backend** | Endpoint `GET /api/v1/tenants/{subdomain}/branding` para retornar logo_url, primary_color, company_name. Tabela `tenant_branding` |
| **AI/LLM** | Nenhum |
| **Protótipo Replit** | Atualizar `plataforma-lia/src/components/pages/login-page.tsx` e `plataforma-lia/src/components/login-page.tsx` com suporte a branding dinâmico |

#### NOVO CARD: AUTH-005 — Wildcard SSL + Google Cloud Multi-Brand

```yaml
Titulo: [INFRA] Configuração Wildcard SSL + Google Cloud para Multi-Brand/Subdomínio
Tipo: Infraestrutura
Sprint: 1
Pontos: 5
Prioridade: Crítica
Epic: EPIC-AUTH
Status: 📋 A Criar no Jira

Descricao: |
  Configurar certificado SSL wildcard (*.wedotalent.cc) e DNS no Google Cloud
  para suportar subdomínios por empresa (ex: itau.wedotalent.cc, ambev.wedotalent.cc).
  Isso habilita white label e customização de marca por tenant.

Historia de Usuario: |
  Como administrador da plataforma, eu quero que cada empresa cliente
  tenha seu próprio subdomínio para oferecer uma experiência white label.

Regras de Negocio:
  1. Wildcard SSL para *.wedotalent.cc
  2. DNS configurado no Google Cloud
  3. Nginx/proxy reverso roteando por subdomínio → tenant_id
  4. Redirecionamento de www e root para subdomínio padrão
  5. Suporte futuro a domínio customizado (ex: rh.itau.com.br)

Requisitos Tecnicos:
  Backend:
    - Middleware de resolução de tenant por subdomínio
    - Tabela tenants: id, subdomain, company_name, logo_url, primary_color, custom_domain
    - Nginx config para wildcard routing
  Frontend:
    - Detecção de subdomínio no client-side
    - Carregamento dinâmico de branding

DoD:
  - [ ] Wildcard SSL emitido e configurado
  - [ ] DNS wildcard configurado no Google Cloud
  - [ ] Resolução de tenant por subdomínio funcionando
  - [ ] Fallback para tenant padrão se subdomínio não encontrado
  - [ ] Teste com 2+ subdomínios

Criterios de Aceitacao:
  - [ ] itau.wedotalent.cc resolve para tenant correto
  - [ ] SSL válido em qualquer subdomínio
  - [ ] Logo e branding carregam dinamicamente
```

| Impacto | Detalhes |
|---------|---------|
| **UI/Frontend** | Middleware de detecção de subdomínio, theme provider dinâmico |
| **Backend** | Middleware tenant resolver, tabela `tenants`, configuração Nginx |
| **AI/LLM** | Nenhum |
| **Protótipo Replit** | Criar simulação de multi-tenant com query param `?tenant=itau` para demonstrar branding dinâmico |

#### NOVO CARD: AUTH-006 — Revisão Final de Design pelo Lucas

```yaml
Titulo: [DESIGN] Revisão Final de Design/Marca pelo Lucas
Tipo: Design
Sprint: 1
Pontos: 3
Prioridade: Alta
Epic: EPIC-AUTH
Status: 📋 A Criar no Jira

Descricao: |
  Lucas faz revisão final dos assets visuais: logo atualizado da WeDo Talent,
  marca da LIA, ícones, paleta de cores, e aplica nas telas de login/onboarding.

Historia de Usuario: |
  Como stakeholder, eu quero que a identidade visual da plataforma
  esteja atualizada e consistente antes do lançamento.

Regras de Negocio:
  1. Logo WeDo Talent atualizado
  2. Logo LIA atualizado
  3. Paleta de cores validada
  4. Assets para tela de login/onboarding
  5. Guia de marca para white label

DoD:
  - [ ] Assets entregues pelo Lucas
  - [ ] Logo aplicado na tela de login
  - [ ] Favicon atualizado
  - [ ] Email templates com marca atualizada
```

| Impacto | Detalhes |
|---------|---------|
| **UI/Frontend** | Substituir assets de logo/marca em todo o app |
| **Backend** | Nenhum |
| **AI/LLM** | Nenhum |
| **Protótipo Replit** | Atualizar logos e assets quando Lucas entregar |

---

### ÉPICO 2: Wizard Conversacional (EPIC-WIZARD) — 13→14 cards

**Status Reunião:** Passaram rápido, foco em WSI dentro do wizard

#### Decisões da Reunião:
1. Estágio de perguntas WSI (WIZ-012) é parte de edição da vaga
2. Quality Gates WSI (WIZ-013) faz parte do wizard
3. Geração de perguntas WSI é Épico 4 (separado)
4. Revisão metodológica com André fica para quando tiver screening + respostas funcionando

#### NOVO CARD: WIZ-014 — Revisão Metodologia Wizard com André

```yaml
Titulo: [PROCESSO] Revisão de Metodologia Wizard Ponta a Ponta com André
Tipo: Processo/Validação
Sprint: Pós-MVP (quando screening WSI estiver funcional)
Pontos: 5
Prioridade: Media
Epic: EPIC-WIZARD
Status: 📋 A Criar no Jira

Descricao: |
  Sessão de revisão com André para validar toda a metodologia WSI
  implementada no wizard: geração de perguntas, condução de triagem,
  avaliação de respostas, e cálculo de scores.

Historia de Usuario: |
  Como responsável pela metodologia, André quer validar que a implementação
  técnica preserva a integridade do WSI.

Regras de Negocio:
  1. Só pode acontecer quando: geração de perguntas + triagem + respostas estiverem funcionando
  2. André valida: sequência de perguntas, critérios de avaliação, pesos
  3. Resultado: documento de validação + ajustes necessários
  4. Pode gerar novos cards de correção

DoD:
  - [ ] Sessão realizada com André
  - [ ] Documento de validação criado
  - [ ] Ajustes identificados registrados como cards
```

| Impacto | Detalhes |
|---------|---------|
| **UI/Frontend** | Nenhum direto (possíveis ajustes pós-validação) |
| **Backend** | Nenhum direto (possíveis ajustes pós-validação) |
| **AI/LLM** | Possíveis ajustes nos prompts de geração WSI |
| **Protótipo Replit** | Ter demo funcional para André validar |

---

### ÉPICO 3: Busca e Mapeamento (EPIC-MAPPING) — 6+7 cards

**Status Reunião:** Maioria feita, filtros avançados com dificuldade técnica

#### Decisões da Reunião:
1. Lista de candidatos, busca semântica, matching score IA, sugestões proativas: **OK**
2. MAP-003 (Filtros avançados): dificuldade com filtros de shortlisted/placement, Felipe quase termina
3. Adicionar candidato à vaga: feito

#### NOVO CARD: MAP-007* — Revisão de Qualidade de Busca com André

> ⚠️ **CONFLITO DE NUMERAÇÃO**: Já existem MAP-007 a MAP-013 no documento `epic-wdt-talent-funnel.md` (WDT Talent Funnel cards). Este card de revisão com André precisa de numeração diferente, sugerimos **MAP-014**.

```yaml
Titulo: [PROCESSO] Revisão de Qualidade de Busca com André
Codigo: MAP-014 (renumerar para evitar conflito com MAP-007 do WDT)
Tipo: Processo/Validação
Sprint: 3
Pontos: 3
Prioridade: Media
Epic: EPIC-MAPPING
Status: 📋 A Criar no Jira

Descricao: |
  André revisa a qualidade dos resultados de busca: relevância dos candidatos
  retornados, ordenação, e feedback sobre gaps.

DoD:
  - [ ] Sessão de revisão com André
  - [ ] Feedback documentado
  - [ ] Ajustes identificados
```

| Impacto | Detalhes |
|---------|---------|
| **UI/Frontend** | Nenhum direto |
| **Backend** | Possíveis ajustes em scoring/ranking após feedback |
| **AI/LLM** | Possíveis ajustes em embeddings/relevância |
| **Protótipo Replit** | Ter busca funcional para André testar |

---

### ÉPICO 4: Geração de Perguntas WSI (EPIC-WSI) — 5→5 cards (1 removido, 1 novo)

**Status Reunião:** Motor e blocos prontos, decisão crucial sobre edição

#### Decisões da Reunião:
1. Motor de geração: **pronto**
2. Blocos de metodologia: **pronto**
3. Preview: precisa trabalhar para funcionar com screening
4. **DECISÃO CRÍTICA**: Remover edição manual direta (WSI-004) — pode quebrar metodologia
5. Substituir por edição via prompt conversacional
6. Aprovação: em revisão (dúvida se recrutador aprova ou IA decide)

#### CARD WSI-004 — REMOVER ❌

**Título:** Edição Manual de Perguntas WSI  
**Ação:** REMOVER do backlog  
**Justificativa:** Edição manual direta poderia quebrar a integridade da metodologia WSI. A substituição é edição via prompt conversacional (WSI-006).

#### NOVO CARD: WSI-006 — Edição de Perguntas via Prompt Conversacional

```yaml
Titulo: [AI] Edição de Perguntas WSI via Prompt Conversacional
Tipo: Feature
Sprint: 2
Pontos: 8
Prioridade: Alta
Epic: EPIC-WSI
Status: 📋 A Criar no Jira

Descricao: |
  Em vez de editar perguntas WSI diretamente (o que quebraria a metodologia),
  o recrutador pede ajustes via chat com a LIA. Exemplo: "Não gostei da
  pergunta sobre liderança, quero algo mais voltado a gestão de conflitos".
  A LIA regenera as perguntas mantendo a integridade do WSI.

Historia de Usuario: |
  Como recrutador, eu quero pedir ajustes nas perguntas geradas sem
  quebrar a metodologia WSI, usando linguagem natural.

Regras de Negocio:
  1. Recrutador NÃO edita texto das perguntas diretamente
  2. Recrutador descreve o que quer mudar via chat
  3. LIA interpreta o pedido e regenera perguntas
  4. Novas perguntas mantêm conformidade WSI (blocos, pesos, sequência)
  5. Preview mostra antes/depois para comparação
  6. Recrutador pode aceitar ou pedir nova iteração
  7. Máximo 5 iterações de ajuste por bloco

Requisitos Tecnicos:
  Backend:
    - Endpoint: POST /api/v1/wsi/questions/adjust
    - Body: { job_id, block_id, adjustment_prompt, current_questions }
    - WSIQuestionAdjuster service (usa LLM para regenerar)
    - Validação de conformidade WSI pós-geração
  Frontend:
    - Chat integrado ao preview de perguntas
    - Diff view (antes/depois)
    - Botões "Aceitar" / "Pedir outro ajuste"

Configuracao LLM:
  Prompt de Ajuste:
    - System: "Você é especialista em metodologia WSI. Regenere as perguntas
      mantendo a estrutura do bloco {{block_name}} e os critérios de avaliação."
    - User: "O recrutador pediu: {{adjustment_prompt}}. Perguntas atuais:
      {{current_questions}}. Gere novas perguntas que atendam ao pedido
      sem comprometer a integridade metodológica."
  Modelo: gemini-2.5-flash (rápido para iterações)
  Temperature: 0.7

Design & Componentes:
  Componentes Existentes:
    - Chat sidebar (reutilizar)
    - WSIQuestionsPanel
  Novos Componentes:
    - QuestionAdjustmentChat - chat focado em ajustes
    - QuestionDiffView - antes/depois das perguntas
    - AdjustmentCounter - "Ajuste 2 de 5"
  Design Tokens:
    Before: --lia-text-tertiary (#6B7280)
    After: --wedo-cyan (#60BED1)
    Accepted: --wedo-green (#22C55E)

DoD:
  - [ ] Chat de ajuste funcional
  - [ ] LLM regenera perguntas mantendo WSI
  - [ ] Diff view mostra antes/depois
  - [ ] Validação de conformidade WSI
  - [ ] Máximo de iterações respeitado

Criterios de Aceitacao:
  - [ ] Recrutador pede ajuste em linguagem natural
  - [ ] Perguntas regeneradas mantêm conformidade WSI
  - [ ] Preview antes/depois funciona
  - [ ] Aceitação/rejeição funciona
```

| Impacto | Detalhes |
|---------|---------|
| **UI/Frontend** | Novo componente de chat de ajustes integrado ao WSIQuestionsPanel. Diff view. Arquivos: `WSIQuestionsStage.tsx`, `WSIQuestionsPanel.tsx` |
| **Backend** | Novo endpoint `/api/v1/wsi/questions/adjust`, novo service `WSIQuestionAdjuster`, validação de conformidade WSI |
| **AI/LLM** | Novo prompt de ajuste com contexto de bloco WSI + pedido do recrutador. Gemini 2.5 Flash |
| **Protótipo Replit** | Criar componente `QuestionAdjustmentChat.tsx`, integrar ao `WSIQuestionsStage.tsx` |

---

### ÉPICO 5: Triagem WhatsApp (EPIC-TRIAGEM) — 11→13 cards

**Status Reunião:** Parcialmente pronto, decisões importantes sobre Twilio

#### Decisões da Reunião:
1. **Twilio ficou sem sentido** — número precisa estar homologado, pesquisar alternativas (Tudu, Zenvia, Slickflow). ⚠️ **DISCLAIMER: A pesquisa sobre Twilio e alternativas é de responsabilidade do Paulo Moraes.**
2. Envio de mensagem, webhook, fluxo LIA, persistência: **funcionam**
3. **TRI-006 refatorar**: tela de monitoramento em tempo real NÃO faz sentido → transcrição completa da triagem no card de evento existente na tab Activities do candidato + acesso via ícone no card Kanban e tabela de candidatos
4. Timeout existe (fixo), retentativas: não existe, precisa fazer
5. Templates Meta: sincronização complexa
6. Pré-qualificação automatizada: precisa definir autonomia da LIA
7. **Novo**: candidato poder reportar problemas (LIA alucinando → digita código → incidente para time WeDo Talent, NÃO recrutador; LIA avisa procedimento pós-LGPD; SLA 24h)

#### CARD TRI-001 — AJUSTAR
**Título:** Integração WhatsApp para Triagem  
**Ajuste:** Reavaliar Twilio, documentar pesquisa de alternativas (Tudu, Zenvia, Slickflow)

> ⚠️ **DISCLAIMER:** A pesquisa e avaliação sobre Twilio e suas alternativas é de responsabilidade exclusiva do **Paulo Moraes**.

| Impacto | Detalhes |
|---------|---------|
| **UI/Frontend** | Nenhum imediato |
| **Backend** | Abstração de provider de WhatsApp (interface que suporta Twilio, Zenvia, etc.) |
| **AI/LLM** | Nenhum |
| **Protótipo Replit** | Nenhum (lógica de provider é produção) |

#### CARD TRI-006 — REFATORAR 🔄
**Título Atual:** Tela de Monitoramento de Triagem em Tempo Real  
**Novo Título:** Transcrição Completa da Triagem no Card de Atividade do Candidato  
**Justificativa:** Recrutador não precisa ver triagem em tempo real. O valor está em consultar a transcrição/histórico completo da triagem. A tab Activities do preview do candidato JÁ possui cards de atividades/eventos — o evento de triagem é um desses cards. Ao clicar nele, deve exibir a transcrição completa. NÃO criar aba "Conversas" separada.

| Impacto | Detalhes |
|---------|---------|
| **UI/Frontend** | NÃO criar aba "Conversas" nova. Enriquecer o card de evento de triagem existente na tab Activities do preview do candidato. Ao clicar no card do evento de triagem, expandir/abrir a transcrição completa (timeline de mensagens LIA↔candidato). Componentes: adaptar `CandidateActivityCard.tsx` (existente) para suportar expand com transcrição. Criar `ScreeningTranscriptView.tsx` para renderizar a timeline de mensagens. Adicionar ícone de acesso rápido à triagem no card do Kanban (`CandidateCard.tsx`) e na tabela de candidatos dentro da vaga. |
| **Backend** | Endpoint `GET /api/v1/candidates/{id}/screening-transcript?job_id={job_id}` retornando transcrição paginada da triagem |
| **AI/LLM** | Nenhum |
| **Protótipo Replit** | Adaptar card de atividade de triagem na tab Activities do `candidate-detail-sidebar.tsx` para expandir com transcrição. Criar `ScreeningTranscriptView.tsx`. Adicionar ícone de triagem no `CandidateCard.tsx` (Kanban) e na tabela de candidatos. |

#### CARD TRI-009 — AJUSTAR
**Título:** Templates de Mensagem WhatsApp  
**Ajuste:** Adicionar complexidade de sincronização com Meta. Templates precisam ser aprovados no Meta Business antes de usar.

| Impacto | Detalhes |
|---------|---------|
| **UI/Frontend** | Status de aprovação do template (pendente/aprovado/rejeitado pelo Meta) |
| **Backend** | Integração com Meta Business API para submissão e polling de status de templates |
| **AI/LLM** | Nenhum |

#### CARD TRI-011 — ADIAR ⏸️
**Título:** Pré-qualificação Automatizada  
**Ação:** Mover para discussão futura, precisa definição de autonomia da LIA

#### NOVO CARD: TRI-013 — Sistema de Reporte de Problemas pelo Candidato

```yaml
Titulo: [FULL-STACK] Sistema de Reporte de Problemas pelo Candidato
Tipo: Feature
Sprint: 3
Pontos: 5
Prioridade: Alta
Epic: EPIC-TRIAGEM
Status: 📋 A Criar no Jira

Descricao: |
  Sistema de reporte de problemas durante a triagem via WhatsApp.
  Ao iniciar a triagem (após aceite LGPD), a LIA informa proativamente
  o candidato sobre o procedimento de reporte: se houver qualquer problema,
  ele pode digitar palavras-chave (ex: "AJUDA", "#PROBLEMA") e receberá
  retorno em até 24 horas. Ao detectar a keyword, a LIA pausa a conversa,
  cria um incidente e notifica o time WeDo Talent (suporte/operações),
  NÃO o recrutador do cliente.

Historia de Usuario: |
  Como candidato em triagem via WhatsApp, eu quero ser informado no início
  da triagem sobre como reportar problemas, e se a IA não fizer sentido,
  eu quero poder digitar um código para que o time de suporte me ajude.

Regras de Negocio:
  1. LIA informa procedimento de reporte no INÍCIO da triagem (pós-LGPD):
     "Se a qualquer momento você tiver algum problema ou eu não fizer sentido,
     basta digitar AJUDA que nosso time será notificado e retornará em até 24 horas."
  2. Palavras-chave de escape: "AJUDA", "#PROBLEMA", "PARAR", "HUMANO"
  3. Ao detectar: pausar conversa LIA imediatamente
  4. Criar incidente com: candidato_id, job_id, timestamp, últimas 5 mensagens
  5. Notificar time WeDo Talent (suporte/operações) — NÃO o recrutador do cliente
  6. Candidato recebe: "Entendi! Nosso time foi notificado e entrará em contato em até 24 horas. 🙏"
  7. SLA de resposta: 24 horas (configurável por tenant)
  8. Time WeDo Talent pode: assumir conversa, resetar LIA, ou escalonar

Requisitos Tecnicos:
  Backend:
    - Detecção de palavras-chave no message handler
    - POST /api/v1/incidents (criação automática)
    - Modelo: screening_incidents (candidate_id, job_id, trigger_keyword, last_messages, status, assigned_to)
    - Notificação para time WeDo Talent (suporte) via email + push
    - Mensagem proativa da LIA no início da triagem (pós-LGPD) informando procedimento
  Frontend:
    - Painel de Incidentes para time WeDo Talent (lista + detalhes)
    - Badge no sidebar: "3 incidentes pendentes"
    - Click no incidente → ver conversa + opções

Design & Componentes:
  Novos Componentes:
    - IncidentsPanel - lista de incidentes (para time WeDo Talent)
    - IncidentDetailView - detalhes + conversa
    - IncidentBadge - contador no sidebar
  Design Tokens:
    Urgente: --electric-red (#de1c31)
    Pendente: --wedo-yellow (#EAB308)
    Resolvido: --wedo-green (#22C55E)

DoD:
  - [ ] LIA informa procedimento de reporte no início da triagem
  - [ ] Detecção de palavras-chave funcional
  - [ ] Incidente criado automaticamente
  - [ ] Notificação ao time WeDo Talent (NÃO ao recrutador)
  - [ ] Candidato recebe confirmação com prazo de 24h
  - [ ] Painel de incidentes funcional
  - [ ] Conversa pausada ao detectar problema
```

| Impacto | Detalhes |
|---------|---------|
| **UI/Frontend** | Novo painel de incidentes (para time WeDo Talent), badge no sidebar, view de detalhes. ~3 novos componentes |
| **Backend** | Tabela `screening_incidents`, endpoints de CRUD, detecção de keywords no message handler, notificação para time WeDo Talent (suporte), mensagem proativa da LIA pós-LGPD |
| **AI/LLM** | Detecção de intent "ajuda/problema" no classificador de mensagens + mensagem proativa de orientação no início |
| **Protótipo Replit** | Criar `IncidentsPanel.tsx`, `IncidentDetailView.tsx`, integrar ao sidebar |

#### NOVO CARD: TRI-014 — Pesquisa de Alternativas a Twilio

> ⚠️ **DISCLAIMER:** A pesquisa e avaliação sobre Twilio e suas alternativas é de responsabilidade exclusiva do **Paulo Moraes**.

```yaml
Titulo: [PESQUISA] Pesquisa de Alternativas a Twilio para Disparo WhatsApp
Tipo: Research/Spike
Sprint: 1
Pontos: 3
Prioridade: Crítica
Epic: EPIC-TRIAGEM
Status: 📋 A Criar no Jira
Responsavel: Paulo Moraes (pesquisa exclusiva)

Descricao: |
  ⚠️ DISCLAIMER: A pesquisa sobre Twilio e alternativas é de responsabilidade
  exclusiva do Paulo Moraes.

  Pesquisar e comparar alternativas ao Twilio para disparo de mensagens
  WhatsApp, priorizando soluções que aceitem número fornecido pelo cliente
  e tenham homologação simplificada no Brasil.

  Alternativas a avaliar:
  - Tudu (Brasil)
  - Zenvia (Brasil)
  - Slickflow
  - API oficial WhatsApp Business Cloud
  - Gupshup

Criterios de Avaliacao:
  1. Custo por mensagem
  2. Facilidade de homologação de número
  3. Suporte a templates Meta
  4. Webhook de status (entregue, lido)
  5. SDK/API quality
  6. Suporte Brasil
  7. SLA de entrega

DoD:
  - [ ] Tabela comparativa preenchida
  - [ ] POC com top 2 alternativas
  - [ ] Recomendação final documentada
```

| Impacto | Detalhes |
|---------|---------|
| **UI/Frontend** | Nenhum |
| **Backend** | Interface abstrata de WhatsApp provider + implementação do escolhido |
| **AI/LLM** | Nenhum |
| **Protótipo Replit** | Nenhum (pesquisa) |

---

### ÉPICO 6: Score WSI (EPIC-SCORE) — 8 cards

**Status Reunião:** Parcialmente implementado

#### Decisões da Reunião:
1. Cálculo de Score: **implementado**
2. Big Five e Bloom/Dreyfus: são **metodologias aplicadas na construção das perguntas**, não scores separados
3. Comparação entre candidatos (SCO-007): questão de consistência de score entre buscas
4. Histórico de scores: como candidato foi avaliado em outras vagas

#### CARDS SCO-002 e SCO-003 — AJUSTAR
**Ajuste:** Esclarecer que Big Five (SCO-002) e Bloom/Dreyfus (SCO-003) são metodologias aplicadas na geração de perguntas WSI, não cálculos de score separados. Possivelmente consolidar/associar ao Épico 4 (WSI).

| Impacto | Detalhes |
|---------|---------|
| **UI/Frontend** | Nenhuma mudança estrutural. A visualização de Big Five e Bloom/Dreyfus continua existindo como parte do resultado WSI, não como scores independentes |
| **Backend** | Esclarecer que Big Five/Bloom/Dreyfus são inputs da geração de perguntas (Épico 4), e os resultados aparecem como dimensões do score WSI (Épico 6). Pode remover endpoints duplicados |
| **AI/LLM** | Os frameworks já estão embutidos nos prompts de geração WSI |
| **Protótipo Replit** | Nenhum (esclarecimento de arquitetura) |

---

### ÉPICO 7: Gates de Aprovação (EPIC-GATES) — 7→8 cards

**Status Reunião:** Fluxo discutido em detalhe

#### Decisões da Reunião:
1. Gate 1 (aprovar mapeados): botão aprovar/reprovar na coluna Funil do Kanban
2. Gate 2 (aprovar triados): mesma mecânica, mas com feedback obrigatório
3. Modal de reprovação: precisa de campo para motivo
4. **Feedback customizado: gerado pela IA, recrutador NÃO edita diretamente**
5. Aprovação em massa: seleciona vários e executa
6. Histórico de decisões: super válido, sistema de auditoria

#### CARD GAT-003 — AJUSTAR
**Título:** Modal de Reprovação com Motivo  
**Ajuste:** Adicionar campo de motivo/anotação interna na reprovação. O card já tem isso descrito, confirmar que está conforme reunião.

| Impacto | Detalhes |
|---------|---------|
| **UI/Frontend** | Confirmar que o componente tem: select de motivo (obrigatório), campo de anotação interna (opcional), preview de feedback gerado por IA. Arquivo: criar `RejectionModal.tsx` |
| **Backend** | Validar que endpoint salva motivo + anotação + feedback gerado |
| **AI/LLM** | Nenhum (feedback é GAT-004) |
| **Protótipo Replit** | Verificar `batch-approval-modal.tsx` existente, adaptar/criar `RejectionModal.tsx` |

#### CARD GAT-004 — AJUSTAR
**Título:** Geração de Feedback LIA  
**Ajuste:** Esclarecer que feedback é 100% gerado por IA, sem edição direta pelo recrutador. Recrutador apenas aprova ou pede regeneração.

> 📌 **Referência cruzada TRI-013:** Se o candidato reportou um incidente durante a triagem (via "AJUDA"), esse contexto deve ser incluído no prompt de geração de feedback. Candidatos que tiveram dificuldades técnicas reportadas devem receber feedback com tom mais empático e reconhecimento da situação.

| Impacto | Detalhes |
|---------|---------|
| **UI/Frontend** | Remover textarea de edição direta. Substituir por: preview do feedback gerado + botão "Regenerar" + botão "Aprovar e Enviar" |
| **Backend** | Endpoint de regeneração de feedback. Incluir flag `had_incident` no contexto quando candidato reportou problema via TRI-013 |
| **AI/LLM** | Prompt de geração de feedback com contexto: motivo da reprovação, perfil do candidato, vaga, tom empático e profissional. Se `had_incident=true`, ajustar tom para reconhecer dificuldade técnica reportada |

#### NOVO CARD: GAT-008 — Aprendizagem da IA sobre Aprovações/Reprovações

```yaml
Titulo: [AI] Aprendizagem da IA sobre Padrões de Aprovação/Reprovação
Tipo: Feature
Sprint: 4
Pontos: 8
Prioridade: Alta
Epic: EPIC-GATES
Status: 📋 A Criar no Jira

Descricao: |
  A LIA aprende com decisões de aprovação e reprovação dos recrutadores
  para melhorar buscas futuras. Gera métricas, estatísticas e inteligência
  com base nos padrões de aceitação/rejeição.

Historia de Usuario: |
  Como recrutador, eu quero que a LIA melhore suas recomendações
  com base nas minhas decisões anteriores.

Regras de Negocio:
  1. Registrar perfil do candidato + decisão + motivo
  2. Após N reprovações por motivo similar → sugerir ajuste no filtro de busca
  3. Gerar estatísticas: taxa de aprovação por vaga, motivos mais comuns
  4. Aprendizado por recrutador e por empresa
  5. Suggestions proativas: "Nos últimos 30 dias, 80% dos reprovados tinham < 3 anos de experiência. Quer aumentar o filtro?"

Requisitos Tecnicos:
  Backend:
    - LearningFromDecisionsService
    - Agregações de decisões por motivo, perfil, recrutador
    - Sugestões de ajuste de busca baseadas em padrões
  Frontend:
    - InsightsPanel no dashboard
    - Sugestões inline na busca
  AI/LLM:
    - Análise de padrões com LLM para gerar insights textuais

DoD:
  - [ ] Dados de decisões registrados com contexto
  - [ ] Agregações por motivo/perfil funcionando
  - [ ] Pelo menos 3 tipos de sugestões proativas
  - [ ] Dashboard com estatísticas de decisões
```

| Impacto | Detalhes |
|---------|---------|
| **UI/Frontend** | Novo painel de insights de decisões no dashboard. Sugestões inline na busca |
| **Backend** | Novo service `LearningFromDecisionsService`, agregações, tabela de padrões |
| **AI/LLM** | Análise de padrões de aprovação/reprovação com LLM, geração de insights textuais |
| **Protótipo Replit** | Componente de insights/estatísticas de decisões |

---

### ÉPICO 8: Templates de Comunicação (EPIC-TEMPLATES) — 7→8 cards

**Status Reunião:** Todos construídos no Replit

#### Decisões da Reunião:
1. Todos os templates já existem no Replit (Configurações > Comunicação e Alertas)
2. Mensagem inicial WhatsApp: precisa de **2 templates** (consentimento + apresentação da vaga)
3. WhatsApp template creation bloqueado no front por Felipe (aguardando sincronização Meta)

#### CARD TPL-001 — AJUSTAR
**Ajuste:** Esclarecer que são 2 templates de abordagem: (1) Consentimento LGPD + (2) Apresentação da vaga

> 📌 **Referência cruzada TRI-013:** Quando o candidato aceita o consentimento LGPD (`approach_consent`), a LIA envia automaticamente a mensagem proativa orientando sobre o procedimento de reporte de problemas (digitar "AJUDA"). Ou seja, a aceitação do `approach_consent` é o gatilho que dispara a orientação do TRI-013.

| Impacto | Detalhes |
|---------|---------|
| **UI/Frontend** | Separar template de abordagem em 2 cards/abas: "Consentimento" e "Apresentação". Arquivo: `email-templates-manager.tsx` |
| **Backend** | 2 tipos distintos: `approach_consent` e `approach_presentation`. Nota: aceitação do `approach_consent` dispara mensagem proativa TRI-013 (orientação sobre reporte de problemas) |
| **AI/LLM** | Nenhum |
| **Protótipo Replit** | Já existe em `email-templates-manager.tsx`, ajustar para separar os 2 tipos |

#### NOVO CARD: TPL-008 — Sincronização de Templates WhatsApp com Meta

```yaml
Titulo: [BACKEND] Sincronização de Templates WhatsApp com Meta Business
Tipo: Feature
Sprint: 3
Pontos: 8
Prioridade: Alta
Epic: EPIC-TEMPLATES
Status: 📋 A Criar no Jira

Descricao: |
  Implementar sincronização bidirecional entre templates WhatsApp
  da plataforma e o Meta Business Manager. Templates precisam ser
  aprovados pelo Meta antes de usar para disparo.

Historia de Usuario: |
  Como recrutador, eu quero que meus templates WhatsApp sejam
  automaticamente submetidos ao Meta para aprovação.

Regras de Negocio:
  1. Criar template na plataforma → submeter ao Meta para aprovação
  2. Polling de status: PENDING → APPROVED / REJECTED
  3. Se rejeitado: mostrar motivo + sugerir correção
  4. Templates aprovados ficam disponíveis para uso
  5. Sincronizar templates existentes no Meta → plataforma
  6. Suportar variáveis {{1}}, {{2}} do formato Meta

Requisitos Tecnicos:
  Backend:
    - MetaTemplateSync service
    - WhatsApp Business Management API
    - Webhook para status updates
    - Tabela: whatsapp_template_sync (template_id, meta_template_id, status, rejection_reason)
  Frontend:
    - Status de aprovação no editor de templates
    - Badge: "Pendente Meta", "Aprovado", "Rejeitado"

DoD:
  - [ ] Submissão ao Meta funcional
  - [ ] Polling de status implementado
  - [ ] Status visível no frontend
  - [ ] Templates rejeitados com motivo
```

| Impacto | Detalhes |
|---------|---------|
| **UI/Frontend** | Badge de status Meta no editor de templates, feedback de rejeição |
| **Backend** | Integração com Meta Business Management API, webhook de status |
| **AI/LLM** | Nenhum |
| **Protótipo Replit** | Simulação de status de aprovação Meta nos templates WhatsApp |

---

### ÉPICO 9: Agendamento Automático (EPIC-AGE) — 8 cards

**Status Reunião:** Nada pronto, depende de Azure/Microsoft

#### Decisões:
- Integração Microsoft Graph pendente (trocando conta Microsoft)
- Priorizar Teams como primeira integração
- Google Meet futuro
- **Sem alterações de estrutura, mas nenhum card para sprint imediata**

---

### ÉPICO 10: Notificações (EPIC-NOT) — 6→7 cards

**Status Reunião:** Nada pronto, adiado

> 📌 **AÇÃO PENDENTE:** Antes de implementar qualquer card deste épico, é necessário fazer um **mapeamento completo de todos os eventos notificáveis** da plataforma. Os 5 tipos atuais (candidato_triado, entrevista_confirmada, entrevista_cancelada, mensagem_whatsapp, sistema) são insuficientes. Ver **PARTE 11** deste documento para o mapeamento detalhado com ~30 eventos categorizados por origem, trigger, template, mensagem estratégica e ação esperada do recrutador.

#### Decisões:
1. Sistema necessário (Anderson sente falta quando busca termina)
2. Pode destrinchar por entidade
3. **Épico inteiro adiado** para sprints posteriores
4. Falta card de notificação via Teams
5. **Novo (pós-reunião):** Necessário mapeamento completo de TODOS os eventos notificáveis antes de implementar — categorizar por LIA/AI, Sistema, Agentes, Plataforma, Candidato; definir triggers, templates com mensagens estratégicas, canais (bell/push/email/Teams), e ação esperada do recrutador

#### NOVO CARD: NOT-007 — Notificações via Teams

```yaml
Titulo: [BACKEND] Notificações para Recrutador via Microsoft Teams
Tipo: Feature
Sprint: Pós-MVP
Pontos: 5
Prioridade: Media
Epic: EPIC-NOT
Status: 📋 A Criar no Jira

Descricao: |
  Enviar notificações para recrutadores via Microsoft Teams usando
  Microsoft Graph API. Eventos como: busca concluída, candidato triado,
  incidente de triagem, etc.

Requisitos Tecnicos:
  Backend:
    - TeamsNotificationService
    - Microsoft Graph API: Chat.ReadWrite
    - Webhook ou Proactive messaging via Bot Framework

DoD:
  - [ ] Notificação enviada via Teams
  - [ ] Configurável por tipo de evento
  - [ ] Suporte multi-tenant
```

---

### ÉPICO 11: Kanban e Tabela (EPIC-KAN) — 27 cards (2 ajustes, 3 novos)

**Status Reunião:** Maioria feita, revisão de front pendente

#### Decisões da Reunião:
1. Kanban 4 colunas, card, drag-and-drop, menu de ações: **OK**
2. **KAN-005 (Ícones Ação Rápida): OBSOLETO** ❌
3. Badge WSI, filtros, tabela, paginação, colunas ordenáveis: **OK**
4. Preview lateral: pendência de revisão de front
5. Tab Parecer LIA: precisa destrinchar mais
6. Tabela de vagas, arquivar vaga: **OK**
7. Duplicar vaga: **não tem ainda**
8. **3 novos cards** de ações no Kanban

#### CARD KAN-005 — OBSOLETO ❌
**Título:** Ícones de Ação Rápida no Card  
**Ação:** Marcar como OBSOLETO/Cancelado no Jira

#### NOVO CARD: KAN-NEW1 — Disparar Triagem Dentro da Vaga

```yaml
Titulo: [FULL-STACK] Botão Disparar Triagem Dentro da Vaga
Tipo: Feature
Sprint: 3
Pontos: 5
Prioridade: Alta
Epic: EPIC-KAN-001
Status: 📋 A Criar no Jira

Descricao: |
  Botão dentro da vaga para selecionar candidatos da coluna "Funil"
  e disparar triagem WSI em lote. Gera screening para cada candidato
  selecionado.

Historia de Usuario: |
  Como recrutador, eu quero selecionar candidatos aprovados no Gate 1
  e disparar a triagem WSI de todos de uma vez.

Regras de Negocio:
  1. Disponível na view da vaga (Kanban ou Tabela)
  2. Selecionar candidatos da coluna "Funil Aprovado"
  3. Botão "Disparar Triagem" aparece com N selecionados
  4. Confirmação: "Iniciar triagem WSI para N candidatos?"
  5. Progresso: "Enviando 3/10..."
  6. Candidatos movidos para coluna "Em Triagem"

Requisitos Tecnicos:
  Backend:
    - POST /api/v1/screening/batch-start
    - Body: { job_id, candidate_ids: string[] }
    - Enfileirar envio de mensagens WhatsApp
  Frontend:
    - BatchScreeningButton component
    - ScreeningProgressModal
    - Integração com seleção múltipla existente

DoD:
  - [ ] Seleção de candidatos funcional
  - [ ] Disparo em lote funcional
  - [ ] Progresso visível
  - [ ] Candidatos movidos no Kanban
```

| Impacto | Detalhes |
|---------|---------|
| **UI/Frontend** | Botão "Disparar Triagem" no header da vaga, modal de confirmação, barra de progresso. Integrar à seleção múltipla existente |
| **Backend** | Endpoint `POST /api/v1/screening/batch-start`, serviço de enfileiramento |
| **AI/LLM** | Nenhum (usa fluxo existente de triagem por candidato) |
| **Protótipo Replit** | Criar `BatchScreeningButton.tsx`, `ScreeningProgressModal.tsx` na página do Kanban |

#### NOVO CARD: KAN-NEW2 — Solicitar Novos Candidatos com Critérios Refinados

```yaml
Titulo: [FULL-STACK] Solicitar Novos Candidatos com Critérios Refinados
Tipo: Feature
Sprint: 3
Pontos: 8
Prioridade: Alta
Epic: EPIC-KAN-001
Status: 📋 A Criar no Jira

Descricao: |
  Botão "Adicionar mais candidatos" dentro da vaga que inicia nova busca
  usando a JD + feedback de aprovação/reprovação para refinar os critérios.
  A LIA aprende com os padrões de decisão anteriores.

Historia de Usuario: |
  Como recrutador, eu quero pedir mais candidatos com base no que já aprovei
  e reprovei, sem precisar refazer toda a busca manualmente.

Regras de Negocio:
  1. Botão "Adicionar mais candidatos" na vaga
  2. Usa JD + critérios da busca original como base
  3. Enriquece com: motivos de reprovação, perfis aprovados
  4. LIA sugere refinamentos: "Baseado nas reprovações, sugiro aumentar experiência mínima para 5 anos"
  5. Recrutador pode aceitar/ajustar sugestões
  6. Nova busca retorna candidatos não vistos anteriormente

Requisitos Tecnicos:
  Backend:
    - POST /api/v1/jobs/{id}/request-more-candidates
    - Análise de padrões de aprovação/reprovação
    - Exclusão de candidatos já avaliados
  Frontend:
    - RefinedSearchModal
    - SuggestionsList com accept/reject
  AI/LLM:
    - Prompt para análise de padrões e sugestão de refinamentos

DoD:
  - [ ] Botão funcional na vaga
  - [ ] Análise de padrões gera sugestões
  - [ ] Busca refinada exclui candidatos já vistos
  - [ ] Novos candidatos adicionados ao funil
```

| Impacto | Detalhes |
|---------|---------|
| **UI/Frontend** | Botão no header da vaga, modal de refinamento com sugestões da IA, lista de sugestões com accept/reject |
| **Backend** | Análise de decisões anteriores, endpoint de busca refinada, exclusão de candidatos já avaliados |
| **AI/LLM** | Análise de padrões de aprovação/reprovação para gerar sugestões de refinamento |
| **Protótipo Replit** | Criar `RefinedSearchModal.tsx`, integrar à página do Kanban |

#### NOVO CARD: KAN-NEW3 — Buscar Candidatos Similares

```yaml
Titulo: [AI] Buscar Candidatos Similares a Este
Tipo: Feature
Sprint: 3
Pontos: 5
Prioridade: Media
Epic: EPIC-KAN-001
Status: 📋 A Criar no Jira

Descricao: |
  Ação no card do candidato: "Buscar similares". Usa o perfil do candidato
  como referência para encontrar perfis parecidos na base.

Historia de Usuario: |
  Como recrutador, eu quero encontrar candidatos com perfil similar
  a um candidato que gostei, sem precisar definir filtros manualmente.

Regras de Negocio:
  1. Ação disponível no menu de contexto do card
  2. Usa embedding do perfil como query de busca semântica
  3. Retorna top 10 similares (excluindo já avaliados)
  4. Mostra score de similaridade (%)
  5. Permite adicionar similares à vaga

Requisitos Tecnicos:
  Backend:
    - POST /api/v1/candidates/{id}/find-similar
    - Busca por embedding/vetor de perfil
    - Filtro por vaga (excluir já avaliados)
  Frontend:
    - SimilarCandidatesModal
    - SimilarityScoreBadge

DoD:
  - [ ] Busca semântica por similaridade funcional
  - [ ] Top 10 retornados com score
  - [ ] Adicionar similar à vaga funciona
```

| Impacto | Detalhes |
|---------|---------|
| **UI/Frontend** | Item no menu de contexto do card, modal de resultados similares com score |
| **Backend** | Busca semântica por embedding do perfil, endpoint |
| **AI/LLM** | Embedding de perfil para busca vetorial |
| **Protótipo Replit** | Criar `SimilarCandidatesModal.tsx`, adicionar ação ao card do Kanban |

---

### ÉPICO 14: Integrações MVP (EPIC-INT) — 33 cards (ajustes significativos)

**Status Reunião:** Misto — algumas prontas, várias pendentes

#### Decisões da Reunião:
1. **INT-LLM-001 (Claude): ADIAR** — MVP só com Gemini ⏸️
2. **INT-LLM-003 (Router): PÓS-MVP** ⏸️
3. **INT-LLM-004 (Fallback): PÓS-MVP** ⏸️
4. INT-LLM-005 (Gestão de Prompts): **precisa para D-zero** — tabela de consumo agrupada por company
5. INT-LLM-006 (Cache): **precisa fazer**
6. INT-LLM-007 (Custos): **precisa fazer**
7. INT-MSG-001 (Azure): precisa refazer config (mudança de conta)
8. INT-WOS-005 (User Management SDK): provavelmente não precisa (só web, não app)

#### CARDS INT-LLM-001, INT-LLM-003, INT-LLM-004 — ADIAR ⏸️
**Ação:** Marcar como Pós-MVP no Jira. MVP usa exclusivamente Gemini.

| Impacto | Detalhes |
|---------|---------|
| **Simplificação** | Remove complexidade do MVP — sem necessidade de router multi-modelo ou fallback. Todos os prompts usam Gemini 2.5 Flash/Pro |

#### CARDS INT-LLM-005, INT-LLM-006, INT-LLM-007 — MANTER (MVP)
**Ajuste INT-LLM-005:** Adicionar tabela de consumo agrupada por company  
**Ajuste INT-LLM-006:** Cachear perguntas E respostas (não só prompts)  
**Ajuste INT-LLM-007:** Dashboard de custos agrupado por empresa

| Impacto | Detalhes |
|---------|---------|
| **UI/Frontend** | Dashboard de consumo por empresa (INT-LLM-007). Já existe protótipo em `ConsumptionChart.tsx`, `ConsumptionSummaryCard.tsx`, `AgentBreakdown.tsx` |
| **Backend** | Ajustar tracking para Gemini-only (sem multi-model), agregar por company_id |
| **AI/LLM** | Cache inteligente de perguntas/respostas WSI |

#### CARD INT-MSG-001 — AJUSTAR
**Ajuste:** Precisa refazer config (mudança de conta Microsoft)

#### CARD INT-WOS-005 — AVALIAR
**Ajuste:** Pode não precisar se plataforma é só web (sem app mobile)

#### NOVO CARD: INT-ALT-001 — Alternativa a Twilio para WhatsApp
(Mesma pesquisa de TRI-014, consolidar em um só card)

> ⚠️ **DISCLAIMER:** A pesquisa e avaliação sobre Twilio e suas alternativas é de responsabilidade exclusiva do **Paulo Moraes**.

---

### ÉPICO 15: Agentes IA Especializados (EPIC-AGENTS) — 8 cards

**Status Reunião:** Revisão rápida, sem profundidade

#### Decisões:
- Agente Avaliador WSI: precisa existir
- Agente Triagem Curricular: dúvida se é separado
- Cards precisam revisão detalhada na próxima reunião
- **Sem alterações por agora**

---

## PARTE 2: RESUMO CONSOLIDADO DE IMPACTOS

### 2.1 IMPACTO UI/FRONTEND — Componentes a Criar ou Ajustar

#### CRIAR (Novos Componentes — Protótipo Replit)

| # | Componente | Card | Complexidade | Sprint |
|---|-----------|------|-------------|--------|
| 1 | Login com branding dinâmico (logo/cores por tenant) | AUTH-001 | Media | 1 |
| 2 | Simulação multi-tenant (`?tenant=xxx`) | AUTH-005 | Baixa | 1 |
| 3 | `QuestionAdjustmentChat.tsx` | WSI-006 | Alta | 2 |
| 4 | `QuestionDiffView.tsx` (antes/depois) | WSI-006 | Media | 2 |
| 5 | `ScreeningTranscriptView.tsx` (transcrição completa da triagem) | TRI-006 | Media | 3 |
| 6 | `IncidentsPanel.tsx` + `IncidentDetailView.tsx` | TRI-013 | Media | 3 |
| 7 | `IncidentBadge.tsx` no sidebar | TRI-013 | Baixa | 3 |
| 8 | `RejectionModal.tsx` (com motivo obrigatório) | GAT-003 | Media | 3 |
| 9 | Feedback preview (IA, sem edição) no GAT-004 | GAT-004 | Baixa | 3 |
| 10 | Insights de decisões no dashboard | GAT-008 | Media | 4 |
| 11 | Status aprovação Meta nos templates WhatsApp | TPL-008 | Baixa | 3 |
| 12 | `BatchScreeningButton.tsx` + `ScreeningProgressModal.tsx` | KAN-NEW1 | Media | 3 |
| 13 | `RefinedSearchModal.tsx` | KAN-NEW2 | Alta | 3 |
| 14 | `SimilarCandidatesModal.tsx` | KAN-NEW3 | Media | 3 |

#### AJUSTAR (Componentes Existentes)

| # | Componente Existente | Ajuste | Card |
|---|---------------------|--------|------|
| 1 | `login-page.tsx` | Aceitar branding dinâmico | AUTH-001 |
| 2 | `WSIQuestionsStage.tsx` | Integrar chat de ajustes | WSI-006 |
| 3 | `candidate-detail-sidebar.tsx` | Enriquecer card de evento de triagem na tab Activities com transcrição expandível | TRI-006 |
| 3b | `CandidateCard.tsx` (Kanban) | Adicionar ícone de acesso à transcrição da triagem | TRI-006 |
| 4 | `email-templates-manager.tsx` | Separar em consentimento + apresentação | TPL-001 |
| 5 | `batch-approval-modal.tsx` | Adicionar campo de motivo | GAT-003 |
| 6 | `CandidateCard.tsx` (Kanban) | Adicionar ação "Buscar similares" | KAN-NEW3 |
| 7 | Página da vaga (Kanban) | Botões "Disparar Triagem" e "Mais Candidatos" | KAN-NEW1, KAN-NEW2 |

#### REMOVER/CANCELAR

| # | Componente | Motivo | Card |
|---|-----------|--------|------|
| 1 | Tela de monitoramento de triagem em tempo real | Refatorada: transcrição no card de evento existente na tab Activities | TRI-006 |
| 2 | QuickActionIcons (se existir) | Card obsoleto | KAN-005 |
| 3 | Edição manual de perguntas WSI | Substituída por chat conversacional | WSI-004 |

---

### 2.2 IMPACTO BACKEND — Endpoints e Serviços

#### CRIAR (Novos)

| # | Endpoint/Service | Card | Sprint |
|---|-----------------|------|--------|
| 1 | `GET /api/v1/tenants/{subdomain}/branding` | AUTH-001/005 | 1 |
| 2 | Middleware tenant resolver (subdomínio → tenant_id) | AUTH-005 | 1 |
| 3 | `POST /api/v1/wsi/questions/adjust` + WSIQuestionAdjuster | WSI-006 | 2 |
| 4 | Abstração de WhatsApp provider (interface) | TRI-001/014 | 1-2 |
| 5 | `GET /api/v1/candidates/{id}/screening-transcript?job_id={job_id}` | TRI-006 | 3 |
| 6 | Detecção de keywords de escape + `POST /api/v1/incidents` + notificação time WeDo Talent | TRI-013 | 3 |
| 7 | `POST /api/v1/screening/batch-start` | KAN-NEW1 | 3 |
| 8 | `POST /api/v1/jobs/{id}/request-more-candidates` | KAN-NEW2 | 3 |
| 9 | `POST /api/v1/candidates/{id}/find-similar` | KAN-NEW3 | 3 |
| 10 | LearningFromDecisionsService | GAT-008 | 4 |
| 11 | MetaTemplateSync service | TPL-008 | 3 |
| 12 | TeamsNotificationService | NOT-007 | Pós-MVP |

#### AJUSTAR (Existentes)

| # | Endpoint/Service | Ajuste | Card |
|---|-----------------|--------|------|
| 1 | Message handler WhatsApp | Detectar keywords de escape + mensagem proativa pós-LGPD + notificação time WeDo Talent | TRI-013 |
| 2 | Template service | Separar approach_consent / approach_presentation | TPL-001 |
| 3 | Feedback generation | Remover edição manual, só preview+regenerar | GAT-004 |
| 4 | LLM tracking | Gemini-only, agregar por company | INT-LLM-005/007 |
| 5 | Azure App Registration | Refazer config (conta nova) | INT-MSG-001 |

#### TABELAS DE BANCO (Novas)

| Tabela | Card | Campos Chave |
|--------|------|-------------|
| `tenant_branding` | AUTH-005 | tenant_id, subdomain, logo_url, primary_color, company_name |
| `screening_incidents` | TRI-013 | candidate_id, job_id, trigger_keyword, last_messages, status, assigned_to |
| `whatsapp_template_sync` | TPL-008 | template_id, meta_template_id, status, rejection_reason |

---

### 2.3 IMPACTO AI/LLM

| # | Funcionalidade | Card | Modelo | Sprint |
|---|---------------|------|--------|--------|
| 1 | Ajuste de perguntas WSI via prompt conversacional | WSI-006 | Gemini 2.5 Flash | 2 |
| 2 | Detecção de intent "ajuda/problema" na triagem | TRI-013 | Gemini 2.5 Flash | 3 |
| 3 | Feedback de reprovação (100% gerado por IA) | GAT-004 | Gemini 2.5 Flash | 3 |
| 4 | Análise de padrões aprovação/reprovação | GAT-008 | Gemini 2.5 Pro | 4 |
| 5 | Sugestão de refinamento de busca | KAN-NEW2 | Gemini 2.5 Pro | 3 |
| 6 | Busca semântica por similaridade de perfil | KAN-NEW3 | Embedding Gemini | 3 |
| 7 | Cache de perguntas e respostas LLM | INT-LLM-006 | N/A (Redis) | 3 |
| 8 | Monitoramento de custos Gemini por empresa | INT-LLM-007 | N/A (tracking) | 4 |

**Decisão Chave: MVP usa exclusivamente Gemini** (Claude adiado para pós-MVP)

---

## PARTE 3: LISTA DE TAREFAS

### 3.1 TAREFAS PROTÓTIPO REPLIT (Paulo)

#### Sprint 1 (Imediata)
- [ ] AUTH-001: Atualizar `login-page.tsx` com suporte a branding dinâmico
- [ ] AUTH-005: Criar simulação multi-tenant com query param `?tenant=`
- [ ] TRI-014: Documentar pesquisa de alternativas a Twilio (não é código) — ⚠️ responsabilidade Paulo Moraes

#### Sprint 2
- [ ] WSI-006: Criar `QuestionAdjustmentChat.tsx` com integração ao WSIQuestionsStage
- [ ] WSI-006: Criar `QuestionDiffView.tsx` para visualização antes/depois
- [ ] WSI-006: Criar endpoint `/api/v1/wsi/questions/adjust` no backend Python

#### Sprint 3
- [ ] TRI-006: Enriquecer card de evento de triagem no `candidate-detail-sidebar.tsx` com transcrição expandível + criar `ScreeningTranscriptView.tsx` + ícone no Kanban card e tabela de candidatos
- [ ] TRI-013: Criar `IncidentsPanel.tsx`, `IncidentDetailView.tsx`, `IncidentBadge.tsx`
- [ ] GAT-003: Criar/ajustar `RejectionModal.tsx` com motivo obrigatório
- [ ] GAT-004: Ajustar preview de feedback (sem edição, só regenerar)
- [ ] TPL-001: Separar templates de abordagem em consentimento + apresentação
- [ ] TPL-008: Adicionar status de aprovação Meta nos templates WhatsApp
- [ ] KAN-NEW1: Criar `BatchScreeningButton.tsx` e `ScreeningProgressModal.tsx`
- [ ] KAN-NEW2: Criar `RefinedSearchModal.tsx`
- [ ] KAN-NEW3: Criar `SimilarCandidatesModal.tsx`, adicionar ação ao menu do card
- [ ] KAN-005: Remover/marcar como obsoleto

#### Sprint 4
- [ ] GAT-008: Criar componente de insights de decisões no dashboard
- [ ] INT-LLM-007: Validar/ajustar dashboard de consumo existente (ConsumptionChart, etc.)

### 3.2 TAREFAS PRODUÇÃO (Anderson + Time Externo)

#### Sprint 1 (Imediata)
- [ ] AUTH-005: Configurar Wildcard SSL no Google Cloud
- [ ] AUTH-005: Configurar DNS wildcard para *.wedotalent.cc
- [ ] AUTH-005: Implementar middleware tenant resolver (Rails)
- [ ] AUTH-001: Tabela `tenant_branding` + endpoint de branding
- [ ] AUTH-006: Coordenar entrega de assets com Lucas
- [ ] TRI-014: Pesquisar alternativas a Twilio (Tudu, Zenvia, Slickflow) — ⚠️ responsabilidade Paulo Moraes
- [ ] TRI-001: Implementar abstração de WhatsApp provider
- [ ] INT-MSG-001: Refazer config Azure App Registration (nova conta)

#### Sprint 2
- [ ] WSI-006: Implementar WSIQuestionAdjuster service (Rails/Python FastAPI)
- [ ] WSI-006: Endpoint `/api/v1/wsi/questions/adjust`
- [ ] WSI-004: Remover edição manual de perguntas (se existir)
- [ ] INT-LLM-005: Gestão de prompts com tabela de consumo por company

#### Sprint 3
- [ ] TRI-006: Endpoint `GET /api/v1/candidates/{id}/screening-transcript?job_id={job_id}`
- [ ] TRI-013: Mensagem proativa pós-LGPD + detecção de escape keywords + tabela `screening_incidents` + notificação time WeDo Talent (NÃO recrutador)
- [ ] GAT-003: Validar endpoint de reprovação com motivo
- [ ] GAT-004: Endpoint de feedback gerado por IA (sem edição manual)
- [ ] TPL-001: Separar tipos `approach_consent` / `approach_presentation`
- [ ] TPL-008: MetaTemplateSync service + WhatsApp Business API
- [ ] KAN-NEW1: `POST /api/v1/screening/batch-start`
- [ ] KAN-NEW2: `POST /api/v1/jobs/{id}/request-more-candidates` + análise de padrões
- [ ] KAN-NEW3: `POST /api/v1/candidates/{id}/find-similar` + busca vetorial
- [ ] INT-LLM-006: Cache Redis para perguntas/respostas LLM

#### Sprint 4
- [ ] GAT-008: LearningFromDecisionsService + agregações
- [ ] INT-LLM-007: Tracking de custos Gemini por empresa + alertas

#### Pós-MVP
- [ ] **NOT-MAP: Mapeamento completo de eventos notificáveis (CRÍTICO — bloqueia Épico 10 inteiro)**
  - [ ] Mapear TODOS os eventos de cada épico que geram notificação
  - [ ] Definir triggers, templates, mensagens estratégicas e canais (bell, push, email, Teams)
  - [ ] Categorizar por: LIA/AI, Sistema, Agentes, Plataforma, Candidato
  - [ ] Para cada evento: trigger, destinatário, prioridade, template da mensagem, ação esperada do recrutador, deep link
  - [ ] Validar com Anderson (qual informação ele precisa para tomar decisão rápida)
  - [ ] Ver PARTE 11 deste documento para mapeamento detalhado
- [ ] NOT-007: TeamsNotificationService
- [ ] NOT-001 a NOT-006: Implementar sistema de notificações (depende do mapeamento NOT-MAP)
- [ ] INT-LLM-001: Integração Anthropic Claude (se cliente exigir)
- [ ] INT-LLM-003: Router de modelos multi-LLM
- [ ] INT-LLM-004: Fallback entre modelos
- [ ] WIZ-014: Sessão de validação com André
- [ ] TRI-011: Pré-qualificação automatizada (definir autonomia da LIA)

---

## PARTE 4: CARDS REMOVIDOS/ADIADOS — RESUMO

| Card | Ação | Justificativa |
|------|------|---------------|
| **WSI-004** | ❌ REMOVER | Edição manual quebra integridade WSI → substituído por WSI-006 (conversacional) |
| **KAN-005** | ❌ OBSOLETO | Confirmado obsoleto na reunião |
| **TRI-006** | 🔄 REFATORAR | Tela de monitoramento → Transcrição completa no card de evento existente na tab Activities + ícone no Kanban/tabela |
| **TRI-011** | ⏸️ ADIAR | Precisa definição de autonomia da LIA |
| **INT-LLM-001** | ⏸️ ADIAR | MVP usa só Gemini. Claude só se cliente exigir |
| **INT-LLM-003** | ⏸️ PÓS-MVP | Router multi-modelo desnecessário sem Claude no MVP |
| **INT-LLM-004** | ⏸️ PÓS-MVP | Fallback desnecessário sem múltiplos modelos |
| **INT-WOS-005** | ❓ AVALIAR | Pode não precisar se plataforma é só web |
| **Épico 10** | ⏸️ ADIADO | Inteiro adiado (exceto NOT-007 criado para pós-MVP) |
| **Épico 12** | ⏸️ PÓS-MVP | JD Avançado |
| **Épico 13** | ⏸️ PÓS-MVP | Config Avançadas |

---

## PARTE 5: ORDEM IDEAL DOS 15 ÉPICOS PARA O MVP

### 5.0 Filosofia de Construção: Fatias Verticais (Vertical Slices)

A ordem de desenvolvimento segue a abordagem de **fatias verticais**, onde cada sprint entrega funcionalidades completas de ponta a ponta (frontend + backend + IA), em vez de construir por camada horizontal (todo frontend → todo backend → toda IA).

```
❌ NÃO RECOMENDADO — Construção por Camada Horizontal:

  Sprint 1: Todo o Frontend (15 telas bonitas, nenhuma funciona)
  Sprint 2: Todo o Backend (15 APIs, descobre que metade dos contratos estão errados)
  Sprint 3: Toda a IA (15 prompts, integração nunca foi testada)
  Sprint 4: Integrar tudo → 💥 bugs de integração em cascata, retrabalho massivo

  Problemas:
  • Ninguém testa nada até o final
  • Feedback do recrutador chega tarde demais
  • Riscos de integração se acumulam
  • Contratos de API divergem entre front e back
  • Retrabalho exponencial


✅ RECOMENDADO — Construção por Fatia Vertical (adotado neste projeto):

  Sprint 1: Login COMPLETO (front + back + SSO)
           + Wizard COMPLETO (front + back + IA/Gemini)
           + Kanban ESTRUTURA (front + back + drag-and-drop)
           → Entregável: "Recrutador faz login, cria vaga, vê Kanban" ✅ testável

  Sprint 2: Busca COMPLETA (front + back + embeddings)
           + Perguntas WSI COMPLETAS (front + back + geração IA)
           → Entregável: "Recrutador busca candidatos e gera perguntas" ✅ testável

  Sprint 3: Triagem COMPLETA (front + back + WhatsApp + IA)
           + Score + Gates + Templates
           → Entregável: "Candidato é triado, avaliado e aprovado/reprovado" ✅ testável

  Sprint 4: Agendamento + Agentes IA + Polimento
           → Entregável: "Entrevista agendada automaticamente" ✅ testável

  Vantagens:
  • Cada sprint entrega valor testável pelo recrutador
  • Bugs de integração são descobertos e corrigidos cedo
  • Feedback contínuo do Anderson/André
  • Contratos de API validados na prática
  • Risco distribuído ao longo do projeto
```

**Como isso se aplica aos dois ambientes:**

| Aspecto | Protótipo Replit (Paulo) | Produção (Anderson + Time) |
|---------|------------------------|---------------------------|
| **Objetivo** | Referência visual e funcional | Código de produção |
| **Construção** | Fatia vertical: tela + API mock + comportamento IA | Fatia vertical: Vue + Rails API + FastAPI IA |
| **Entrega Sprint 1** | Login + Wizard + Kanban funcionando no Replit | Login + Wizard + Kanban no Rails/Vue |
| **Validação** | Paulo apresenta demo para o time | Anderson testa em staging |
| **Sincronização** | Replit como referência de UX para produção | Produção implementa com base no Replit |

> **Nota:** O protótipo Replit pode avançar mais rápido porque usa React + mocks. A produção acompanha com a implementação real em Rails/Vue/FastAPI. Cada apresentação semanal do Replit serve como validação visual para o time de produção.

### 5.1 Diagrama de Dependências entre Épicos

```
CAMINHO CRÍTICO (bloqueante):

  Épico 1 (Auth) ─────────────────────────────────────────────────────┐
       │                                                               │
       ▼                                                               │
  Épico 2 (Wizard) ──→ Épico 4 (Perguntas WSI) ──→ Épico 6 (Score)   │
       │                      │                          │             │
       ▼                      ▼                          ▼             │
  Épico 3 (Busca) ──→ Épico 5 (Triagem WhatsApp) ──→ Épico 7 (Gates) │
       │                      │                          │             │
       ▼                      ▼                          ▼             │
  Épico 11 (Kanban) ←─ Épico 8 (Templates) ──→ Épico 9 (Agenda)      │
                                                                       │
  Épico 14 (Integrações) ←────────────────────────────────────────────┘
       │                         (transversal, apoia todos)
       ▼
  Épico 15 (Agentes IA)

ADIADOS/PÓS-MVP:
  Épico 10 (Notificações) — adiado inteiro
  Épico 12 (JD Avançado) — pós-MVP
  Épico 13 (Config Avançadas) — pós-MVP
```

### 5.2 Ordem Ideal de Execução — Sprint a Sprint

| Ordem | Sprint | Épico | Nome | Cards MVP | Justificativa |
|-------|--------|-------|------|-----------|---------------|
| **1** | Sprint 1 | **Épico 1** | Autenticação | 4 + 2 novos = 6 | **Fundação.** Sem login, nada funciona. Inclui subdomínio por empresa (AUTH-005) e wildcard SSL |
| **2** | Sprint 1 | **Épico 14** | Integrações (parcial) | ~10 de 33 | **Fundação.** WorkOS, Gemini, Azure — infraestrutura que todos os outros épicos usam. INT-LLM-001/003/004 adiados |
| **3** | Sprint 1 | **Épico 11** | Kanban e Tabela (parcial) | ~15 de 27 | **Estrutura visual.** O Kanban é a tela principal do recrutador. Sprint 1 = estrutura base + colunas + card |
| **4** | Sprint 1-2 | **Épico 2** | Wizard Conversacional | 13 + 1 novo = 14 | **Criação de vagas.** O wizard é o ponto de entrada do fluxo. Precisa de Auth (Épico 1) para funcionar |
| **5** | Sprint 2 | **Épico 3** | Busca e Mapeamento | 6 + 7 WDT + 1 novo = 14 | **Core do produto.** Sem busca, não há candidatos. Depende do Wizard (Épico 2) para ter vagas |
| **6** | Sprint 2 | **Épico 4** | Geração de Perguntas WSI | 5 - 1 + 1 = 5 | **Preparação para triagem.** Gera perguntas a partir da JD criada no Wizard. Depende de Épico 2 |
| **7** | Sprint 2-3 | **Épico 5** | Triagem WhatsApp | 11 + 2 novos = 13 | **Execução da triagem.** Usa perguntas WSI (Épico 4) para triar candidatos encontrados (Épico 3). Depende de alternativa ao Twilio (TRI-014) — ⚠️ pesquisa sob responsabilidade do Paulo Moraes |
| **8** | Sprint 3 | **Épico 6** | Score WSI | 8 | **Resultado da triagem.** Calcula score a partir das respostas da triagem (Épico 5). Depende de Épicos 4+5 |
| **9** | Sprint 3 | **Épico 7** | Gates de Aprovação | 7 + 1 novo = 8 | **Decisão.** Recrutador aprova/reprova com base no score WSI (Épico 6). Feedback 100% IA |
| **10** | Sprint 3 | **Épico 8** | Templates de Comunicação | 7 + 1 novo = 8 | **Comunicação.** Templates usados na triagem (Épico 5), gates (Épico 7), e agendamento (Épico 9) |
| **11** | Sprint 3 | **Épico 11** | Kanban (restante) | ~12 restantes + 3 novos | **Completar Kanban.** Actions avançadas: disparar triagem em lote, buscar similares, pedir mais candidatos |
| **12** | Sprint 4 | **Épico 9** | Agendamento Automático | 8 | **Pós-aprovação.** Agenda entrevista para candidatos aprovados no Gate 2. Depende de Microsoft Graph (INT-MSG-001) |
| **13** | Sprint 4 | **Épico 15** | Agentes IA Especializados | 8 | **Orquestração avançada.** Agentes autônomos que coordenam triagem e avaliação. Depende de Épicos 4-7 |
| **14** | Sprint 4 | **Épico 14** | Integrações (restante) | ~23 restantes | **Completar integrações.** LLM cache, custos, gestão de prompts por empresa |
| — | ⏸️ Pós-MVP | **Épico 10** | Notificações | 6 + 1 novo = 7 | Adiado por decisão da reunião |
| — | ⏸️ Pós-MVP | **Épico 12** | JD e Wizard Avançado | 5 | Features avançadas do wizard |
| — | ⏸️ Pós-MVP | **Épico 13** | Configurações Avançadas | 6 | Config avançadas de empresa |

### 5.3 Resumo por Sprint

| Sprint | Duração Est. | Épicos | Cards | Entregável Principal |
|--------|-------------|--------|-------|---------------------|
| **Sprint 1** | 2-3 semanas | 1, 14 (parcial), 11 (parcial), 2 | ~45 | **Recrutador faz login, cria vaga, vê Kanban** |
| **Sprint 2** | 2-3 semanas | 2 (restante), 3, 4, 5 (início) | ~40 | **Busca candidatos, gera perguntas WSI, inicia triagem** |
| **Sprint 3** | 2-3 semanas | 5 (restante), 6, 7, 8, 11 (restante) | ~45 | **Triagem completa, score WSI, aprovação, templates** |
| **Sprint 4** | 2-3 semanas | 9, 15, 14 (restante) | ~30 | **Agendamento, agentes IA, integrações finais** |
| **TOTAL MVP** | **8-12 semanas** | **12 épicos ativos** | **~160 cards** | **Ciclo completo de recrutamento com IA** |

### 5.4 Bloqueios Identificados

| Bloqueio | Épicos Afetados | Ação Necessária | Sprint |
|----------|----------------|-----------------|--------|
| Alternativa ao Twilio | Épico 5 (Triagem) | TRI-014: Pesquisar Tudu/Zenvia/Slickflow — ⚠️ Paulo Moraes | Sprint 1 |
| Conta Microsoft (Azure) | Épico 9 (Agendamento), Épico 14 (INT-MSG) | Refazer App Registration | Sprint 1 |
| Assets do Lucas | Épico 1 (AUTH-006) | Coordenar entrega de marca | Sprint 1 |
| Validação do André | Épico 4 (WSI), Épico 3 (Busca) | WIZ-014, MAP-014 | Sprint 3+ |
| Aprovação templates Meta | Épico 8 (Templates) | TPL-008: Sincronização Meta Business | Sprint 3 |

---

## PARTE 6: BACKLOG PÓS-MVP CONSOLIDADO

### 6.1 Cards/Épicos Adiados da Reunião (MVP → Pós-MVP)

| # | Card/Épico | Tipo | Motivo do Adiamento | Pré-requisito |
|---|-----------|------|--------------------|--------------| 
| 1 | **Épico 10 — Notificações** (7 cards, incluindo NOT-007) | Épico inteiro | Adiado por decisão da reunião. Anderson sente falta, mas não é bloqueante para MVP | Épicos 5-7 funcionando |
| 2 | **Épico 12 — JD e Wizard Avançado** (5 cards) | Épico inteiro | Features avançadas não essenciais para MVP | Épico 2 completo |
| 3 | **Épico 13 — Config Avançadas** (6 cards) | Épico inteiro | Configurações avançadas de empresa | Épico 1 completo |
| 4 | **INT-LLM-001** — Integração Anthropic Claude | Card individual | MVP usa exclusivamente Gemini. Claude só se cliente exigir | Gemini estável |
| 5 | **INT-LLM-003** — Router de Modelos Multi-LLM | Card individual | Desnecessário sem múltiplos modelos no MVP | INT-LLM-001 |
| 6 | **INT-LLM-004** — Fallback entre Modelos | Card individual | Desnecessário sem router multi-modelo | INT-LLM-003 |
| 7 | **TRI-011** — Pré-qualificação Automatizada | Card individual | Precisa definição de autonomia da LIA | Épico 5 completo + reunião com André |
| 8 | **WIZ-014** — Revisão Metodologia com André | Card individual | Só após screening + respostas funcionando | Épicos 4+5+6 completos |
| 9 | **MAP-014** — Revisão Qualidade Busca com André | Card individual | Só após busca funcional | Épico 3 completo |
| 10 | **INT-WOS-005** — User Management SDK WorkOS | Card individual | Pode não precisar (plataforma é só web) | Avaliar necessidade |

### 6.2 Épicos Pós-MVP Já Planejados (WDT Talent Funnel)

> **📄 Documento completo:** [epic-wdt-talent-funnel.md](./epic-wdt-talent-funnel.md)

| Épico | Nome | Cards | SP | Sprints | Dependência |
|-------|------|-------|-----|---------|-------------|
| **16** | Otimização Estatística de Busca | 8 | 38 | 3-5 | Épico 3 (MVP) |
| **17** | Base de Critérios de Avaliação ⭐ GAME CHANGER | 7 | 52 | 6-11 | Épico 16 |
| **18** | Aprendizado e Features Avançadas | 6 | 42 | 12-17 | Épicos 16+17 |
| **19** | Observabilidade e Documentação de Busca | 2 | 16 | 2+/18 | Épicos 16-18 |
| **TOTAL WDT** | | **23** | **148** | **18 sprints** | |

### 6.3 Priorização Pós-MVP (Ordem Sugerida)

```
Fase Pós-MVP 1 (imediata após MVP):
  ├── Épico 10: Notificações (7 cards) — alta demanda do recrutador
  ├── INT-LLM-001: Claude — se cliente exigir
  └── TRI-011: Pré-qualificação automatizada — após definir autonomia LIA

Fase Pós-MVP 2 (melhoria contínua):
  ├── Épico 16: Otimização Estatística de Busca (8 cards, 38 SP)
  ├── WIZ-014 + MAP-014: Validações com André
  └── Épico 12: JD Avançado (5 cards)

Fase Pós-MVP 3 (game changer):
  ├── Épico 17: Base de Critérios de Avaliação (7 cards, 52 SP) ⭐
  ├── INT-LLM-003 + INT-LLM-004: Router + Fallback multi-modelo
  └── Épico 13: Config Avançadas (6 cards)

Fase Pós-MVP 4 (inteligência avançada):
  ├── Épico 18: Aprendizado e Features Avançadas (6 cards, 42 SP)
  └── Épico 19: Observabilidade e Documentação (2 cards, 16 SP)
```

### 6.4 Contagem Total Pós-MVP

| Categoria | Cards | SP Estimados |
|-----------|-------|-------------|
| Épicos MVP adiados (10, 12, 13) | 18 | ~60 |
| Cards individuais adiados (LLM, TRI, WIZ, MAP, WOS) | 7 | ~30 |
| WDT Talent Funnel (Épicos 16-19) | 23 | 148 |
| **TOTAL PÓS-MVP** | **48** | **~238** |

---

## PARTE 7: PRÓXIMOS PASSOS COMBINADOS

1. ✅ Paulo faz análise da transcrição (este documento)
2. ⬜ Paulo manda para Anderson revisar
3. ⬜ Segunda-feira: 1h para definir quais épicos/cards na sprint da semana
4. ⬜ Anderson revisa o que está pronto e bloca o que falta
5. ⬜ Paulo faz apresentações semanais do Replit para o time (primeiro dia da sprint)
6. ⬜ Após validação deste documento: atualizar `lia-mvp-cards-jira.md` e criar cards no Jira

---

**Nota:** Este documento deve ser validado por Paulo e Anderson ANTES de atualizar os cards no `lia-mvp-cards-jira.md` e no Jira.

---

## PARTE 8: CARDS NOVOS — ESPECIFICAÇÃO COMPLETA (FORMATO JIRA)

### 8.1 Novos Cards (7 cards) — Primeira Parte (AUTH, WIZ, MAP, WSI, TRI)

> Os 7 cards abaixo são as especificações completas no formato Jira (mesmo padrão de `docs/lia-mvp-cards-jira.md`) dos cards novos identificados na PARTE 1 deste documento. Cada card inclui todas as seções obrigatórias: Design & Componentes, Comportamento de UI, Referências de Design, Arquivos de Referência, DoD e Critérios de Aceitação.

---

### CARD AUTH-005: Wildcard SSL + Google Cloud Multi-Brand

```yaml
Titulo: "[INFRA] Configuração Wildcard SSL + Google Cloud para Multi-Brand/Subdomínio"
Tipo: Infraestrutura
Sprint: 1
Pontos: 5
Prioridade: Crítica
Epic: EPIC-AUTH
Status: 📋 A Criar no Jira
Dependencias: Nenhuma (card fundacional)

Descricao: |
  Configurar certificado SSL wildcard (*.wedotalent.cc) e DNS no Google Cloud
  para suportar subdomínios por empresa (ex: itau.wedotalent.cc, ambev.wedotalent.cc).
  Isso habilita white label e customização de marca por tenant.
  Inclui middleware de resolução de tenant, tabela de tenants no banco,
  configuração Nginx para wildcard routing e detecção client-side de subdomínio.

Historia de Usuario: |
  Como administrador da plataforma, eu quero que cada empresa cliente
  tenha seu próprio subdomínio (ex: itau.wedotalent.cc) para oferecer
  uma experiência white label com logo e cores customizadas.

Regras de Negocio:
  1. Wildcard SSL para *.wedotalent.cc (Let's Encrypt ou Google-managed)
  2. DNS configurado no Google Cloud DNS com registro *.wedotalent.cc
  3. Nginx/proxy reverso roteando por subdomínio → tenant_id
  4. Redirecionamento de www e root para subdomínio padrão (app.wedotalent.cc)
  5. Suporte futuro a domínio customizado (ex: rh.itau.com.br) via campo custom_domain
  6. Tenant padrão (fallback) se subdomínio não encontrado na tabela
  7. Cache de resolução de tenant com TTL de 5 minutos
  8. Subdomínios reservados: www, app, api, admin, staging, dev

Requisitos Tecnicos:
  Frontend:
    - Detecção de subdomínio via window.location.hostname no client-side
    - Hook useTenant() que resolve tenant a partir do subdomínio
    - ThemeProvider dinâmico que aplica cores e logo do tenant
    - Fallback para branding padrão WeDo Talent se tenant não encontrado
    - Carregamento de logo via URL do tenant (logo_url)
  Backend:
    - Middleware TenantResolver que extrai subdomínio do Host header
    - Tabela tenants: id (UUID), subdomain (VARCHAR UNIQUE), company_name, logo_url, primary_color, secondary_color, custom_domain (nullable), favicon_url, created_at, updated_at
    - Endpoint GET /api/v1/tenants/{subdomain}/branding → { company_name, logo_url, primary_color, secondary_color, favicon_url }
    - Nginx config com server_name *.wedotalent.cc e proxy_pass para app
    - Validação de subdomínio: lowercase, alfanumérico + hífens, 3-63 chars
  Dados:
    - tenants: id, subdomain, company_name, logo_url, primary_color, secondary_color, custom_domain, favicon_url, is_active, created_at, updated_at
    - Seed inicial: tenant "app" (padrão WeDo Talent) + tenant "demo" (para testes)
  Validacoes:
    - Subdomínio deve ser único e não estar na lista de reservados
    - logo_url deve ser URL válida (HTTPS)
    - primary_color deve ser hex válido (#RRGGBB)
    - custom_domain deve ter CNAME configurado antes de ativar

Design & Componentes:
  Componentes Existentes:
    - LoginPage - tela de login (já existe)
    - AuthContext - contexto de autenticação
    - ThemeProvider - Next.js theme provider
  Novos Componentes:
    - TenantProvider - provider de contexto de tenant
    - TenantBrandingLoader - loader assíncrono de branding
    - DynamicLogo - componente que renderiza logo do tenant
  Design Tokens:
    Background: --lia-bg-primary (dinâmico por tenant, default #FFFFFF)
    Accent: --wedo-cyan (dinâmico por tenant, default #60BED1)
    Text: --lia-text-primary (#111827)
    Fallback: --lia-bg-secondary (#F3F4F6)
  Layout:
    Container: Mesmo layout do login atual
    Logo: Substituído dinamicamente pelo logo_url do tenant
    Cores: primary_color aplicada em botões e accents
    Favicon: favicon_url do tenant no <head>
  Estados:
    - Loading: skeleton enquanto resolve tenant
    - Resolved: branding do tenant aplicado
    - Fallback: branding padrão WeDo Talent
    - Error: tenant não encontrado → fallback + log
  Acessibilidade:
    - Contraste mínimo WCAG AA entre primary_color e texto
    - Alt text no logo dinâmico com company_name
    - Fallback de cor se primary_color não passar contraste

Comportamento de UI:
  Fluxo Principal:
    1. Usuário acessa itau.wedotalent.cc
    2. Client detecta subdomínio "itau" via window.location.hostname
    3. TenantProvider chama GET /api/v1/tenants/itau/branding
    4. Loading skeleton enquanto resolve
    5. Branding carregado: logo Itaú, cor laranja, favicon Itaú
    6. Tela de login renderiza com branding customizado
    7. Após login, branding persiste em toda a sessão

  Layout:
    Desktop: Logo centralizado (max 200px largura), card de login centralizado
    Mobile: Logo 100% largura com padding, card full-width
    Tablet: Mesmo layout desktop com max-w-md

  Estados de Botoes:
    Entrar:
      - Default: bg dinâmico (primary_color do tenant)
      - Hover: primary_color com 10% darker
      - Loading: spinner + "Entrando..."
      - Disabled: opacity 50% durante loading

  Validacoes Inline:
    Subdominio:
      - Não encontrado: fallback silencioso para branding padrão
    Logo:
      - Erro de carregamento: fallback para texto do company_name

  Mensagens de Feedback:
    - Tenant não encontrado: log interno, UX sem erro visível (fallback)
    - SSL inválido: erro de browser (não controlável pelo app)
    - Branding carregado: transição suave de skeleton para conteúdo

Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md (Seções: 1.2 Paleta de Cores, 2.1 Botões, 2.2 Inputs & Forms, 2.3 Cards)"
  Figma: "[A ser preenchido pelo time de Design — tela de login multi-tenant]"
  Assets:
    - "Logo WeDo Talent (fallback): /public/logos/wedo-talent-logo.svg"
    - "Favicon padrão: /public/favicon.ico"
  Tokens:
    - "accent-primary: dinâmico por tenant (default #60BED1)"
    - "bg-primary: dinâmico por tenant (default #FFFFFF)"
    - "text-primary: #111827"

DoD:
  - [ ] Wildcard SSL emitido e configurado no Google Cloud
  - [ ] DNS wildcard *.wedotalent.cc configurado e propagado
  - [ ] Nginx config com wildcard server_name funcionando
  - [ ] Middleware TenantResolver extraindo subdomínio do Host header
  - [ ] Tabela tenants criada com migration e seed inicial
  - [ ] Endpoint GET /api/v1/tenants/{subdomain}/branding retornando dados
  - [ ] Frontend detectando subdomínio e aplicando branding dinâmico
  - [ ] Fallback para tenant padrão se subdomínio não encontrado
  - [ ] Cache de resolução de tenant com TTL 5min
  - [ ] Teste com 2+ subdomínios (itau.wedotalent.cc, demo.wedotalent.cc)
  - [ ] Responsivo mobile

Criterios de Aceitacao:
  - [ ] itau.wedotalent.cc resolve para tenant correto com branding Itaú
  - [ ] demo.wedotalent.cc resolve para tenant demo com branding demo
  - [ ] SSL válido em qualquer subdomínio (*.wedotalent.cc)
  - [ ] Logo e cores carregam dinamicamente por tenant
  - [ ] Subdomínio inexistente mostra branding padrão WeDo Talent (fallback)
  - [ ] Subdomínios reservados (www, api, admin) não conflitam
  - [ ] Favicon atualizado por tenant
  - [ ] Performance: resolução de tenant < 200ms (com cache)

Arquivos de Referencia (Prototipo Replit):
  - login-page.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/pages/login-page.tsx
  - auth-context.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/auth-context.tsx
  - auth-headers.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/lib/api/auth-headers.ts
  - workos.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/lib/workos.ts
```

---

### CARD AUTH-006: Revisão Final de Design pelo Lucas

```yaml
Titulo: "[DESIGN] Revisão Final de Design/Marca pelo Lucas"
Tipo: Design
Sprint: 1
Pontos: 3
Prioridade: Alta
Epic: EPIC-AUTH
Status: 📋 A Criar no Jira
Dependencias: AUTH-001

Descricao: |
  Lucas faz revisão final dos assets visuais: logo atualizado da WeDo Talent,
  marca da LIA, ícones, paleta de cores, e aplica nas telas de login/onboarding.
  Entrega inclui guia de marca para white label e assets em múltiplos formatos
  (SVG, PNG @1x/@2x/@3x).

Historia de Usuario: |
  Como stakeholder, eu quero que a identidade visual da plataforma
  esteja atualizada e consistente antes do lançamento do MVP,
  garantindo profissionalismo e reconhecimento de marca.

Regras de Negocio:
  1. Logo WeDo Talent atualizado (versões: completo, ícone, monocromático)
  2. Logo LIA atualizado (avatar, ícone, variações de cor)
  3. Paleta de cores validada e documentada (primária, secundária, semânticas)
  4. Assets para tela de login (background, ilustrações, logo)
  5. Assets para onboarding (ícones de etapas, ilustrações)
  6. Guia de marca para white label (o que pode/não pode ser customizado)
  7. Favicon e Open Graph images atualizados
  8. Email templates com marca atualizada (headers, footers)

Requisitos Tecnicos:
  Frontend:
    - Substituir assets de logo/marca em /public/logos/
    - Atualizar favicon.ico e apple-touch-icon.png
    - Atualizar Open Graph images em /public/images/
    - Aplicar paleta validada nos design tokens (globals.css)
  Backend:
    - Nenhuma alteração direta
  Dados:
    - Nenhuma alteração
  Validacoes:
    - SVG acessível (título e descrição)
    - PNG mínimo 2x para retina
    - Favicon em múltiplos tamanhos (16, 32, 180, 192, 512)

Design & Componentes:
  Componentes Existentes:
    - LoginPage - tela de login (atualizar logo)
    - Sidebar - menu lateral (atualizar logo)
    - Header - cabeçalho (atualizar logo)
    - EmailTemplate - templates de email (atualizar marca)
  Novos Componentes:
    - Nenhum (apenas atualização de assets)
  Design Tokens:
    Primary: --wedo-cyan (#60BED1) — a ser validado pelo Lucas
    Secondary: --wedo-navy (#1E3A5F) — a ser validado pelo Lucas
    Accent: --lia-purple (#8B5CF6) — a ser validado pelo Lucas
    Success: --wedo-green (#22C55E)
    Error: --electric-red (#de1c31)
    Warning: --wedo-yellow (#EAB308)
  Layout:
    Logo no Login: centralizado, max-width 200px, margin-bottom 32px
    Logo no Sidebar: 140px × auto, padding 16px
    Favicon: quadrado, fundo transparente (SVG) ou sólido (ICO)
  Estados:
    - Default: logo padrão WeDo Talent
    - White Label: logo substituído pelo tenant (AUTH-005)
    - Dark Mode: versão monocromática clara (futuro)
    - Loading: skeleton no lugar do logo
  Acessibilidade:
    - Alt text descritivo em todos os logos ("Logo WeDo Talent")
    - SVGs com role="img" e aria-label
    - Contraste WCAG AA em todas as variações de cor

Comportamento de UI:
  Fluxo Principal:
    1. Lucas entrega assets via Figma/Google Drive
    2. Dev substitui arquivos em /public/logos/ e /public/images/
    3. Atualiza referências de importação nos componentes
    4. Atualiza design tokens no globals.css se paleta mudar
    5. Verifica todas as telas: login, sidebar, header, emails
    6. Deploy e validação visual

  Layout:
    Login: Logo centralizado acima do formulário
    Sidebar: Logo no topo, versão compacta quando sidebar colapsado
    Header: Logo pequeno (32px height) à esquerda
    Emails: Logo no header do template, 200px max-width

  Estados de Botoes:
    N/A (card de design, sem botões novos)

  Validacoes Inline:
    N/A

  Mensagens de Feedback:
    - Assets não carregados: fallback para texto "WeDo Talent"
    - Imagem corrompida: alt text visível

Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md (Seções: 1.2 Paleta de Cores, 1.3 Tipografia, 2.14 Avatars — Referência global de marca)"
  Figma: "[A ser preenchido pelo Lucas — link do projeto de marca]"
  Assets:
    - "Logo WeDo Talent: /public/logos/wedo-talent-logo.svg (a ser atualizado)"
    - "Logo LIA: /public/logos/lia-avatar.svg (a ser atualizado)"
    - "Favicon: /public/favicon.ico (a ser atualizado)"
  Tokens:
    - "accent-primary: #60BED1 (a ser validado)"
    - "accent-secondary: #1E3A5F (a ser validado)"
    - "lia-accent: #8B5CF6 (a ser validado)"

DoD:
  - [ ] Assets entregues pelo Lucas (logo, ícones, paleta)
  - [ ] Logo WeDo Talent atualizado na tela de login
  - [ ] Logo WeDo Talent atualizado no sidebar e header
  - [ ] Logo LIA (avatar) atualizado
  - [ ] Favicon atualizado em todos os tamanhos
  - [ ] Open Graph images atualizadas
  - [ ] Email templates com marca atualizada
  - [ ] Paleta de cores aplicada nos design tokens
  - [ ] Guia de marca para white label documentado
  - [ ] Todas as telas verificadas visualmente

Criterios de Aceitacao:
  - [ ] Logo WeDo Talent aparece corretamente em login, sidebar, header
  - [ ] Logo LIA aparece no chat e interações com IA
  - [ ] Favicon correto no browser tab
  - [ ] Paleta de cores consistente em toda a plataforma
  - [ ] Email templates com marca atualizada (verificar em 3 clients: Gmail, Outlook, Apple Mail)
  - [ ] Assets em SVG com acessibilidade (alt text, aria-label)
  - [ ] Guia de white label entregue e revisado

Arquivos de Referencia (Prototipo Replit):
  - login-page.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/pages/login-page.tsx
  - auth-context.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/auth-context.tsx
  - globals.css: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/styles/globals.css
  - logos: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/public/logos/
```

---

### CARD WIZ-014: Revisão Metodologia Wizard com André

```yaml
Titulo: "[PROCESSO] Revisão de Metodologia Wizard Ponta a Ponta com André"
Tipo: Processo/Validação
Sprint: Pós-MVP
Pontos: 5
Prioridade: Média
Epic: EPIC-WIZARD
Status: 📋 A Criar no Jira
Dependencias: WSI-001, TRI-004, SCO-001

Descricao: |
  Sessão de revisão com André para validar toda a metodologia WSI
  implementada no wizard: geração de perguntas, condução de triagem,
  avaliação de respostas, e cálculo de scores. Só pode acontecer
  quando o fluxo completo (wizard → perguntas → triagem → score)
  estiver funcional no protótipo ou em staging.

Historia de Usuario: |
  Como responsável pela metodologia WSI, André quer validar que a
  implementação técnica preserva a integridade científica do método,
  incluindo sequência de perguntas, critérios de avaliação e pesos.

Regras de Negocio:
  1. Pré-requisito: geração de perguntas WSI (Épico 4) funcional
  2. Pré-requisito: triagem WhatsApp (Épico 5) funcional com respostas
  3. Pré-requisito: cálculo de score WSI (Épico 6) funcional
  4. André valida: sequência de perguntas, critérios de avaliação, pesos por bloco
  5. André valida: tom conversacional da LIA na triagem
  6. André valida: interpretação de respostas e scoring
  7. Resultado: documento de validação + lista de ajustes necessários
  8. Ajustes geram novos cards de correção no backlog
  9. Segunda rodada de validação após ajustes implementados

Requisitos Tecnicos:
  Frontend:
    - Nenhum componente novo direto
    - Demo funcional do fluxo completo para André testar
    - Possibilidade de gravar sessão para referência
  Backend:
    - Nenhuma alteração direta
    - Dados de teste com vagas e candidatos realistas para validação
  Dados:
    - Seed de vagas de teste variadas (tech, comercial, liderança)
    - Seed de candidatos simulados para triagem
  Validacoes:
    - Checklist de validação metodológica (preparar antes da sessão)
    - Documento de conformidade WSI preenchido por André

Design & Componentes:
  Componentes Existentes:
    - JobWizard - wizard de criação de vaga (fluxo completo)
    - WSIQuestionsStage - estágio de perguntas WSI
    - WSIQuestionsPanel - painel de perguntas geradas
    - ScreeningChat - chat de triagem (candidato)
    - ScoreDisplay - exibição de score WSI
  Novos Componentes:
    - Nenhum (validação de processo, não de UI)
  Design Tokens:
    N/A (sem alterações visuais)
  Layout:
    N/A (sessão presencial/remota de validação)
  Estados:
    - Pré-validação: preparação de dados e ambiente
    - Em validação: sessão com André em andamento
    - Pós-validação: documento de feedback recebido
    - Ajustes: cards de correção criados e em andamento
  Acessibilidade:
    N/A (processo, não componente)

Comportamento de UI:
  Fluxo Principal:
    1. Preparar ambiente de staging/demo com dados realistas
    2. Agendar sessão de 2-3h com André
    3. André navega pelo fluxo: criar vaga → gerar perguntas → simular triagem → ver scores
    4. André documenta observações por bloco WSI
    5. Consolidar feedback em documento de validação
    6. Criar cards de ajuste para cada item identificado
    7. Implementar ajustes
    8. Segunda rodada de validação (se necessário)

  Layout:
    N/A (processo de validação)

  Estados de Botoes:
    N/A

  Validacoes Inline:
    N/A

  Mensagens de Feedback:
    N/A

Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md (Seções: PARTE 3 Padrões de Interface — Referência metodológica)"
  Figma: "N/A (processo de validação)"
  Assets:
    - "Checklist de validação WSI (a ser criado antes da sessão)"
    - "Template de documento de validação metodológica"
  Tokens:
    - "N/A"

DoD:
  - [ ] Sessão de validação realizada com André (2-3h)
  - [ ] Documento de validação criado com observações por bloco WSI
  - [ ] Ajustes identificados registrados como cards no Jira
  - [ ] Priorização dos ajustes definida com André
  - [ ] Segunda rodada de validação agendada (se necessário)

Criterios de Aceitacao:
  - [ ] André consegue navegar pelo fluxo completo: vaga → perguntas → triagem → score
  - [ ] Perguntas geradas estão em conformidade com a metodologia WSI
  - [ ] Sequência de blocos WSI respeita a ordem metodológica
  - [ ] Critérios de avaliação e pesos estão corretos por bloco
  - [ ] Tom conversacional da LIA é adequado para triagem profissional
  - [ ] Scoring de respostas reflete a metodologia validada
  - [ ] Documento de validação assinado/aprovado por André

Arquivos de Referencia (Prototipo Replit):
  - WSIQuestionsStage.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/job-wizard/stages/WSIQuestionsStage.tsx
  - WSIQuestionsPanel.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/ui-actions/panels/WSIQuestionsPanel.tsx
  - screening-config: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/screening-config/
  - wsi-components: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/wsi/
```

---

### CARD MAP-014: Revisão de Qualidade de Busca com André

```yaml
Titulo: "[PROCESSO] Revisão de Qualidade de Busca com André"
Tipo: Processo/Validação
Sprint: 3
Pontos: 3
Prioridade: Média
Epic: EPIC-MAPPING
Status: 📋 A Criar no Jira
Dependencias: MAP-001, MAP-003

Descricao: |
  André revisa a qualidade dos resultados de busca: relevância dos candidatos
  retornados, ordenação, filtros, e documenta feedback sobre gaps de qualidade.
  Sessão prática com busca funcional (ElasticSearch + PGVector + WRF) para
  validar que o sistema retorna candidatos relevantes para diferentes perfis de vaga.

Historia de Usuario: |
  Como responsável pela qualidade de recrutamento, André quer validar
  que os resultados de busca são relevantes e bem ordenados, garantindo
  que recrutadores encontrem os melhores candidatos rapidamente.

Regras de Negocio:
  1. Pré-requisito: busca semântica funcional (MAP-001 + MAP-002)
  2. Pré-requisito: filtros avançados funcionando (MAP-003)
  3. André testa 5-10 buscas com perfis variados (tech, comercial, liderança)
  4. Avaliação por busca: relevância top-5, relevância top-10, falsos positivos
  5. Documentar gaps: candidatos esperados mas não retornados
  6. Documentar ruído: candidatos irrelevantes no top-10
  7. Feedback sobre ordenação: o melhor candidato está no topo?
  8. Resultado: documento de feedback + lista de ajustes de scoring/ranking

Requisitos Tecnicos:
  Frontend:
    - Nenhum componente novo direto
    - Busca funcional com resultados reais para André testar
    - Filtros avançados aplicáveis durante teste
  Backend:
    - Nenhuma alteração direta
    - Dados reais ou realistas seedados para buscas de teste
    - Logs de busca habilitados para análise posterior
  Dados:
    - Base de candidatos seedada com perfis variados (mínimo 100)
    - Vagas de teste com diferentes perfis e requisitos
  Validacoes:
    - Checklist de qualidade de busca (preparar antes da sessão)
    - Métricas: precision@5, precision@10, NDCG por busca

Design & Componentes:
  Componentes Existentes:
    - SmartSearchInput - campo de busca inteligente
    - SearchResultsCard - card de resultado de busca
    - AdvancedFiltersModal - filtros avançados
    - MatchingScoreBadge - badge de score
  Novos Componentes:
    - Nenhum (validação de qualidade, não de UI)
  Design Tokens:
    N/A (sem alterações visuais)
  Layout:
    N/A (sessão de validação)
  Estados:
    - Pré-validação: preparar dados e checklist
    - Em validação: André testando buscas
    - Pós-validação: feedback documentado
    - Ajustes: implementação de melhorias
  Acessibilidade:
    N/A (processo, não componente)

Comportamento de UI:
  Fluxo Principal:
    1. Preparar ambiente com base de candidatos realista (100+ perfis)
    2. Preparar checklist de qualidade com 10 buscas planejadas
    3. Agendar sessão de 1-2h com André
    4. André executa cada busca e avalia resultados
    5. Anotar por busca: top-5 relevantes? falsos positivos? faltando alguém?
    6. Testar filtros: skill, experiência, localização, senioridade
    7. Documentar feedback consolidado
    8. Criar cards de ajuste para gaps identificados

  Layout:
    N/A (processo de validação)

  Estados de Botoes:
    N/A

  Validacoes Inline:
    N/A

  Mensagens de Feedback:
    N/A

Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md (Seções: 2.5 Tabelas, 2.6 Badges & Tags, 2.13 Progress Indicators)"
  Figma: "N/A (processo de validação)"
  Assets:
    - "Checklist de qualidade de busca (a ser criado antes da sessão)"
    - "Template de feedback de qualidade"
  Tokens:
    - "N/A"

DoD:
  - [ ] Sessão de revisão realizada com André (1-2h)
  - [ ] Feedback documentado por busca (mínimo 5 buscas avaliadas)
  - [ ] Gaps de qualidade identificados e registrados
  - [ ] Ajustes de scoring/ranking documentados como cards
  - [ ] Métricas de precision@5 e precision@10 calculadas

Criterios de Aceitacao:
  - [ ] André consegue buscar candidatos com busca semântica
  - [ ] Filtros avançados funcionam corretamente na sessão
  - [ ] Top-5 resultados são relevantes em pelo menos 80% das buscas
  - [ ] Falsos positivos identificados são < 20% dos resultados
  - [ ] Feedback documentado com ações claras de melhoria
  - [ ] Cards de ajuste criados para cada gap identificado

Arquivos de Referencia (Prototipo Replit):
  - search-results-card.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/search/search-results-card.tsx
  - smart-search-input.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/search/smart-search-input.tsx
  - advanced-filters-modal.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/filters/advanced-filters-modal.tsx
  - search hooks: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/
```

---

### CARD WSI-006: Edição de Perguntas WSI via Prompt Conversacional

```yaml
Titulo: "[AI] Edição de Perguntas WSI via Prompt Conversacional"
Tipo: Feature (AI + Full-Stack)
Sprint: 2
Pontos: 8
Prioridade: Alta
Epic: EPIC-WSI
Status: 📋 A Criar no Jira
Dependencias: WSI-001, WSI-002, WSI-003
Substitui: WSI-004 (removido — edição manual direta quebra integridade WSI)

Descricao: |
  Em vez de editar perguntas WSI diretamente (o que quebraria a metodologia),
  o recrutador pede ajustes via chat com a LIA. Exemplo: "Não gostei da
  pergunta sobre liderança, quero algo mais voltado a gestão de conflitos".
  A LIA regenera as perguntas mantendo a integridade do WSI.
  Máximo de 5 iterações de ajuste por bloco para evitar degradação da qualidade.

Historia de Usuario: |
  Como recrutador, eu quero pedir ajustes nas perguntas geradas pela LIA
  sem quebrar a metodologia WSI, usando linguagem natural para descrever
  o que precisa mudar.

Regras de Negocio:
  1. Recrutador NÃO edita texto das perguntas diretamente
  2. Recrutador descreve o que quer mudar via chat com LIA
  3. LIA interpreta o pedido e regenera perguntas mantendo conformidade WSI
  4. Novas perguntas mantêm estrutura do bloco WSI (blocos, pesos, sequência)
  5. Preview mostra antes/depois (diff) para comparação clara
  6. Recrutador pode aceitar ou pedir nova iteração
  7. Máximo 5 iterações de ajuste por bloco
  8. Após 5 iterações: mensagem "Limite atingido. Aceite ou volte ao original."
  9. Opção de reverter para perguntas originais a qualquer momento
  10. Log de todas as iterações para auditoria

Requisitos Tecnicos:
  Frontend:
    - QuestionAdjustmentChat: chat inline focado em ajustes de perguntas
    - QuestionDiffView: antes/depois side-by-side das perguntas
    - AdjustmentCounter: indicador "Ajuste 2 de 5"
    - Botões "Aceitar alteração" / "Pedir outro ajuste" / "Reverter ao original"
    - Integrar ao WSIQuestionsStage existente
    - Loading state durante regeneração (skeleton das perguntas)
  Backend:
    - POST /api/v1/wsi/questions/adjust
    - Request: { job_id, block_id, adjustment_prompt, current_questions, iteration_count }
    - Response: { new_questions, wsi_compliance_check, iteration, diff }
    - WSIQuestionAdjuster service com validação de conformidade WSI
    - Validação pós-geração: bloco correto, número de perguntas, formato
    - Persistência de histórico de ajustes: question_adjustment_history
  Dados:
    - question_adjustment_history: id, job_id, block_id, iteration, original_questions, adjusted_questions, adjustment_prompt, wsi_compliance_passed, created_at
  Validacoes:
    - iteration_count <= 5 por bloco
    - adjustment_prompt não vazio (mínimo 10 caracteres)
    - WSI compliance check pós-geração (estrutura de bloco preservada)

Integracoes Externas:
  LLM (Gemini):
    - Tipo: AI API
    - Uso: Regeneração de perguntas WSI com ajustes solicitados pelo recrutador
    - Serviço: wsi_question_adjuster.py
    - SDK: google-generativeai
    - Secret: GEMINI_API_KEY
    - Custo: ~$0.002-0.005 por ajuste (Flash)
    - Rate Limit: 60 RPM (requests por minuto)
    - Documentacao: https://ai.google.dev/docs

Configuracao LLM:
  Modelo: Gemini 2.5 Flash (rápido para iterações)
  Temperature: 0.7
  Max Tokens: 2000
  
  Prompt Template: |
    <role>
    Você é especialista em metodologia WSI (Weighted Structured Interview) da 
    plataforma WeDo Talent. Sua tarefa é regenerar perguntas de avaliação mantendo 
    a integridade metodológica do WSI.
    </role>
    
    <context>
    Vaga: {{job_title}} (Nível: {{seniority_level}})
    Bloco WSI: {{block_name}}
    Competências avaliadas: {{block_competencies}}
    Iteração atual: {{iteration_count}} de 5
    
    Perguntas atuais:
    {{current_questions}}
    Pedido de ajuste do recrutador:
    "{{adjustment_prompt}}"
    </context>
    
    <task>
    1. Analise o pedido do recrutador e regenere as perguntas WSI atendendo ao ajuste solicitado
    2. Mantenha a conformidade metodológica WSI (estrutura de bloco, formato STAR, competências)
    3. Retorne as perguntas ajustadas com resumo das alterações e checklist de conformidade
    </task>
    
    <constraints>
    1. Manter EXATAMENTE o mesmo número de perguntas do bloco original
    2. Preservar o formato situacional/comportamental WSI (STAR method)
    3. Manter alinhamento com as competências definidas para o bloco
    4. Adequar complexidade ao nível de senioridade do cargo
    5. Não introduzir perguntas fora do escopo das competências do bloco
    6. Cada pergunta deve ter critérios de avaliação claros
    7. Perguntas devem ser abertas (evitar sim/não)
    </constraints>
    
    <output_format>
    {
      "adjusted_questions": [
        {
          "id": "q1",
          "question": "...",
          "competency": "...",
          "evaluation_criteria": ["..."],
          "difficulty": "junior|pleno|senior|lead"
        }
      ],
      "changes_summary": "Resumo das alterações realizadas",
      "wsi_compliance_check": {
        "block_structure_preserved": true,
        "question_count_match": true,
        "competencies_aligned": true,
        "format_valid": true
      }
    }
    </output_format>

Design & Componentes:
  Componentes Existentes:
    - WSIQuestionsPanel - painel de perguntas geradas
    - WSIQuestionsStage - estágio do wizard
    - ChatSidebar - sidebar de chat (reutilizar layout)
    - Button - botões de ação
    - Card - container
    - Badge - contador
  Novos Componentes:
    - QuestionAdjustmentChat - chat focado em ajustes WSI
    - QuestionDiffView - visualização antes/depois das perguntas
    - AdjustmentCounter - badge "Ajuste 2 de 5" com barra de progresso
    - RevertButton - botão para reverter ao original
  Design Tokens:
    Before (original): --lia-text-tertiary (#6B7280)
    After (ajustado): --wedo-cyan (#60BED1)
    Accepted: --wedo-green (#22C55E)
    Rejected: --electric-red (#de1c31)
    Counter: --wedo-yellow (#EAB308)
    Diff Added: --lia-bg-success-subtle (#F0FDF4)
    Diff Removed: --lia-bg-error-subtle (#FEF2F2)
  Layout:
    Container: flex row — perguntas (60%) + chat de ajuste (40%)
    DiffView: side-by-side em desktop, stacked em mobile
    Counter: badge no topo do chat (sticky)
    Botões: footer fixo do chat panel
  Estados:
    - Default: perguntas exibidas, chat colapsado
    - Editing: chat aberto, recrutador digitando pedido
    - Loading: skeleton nas perguntas enquanto LLM regenera
    - Diff: antes/depois exibido para comparação
    - Accepted: perguntas novas aplicadas, diff verde
    - Reverted: voltou ao original, toast de confirmação
    - Max Iterations: chat desabilitado, mensagem de limite
  Acessibilidade:
    - Chat com role="log" e aria-live="polite"
    - Diff view com aria-label "Comparação de perguntas"
    - Counter com aria-label "Ajuste 2 de 5"
    - Botões com aria-label descritivo
    - Keyboard navigation: Tab entre chat e diff

Comportamento de UI:
  Fluxo Principal:
    1. Recrutador visualiza perguntas WSI geradas no WSIQuestionsStage
    2. Clica em "Ajustar perguntas" → chat de ajuste abre à direita
    3. Digita pedido: "Quero perguntas mais focadas em gestão de conflitos"
    4. Loading: skeleton nas perguntas + spinner no chat
    5. LIA retorna novas perguntas + diff view (antes/depois)
    6. Recrutador avalia: "Aceitar" ou "Pedir outro ajuste"
    7. Se aceitar: perguntas atualizadas, chat fecha, toast de sucesso
    8. Se pedir ajuste: volta ao passo 3 (iteration_count++)
    9. Se iteration_count == 5: mensagem de limite, só aceitar/reverter

  Layout:
    Desktop: Split view 60/40 (perguntas | chat)
    Tablet: Split view 50/50
    Mobile: Tab switching (perguntas ↔ chat)

  Estados de Botoes:
    Ajustar Perguntas:
      - Default: bg-transparent, border --wedo-cyan, text --wedo-cyan
      - Hover: bg-wedo-cyan/10
      - Active: chat aberto, botão vira "Fechar ajuste"
    Aceitar Alteração:
      - Default: bg-wedo-green, text white
      - Hover: bg-wedo-green/90
      - Disabled: durante loading
    Pedir Outro Ajuste:
      - Default: bg-transparent, border --lia-border-subtle
      - Hover: bg-lia-bg-secondary
      - Disabled: se iteration_count >= 5
    Reverter ao Original:
      - Default: text --electric-red, underline
      - Hover: bg-red-50
      - Confirm: dialog "Tem certeza? Todas as alterações serão perdidas."

  Validacoes Inline:
    Prompt de Ajuste:
      - Vazio: "Descreva o que você gostaria de ajustar nas perguntas"
      - Muito curto (< 10 chars): "Descreva com mais detalhes o ajuste desejado"
    Limite de Iterações:
      - Atingido: "Você atingiu o limite de 5 ajustes para este bloco. Aceite as perguntas atuais ou reverta ao original."

  Mensagens de Feedback:
    - Sucesso ajuste: "Perguntas ajustadas com sucesso! Verifique o antes/depois."
    - Sucesso aceite: "Perguntas atualizadas! ✓ Conformidade WSI validada."
    - Revertido: "Perguntas revertidas ao original."
    - Erro LLM: "Erro ao regenerar perguntas. Tente novamente."
    - Falha conformidade: "As perguntas geradas não passaram na validação WSI. Tentando novamente..."
    - Limite atingido: "Limite de 5 ajustes atingido. Aceite ou reverta."

Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md (Seções: 2.3 Cards, 2.2 Inputs & Forms, 2.6 Badges & Tags, 2.13 Progress Indicators)"
  Figma: "[A ser preenchido pelo time de Design — tela de ajuste WSI]"
  Assets:
    - "Ícone de ajuste: lucide-react/Wand2"
    - "Ícone de diff: lucide-react/GitCompare"
    - "Ícone de reverter: lucide-react/RotateCcw"
  Tokens:
    - "diff-added: #F0FDF4"
    - "diff-removed: #FEF2F2"
    - "accent-primary: #60BED1"
    - "success: #22C55E"

DoD:
  - [ ] Chat de ajuste funcional e integrado ao WSIQuestionsStage
  - [ ] LLM (Gemini 2.5 Flash) regenera perguntas a partir do prompt do recrutador
  - [ ] Validação de conformidade WSI pós-geração funcional
  - [ ] Diff view (antes/depois) renderiza corretamente
  - [ ] Contador de iterações funcional (máximo 5 por bloco)
  - [ ] Botão "Reverter ao original" funciona
  - [ ] Persistência de histórico de ajustes no banco
  - [ ] Responsivo (desktop, tablet, mobile)
  - [ ] Loading states e error handling

Criterios de Aceitacao:
  - [ ] Recrutador pede ajuste em linguagem natural e recebe perguntas regeneradas
  - [ ] Perguntas regeneradas mantêm conformidade WSI (estrutura de bloco preservada)
  - [ ] Preview antes/depois (diff) funciona com highlighting de mudanças
  - [ ] Aceitação aplica novas perguntas e fecha chat com toast de sucesso
  - [ ] Rejeição permite novo pedido de ajuste (até 5x)
  - [ ] Após 5 iterações, chat desabilitado com mensagem de limite
  - [ ] Reverter ao original funciona com confirmação
  - [ ] Erro de LLM exibe mensagem amigável e permite retry

Arquivos de Referencia (Prototipo Replit):
  - WSIQuestionsStage.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/job-wizard/stages/WSIQuestionsStage.tsx
  - WSIQuestionsPanel.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/ui-actions/panels/WSIQuestionsPanel.tsx
  - wsi-components: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/wsi/
  - chat-sidebar: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/chat/
  - job-wizard hooks: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/job-wizard/hooks/
```

---

### CARD TRI-013: Sistema de Reporte de Problemas pelo Candidato

```yaml
Titulo: "[FULL-STACK] Sistema de Reporte de Problemas pelo Candidato"
Tipo: Feature (Full-Stack)
Sprint: 3
Pontos: 5
Prioridade: Alta
Epic: EPIC-TRIAGEM
Status: 📋 A Criar no Jira
Dependencias: TRI-003, TRI-004

Descricao: |
  Sistema de reporte de problemas durante a triagem via WhatsApp.
  Ao iniciar a triagem (após aceite LGPD), a LIA informa proativamente
  o candidato sobre o procedimento de reporte: se houver qualquer problema,
  ele pode digitar palavras-chave (ex: "AJUDA", "#PROBLEMA") e receberá
  retorno em até 24 horas. Ao detectar a keyword, a LIA pausa a conversa,
  cria um incidente e notifica o time WeDo Talent (suporte/operações),
  NÃO o recrutador do cliente. O time WeDo Talent pode assumir a
  conversa manualmente, resetar a LIA ou escalonar.

Historia de Usuario: |
  Como candidato em triagem via WhatsApp, eu quero ser informado no início
  da triagem sobre como reportar problemas, e se a IA não fizer sentido,
  eu quero poder digitar um código para que o time de suporte me ajude
  em até 24 horas.

Regras de Negocio:
  1. LIA informa procedimento de reporte no INÍCIO da triagem (pós-LGPD):
     "Se a qualquer momento você tiver algum problema ou eu não fizer sentido,
     basta digitar AJUDA que nosso time será notificado e retornará em até 24 horas."
  2. Palavras-chave de escape: "AJUDA", "#PROBLEMA", "PARAR", "HUMANO", "HELP"
  3. Detecção case-insensitive e com tolerância a acentos (AJUDA = ajuda = Ajudá)
  4. Ao detectar keyword: pausar conversa da LIA imediatamente
  5. Criar incidente automático com: candidato_id, job_id, timestamp, últimas 5 mensagens, trigger_keyword
  6. Notificar time WeDo Talent (suporte/operações) — NÃO o recrutador do cliente: push notification + email
  7. Candidato recebe mensagem: "Entendi! Nosso time foi notificado e entrará em contato em até 24 horas. 🙏"
  8. Time WeDo Talent pode: (a) assumir conversa manualmente, (b) resetar LIA, (c) marcar como resolvido, (d) escalonar
  9. SLA de resposta: 24 horas (configurável por tenant)
  10. Escalonamento: se SLA não cumprido, notificar admin WeDo Talent
  11. Incidente resolvido: log de resolução + candidato pode continuar triagem

Requisitos Tecnicos:
  Frontend:
    - IncidentsPanel: lista de incidentes pendentes/resolvidos com filtros (para time WeDo Talent)
    - IncidentDetailView: detalhes do incidente + histórico de conversa + ações
    - IncidentBadge: contador de incidentes pendentes no sidebar/header
    - Botões de ação: "Assumir conversa" / "Resetar LIA" / "Marcar resolvido" / "Escalonar"
    - Integração com sistema de notificações existente
  Backend:
    - Mensagem proativa da LIA no início da triagem (pós-LGPD) informando procedimento de reporte
    - Detecção de palavras-chave no message handler (WhatsApp webhook)
    - POST /api/v1/incidents (criação automática ao detectar keyword)
    - GET /api/v1/incidents (lista paginada com filtros: status, job_id, date)
    - GET /api/v1/incidents/{id} (detalhes + conversa)
    - PATCH /api/v1/incidents/{id} (atualizar status: assigned, resolved)
    - POST /api/v1/incidents/{id}/assign (time WeDo Talent assume)
    - POST /api/v1/incidents/{id}/resolve (marcar resolvido)
    - Notificação push + email para time WeDo Talent (suporte/operações) — NÃO para recrutador do cliente
    - SLA checker: job agendado que verifica incidentes não resolvidos (SLA padrão 24h)
  Dados:
    - screening_incidents: id, candidate_id, job_id, trigger_keyword, last_messages (JSONB), status (enum: open, assigned, resolved, escalated), assigned_to (user_id nullable), resolution_note, sla_deadline, created_at, resolved_at, updated_at
    - incident_notifications: id, incident_id, user_id, channel (push/email), sent_at, read_at
  Validacoes:
    - Palavras-chave não devem gerar falsos positivos em contexto normal
    - Incidente duplicado: não criar novo se já existe incidente aberto para mesmo candidato+vaga
    - SLA deadline: 24 horas a partir da criação do incidente (configurável por tenant)

Design & Componentes:
  Componentes Existentes:
    - NotificationCenter - centro de notificações (adicionar badge)
    - CandidateCard - card do candidato (adicionar indicador de incidente)
    - Sidebar - menu lateral (adicionar badge de incidentes)
    - Toast - feedback de ações
    - Badge - contadores
  Novos Componentes:
    - IncidentsPanel - painel com lista de incidentes (tabela + filtros)
    - IncidentDetailView - detalhes do incidente com timeline de conversa
    - IncidentBadge - badge vermelho com contador no sidebar
    - IncidentActionBar - barra de ações (assumir, resetar, resolver)
    - IncidentSLAIndicator - indicador visual de tempo restante do SLA
  Design Tokens:
    Urgente/Aberto: --electric-red (#de1c31)
    Atribuído: --wedo-yellow (#EAB308)
    Resolvido: --wedo-green (#22C55E)
    Escalado: --electric-red (#de1c31) + pulsing animation
    SLA OK: --wedo-green (#22C55E)
    SLA Warning (< 30min): --wedo-yellow (#EAB308)
    SLA Estourado: --electric-red (#de1c31)
    Background: --lia-bg-primary (#FFFFFF)
    Card Border Incident: --electric-red (#de1c31) / 20% opacity
  Layout:
    IncidentsPanel: full-width table com colunas (candidato, vaga, keyword, status, SLA, ações)
    IncidentDetail: split view — detalhes (60%) + conversa (40%)
    Badge: circle vermelho no sidebar, 20px, font-size 11px
    Mobile: stack vertical (detalhes acima, conversa abaixo)
  Estados:
    - Sem incidentes: painel vazio com ícone e texto "Nenhum incidente pendente"
    - Incidentes pendentes: badge vermelho pulsante no sidebar
    - Incidente aberto: card vermelho com timer SLA
    - Incidente atribuído: card amarelo com nome do operador WeDo Talent
    - Incidente resolvido: card verde com nota de resolução
    - SLA estourado: card vermelho com ícone de alerta + escalonamento
  Acessibilidade:
    - Badge com aria-label "X incidentes pendentes"
    - Lista com role="list" e items com role="listitem"
    - Ações com aria-label descritivo
    - SLA timer com aria-live="polite" para atualizações
    - Cores complementadas com ícones (não depender só de cor)

Comportamento de UI:
  Fluxo Proativo (Início da Triagem):
    1. Candidato aceita LGPD e inicia triagem
    2. LIA envia mensagem proativa informando procedimento de reporte:
       "Se a qualquer momento você tiver algum problema ou eu não fizer sentido,
       basta digitar AJUDA que nosso time será notificado e retornará em até 24 horas."
    3. Triagem prossegue normalmente

  Fluxo de Reporte:
    1. Candidato digita "AJUDA" durante triagem WhatsApp
    2. Backend detecta keyword, pausa conversa da LIA
    3. Candidato recebe: "Entendi! Nosso time foi notificado e entrará em contato em até 24 horas. 🙏"
    4. Incidente criado automaticamente com últimas 5 mensagens
    5. Time WeDo Talent (suporte) recebe notificação push + email
    6. Badge vermelho aparece no sidebar do operador WeDo Talent
    7. Operador abre IncidentsPanel, vê incidente com SLA timer (24h)
    8. Clica no incidente → IncidentDetailView com conversa
    9. Escolhe: "Assumir conversa" (fala direto com candidato), "Resetar LIA", ou "Escalonar"
    10. Ao resolver: marca como resolvido com nota, candidato pode continuar

  Layout:
    Desktop: Sidebar badge + IncidentsPanel full-width + IncidentDetail split 60/40 (painel do time WeDo Talent)
    Tablet: IncidentsPanel full-width, IncidentDetail stacked
    Mobile: Badge no header, lista mobile-friendly, detail full-screen

  Estados de Botoes:
    Assumir Conversa:
      - Default: bg-wedo-cyan, text white
      - Hover: bg-wedo-cyan/90
      - Loading: spinner + "Assumindo..."
      - Disabled: se já atribuído a outro operador
    Resetar LIA:
      - Default: bg-transparent, border --wedo-yellow
      - Hover: bg-wedo-yellow/10
      - Confirm: dialog "Resetar a LIA e retomar triagem automática?"
    Marcar Resolvido:
      - Default: bg-wedo-green, text white
      - Hover: bg-wedo-green/90
      - Requires: nota de resolução obrigatória (mínimo 10 chars)

  Validacoes Inline:
    Nota de Resolução:
      - Vazia: "Descreva como o incidente foi resolvido"
      - Muito curta (< 10 chars): "Detalhe a resolução (mínimo 10 caracteres)"

  Mensagens de Feedback:
    - Incidente criado: "[interno] Novo incidente #123 — candidato João Silva na vaga Analista" (toast para time WeDo Talent)
    - Conversa assumida: "Você assumiu a conversa com João Silva. Mensagens serão enviadas por você."
    - LIA resetada: "LIA reiniciada. A triagem automática continuará de onde parou."
    - Incidente resolvido: "Incidente #123 resolvido. Candidato pode continuar a triagem."
    - SLA estourado: "⚠️ Incidente #123 sem resposta há 24h. Escalonando para admin WeDo Talent."
    - Erro: "Erro ao processar incidente. Tente novamente."

Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md (Seções: 2.3 Cards, 2.6 Badges & Tags, 2.8 Toasts & Alerts, 2.11 Dropdowns & Menus)"
  Figma: "[A ser preenchido pelo time de Design — tela de incidentes]"
  Assets:
    - "Ícone de alerta: lucide-react/AlertTriangle"
    - "Ícone de resolver: lucide-react/CheckCircle"
    - "Ícone de assumir: lucide-react/UserCheck"
    - "Ícone de resetar: lucide-react/RotateCcw"
    - "Ícone de SLA: lucide-react/Clock"
  Tokens:
    - "urgente: #de1c31"
    - "atribuido: #EAB308"
    - "resolvido: #22C55E"
    - "bg-primary: #FFFFFF"

DoD:
  - [ ] LIA informa procedimento de reporte no início da triagem (pós-LGPD)
  - [ ] Detecção de palavras-chave de escape funcional no message handler
  - [ ] Conversa da LIA pausada ao detectar keyword
  - [ ] Incidente criado automaticamente com últimas 5 mensagens
  - [ ] Notificação push + email enviada ao time WeDo Talent (NÃO ao recrutador do cliente)
  - [ ] Candidato recebe confirmação com prazo de 24h
  - [ ] IncidentsPanel com lista e filtros funcional (para time WeDo Talent)
  - [ ] IncidentDetailView com conversa e ações funcional
  - [ ] Badge de incidentes no sidebar com contador
  - [ ] Ação "Assumir conversa" funcional
  - [ ] Ação "Resetar LIA" funcional
  - [ ] Ação "Marcar resolvido" com nota obrigatória
  - [ ] SLA timer (24h) e escalonamento funcional
  - [ ] Responsivo (desktop, tablet, mobile)

Criterios de Aceitacao:
  - [ ] LIA envia mensagem proativa sobre reporte no início da triagem (pós-LGPD)
  - [ ] Candidato digita "AJUDA" → conversa pausa imediatamente
  - [ ] Candidato recebe mensagem de confirmação com prazo de 24h
  - [ ] Incidente aparece na lista do time WeDo Talent em < 5 segundos
  - [ ] Notificação push + email recebida pelo time WeDo Talent (NÃO pelo recrutador)
  - [ ] Badge vermelho aparece no sidebar com contagem correta
  - [ ] Operador WeDo Talent consegue ver histórico de conversa no detalhe do incidente
  - [ ] "Assumir conversa" permite envio manual de mensagens ao candidato
  - [ ] "Resetar LIA" retoma triagem automática
  - [ ] SLA timer funciona corretamente (24 horas)
  - [ ] Incidentes duplicados não são criados (mesmo candidato+vaga)

Arquivos de Referencia (Prototipo Replit):
  - notification-center.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/notifications/notification-center.tsx
  - notification-context.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/notifications/notification-context.tsx
  - screening-config: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/screening-config/
  - kanban-board: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/kanban/components/KanbanBoard.tsx
  - candidate-card: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/kanban/components/CandidateCard.tsx
```

---

### CARD TRI-014: Pesquisa de Alternativas a Twilio

> ⚠️ **DISCLAIMER:** A pesquisa e avaliação sobre Twilio e suas alternativas é de responsabilidade exclusiva do **Paulo Moraes**.

```yaml
Titulo: "[PESQUISA] Pesquisa de Alternativas a Twilio para Disparo WhatsApp"
Tipo: Research/Spike
Sprint: 1
Pontos: 3
Prioridade: Crítica
Epic: EPIC-TRIAGEM
Status: 📋 A Criar no Jira
Responsavel: Paulo Moraes (pesquisa exclusiva)
Dependencias: Nenhuma (card bloqueante — habilita Épico 5 inteiro)
Consolida: INT-ALT-001 (Alternativa a Twilio para WhatsApp — mesmo escopo, card único)

Descricao: |
  ⚠️ DISCLAIMER: A pesquisa sobre Twilio e alternativas é de responsabilidade
  exclusiva do Paulo Moraes.

  Pesquisar e comparar alternativas ao Twilio para disparo de mensagens
  WhatsApp Business, priorizando soluções que aceitem número fornecido
  pelo cliente (BYOD — Bring Your Own Device) e tenham homologação
  simplificada no Brasil. Twilio ficou sem sentido por exigir número
  homologado e ter processo complexo no Brasil.
  Este card consolida INT-ALT-001 (mesmo escopo) em um único card.

Historia de Usuario: |
  Como CTO, eu quero avaliar alternativas ao Twilio para disparo de
  WhatsApp que sejam mais viáveis no Brasil (homologação, custo, suporte),
  para desbloquear o desenvolvimento da triagem via WhatsApp.

Regras de Negocio:
  1. Avaliar mínimo 5 alternativas: Tudu, Zenvia, Slickflow, WhatsApp Business Cloud API, Gupshup
  2. Critérios obrigatórios de avaliação (ver lista abaixo)
  3. Tabela comparativa completa com pontuação por critério
  4. POC (Proof of Concept) com as 2 melhores alternativas
  5. POC deve incluir: envio de mensagem, recebimento de webhook, template Meta
  6. Recomendação final documentada com justificativa
  7. Considerar: escalabilidade (1K → 100K mensagens/mês), multi-tenant, logs/auditoria
  8. Budget de referência: máximo R$ 0,15/mensagem (média)
  9. Resultado deve habilitar implementação de abstração de provider (TRI-001)

Criterios de Avaliacao:
  1. Custo por mensagem (HSM template + sessão 24h)
  2. Facilidade de homologação de número no Brasil (BYOD vs número deles)
  3. Suporte a templates Meta (criação, submissão, aprovação, variáveis)
  4. Webhook de status (enviado, entregue, lido, falha) com latência
  5. SDK/API quality (documentação, tipagem, exemplos, SDKs oficiais)
  6. Suporte Brasil (idioma, SLA de suporte, horário, representante local)
  7. SLA de entrega de mensagens (< 5s para 95% das mensagens)
  8. Sandbox/ambiente de teste gratuito para desenvolvimento
  9. Escalabilidade (throughput, rate limits, filas)
  10. Compliance (LGPD, dados no Brasil, criptografia)

Requisitos Tecnicos:
  Frontend:
    - Nenhum (pesquisa e documentação)
  Backend:
    - POC com 2 providers: script de envio + recebimento de webhook
    - Validar: latência de entrega, formato de webhook, retry policy
    - Documentar interface abstrata para WhatsApp provider
  Dados:
    - Tabela comparativa em formato Markdown/spreadsheet
    - Logs da POC: tempos de entrega, taxas de sucesso, erros
  Validacoes:
    - POC deve enviar mínimo 50 mensagens de teste por provider
    - Webhook deve ser recebido em < 10s após envio
    - Template Meta deve ser aprovado no sandbox

Design & Componentes:
  Componentes Existentes:
    - Nenhum (pesquisa, não UI)
  Novos Componentes:
    - Nenhum (pesquisa, não UI)
  Design Tokens:
    N/A
  Layout:
    N/A (documento de pesquisa)
  Estados:
    - Pesquisa: levantamento de informações e pricing
    - POC: implementação e teste com top 2
    - Análise: consolidação de resultados
    - Recomendação: documento final com decisão
  Acessibilidade:
    N/A

Comportamento de UI:
  Fluxo Principal:
    1. Levantar informações de pricing e features de cada provider
    2. Preencher tabela comparativa com 10 critérios × 5 providers
    3. Pontuar cada provider por critério (1-5)
    4. Selecionar top 2 por pontuação total
    5. Implementar POC com top 2 (envio + webhook + template)
    6. Executar testes: 50 mensagens por provider, medir latência e taxa de sucesso
    7. Consolidar resultados em documento de recomendação
    8. Apresentar para time e tomar decisão

  Layout:
    N/A (documento)

  Estados de Botoes:
    N/A

  Validacoes Inline:
    N/A

  Mensagens de Feedback:
    N/A

Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md (Seções: N/A — Card de pesquisa documental)"
  Figma: "N/A (pesquisa)"
  Assets:
    - "Template de tabela comparativa de providers"
    - "Template de documento de recomendação técnica"
  Tokens:
    - "N/A"

DoD:
  - [ ] Tabela comparativa preenchida com 5 providers × 10 critérios
  - [ ] POC implementada com top 2 alternativas
  - [ ] POC testada: mínimo 50 mensagens por provider
  - [ ] Webhook de status validado (enviado, entregue, lido)
  - [ ] Template Meta submetido e aprovado no sandbox de cada provider
  - [ ] Métricas de POC documentadas (latência, taxa sucesso, custo real)
  - [ ] Recomendação final documentada com justificativa
  - [ ] Interface abstrata de WhatsApp provider documentada (para TRI-001)
  - [ ] INT-ALT-001 marcado como consolidado neste card

Criterios de Aceitacao:
  - [ ] Todos os 5 providers avaliados com 10 critérios cada
  - [ ] Pontuação total calculada e ranking definido
  - [ ] POC com top 2 providers funcional (envio + recebimento)
  - [ ] Latência de entrega < 5s para 95% das mensagens em ambas as POCs
  - [ ] Custo por mensagem dentro do budget (≤ R$ 0,15/msg)
  - [ ] Recomendação final clara com provider escolhido
  - [ ] Documento acessível para todo o time técnico
  - [ ] Interface abstrata de provider permite trocar provider sem mudar código de negócio

Arquivos de Referencia (Prototipo Replit):
  - screening-config: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/screening-config/
  - middleware: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/middleware/
  - services: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/
  - whatsapp-related: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/ats_clients/
```

---

### 8.2 Novos Cards — Segunda Parte (GAT, TPL, NOT, KAN)

> Os 6 cards abaixo são especificações completas no formato Jira dos cards novos identificados na reunião de 06/02/2026 para os épicos Gates, Templates, Notificações e Kanban.

---

### CARD GAT-008: Aprendizagem da IA sobre Aprovações/Reprovações

```yaml
Titulo: "[AI + FULL-STACK] Aprendizagem da IA sobre Aprovações/Reprovações"
Tipo: Feature (AI + Full-Stack)
Sprint: 4
Pontos: 8
Prioridade: Alta
Epic: EPIC-GATES
Status: 📋 A Criar no Jira
Dependencias: GAT-001, GAT-003, GAT-004

Descricao: |
  A LIA aprende com os padrões de aprovação e reprovação dos recrutadores
  para melhorar buscas futuras. Agrega dados por motivo de reprovação,
  perfil do candidato e recrutador, gerando sugestões proativas de ajuste
  nos filtros de busca. Aprendizado segmentado por recrutador E por empresa.

Historia de Usuario: |
  Como recrutador, eu quero que a LIA aprenda com minhas decisões de
  aprovação/reprovação para sugerir ajustes nos critérios de busca e
  melhorar a qualidade dos candidatos apresentados.

Regras de Negocio:
  1. Agregar decisões por motivo, perfil do candidato e recrutador
  2. Após N reprovações pelo mesmo motivo, sugerir ajuste de filtro
  3. Calcular taxa de aprovação por vaga e motivos mais comuns
  4. Aprendizado segmentado por recrutador E por empresa (company_id)
  5. Sugestões proativas: "Nos últimos 30 dias, 80% dos reprovados tinham < 3 anos de experiência. Deseja aumentar o filtro?"
  6. Painel de insights no dashboard com estatísticas
  7. Sugestões inline na busca (junto ao smart-search-input)
  8. Mínimo 10 decisões para gerar primeira sugestão
  9. Recrutador pode aceitar ou ignorar sugestão (feedback loop)

Requisitos Tecnicos:
  Backend:
    - LearningFromDecisionsService class
    - Agregações por reason/profile/recruiter/company
    - Geração de sugestões baseada em padrões
    - POST /api/v1/gates/insights (retorna insights + sugestões)
    - GET /api/v1/gates/stats?job_id={id} (estatísticas por vaga)
    - POST /api/v1/gates/suggestions/{id}/feedback (aceitar/ignorar)
  Frontend:
    - InsightsPanel (dashboard) — painel com gráficos e sugestões
    - Inline suggestions no smart-search-input
  Dados:
    - gate_decision_aggregates: company_id, recruiter_id, reason_code, count, period
    - gate_suggestions: id, company_id, suggestion_type, suggestion_text, confidence, status (pending/accepted/ignored)
  Validacoes:
    - Mínimo 10 decisões para gerar sugestão
    - Confiança mínima 0.7 para exibir sugestão

Integracoes Externas:
  LLM (Gemini):
    - Tipo: AI API
    - Uso: Análise de padrões de decisão e geração de insights textuais
    - Serviço: gate_learning_service.py
    - SDK: google-generativeai
    - Secret: GEMINI_API_KEY
    - Custo: ~$0.01-0.03 por análise (Pro)
    - Rate Limit: 60 RPM
    - Documentacao: https://ai.google.dev/docs

Configuracao LLM:
  Modelo: Gemini 2.5 Pro (análise complexa de padrões)
  Temperatura: 0.4
  Max Tokens: 1000
  Uso: Análise de padrões textuais para gerar insights em linguagem natural
  
  Prompt Template: |
    <role>
    Você é um analista de dados de recrutamento da plataforma WeDo Talent.
    Analise os padrões de decisão dos recrutadores e gere insights acionáveis.
    </role>
    
    <data>
    Decisões recentes (últimos 30 dias):
    {{decision_summary}}
    
    Motivos de reprovação mais frequentes:
    {{top_rejection_reasons}}
    
    Taxa de aprovação por vaga:
    {{approval_rates}}
    </data>
    
    <task>
    1. Identifique padrões relevantes (ex: "80% dos reprovados tinham < 3 anos de experiência")
    2. Gere sugestões de refinamento de critérios de busca
    3. Destaque anomalias (ex: taxa de aprovação muito baixa em vaga específica)
    </task>
    
    <output_format>
    {
      "insights": [
        { "text": "...", "type": "pattern|anomaly|trend", "confidence": 0.0-1.0 }
      ],
      "suggestions": [
        { "text": "...", "action": "adjust_filter|review_criteria|escalate", "impact": "high|medium|low" }
      ]
    }
    </output_format>

Design & Componentes:
  Componentes Existentes:
    - DashboardPage - página de dashboards existente
    - SmartSearchInput - input de busca inteligente
    - Card - container de insights
    - Badge - indicadores
  Novos Componentes:
    - DecisionInsightsPanel - painel de insights de decisões
    - InsightCard - card individual de insight
    - SuggestionInline - sugestão inline na busca
    - ApprovalRateChart - gráfico de taxa de aprovação
  Design Tokens:
    Insight Background: --lia-bg-secondary (#F9FAFB)
    Suggestion: --wedo-cyan (#60BED1)
    Positive Trend: --wedo-green (#22C55E)
    Negative Trend: --electric-red (#de1c31)
    Neutral: --lia-text-tertiary (#6B7280)
  Layout:
    InsightsPanel: max-w-4xl, grid 2 cols
    InsightCard: border rounded, p-4, shadow-sm
    SuggestionInline: inline-flex, bg-cyan-50, rounded-full, px-3 py-1
  Estados:
    - Loading (skeleton)
    - Empty (< 10 decisões, mensagem informativa)
    - Populated (insights + sugestões)
    - Suggestion Accepted (feedback visual)
  Acessibilidade:
    - ARIA-live para sugestões dinâmicas
    - Labels descritivos em gráficos
    - Contraste WCAG AA

Comportamento de UI:
  Fluxo Principal:
    1. Recrutador acessa dashboard
    2. InsightsPanel carrega estatísticas agregadas
    3. Gráfico mostra taxa de aprovação por vaga
    4. Cards de sugestão aparecem se houver padrões detectados
    5. Recrutador clica "Aceitar sugestão" → filtro ajustado na busca
    6. Ou clica "Ignorar" → sugestão removida + feedback registrado

  Layout:
    Desktop: InsightsPanel ocupa seção do dashboard
    Mobile: Cards empilhados verticalmente

  Estados de Botoes:
    Aceitar:
      - Default: bg-wedo-cyan, texto branco
      - Hover: bg-wedo-cyan-dark
      - Loading: spinner
    Ignorar:
      - Default: bg-transparent, texto secondary
      - Hover: bg-gray-100

  Validacoes Inline:
    - "Dados insuficientes para gerar insights (mínimo 10 decisões)"

  Mensagens de Feedback:
    Sucesso: "Sugestão aceita! Filtro ajustado na próxima busca."
    Ignorado: "Sugestão ignorada."

Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md (Seções: 2.3 Cards, 2.6 Badges & Tags, 2.1 Botões, PARTE 4 Charts (se existir))"
  Figma: "Seção 8.2 — Gates Insights"
  Assets:
    - "Ícone de lâmpada para sugestões"
    - "Ícone de gráfico para insights"
  Tokens:
    - "--wedo-cyan (#60BED1)"
    - "--lia-bg-secondary (#F9FAFB)"

DoD:
  - [ ] LearningFromDecisionsService funcional com agregações
  - [ ] Endpoint de insights retornando dados reais
  - [ ] InsightsPanel renderizando no dashboard
  - [ ] Sugestões inline aparecendo na busca quando aplicável
  - [ ] Gemini 2.5 Pro gerando insights textuais
  - [ ] Feedback de aceitar/ignorar funcional
  - [ ] Dados segmentados por recrutador e empresa
  - [ ] Responsivo (desktop, tablet)

Criterios de Aceitacao:
  - [ ] Após 10+ reprovações com mesmo motivo, sugestão aparece
  - [ ] Taxa de aprovação por vaga exibida corretamente
  - [ ] Recrutador aceita sugestão → filtro refletido na busca
  - [ ] Recrutador ignora sugestão → não reaparece
  - [ ] Insights textuais gerados pelo Gemini são claros e acionáveis
  - [ ] Dados de uma empresa não vazam para outra (multi-tenant)

Arquivos de Referencia (Prototipo Replit):
  - dashboards-page: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/pages/dashboards-page.tsx
  - smart-search-input: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/search/smart-search-input.tsx
```

---

### CARD TPL-008: Sincronização de Templates WhatsApp com Meta

```yaml
Titulo: "[FULL-STACK] Sincronização de Templates WhatsApp com Meta Business Manager"
Tipo: Feature (Backend + Frontend)
Sprint: 3
Pontos: 8
Prioridade: Alta
Epic: EPIC-TEMPLATES
Status: 📋 A Criar no Jira
Dependencias: TPL-001, TRI-001

Descricao: |
  Sincronização bidirecional entre os templates de WhatsApp da plataforma
  e o Meta Business Manager. Templates criados na plataforma são submetidos
  ao Meta para aprovação. Status de aprovação (Pending, Approved, Rejected)
  é atualizado via webhook. Suporte ao formato de variáveis Meta ({{1}}, {{2}}).

Historia de Usuario: |
  Como admin, eu quero que os templates de WhatsApp criados na plataforma
  sejam automaticamente submetidos ao Meta para aprovação, e que eu possa
  ver o status de aprovação em tempo real.

Regras de Negocio:
  1. Templates criados na plataforma são submetidos ao Meta Business Manager
  2. Status de aprovação: Pendente Meta, Aprovado, Rejeitado
  3. Motivo de rejeição exibido quando rejeitado pelo Meta
  4. Webhook recebe atualizações de status do Meta
  5. Suporte ao formato de variáveis Meta: {{1}}, {{2}}, {{3}}
  6. Re-submissão possível após correção de template rejeitado
  7. Sync automático ao salvar template na plataforma

Requisitos Tecnicos:
  Backend:
    - MetaTemplateSyncService class
    - WhatsApp Business Management API integration
    - Webhook endpoint para status updates do Meta
    - Tabela whatsapp_template_sync: id, template_id, meta_template_id, status (pending/approved/rejected), rejection_reason, submitted_at, updated_at
    - POST /api/v1/templates/{id}/submit-to-meta
    - GET /api/v1/templates/{id}/meta-status
  Frontend:
    - Badge de status Meta no editor de templates (Pendente Meta, Aprovado, Rejeitado)
    - Exibição de motivo de rejeição quando rejeitado
    - Botão "Re-submeter" para templates rejeitados
  Dados:
    - whatsapp_template_sync: id, template_id, meta_template_id, status, rejection_reason, submitted_at, updated_at
  Validacoes:
    - Variáveis no formato {{N}} validadas antes de submissão
    - Conteúdo dentro dos limites do Meta (1024 chars)

Integracoes Externas:
  WhatsApp Business Management API:
    - Endpoint: graph.facebook.com/v18.0/{waba_id}/message_templates
    - Tipo: REST API
    - Autenticação: Bearer token (System User Token)
    - Webhook: Recebe atualizações de status de templates
    - Documentacao: https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates

  API Contract Details:
    Submit Template:
      Method: POST
      URL: graph.facebook.com/v18.0/{{waba_id}}/message_templates
      Headers:
        Authorization: Bearer {{system_user_token}}
        Content-Type: application/json
      Body: |
        {
          "name": "{{template_name}}",
          "language": "pt_BR",
          "category": "MARKETING|UTILITY|AUTHENTICATION",
          "components": [
            {
              "type": "HEADER",
              "format": "TEXT",
              "text": "{{header_text}}"
            },
            {
              "type": "BODY",
              "text": "{{body_text_with_variables}}"
            },
            {
              "type": "FOOTER",
              "text": "{{footer_text}}"
            }
          ]
        }
      Response: |
        { "id": "meta_template_id", "status": "PENDING", "category": "..." }
    Get Status:
      Method: GET
      URL: graph.facebook.com/v18.0/{{meta_template_id}}
      Response: |
        { "id": "...", "status": "APPROVED|REJECTED|PENDING", "rejected_reason": "..." }
    Webhook Events:
      Subscription: message_template_status_update
      Payload: |
        {
          "entry": [{
            "changes": [{
              "field": "message_template_status_update",
              "value": {
                "event": "APPROVED|REJECTED",
                "message_template_id": "...",
                "message_template_name": "...",
                "reason": "..." 
              }
            }]
          }]
        }
    Required Scopes:
      - whatsapp_business_management
      - whatsapp_business_messaging
    Rate Limits:
      - 200 templates per WABA
      - 10 requests/second

Design & Componentes:
  Componentes Existentes:
    - EmailTemplatesManager - gerenciador de templates existente
    - EmailTemplateFormModal - modal de edição de template
    - Badge - indicadores de status
    - Button - ações
  Novos Componentes:
    - MetaStatusBadge - badge com cores por status Meta
    - RejectionReasonDisplay - exibição do motivo de rejeição
    - ResubmitButton - botão de re-submissão
  Design Tokens:
    Pending: --wedo-yellow (#EAB308)
    Approved: --wedo-green (#22C55E)
    Rejected: --electric-red (#de1c31)
    Badge Background Pending: bg-yellow-100
    Badge Background Approved: bg-green-100
    Badge Background Rejected: bg-red-100
  Layout:
    Badge: inline-flex, rounded-full, px-2.5 py-0.5
    RejectionReason: border-l-4 border-red, bg-red-50, p-3
  Estados:
    - Not Submitted (sem badge)
    - Pending (badge amarelo pulsando)
    - Approved (badge verde estático)
    - Rejected (badge vermelho + motivo)
  Acessibilidade:
    - ARIA-label no badge com status completo
    - Motivo de rejeição anunciado por screen readers

Comportamento de UI:
  Fluxo Principal:
    1. Admin cria/edita template de WhatsApp na plataforma
    2. Ao salvar, template é automaticamente submetido ao Meta
    3. Badge "Pendente Meta" aparece (amarelo, pulsando)
    4. Webhook recebe atualização do Meta
    5a. Se aprovado: badge muda para "Aprovado" (verde)
    5b. Se rejeitado: badge muda para "Rejeitado" (vermelho) + motivo exibido
    6. Se rejeitado: admin corrige e clica "Re-submeter"

  Layout:
    Badge: Ao lado do nome do template no editor
    RejectionReason: Abaixo do editor, em destaque

  Mensagens de Feedback:
    Submetido: "Template submetido ao Meta para aprovação. Aguarde..."
    Aprovado: "Template aprovado pelo Meta! Pronto para uso."
    Rejeitado: "Template rejeitado pelo Meta. Motivo: {{reason}}"

Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md (Seções: 2.6 Badges & Tags, 2.1 Botões, 2.8 Toasts & Alerts)"
  Figma: "Seção 8.2 — Meta Template Sync"
  Assets:
    - "Ícone Meta/WhatsApp"
  Tokens:
    - "--wedo-yellow (#EAB308)"
    - "--wedo-green (#22C55E)"
    - "--electric-red (#de1c31)"

DoD:
  - [ ] MetaTemplateSyncService funcional
  - [ ] Submissão de template ao Meta via API
  - [ ] Webhook recebendo atualizações de status
  - [ ] Badge de status renderizando corretamente
  - [ ] Motivo de rejeição exibido quando aplicável
  - [ ] Re-submissão funcional
  - [ ] Variáveis {{N}} validadas

Criterios de Aceitacao:
  - [ ] Template salvo na plataforma → submetido ao Meta automaticamente
  - [ ] Badge de status atualiza conforme resposta do Meta
  - [ ] Motivo de rejeição visível ao admin
  - [ ] Re-submissão após correção funciona
  - [ ] Variáveis Meta ({{1}}, {{2}}) são preservadas e validadas

Arquivos de Referencia (Prototipo Replit):
  - email-templates-manager: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/email-templates/email-templates-manager.tsx
  - email-template-form-modal: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/email-templates/email-template-form-modal.tsx
```

---

### CARD NOT-007: Notificações para Recrutador via Microsoft Teams

```yaml
Titulo: "[BACKEND] Notificações para Recrutador via Microsoft Teams"
Tipo: Feature (Backend)
Sprint: Pós-MVP
Pontos: 5
Prioridade: Média
Epic: EPIC-NOT
Status: 📋 A Criar no Jira
Dependencias: INT-MSG-001

Descricao: |
  Enviar notificações para recrutadores via Microsoft Teams usando
  Microsoft Graph API. Eventos notificáveis: busca concluída, candidato
  triado, incidente de triagem, decisão de gate necessária.
  Configurável por tipo de evento e com suporte multi-tenant.

Historia de Usuario: |
  Como recrutador, eu quero receber notificações da LIA diretamente
  no Microsoft Teams para não perder eventos importantes sem precisar
  abrir a plataforma constantemente.

Regras de Negocio:
  1. Eventos notificáveis: busca concluída, candidato triado, incidente de triagem, decisão de gate necessária
  2. Configurável por tipo de evento (recrutador escolhe quais quer receber via Teams)
  3. Suporte multi-tenant (cada empresa pode ter sua configuração Teams)
  4. Mensagens formatadas com Adaptive Cards (rich formatting)
  5. Deep link para a plataforma na notificação
  6. Rate limiting: máximo 60 msgs/minuto por tenant
  7. Fallback silencioso se Teams indisponível (não bloquear fluxo)

Requisitos Tecnicos:
  Backend:
    - TeamsNotificationService class
    - Microsoft Graph API: Chat.ReadWrite permission
    - Bot Framework proactive messaging
    - Adaptive Card templates por tipo de evento
    - POST /api/v1/notifications/teams/send
    - GET /api/v1/notifications/teams/config
    - PUT /api/v1/notifications/teams/config
  Frontend:
    - Preferências de notificação em Settings (quais eventos receber via Teams)
    - Toggle por tipo de evento
  Dados:
    - teams_notification_config: company_id, user_id, event_types (JSONB), teams_user_id, is_active
    - teams_notification_log: id, user_id, event_type, status (sent/failed), error, sent_at

Integracoes Externas:
  Microsoft Graph API:
    - Tipo: REST API + Bot Framework
    - Scopes: Chat.ReadWrite, User.Read
    - Autenticação: Azure AD OAuth 2.0 (via INT-MSG-001)
    - Documentacao: https://docs.microsoft.com/graph/api/chat-sendactivitynotification

  Adaptive Card Payload Templates:
    busca_concluida: |
      {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.5",
        "body": [
          { "type": "ColumnSet", "columns": [
            { "type": "Column", "width": "auto", "items": [
              { "type": "Image", "url": "{{platform_logo_url}}", "size": "Small" }
            ]},
            { "type": "Column", "width": "stretch", "items": [
              { "type": "TextBlock", "text": "LIA - WeDo Talent", "weight": "Bolder", "size": "Medium" },
              { "type": "TextBlock", "text": "Busca Concluída", "spacing": "None", "isSubtle": true }
            ]}
          ]},
          { "type": "TextBlock", "text": "A busca para **{{job_title}}** foi concluída.", "wrap": true },
          { "type": "FactSet", "facts": [
            { "title": "Candidatos encontrados", "value": "{{candidates_count}}" },
            { "title": "Score médio", "value": "{{avg_score}}%" },
            { "title": "Vaga", "value": "{{job_title}}" }
          ]}
        ],
        "actions": [
          { "type": "Action.OpenUrl", "title": "Ver Candidatos", "url": "{{deep_link}}" }
        ]
      }
    candidato_triado: |
      {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.5",
        "body": [
          { "type": "ColumnSet", "columns": [
            { "type": "Column", "width": "auto", "items": [
              { "type": "Image", "url": "{{platform_logo_url}}", "size": "Small" }
            ]},
            { "type": "Column", "width": "stretch", "items": [
              { "type": "TextBlock", "text": "LIA - WeDo Talent", "weight": "Bolder", "size": "Medium" },
              { "type": "TextBlock", "text": "Triagem Concluída", "spacing": "None", "isSubtle": true }
            ]}
          ]},
          { "type": "TextBlock", "text": "A triagem WSI de **{{candidate_name}}** para a vaga **{{job_title}}** foi concluída.", "wrap": true },
          { "type": "FactSet", "facts": [
            { "title": "Candidato", "value": "{{candidate_name}}" },
            { "title": "Score WSI", "value": "{{wsi_score}}%" },
            { "title": "Classificação", "value": "{{wsi_classification}}" },
            { "title": "Vaga", "value": "{{job_title}}" }
          ]}
        ],
        "actions": [
          { "type": "Action.OpenUrl", "title": "Ver Resultado", "url": "{{deep_link}}" }
        ]
      }
    incidente_triagem: |
      {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.5",
        "body": [
          { "type": "ColumnSet", "columns": [
            { "type": "Column", "width": "auto", "items": [
              { "type": "Image", "url": "{{platform_logo_url}}", "size": "Small" }
            ]},
            { "type": "Column", "width": "stretch", "items": [
              { "type": "TextBlock", "text": "LIA - WeDo Talent", "weight": "Bolder", "size": "Medium" },
              { "type": "TextBlock", "text": "⚠️ Incidente de Triagem", "spacing": "None", "color": "Attention" }
            ]}
          ]},
          { "type": "TextBlock", "text": "Candidato **{{candidate_name}}** reportou um problema durante a triagem.", "wrap": true, "color": "Attention" },
          { "type": "FactSet", "facts": [
            { "title": "Candidato", "value": "{{candidate_name}}" },
            { "title": "Vaga", "value": "{{job_title}}" },
            { "title": "Tipo", "value": "{{incident_type}}" },
            { "title": "Prioridade", "value": "{{priority}}" },
            { "title": "Reportado em", "value": "{{reported_at}}" }
          ]},
          { "type": "TextBlock", "text": "Últimas mensagens:", "weight": "Bolder", "size": "Small" },
          { "type": "TextBlock", "text": "{{last_messages_preview}}", "wrap": true, "isSubtle": true }
        ],
        "actions": [
          { "type": "Action.OpenUrl", "title": "Ver Incidente", "url": "{{deep_link}}" },
          { "type": "Action.OpenUrl", "title": "Assumir Incidente", "url": "{{assign_link}}" }
        ]
      }
    decisao_gate: |
      {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.5",
        "body": [
          { "type": "ColumnSet", "columns": [
            { "type": "Column", "width": "auto", "items": [
              { "type": "Image", "url": "{{platform_logo_url}}", "size": "Small" }
            ]},
            { "type": "Column", "width": "stretch", "items": [
              { "type": "TextBlock", "text": "LIA - WeDo Talent", "weight": "Bolder", "size": "Medium" },
              { "type": "TextBlock", "text": "Decisão Necessária", "spacing": "None", "isSubtle": true }
            ]}
          ]},
          { "type": "TextBlock", "text": "O candidato **{{candidate_name}}** aguarda decisão de gate para a vaga **{{job_title}}**.", "wrap": true },
          { "type": "FactSet", "facts": [
            { "title": "Candidato", "value": "{{candidate_name}}" },
            { "title": "Vaga", "value": "{{job_title}}" },
            { "title": "Etapa", "value": "{{current_stage}}" },
            { "title": "Score WSI", "value": "{{wsi_score}}%" },
            { "title": "Aguardando desde", "value": "{{pending_since}}" }
          ]}
        ],
        "actions": [
          { "type": "Action.OpenUrl", "title": "Avaliar Candidato", "url": "{{deep_link}}" }
        ]
      }

Design & Componentes:
  Componentes Existentes:
    - CommunicationHub - hub de comunicação em Settings
  Novos Componentes:
    - TeamsNotificationPreferences - toggles por evento
  Design Tokens:
    Teams Purple: #6264A7
    Active: --wedo-green (#22C55E)
    Inactive: --lia-text-tertiary (#6B7280)
  Layout:
    Preferences: Dentro de CommunicationHub, seção "Microsoft Teams"
    Toggles: Lista vertical com label + toggle por evento
  Estados:
    - Not Connected (botão "Conectar Teams")
    - Connected (lista de toggles por evento)
    - Saving (loading no toggle)
  Acessibilidade:
    - Labels em todos os toggles
    - ARIA-describedby explicando cada tipo de evento

Comportamento de UI:
  Fluxo Principal:
    1. Recrutador acessa Settings > Comunicação
    2. Seção "Microsoft Teams" mostra status de conexão
    3. Se não conectado: botão "Conectar Teams" (OAuth)
    4. Se conectado: lista de toggles por tipo de evento
    5. Recrutador ativa/desativa eventos desejados
    6. Notificações enviadas automaticamente quando eventos ocorrem

  Mensagens de Feedback:
    Conectado: "Microsoft Teams conectado com sucesso!"
    Salvo: "Preferências de notificação atualizadas."
    Erro: "Não foi possível enviar notificação via Teams."

Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md (Seções: 2.17 Switches & Toggles, 2.3 Cards, 2.1 Botões)"
  Figma: "Seção 8.2 — Teams Notifications"
  Assets:
    - "Ícone Microsoft Teams"
  Tokens:
    - "Teams Purple #6264A7"

DoD:
  - [ ] TeamsNotificationService funcional
  - [ ] Notificações enviadas para os 4 tipos de evento
  - [ ] Preferências configuráveis por recrutador
  - [ ] Adaptive Cards renderizando corretamente no Teams
  - [ ] Deep links funcionando
  - [ ] Multi-tenant suportado

Criterios de Aceitacao:
  - [ ] Recrutador conecta Teams via OAuth
  - [ ] Ativa/desativa eventos específicos
  - [ ] Recebe notificação no Teams quando evento ocorre
  - [ ] Clica no deep link e abre plataforma na seção correta
  - [ ] Dados de um tenant não vazam para outro

Arquivos de Referencia (Prototipo Replit):
  - CommunicationHub: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/settings/CommunicationHub.tsx
```

---

### CARD KAN-011: Disparar Triagem em Lote Dentro da Vaga

```yaml
Titulo: "[FULL-STACK] Disparar Triagem WSI em Lote Dentro da Vaga"
Tipo: Feature (Full-Stack)
Sprint: 3
Pontos: 5
Prioridade: Alta
Epic: EPIC-KAN-001
Status: 📋 A Criar no Jira
Dependencias: KAN-001, GAT-001, TRI-001

Descricao: |
  Permitir que o recrutador selecione candidatos da coluna "Funil Aprovado"
  no Kanban e dispare triagem WSI em lote via WhatsApp. Candidatos selecionados
  recebem mensagens enfileiradas e são movidos para a coluna "Em Triagem".
  Disponível tanto na visualização Kanban quanto na Table view.

Historia de Usuario: |
  Como recrutador, eu quero selecionar múltiplos candidatos aprovados
  e iniciar a triagem WSI para todos de uma vez, sem precisar disparar
  individualmente para cada candidato.

Regras de Negocio:
  1. Seleção múltipla de candidatos na coluna "Funil Aprovado"
  2. Botão "Iniciar Triagem" aparece quando há candidatos selecionados
  3. Confirmação: "Iniciar triagem WSI para N candidatos?"
  4. Mensagens WhatsApp enfileiradas (não disparo simultâneo)
  5. Candidatos movem para coluna "Em Triagem" após disparo
  6. Barra de progresso: "Enviando 3/10..."
  7. Disponível em Kanban e Table views
  8. Limite de 50 candidatos por lote
  9. Erro individual não cancela o lote inteiro

Requisitos Tecnicos:
  Backend:
    - POST /api/v1/screening/batch-start
    - Body: { job_id, candidate_ids[] }
    - Enfileirar mensagens WhatsApp (job queue)
    - Atualizar stage de cada candidato para "em_triagem"
    - Retorno: { total, queued, errors[] }
  Frontend:
    - BatchScreeningButton (aparece quando candidatos selecionados)
    - ScreeningProgressModal (barra de progresso, status por candidato)
    - Checkbox de seleção nos cards de candidato
    - Integração com Kanban e Table views
  Dados:
    - screening_batch: id, company_id, job_id, initiated_by, candidate_ids (JSONB), total_count, queued_count, error_count, status (queued/in_progress/completed/partial_error), started_at, completed_at
  Validacoes:
    - Candidatos devem estar na coluna "Funil Aprovado"
    - Máximo 50 candidatos por lote
    - Candidato não pode ter triagem ativa

Design & Componentes:
  Componentes Existentes:
    - KanbanBoard - board existente
    - KanbanColumn - coluna existente
    - CandidateCard - card de candidato
    - Modal - container de modal
    - Progress - barra de progresso
    - Checkbox - seleção
  Novos Componentes:
    - BatchScreeningButton - botão flutuante de disparo em lote
    - ScreeningProgressModal - modal com progresso de envio
    - BatchConfirmationDialog - confirmação antes de enviar
  Design Tokens:
    Button: --wedo-cyan (#60BED1)
    Progress: --wedo-cyan (#60BED1)
    Success: --wedo-green (#22C55E)
    Error: --electric-red (#de1c31)
    Selected: bg-cyan-50, border-wedo-cyan
  Layout:
    BatchScreeningButton: fixed bottom-right quando candidatos selecionados
    ProgressModal: max-w-md, centered
    Candidate list no modal: max-h-[400px], overflow-y-auto
  Estados:
    - Hidden (nenhum candidato selecionado)
    - Visible (candidatos selecionados, botão aparece)
    - Confirming (dialog de confirmação)
    - Sending (modal de progresso)
    - Completed (resumo final)
    - Partial Error (alguns falharam)
  Acessibilidade:
    - ARIA-label no botão com contagem de selecionados
    - Progress bar com ARIA-valuenow
    - Focus trap no modal

Comportamento de UI:
  Fluxo Principal:
    1. Recrutador seleciona candidatos na coluna "Funil Aprovado" (checkboxes)
    2. BatchScreeningButton aparece: "Iniciar Triagem (N selecionados)"
    3. Click → BatchConfirmationDialog: "Iniciar triagem WSI para N candidatos?"
    4. Confirma → ScreeningProgressModal abre
    5. Barra de progresso: "Enviando 3/10..."
    6. Candidatos movem para "Em Triagem" conforme disparo
    7. Conclusão: "10/10 triagens iniciadas com sucesso"
    8. Se erros: "8/10 iniciadas. 2 falharam: [motivos]"

  Estados de Botoes:
    Iniciar Triagem:
      - Default: bg-wedo-cyan, texto branco, ícone play
      - Hover: bg-wedo-cyan-dark
      - Disabled: opacity-50 (nenhum selecionado)

  Mensagens de Feedback:
    Sucesso: "Triagem iniciada para N candidatos!"
    Parcial: "N triagens iniciadas. X falharam."
    Erro: "Erro ao iniciar triagem em lote."

Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md (Seções: 2.1 Botões, 2.19 Checkboxes, 2.4 Modais, 2.13 Progress Indicators)"
  Figma: "Seção 8.2 — Batch Screening"
  Assets:
    - "Ícone play para disparo"
    - "Ícone check para sucesso"
  Tokens:
    - "--wedo-cyan (#60BED1)"
    - "--wedo-green (#22C55E)"

DoD:
  - [ ] Seleção múltipla de candidatos funcional no Kanban
  - [ ] BatchScreeningButton aparece/desaparece corretamente
  - [ ] Confirmação antes de disparar
  - [ ] Progresso de envio em tempo real
  - [ ] Candidatos movem para "Em Triagem"
  - [ ] Funciona em Kanban e Table views
  - [ ] Limite de 50 candidatos respeitado
  - [ ] Responsivo

Criterios de Aceitacao:
  - [ ] Selecionar 5 candidatos → botão aparece com "5 selecionados"
  - [ ] Confirmar → progresso mostra "Enviando 1/5..." até 5/5
  - [ ] Candidatos movem para coluna "Em Triagem" após disparo
  - [ ] Erro em 1 candidato não cancela os outros 4
  - [ ] Resumo final mostra sucesso/falha por candidato

Arquivos de Referencia (Prototipo Replit):
  - job-kanban-page: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/pages/job-kanban-page.tsx
  - KanbanBoard: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/kanban/components/KanbanBoard.tsx
  - KanbanColumn: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/pages/job-kanban/KanbanColumn.tsx
```

---

### CARD KAN-012: Solicitar Novos Candidatos com Critérios Refinados

```yaml
Titulo: "[AI + FULL-STACK] Solicitar Novos Candidatos com Critérios Refinados"
Tipo: Feature (AI + Full-Stack)
Sprint: 3
Pontos: 8
Prioridade: Alta
Epic: EPIC-KAN-001
Status: 📋 A Criar no Jira
Dependencias: KAN-001, MAP-001, GAT-001

Descricao: |
  Botão "Mais candidatos" na tela da vaga que inicia nova busca
  usando a JD + feedback de aprovação/reprovação para refinar critérios.
  A LIA analisa padrões de decisão e sugere refinamentos. Candidatos
  já avaliados são automaticamente excluídos dos resultados.

Historia de Usuario: |
  Como recrutador, eu quero pedir mais candidatos para minha vaga
  com critérios refinados baseados nas decisões que já tomei,
  sem precisar refazer a busca do zero.

Regras de Negocio:
  1. Botão "Mais candidatos" no header da vaga (Kanban e Table)
  2. LIA analisa padrões de aprovação/reprovação para sugerir refinamentos
  3. Excluir automaticamente candidatos já avaliados (aprovados, reprovados, em triagem)
  4. Lista de sugestões de refinamento com aceitar/rejeitar individual
  5. LIA sugere: "Com base nas reprovações, sugiro aumentar experiência mínima para 5 anos"
  6. Recrutador pode aceitar todas, algumas ou nenhuma sugestão
  7. Nova busca executada com critérios refinados
  8. Resultados adicionados à vaga (não substituem existentes)

Requisitos Tecnicos:
  Backend:
    - POST /api/v1/jobs/{id}/request-more-candidates
    - Body: { accepted_suggestions[], custom_criteria? }
    - Analisar padrões de aprovação/reprovação via LLM
    - Excluir candidate_ids já avaliados
    - Retornar: { suggestions[], new_candidates[] }
  Frontend:
    - RefinedSearchModal - modal com sugestões e resultados
    - SuggestionsList - lista de sugestões com aceitar/rejeitar
    - AddMoreButton - botão no header da vaga
  Dados:
    - refinement_sessions: id, company_id, job_id, recruiter_id, suggestions (JSONB), accepted_suggestions (JSONB), new_candidate_ids (JSONB), search_criteria_snapshot (JSONB), created_at

Integracoes Externas:
  LLM (Gemini):
    - Tipo: AI API
    - Uso: Análise de padrões de decisão para sugerir refinamentos de busca
    - Serviço: candidate_refinement_service.py
    - SDK: google-generativeai
    - Secret: GEMINI_API_KEY
    - Custo: ~$0.01-0.03 por análise (Pro)
    - Rate Limit: 60 RPM
    - Documentacao: https://ai.google.dev/docs

Configuracao LLM:
  Modelo: Gemini 2.5 Pro (análise complexa de padrões)
  Temperatura: 0.5
  Max Tokens: 1500
  Uso: Analisar padrões de decisão e gerar sugestões de refinamento em linguagem natural
  
  Prompt Template: |
    <role>
    Você é especialista em talent acquisition da plataforma WeDo Talent.
    Analise os padrões de aprovação/reprovação e sugira refinamentos
    nos critérios de busca para encontrar candidatos mais adequados.
    </role>
    
    <context>
    Vaga: {{job_title}} ({{job_id}})
    Critérios atuais: {{current_criteria}}
    Candidatos avaliados: {{evaluated_count}}
    Aprovados: {{approved_count}} ({{approval_rate}}%)
    Reprovados: {{rejected_count}}
    </context>
    
    <rejection_patterns>
    {{rejection_analysis}}
    </rejection_patterns>
    
    <task>
    Sugira até 5 refinamentos nos critérios de busca baseados nos padrões.
    Cada sugestão deve ter justificativa baseada nos dados.
    </task>
    
    <output_format>
    {
      "suggestions": [
        {
          "field": "experience_years|skills|education|location|salary",
          "current_value": "...",
          "suggested_value": "...",
          "justification": "...",
          "expected_impact": "high|medium|low"
        }
      ]
    }
    </output_format>

Design & Componentes:
  Componentes Existentes:
    - JobKanbanPage - página da vaga
    - SmartSearchInput - input de busca
    - Modal - container
    - Button - ações
  Novos Componentes:
    - RefinedSearchModal - modal principal
    - SuggestionsList - lista de sugestões
    - SuggestionCard - card individual com aceitar/rejeitar
    - AddMoreCandidatesButton - botão no header
  Design Tokens:
    Suggestion: --wedo-cyan-light (#E0F4F8)
    Accepted: --wedo-green (#22C55E)
    Rejected: --electric-red-light (#FEE2E2)
    Button: --wedo-cyan (#60BED1)
  Layout:
    Modal: max-w-2xl, centered
    SuggestionsList: flex flex-col gap-3
    SuggestionCard: border rounded, p-4, flex justify-between
  Estados:
    - Loading (analisando padrões...)
    - Suggestions Ready (lista de sugestões)
    - Searching (buscando com critérios refinados)
    - Results (novos candidatos encontrados)
    - Empty (nenhum candidato novo encontrado)
  Acessibilidade:
    - Focus trap no modal
    - ARIA-label nos botões aceitar/rejeitar
    - Screen reader anuncia sugestões

Comportamento de UI:
  Fluxo Principal:
    1. Recrutador clica "Mais candidatos" no header da vaga
    2. RefinedSearchModal abre com loading: "Analisando padrões de decisão..."
    3. LIA apresenta sugestões de refinamento
    4. Recrutador aceita/rejeita sugestões individualmente
    5. Clica "Buscar com refinamentos"
    6. Loading: "Buscando candidatos com critérios refinados..."
    7. Resultados aparecem com opção de adicionar à vaga

  Estados de Botoes:
    Mais Candidatos:
      - Default: outline, border-wedo-cyan, texto cyan
      - Hover: bg-wedo-cyan, texto branco
    Aceitar Sugestão:
      - Default: bg-green-50, texto green
      - Active: bg-green-500, texto branco
    Rejeitar Sugestão:
      - Default: bg-red-50, texto red
      - Active: bg-red-500, texto branco

  Mensagens de Feedback:
    Analisando: "Analisando padrões de decisão..."
    Buscando: "Buscando candidatos com critérios refinados..."
    Sucesso: "N novos candidatos encontrados!"
    Vazio: "Nenhum candidato novo encontrado com esses critérios."

Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md (Seções: 2.4 Modais, 2.3 Cards, 2.1 Botões, 2.6 Badges & Tags)"
  Figma: "Seção 8.2 — Refined Search"
  Assets:
    - "Ícone de busca refinada"
    - "Ícone de sugestão IA"
  Tokens:
    - "--wedo-cyan (#60BED1)"
    - "--wedo-green (#22C55E)"

DoD:
  - [ ] Análise de padrões via Gemini 2.5 Pro funcional
  - [ ] Sugestões de refinamento geradas corretamente
  - [ ] Aceitar/rejeitar sugestões funcional
  - [ ] Busca refinada executada com exclusão de já avaliados
  - [ ] Novos candidatos adicionados à vaga
  - [ ] Modal responsivo

Criterios de Aceitacao:
  - [ ] Botão "Mais candidatos" visível no header da vaga
  - [ ] Sugestões baseadas em padrões reais de decisão
  - [ ] Candidatos já avaliados não aparecem nos resultados
  - [ ] Aceitar sugestão reflete no critério de busca
  - [ ] Novos candidatos adicionados com sucesso à vaga

Arquivos de Referencia (Prototipo Replit):
  - job-kanban-page: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/pages/job-kanban-page.tsx
  - smart-search-input: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/search/smart-search-input.tsx
```

---

### CARD KAN-013: Buscar Candidatos Similares

```yaml
Titulo: "[AI + FULL-STACK] Buscar Candidatos Similares via Embedding"
Tipo: Feature (AI + Full-Stack)
Sprint: 3
Pontos: 5
Prioridade: Média
Epic: EPIC-KAN-001
Status: 📋 A Criar no Jira
Dependencias: KAN-002, MAP-001

Descricao: |
  Ação "Buscar similares" no menu de contexto do card de candidato.
  Usa embedding do perfil do candidato para busca semântica por vetor,
  retornando top 10 candidatos mais similares. Filtra por vaga (exclui
  candidatos já avaliados). Score de similaridade (%) exibido.

Historia de Usuario: |
  Como recrutador, eu quero encontrar candidatos similares a um perfil
  que aprovei, para ampliar o pool de candidatos qualificados sem
  precisar refazer a busca manualmente.

Regras de Negocio:
  1. Ação disponível no menu de contexto do card de candidato
  2. Busca baseada em embedding do perfil (vetor semântico)
  3. Retorna top 10 candidatos mais similares
  4. Filtrar por vaga: excluir candidatos já avaliados na vaga atual
  5. Score de similaridade (%) exibido em cada resultado
  6. Botão "Adicionar à vaga" em cada resultado
  7. Candidato base exibido no topo do modal para referência

Requisitos Tecnicos:
  Backend:
    - POST /api/v1/candidates/{id}/find-similar
    - Body: { job_id?, limit: 10, exclude_ids[]? }
    - Embedding-based vector search (cosine similarity)
    - Retorno: { base_candidate, similar_candidates[{ candidate, similarity_score }] }
  Frontend:
    - SimilarCandidatesModal - modal com resultados
    - SimilarityScoreBadge - badge com % de similaridade
    - AddToJobButton - botão para adicionar candidato à vaga
  Dados:
    - candidate_embeddings: candidate_id, embedding (vector), updated_at
    - similar_searches: id, base_candidate_id, job_id, results (JSONB), created_at

Integracoes Externas:
  Embedding Service:
    - Tipo: AI API (Embedding)
    - Uso: Gerar embedding do perfil do candidato para busca por similaridade vetorial
    - Serviço: candidate_similarity_service.py
    - SDK: google-generativeai (text-embedding-004)
    - Secret: GEMINI_API_KEY
    - Custo: ~$0.001 por embedding
    - Documentacao: https://ai.google.dev/docs/embeddings
  Vector Database:
    - Tipo: pgvector (extensão PostgreSQL)
    - Uso: Armazenar e buscar embeddings por similaridade cosine
    - Índice: ivfflat ou hnsw para performance
    - Coluna: candidate_embeddings.embedding (vector(768))

Configuracao LLM:
  Modelo Embedding: text-embedding-004 (Google)
  Dimensões: 768
  Busca: Cosine similarity via pgvector
  Top K: 10 resultados
  Threshold: similarity >= 0.7 (70%)
  
  Fluxo:
    1. Perfil do candidato base → texto concatenado (skills + experiência + educação)
    2. Gerar embedding via text-embedding-004
    3. Buscar top 10 candidatos similares via pgvector (cosine similarity)
    4. Filtrar: excluir já avaliados na vaga, similarity >= 0.7
    5. Retornar com score de similaridade (%)

Design & Componentes:
  Componentes Existentes:
    - CandidateCard - card de candidato (menu de contexto)
    - KanbanCard - card na view Kanban
    - Modal - container
    - Badge - indicadores
    - Button - ações
  Novos Componentes:
    - SimilarCandidatesModal - modal com lista de similares
    - SimilarityScoreBadge - badge circular com %
    - SimilarCandidateCard - card compacto de candidato similar
  Design Tokens:
    High Similarity (>80%): --wedo-green (#22C55E)
    Medium Similarity (60-79%): --wedo-cyan (#60BED1)
    Low Similarity (<60%): --wedo-yellow (#EAB308)
    Badge Background: bg-transparent
    Badge Border: border-2
  Layout:
    Modal: max-w-2xl, centered
    Base Candidate: border-b, p-4, bg-secondary (referência)
    Similar List: flex flex-col gap-3, max-h-[500px] overflow-y-auto
    SimilarCandidateCard: flex items-center justify-between, p-3, border rounded
    SimilarityBadge: w-12 h-12, rounded-full, flex items-center justify-center
  Estados:
    - Loading (buscando similares...)
    - Results (lista de similares)
    - Empty (nenhum similar encontrado)
    - Adding (adicionando candidato à vaga)
  Acessibilidade:
    - Focus trap no modal
    - ARIA-label com score de similaridade
    - Lista navegável via keyboard

Comportamento de UI:
  Fluxo Principal:
    1. Recrutador clica menu de contexto (⋮) no card de candidato
    2. Seleciona "Buscar similares"
    3. SimilarCandidatesModal abre com loading
    4. Candidato base exibido no topo (referência)
    5. Lista de top 10 similares com score (%)
    6. Recrutador clica "Adicionar à vaga" em candidatos desejados
    7. Candidato adicionado → toast de confirmação

  Estados de Botoes:
    Buscar Similares (menu):
      - Default: texto com ícone de busca
      - Hover: bg-gray-100
    Adicionar à Vaga:
      - Default: outline, border-wedo-cyan
      - Hover: bg-wedo-cyan, texto branco
      - Added: bg-green-50, texto green, ícone check

  Mensagens de Feedback:
    Buscando: "Buscando candidatos similares..."
    Sucesso: "Candidato adicionado à vaga com sucesso!"
    Vazio: "Nenhum candidato similar encontrado."

Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md (Seções: 2.4 Modais, 2.3 Cards, 2.6 Badges & Tags, 2.14 Avatars)"
  Figma: "Seção 8.2 — Similar Candidates"
  Assets:
    - "Ícone de busca similar (DNA/fingerprint)"
  Tokens:
    - "--wedo-green (#22C55E)"
    - "--wedo-cyan (#60BED1)"
    - "--wedo-yellow (#EAB308)"

DoD:
  - [ ] Busca por similaridade via embedding funcional
  - [ ] Top 10 resultados com score de similaridade
  - [ ] Exclusão de candidatos já avaliados na vaga
  - [ ] Modal renderizando corretamente
  - [ ] Adicionar candidato à vaga funcional
  - [ ] Ação disponível no menu de contexto do card

Criterios de Aceitacao:
  - [ ] Menu de contexto mostra "Buscar similares"
  - [ ] Modal exibe candidato base + top 10 similares
  - [ ] Score de similaridade (%) visível em cada resultado
  - [ ] "Adicionar à vaga" funciona e atualiza Kanban
  - [ ] Candidatos já na vaga não aparecem nos resultados

Arquivos de Referencia (Prototipo Replit):
  - CandidateCard: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/kanban/components/CandidateCard.tsx
  - KanbanCard: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/pages/job-kanban/KanbanCard.tsx
```

---

## PARTE 9: CARDS EXISTENTES — AJUSTES DETALHADOS (ANTES → DEPOIS)

> Esta seção documenta as alterações field-level em cards existentes de `docs/lia-mvp-cards-jira.md`, identificadas na reunião de alinhamento de 06/02/2026. Formato: campo alterado com valor ANTES e DEPOIS.

---

### 9.1 AUTH-001: Tela de Login (linha 1246)

**Ajuste:** Adicionar suporte a branding dinâmico por tenant

| Campo | ANTES | DEPOIS |
|-------|-------|--------|
| Descricao | "Tela de login da plataforma LIA com suporte a email/senha e integração futura com SSO via WorkOS." | "Tela de login da plataforma LIA com suporte a email/senha e integração futura com SSO via WorkOS, com branding dinâmico por tenant (logo, cores, nome da empresa carregados via subdomínio)." |
| Regras de Negocio | 6 regras (1-6) | Adicionar regra 7: "Logo e cores carregados dinamicamente por subdomínio (ex: itau.wedotalent.cc)" |
| Requisitos Frontend | LoginPage, react-hook-form, zod, toast | Adicionar: "Detecção de subdomínio, carregamento dinâmico de branding via GET /api/v1/tenants/{subdomain}/branding" |
| Dependencias | (não listado) | Adicionar: AUTH-005 |

---

### 9.2 TRI-001: Configuração Twilio WhatsApp (linha 4731)

> ⚠️ **DISCLAIMER:** A pesquisa e avaliação sobre Twilio e suas alternativas é de responsabilidade exclusiva do **Paulo Moraes**.

**Ajuste:** Reavaliar Twilio → abstração de provider

| Campo | ANTES | DEPOIS |
|-------|-------|--------|
| Titulo | "[INTEGRACAO] Configuracao Twilio WhatsApp" | "[INTEGRACAO] Configuração WhatsApp Business API (Provider Abstrato)" |
| Descricao | "Configurar integracao com Twilio para envio e recebimento de mensagens via WhatsApp Business API." | "Configurar integração com provider de WhatsApp Business API (Twilio, Zenvia, Tudu, ou outro selecionado via TRI-014). Implementar abstração de provider para facilitar troca." |
| Regras de Negocio | 7 regras (1-7) | Adicionar regra 8: "Abstração de provider (interface WhatsAppProvider) para suportar múltiplos serviços" |
| Dependencias | (não listado) | Adicionar: TRI-014 |

---

### 9.3 TRI-006: Tela de Monitoramento → Transcrição da Triagem no Card de Atividade (linha 5227)

**Ajuste:** REFATORAR — De dashboard de monitoramento em tempo real para transcrição completa da triagem dentro do card de evento existente na tab Activities do candidato. NÃO criar aba "Conversas" separada.

| Campo | ANTES | DEPOIS |
|-------|-------|--------|
| Titulo | "[FRONTEND] Tela de Monitoramento de Triagens" | "[FRONTEND] Transcrição Completa da Triagem no Card de Atividade do Candidato" |
| Descricao | "Dashboard para recrutador acompanhar triagens em andamento em tempo real, com status e metricas." | "Transcrição completa da triagem acessível via card de evento de triagem na tab Activities do preview do candidato. Ao clicar no card do evento de triagem, expande/abre a transcrição completa (timeline de mensagens LIA↔candidato). Também acessível via ícone no card do Kanban e na tabela de candidatos dentro da vaga. NÃO criar aba 'Conversas' separada." |
| Regras de Negocio | 8 regras sobre monitoramento real-time (lista de triagens ativas, status em tempo real, barra de progresso, etc.) | Novas regras: 1. A tab Activities do preview do candidato JÁ possui cards de atividades/eventos — o evento de triagem é um desses cards; 2. Ao clicar no card do evento de triagem, exibir transcrição completa em timeline; 3. Cada mensagem mostra: remetente (LIA/candidato), timestamp, conteúdo; 4. Paginação de histórico (20 mensagens por página); 5. Status da triagem (ativa/concluída/pausada/timeout); 6. Filtro por vaga (se candidato tem múltiplas triagens); 7. Indicador visual de mensagens da LIA vs candidato; 8. Ícone de acesso rápido à transcrição no card do Kanban; 9. Ícone de acesso rápido na tabela de candidatos dentro da vaga |
| Requisitos Frontend | ScreeningMonitorDashboard, ScreeningSessionCard, MetricsCards, RealTimeUpdates | ScreeningTranscriptView (timeline de mensagens), adaptar CandidateActivityCard (expand com transcrição), ícone em CandidateCard (Kanban) e tabela de candidatos |
| Requisitos Backend | GET /api/backend-proxy/screening/sessions, WebSocket | GET /api/v1/candidates/{id}/screening-transcript?job_id={job_id} (paginado) |

**Componentes removidos:** ScreeningMonitorDashboard, ScreeningSessionCard, MetricsCards, RealTimeUpdates, LiveIndicator
**Componentes novos:** ScreeningTranscriptView, MessageBubble, ScreeningStatusBadge (adaptação de CandidateActivityCard existente, NÃO criar ConversationHistoryTab)

---

### 9.4 TRI-009: Templates de Mensagem WhatsApp (linha 5544)

**Ajuste:** Adicionar complexidade de aprovação Meta

| Campo | ANTES | DEPOIS |
|-------|-------|--------|
| Regras de Negocio | 7 regras (1-7) | Adicionar regra 8: "Templates precisam ser aprovados pelo Meta Business Manager antes de usar (ver TPL-008)" |
| Dependencias | TRI-001 | Adicionar: TPL-008 |

---

### 9.5 TRI-011: Pré-Qualificação Automatizada (linha 5809)

**Ajuste:** Adiar para Pós-MVP

| Campo | ANTES | DEPOIS |
|-------|-------|--------|
| Status | 📋 Pendente Jira | ⏸️ Adiado para Pós-MVP |
| Nota | (não existia) | "Precisa definição de autonomia da LIA antes de implementar. Reunião de 06/02/2026: adiar até que haja consenso sobre até onde a LIA pode decidir autonomamente." |

---

### 9.6 SCO-002: Modelo Big Five Comportamental (linha 6139)

**Ajuste:** Clarificar papel do Big Five no contexto WSI

| Campo | ANTES | DEPOIS |
|-------|-------|--------|
| Descricao | "Implementar a avaliação comportamental baseada no modelo Big Five (OCEAN)..." | Adicionar ao final: "Nota: Big Five é metodologia aplicada na GERAÇÃO de perguntas WSI (Épico 4), não um cálculo de score separado. A visualização aqui mostra os resultados das dimensões Big Five extraídas das respostas da triagem." |

---

### 9.7 SCO-003: Avaliação Bloom/Dreyfus (linha 6318)

**Ajuste:** Clarificar papel do Bloom/Dreyfus no contexto WSI

| Campo | ANTES | DEPOIS |
|-------|-------|--------|
| Descricao | "Implementar a avaliação de competências técnicas usando a Taxonomia de Bloom Revisada (níveis cognitivos) e o Modelo Dreyfus (níveis de proficiência)..." | Adicionar ao final: "Nota: Bloom/Dreyfus é framework aplicado na GERAÇÃO de perguntas WSI (Épico 4), não avaliação separada. Os scores aqui representam a classificação das respostas da triagem nos frameworks Bloom e Dreyfus." |

---

### 9.8 GAT-003: Modal de Reprovação (linha 7756)

**Ajuste:** Confirmar motivo obrigatório + remover edição direta de feedback

| Campo | ANTES | DEPOIS |
|-------|-------|--------|
| Regras de Negocio | 6 regras. Regra 4: "Opção de editar mensagem antes de enviar" | Remover regra 4 (edição direta). Adicionar regra 7: "Feedback 100% gerado por IA (GAT-004), recrutador NÃO edita diretamente. Apenas visualiza, aprova ou pede regeneração." |
| Requisitos Frontend | RejectionModal, ReasonSelect, FeedbackPreview, FeedbackEditor | Remover FeedbackEditor. Manter: RejectionModal, ReasonSelect, FeedbackPreview. Adicionar: RegenerateButton, ApproveAndSendButton |
| Design Componentes Novos | RejectionModal, ReasonSelect, FeedbackPreview, FeedbackEditor | Remover FeedbackEditor. Adicionar: ApproveAndSendButton |
| Estados | Initial, Filled, Previewing, Editing, Submitting | Remover "Editing". Manter: Initial, Filled, Previewing, Submitting. Adicionar: Regenerating |

---

### 9.9 GAT-004: Geração de Feedback LIA (linha 7938)

**Ajuste:** Feedback é 100% IA, sem edição manual. Trocar modelo para Gemini.

> 📌 **Referência cruzada TRI-013:** Se o candidato reportou um incidente durante a triagem (via "AJUDA"), incluir `had_incident=true` no contexto do prompt. Feedback deve reconhecer dificuldade técnica com tom mais empático.

| Campo | ANTES | DEPOIS |
|-------|-------|--------|
| Regras de Negocio | 7 regras | Adicionar regra 8: "Recrutador apenas visualiza e aprova ou pede regeneração. Sem edição direta do texto." Adicionar regra 9: "Se candidato reportou incidente durante triagem (TRI-013), feedback deve ter tom mais empático reconhecendo dificuldade técnica." |
| Configuracao LLM - Modelo | "Claude 3.5 Haiku (rápido e econômico)" | "Gemini 2.5 Flash (MVP usa exclusivamente Gemini)" |
| Configuracao LLM - Custo | "~$0.003 por feedback (Haiku)" | "~$0.001 por feedback (Gemini Flash)" |
| Integracoes Externas | "LLM (Claude/Gemini)" com "Secret: ANTHROPIC_API_KEY ou GEMINI_API_KEY" | "LLM (Gemini)" com "Secret: GEMINI_API_KEY" |
| Design Componentes Novos | FeedbackPreview, RegenerateButton | FeedbackPreview, RegenerateButton, ApproveAndSendButton |
| Nota | (não existia) | "FeedbackEditor removido. Recrutador não edita texto diretamente — apenas aprova ou pede regeneração." |
| Prompt Template | (não existia como template estruturado) | Adicionar Prompt Template XML: `<role>Você é a LIA, assistente de recrutamento da WeDo Talent. Gere feedback profissional e empático para candidato reprovado.</role> <context>Vaga: {{job_title}} | Candidato: {{candidate_name}} | Motivo reprovação: {{rejection_reason}} | Score WSI: {{wsi_score}} | Houve incidente na triagem: {{had_incident}}</context> <constraints>1. Tom profissional e empático 2. Não mencionar score numérico 3. Sugerir áreas de desenvolvimento 4. Se had_incident=true, reconhecer dificuldade técnica com tom mais compreensivo 5. Máximo 200 palavras 6. Não prometer recontato futuro 7. Não mencionar outros candidatos</constraints> <output_format>{"feedback_text": "...", "tone": "empathetic|neutral|encouraging", "development_areas": ["..."]}</output_format>` |

---

### 9.10 TPL-001: Template de Abordagem Inicial (linha 8647)

**Ajuste:** Dividir template de abordagem em 2 tipos

> 📌 **Referência cruzada TRI-013:** A aceitação do `approach_consent` pelo candidato é o gatilho que dispara a mensagem proativa da LIA orientando sobre o procedimento de reporte de problemas ("AJUDA"). Fluxo: `approach_consent` aceito → mensagem proativa TRI-013 → início da triagem.

| Campo | ANTES | DEPOIS |
|-------|-------|--------|
| Regras de Negocio | 7 regras (1-7) | Adicionar regra 8: "Template de abordagem dividido em 2: (a) Consentimento LGPD e (b) Apresentação da vaga". Adicionar regra 9: "Aceitação do approach_consent dispara mensagem proativa TRI-013 (orientação sobre reporte de problemas)" |
| Requisitos Backend | GET/POST/PUT /api/v1/templates/approach, TemplateService | Adicionar: "Tipos: approach_consent e approach_presentation. Campo type no modelo communication_templates atualizado. Evento de aceitação de consent deve disparar mensagem proativa TRI-013." |
| Dados | communication_templates: type ('approach', 'scheduling', ...) | Adicionar tipos: 'approach_consent', 'approach_presentation' |

---

### 9.11 INT-LLM-001: Cliente Anthropic Claude (linha 16388)

**Ajuste:** Adiar para Pós-MVP

| Campo | ANTES | DEPOIS |
|-------|-------|--------|
| Status | 📋 Pendente Jira e funcionando via Replit Integration | ⏸️ Adiado para Pós-MVP |
| Nota | (não existia) | "MVP usa exclusivamente Gemini. Claude só será implementado se cliente enterprise exigir. Reunião 06/02/2026." |

---

### 9.12 INT-LLM-003: Router de Modelos (linha 16512)

**Ajuste:** Adiar para Pós-MVP

| Campo | ANTES | DEPOIS |
|-------|-------|--------|
| Status | 📋 Pendente Jira | ⏸️ Adiado para Pós-MVP |
| Nota | (não existia) | "Router multi-modelo desnecessário sem Claude no MVP. Com Gemini-only, routing é direto. Reunião 06/02/2026." |

---

### 9.13 INT-LLM-004: Fallback entre Modelos (linha 16632)

**Ajuste:** Adiar para Pós-MVP

| Campo | ANTES | DEPOIS |
|-------|-------|--------|
| Status | 📋 Pendente Jira | ⏸️ Adiado para Pós-MVP |
| Nota | (não existia) | "Fallback desnecessário sem múltiplos modelos no MVP. Gemini-only simplifica. Reunião 06/02/2026." |

---

### 9.14 INT-LLM-005: Gestão de Prompts (linha 16724)

**Ajuste:** Adicionar consumo agrupado por empresa

| Campo | ANTES | DEPOIS |
|-------|-------|--------|
| Regras de Negocio | 6 regras (1-6) | Adicionar regra 7: "Tabela de consumo agrupada por company_id" |
| Requisitos | PromptTemplateService, render, CRUD, Versionamento | Adicionar: "Dashboard mostra consumo por empresa (tokens, custo, requests)" |

---

### 9.15 INT-LLM-006: Cache de Respostas (linha 16854)

**Ajuste:** Cachear perguntas E respostas WSI

| Campo | ANTES | DEPOIS |
|-------|-------|--------|
| Regras de Negocio | 6 regras (1-6) | Adicionar regra 7: "Cachear perguntas E respostas WSI (não só prompts). Cache de perguntas geradas por job_id + block_id." |

---

### 9.16 INT-LLM-007: Monitoramento de Custos (linha 16958)

**Ajuste:** Custos agrupados por empresa com alertas

| Campo | ANTES | DEPOIS |
|-------|-------|--------|
| Regras de Negocio | 6 regras. Regra 2: "Agregar por empresa, usuário, tarefa" | Reforçar regra 2 e adicionar regra 7: "Dashboard de custos agrupado por empresa com alertas. Visão consolidada no admin mostrando consumo por company_id com breakdown por modelo e task_type." |

---

### 9.17 INT-MSG-001: Configurar Azure App Registration (linha 15647)

**Ajuste:** Refazer App Registration

| Campo | ANTES | DEPOIS |
|-------|-------|--------|
| Regras de Negocio | 5 regras (1-5) | Adicionar regra 6: "Refazer App Registration (mudança de conta Microsoft). Reunião 06/02/2026: conta original mudou, necessário recriar." |

---

### 9.18 INT-WOS-005: User Management SDK (linha 17619)

**Ajuste:** Avaliar necessidade

| Campo | ANTES | DEPOIS |
|-------|-------|--------|
| Nota | (não existia) | "⚠️ Avaliar necessidade — pode não ser necessário se plataforma é exclusivamente web (sem app mobile). WorkOS User Management SDK é mais relevante para apps com fluxos nativos. Reunião 06/02/2026." |

---

### 9.19 WSI-004: Edição Manual de Perguntas (linha 4434) — ❌ REMOVER

| Campo | ANTES | DEPOIS |
|-------|-------|--------|
| Status | 📋 Pendente Jira | ❌ Removido — Substituído por WSI-006 (edição conversacional) |
| Justificativa | (não existia) | "Edição manual direta poderia quebrar a integridade da metodologia WSI. Substituído por WSI-006 (edição via prompt conversacional com a LIA). Decisão da reunião de 06/02/2026." |

---

### 9.20 KAN-005: Ícones de Ação Rápida (linha 12199) — ❌ OBSOLETO

| Campo | ANTES | DEPOIS |
|-------|-------|--------|
| Status | 📋 Pendente Jira | ❌ Obsoleto — Confirmado na reunião de 06/02/2026 |
| Nota | (não existia) | "Card obsoleto. Ações rápidas já cobertas por outros componentes (menu de contexto, batch actions). Reunião 06/02/2026." |

---

## PARTE 10: LISTA DETALHADA DE AJUSTES NO PROTÓTIPO REPLIT

> Lista organizada por Sprint com referência a cards, componentes a criar/modificar, descrição do trabalho, complexidade e dependências. Foco em ajustes necessários no protótipo Replit para refletir as decisões da reunião de 06/02/2026.

---

### Sprint 1 (Imediata)

#### 10.1 Login branding dinâmico (AUTH-001 + AUTH-005)

```yaml
Card: AUTH-001, AUTH-005
Acao: MODIFICAR

Arquivos:
  MODIFICAR:
    - plataforma-lia/src/components/pages/login-page.tsx
    - plataforma-lia/src/components/login-page.tsx
    - plataforma-lia/src/components/auth-context.tsx

O Que Fazer: |
  Aceitar query param ?tenant=itau para simular multi-tenant no protótipo.
  Carregar logo, cores e company_name dinamicamente baseado no tenant.
  Criar mock de endpoint branding (GET /api/v1/tenants/{subdomain}/branding).
  ThemeProvider deve aplicar cores do tenant em botões e accents.
  Fallback para branding padrão WeDo Talent se tenant não encontrado.

Complexidade: Média
Dependencias: Nenhuma
```

#### 10.2 Pesquisa Twilio alternativas (TRI-014)

> ⚠️ **DISCLAIMER:** A pesquisa e avaliação sobre Twilio e suas alternativas é de responsabilidade exclusiva do **Paulo Moraes**.

```yaml
Card: TRI-014
Acao: CRIAR
Responsavel: Paulo Moraes (pesquisa exclusiva)

Arquivos:
  CRIAR:
    - docs/pesquisa-alternativas-whatsapp.md

O Que Fazer: |
  ⚠️ DISCLAIMER: Responsabilidade exclusiva do Paulo Moraes.

  Documento de pesquisa comparativa (não é código).
  Tabela comparativa: Twilio vs Zenvia vs Tudu vs Slickflow vs WhatsApp Cloud API vs Gupshup.
  Critérios: custo por mensagem, facilidade de homologação no Brasil, templates Meta,
  webhooks de status, SDK/API quality, suporte Brasil, SLA de entrega,
  sandbox/teste, escalabilidade, compliance LGPD.
  Resultado: recomendação final com justificativa.

Complexidade: Baixa (pesquisa)
Dependencias: Nenhuma
```

---

### Sprint 2

#### 10.3 Chat de ajuste de perguntas WSI — Frontend (WSI-006)

```yaml
Card: WSI-006
Acao: CRIAR + MODIFICAR

Arquivos:
  CRIAR:
    - plataforma-lia/src/components/wsi/QuestionAdjustmentChat.tsx
    - plataforma-lia/src/components/wsi/QuestionDiffView.tsx
    - plataforma-lia/src/components/wsi/AdjustmentCounter.tsx
  MODIFICAR:
    - plataforma-lia/src/components/job-wizard/stages/WSIQuestionsStage.tsx
    - plataforma-lia/src/components/expanded-chat/stages/WSIQuestionsStage.tsx
    - plataforma-lia/src/components/ui-actions/panels/WSIQuestionsPanel.tsx

O Que Fazer: |
  Integrar chat lateral para pedir ajustes em linguagem natural.
  QuestionAdjustmentChat: input de texto + histórico de pedidos.
  QuestionDiffView: mostra antes/depois das perguntas (visual diff).
  AdjustmentCounter: "Ajuste 2 de 5" com barra de progresso.
  Conectar ao backend endpoint POST /api/v1/wsi/questions/adjust.
  Botões "Aceitar" / "Pedir outro ajuste" nas perguntas regeneradas.

Complexidade: Alta
Dependencias: Nenhuma
```

#### 10.4 Backend endpoint ajuste WSI (WSI-006)

```yaml
Card: WSI-006
Acao: CRIAR

Arquivos:
  CRIAR:
    - lia-agent-system/app/api/v1/wsi_question_adjust.py
    - lia-agent-system/app/services/wsi_question_adjuster.py

O Que Fazer: |
  POST /api/v1/wsi/questions/adjust
  Body: { job_id, block_id, adjustment_prompt, current_questions }
  WSIQuestionAdjusterService: usa Gemini 2.5 Flash para regenerar perguntas.
  Validação de conformidade WSI pós-geração (blocos, pesos, sequência).
  Retorno: { adjusted_questions[], diff[], iteration_count }
  Máximo 5 iterações por bloco.

Complexidade: Alta
Dependencias: Nenhuma
```

---

### Sprint 3

#### 10.5 Transcrição da triagem no card de atividade do candidato (TRI-006 refatorado)

```yaml
Card: TRI-006
Acao: CRIAR + MODIFICAR

Arquivos:
  MODIFICAR:
    - plataforma-lia/src/components/search/candidate-detail-sidebar.tsx
    - plataforma-lia/src/components/kanban/components/CandidateCard.tsx
  CRIAR:
    - plataforma-lia/src/components/candidate/ScreeningTranscriptView.tsx

O Que Fazer: |
  NÃO criar aba "Conversas" separada. 
  Enriquecer o card de evento de triagem existente na tab Activities do 
  candidate-detail-sidebar.tsx para suportar expand/click com transcrição completa.
  ScreeningTranscriptView: timeline de mensagens estilo WhatsApp (bolhas azul/cinza)
  com remetente (LIA/candidato), timestamp e conteúdo.
  Paginação de histórico (20 mensagens por página).
  Status da triagem (ativa/concluída/pausada/timeout).
  Adicionar ícone de acesso rápido à transcrição no CandidateCard.tsx (Kanban)
  e na tabela de candidatos dentro da vaga.
  Mock data para demonstração.

Complexidade: Média
Dependencias: Nenhuma
```

#### 10.6 Painel de incidentes de triagem (TRI-013)

```yaml
Card: TRI-013
Acao: CRIAR + MODIFICAR

Arquivos:
  CRIAR:
    - plataforma-lia/src/components/incidents/IncidentsPanel.tsx
    - plataforma-lia/src/components/incidents/IncidentDetailView.tsx
    - plataforma-lia/src/components/incidents/IncidentBadge.tsx
  MODIFICAR:
    - Sidebar principal (adicionar badge de incidentes)

O Que Fazer: |
  IncidentsPanel: lista de incidentes com status (urgente/pendente/resolvido) — para time WeDo Talent (suporte).
  IncidentDetailView: detalhes com últimas 5 mensagens, ações (assumir/resetar/resolver/escalonar).
  IncidentBadge: contador de incidentes pendentes no sidebar.
  Cores: urgente (vermelho), pendente (amarelo), resolvido (verde).
  Nota: Notificação vai para time WeDo Talent, NÃO para recrutador do cliente.
  LIA informa procedimento de reporte no início da triagem (pós-LGPD): prazo de 24h.
  Mock data com 3-5 incidentes de exemplo.

Complexidade: Média
Dependencias: Nenhuma
```

#### 10.7 Modal de reprovação ajustado (GAT-003 + GAT-004)

```yaml
Card: GAT-003, GAT-004
Acao: CRIAR + MODIFICAR

Arquivos:
  MODIFICAR:
    - plataforma-lia/src/components/batch-approval-modal.tsx
  CRIAR:
    - plataforma-lia/src/components/modals/rejection-modal.tsx (ou adaptar existente)

O Que Fazer: |
  Confirmar que motivo de reprovação é obrigatório (select predefinido).
  REMOVER edição direta de feedback (FeedbackEditor).
  Adicionar preview de feedback gerado por IA (FeedbackPreview).
  Adicionar botão "Regenerar" para pedir novo feedback da IA.
  Adicionar botão "Aprovar e Enviar" para confirmar envio.
  Trocar referências de Claude para Gemini no código/comentários.
  Estado: motivo → loading (gerando feedback) → preview → regenerar ou aprovar.
  📌 Nota: Se candidato reportou incidente durante triagem (TRI-013),
  incluir badge "Incidente reportado" no modal e considerar contexto
  no prompt de feedback (tom mais empático).

Complexidade: Média
Dependencias: Nenhuma
```

#### 10.8 Templates de abordagem separados (TPL-001)

```yaml
Card: TPL-001
Acao: MODIFICAR

Arquivos:
  MODIFICAR:
    - plataforma-lia/src/components/email-templates/email-templates-manager.tsx

O Que Fazer: |
  Separar template de abordagem em 2 tipos:
  (a) "Consentimento LGPD" — mensagem de coleta de consentimento
  (b) "Apresentação da Vaga" — mensagem de apresentação da oportunidade
  Adicionar toggle/tab para alternar entre os 2 tipos.
  Ajustar filtros e listagem para mostrar os 2 tipos separadamente.
  📌 Nota: A aceitação do consentimento LGPD é o gatilho que dispara
  a mensagem proativa TRI-013 (orientação ao candidato sobre reporte
  de problemas via "AJUDA").

Complexidade: Baixa
Dependencias: TRI-013 (mensagem proativa pós-consentimento)
```

#### 10.9 Status Meta nos templates WhatsApp (TPL-008)

```yaml
Card: TPL-008
Acao: MODIFICAR

Arquivos:
  MODIFICAR:
    - plataforma-lia/src/components/email-templates/email-template-form-modal.tsx

O Que Fazer: |
  Adicionar badge de status Meta no editor de template:
  - Pendente Meta (amarelo, pulsando)
  - Aprovado (verde)
  - Rejeitado (vermelho) com motivo de rejeição
  Simulação com mock data (status fixo por template).
  Mostrar motivo de rejeição quando status = rejected.
  Botão "Re-submeter" para templates rejeitados.

Complexidade: Baixa
Dependencias: Item 10.8 (templates separados)
```

#### 10.10 Botão disparar triagem em lote (KAN-011)

```yaml
Card: KAN-011
Acao: CRIAR + MODIFICAR

Arquivos:
  CRIAR:
    - plataforma-lia/src/components/kanban/components/BatchScreeningButton.tsx
    - plataforma-lia/src/components/modals/screening-progress-modal.tsx
  MODIFICAR:
    - plataforma-lia/src/components/pages/job-kanban-page.tsx

O Que Fazer: |
  BatchScreeningButton: botão flutuante que aparece quando candidatos selecionados
  na coluna "Funil Aprovado". Texto: "Iniciar Triagem (N selecionados)".
  ScreeningProgressModal: modal de confirmação + barra de progresso.
  Confirmação: "Iniciar triagem WSI para N candidatos?"
  Progresso: "Enviando 3/10..." com animação.
  Ao concluir: candidatos movem para coluna "Em Triagem".
  Funciona em Kanban e Table views.

Complexidade: Média
Dependencias: Nenhuma
```

#### 10.11 Modal solicitar mais candidatos (KAN-012)

```yaml
Card: KAN-012
Acao: CRIAR + MODIFICAR

Arquivos:
  CRIAR:
    - plataforma-lia/src/components/modals/refined-search-modal.tsx
  MODIFICAR:
    - plataforma-lia/src/components/pages/job-kanban-page.tsx

O Que Fazer: |
  Botão "Mais candidatos" no header da vaga (Kanban e Table views).
  RefinedSearchModal: modal com 3 fases:
  1. "Analisando padrões..." (loading)
  2. Lista de sugestões de refinamento com aceitar/rejeitar individual
  3. Resultados da busca refinada com "Adicionar à vaga"
  LIA sugere: "Com base nas reprovações, sugiro aumentar experiência mínima para 5 anos"
  Busca exclui candidatos já avaliados.

Complexidade: Alta
Dependencias: Nenhuma
```

#### 10.12 Modal buscar candidatos similares (KAN-013)

```yaml
Card: KAN-013
Acao: CRIAR + MODIFICAR

Arquivos:
  CRIAR:
    - plataforma-lia/src/components/modals/similar-candidates-modal.tsx
  MODIFICAR:
    - plataforma-lia/src/components/kanban/components/CandidateCard.tsx
    - plataforma-lia/src/components/pages/job-kanban/KanbanCard.tsx

O Que Fazer: |
  Ação "Buscar similares" no menu de contexto (⋮) do card de candidato.
  SimilarCandidatesModal: candidato base no topo + top 10 similares.
  SimilarityScoreBadge: badge circular com % de similaridade.
  Cores por faixa: >80% verde, 60-79% cyan, <60% amarelo.
  Botão "Adicionar à vaga" em cada resultado.
  Mock data para demonstração.

Complexidade: Média
Dependencias: Nenhuma
```

#### 10.13 Ação de Limpeza: Remover/marcar KAN-005 como obsoleto (KAN-005)

```yaml
Card: KAN-005
Acao: LIMPEZA — REMOVER/MARCAR COMO DEPRECATED
Nota: "Esta é uma ação de limpeza (cleanup), não uma feature nova. Consistente com PARTE 9, item 9.20 que marca KAN-005 como obsoleto."

Arquivos:
  VERIFICAR:
    - Buscar componente QuickActionIcons no codebase
    - Se existir: remover ou marcar como deprecated com comentário

O Que Fazer: |
  Ação de limpeza: remover ou marcar como deprecated o componente QuickActionIcons (ou similar).
  
  Passo 1: Verificar se existe componente QuickActionIcons ou QuickActionBar no codebase.
  Passo 2: Se existir: 
    - Marcar como @deprecated com comentário explicativo
    - Nota: "Substituído por menu de contexto e batch actions. Obsoletizado em reunião 06/02/2026. Ver PARTE 9, item 9.20."
    - Remover referências em outros componentes que usam esse card
  Passo 3: Se não existir: apenas documentar que card foi obsoletado na reunião.
  
  Esta é uma ação de limpeza de código morto/Dead Code, não uma feature a construir.
  Ações rápidas já estão cobertas por: menu de contexto (⋮), batch actions (seleção múltipla), e KAN-011/KAN-012/KAN-013.

Complexidade: Baixa
Dependencias: Nenhuma
```

---

### Sprint 4

#### 10.14 Insights de decisões no dashboard (GAT-008)

```yaml
Card: GAT-008
Acao: CRIAR + MODIFICAR

Arquivos:
  CRIAR:
    - plataforma-lia/src/components/dashboard/DecisionInsightsPanel.tsx
  MODIFICAR:
    - plataforma-lia/src/components/pages/dashboards-page.tsx

O Que Fazer: |
  DecisionInsightsPanel: painel com estatísticas de aprovação/reprovação.
  Taxa de aprovação por vaga (gráfico de barras).
  Motivos mais comuns de reprovação (donut chart).
  Sugestões inline da IA: "80% dos reprovados tinham < 3 anos. Ajustar filtro?"
  Cards de sugestão com botões "Aceitar" / "Ignorar".
  Integrar no dashboard principal como nova seção.

Complexidade: Média
Dependencias: Itens do Sprint 3 (10.7 — GAT-003/004)
```

#### 10.15 Dashboard de consumo LLM (INT-LLM-005/007)

```yaml
Card: INT-LLM-005, INT-LLM-007
Acao: VERIFICAR + AJUSTAR

Arquivos:
  VERIFICAR/AJUSTAR:
    - Componentes existentes: ConsumptionChart, ConsumptionSummaryCard, AgentBreakdown
    - plataforma-lia/src/components/admin/ai-consumption/

O Que Fazer: |
  Validar que dashboard de consumo LLM agrupa por empresa (company_id).
  Ajustar para Gemini-only no MVP:
  - Remover referências a Claude nos labels e breakdowns
  - Ajustar pricing table para Gemini 2.5 Pro/Flash
  Garantir que alertas de budget estão configurados (50%, 80%, 100%).
  Adicionar coluna company_name na tabela de consumo.

Complexidade: Baixa
Dependencias: Nenhuma
```

---

### Tabela Resumo de Ajustes no Protótipo

| Sprint | Itens | Componentes a Criar | Componentes a Modificar | Complexidade Total |
|--------|-------|---------------------|------------------------|--------------------|
| **Sprint 1** | 2 (10.1, 10.2) | 1 (doc) | 3 | Média |
| **Sprint 2** | 2 (10.3, 10.4) | 5 | 3 | Alta |
| **Sprint 3** | 9 (10.5–10.13) | 11 | 9 | Alta |
| **Sprint 4** | 2 (10.14, 10.15) | 1 | 2 | Média |
| **TOTAL** | **15 itens** | **18 componentes** | **17 componentes** | **Alta** |

---

## PARTE 11: MAPEAMENTO COMPLETO DE EVENTOS NOTIFICÁVEIS (ÉPICO 10)

> Este mapeamento é pré-requisito para a implementação do Épico 10 (Notificações). Define TODOS os eventos da plataforma que devem gerar notificações para o recrutador, organizados por categoria de origem. Para cada evento: trigger, canais, prioridade, template da mensagem com informações estratégicas, ação esperada e deep link.
>
> **Objetivo:** O recrutador deve ser informado de forma estratégica sobre tudo que acontece em suas vagas, com informações que ajudem a tomar decisões, otimizar tempo e acompanhar processos sem precisar abrir a plataforma a cada momento.

### 11.1 Categorias de Origem

| Categoria | Fonte | Ícone | Exemplos |
|-----------|-------|-------|----------|
| **LIA / AI** | Ações da inteligência artificial | 🤖 | Sugestões, insights, enriquecimento, análise |
| **Sistema** | Eventos automáticos da plataforma | ⚙️ | Busca concluída, score calculado, SLA |
| **Agentes** | Agentes autônomos especializados | 🔄 | Triagem batch, avaliação WSI, screening |
| **Candidato** | Ações ou eventos do candidato | 👤 | Resposta WhatsApp, incidente, cancelamento |
| **Plataforma** | Administrativo e configuração | 🏢 | Manutenção, limites, billing, integrações |

### 11.2 Canais de Notificação

| Canal | Prioridade | Latência | Uso |
|-------|-----------|----------|-----|
| **Bell (in-app)** | Todas | Real-time (WebSocket) | Padrão para todos os eventos |
| **Push (browser)** | Alta e Crítica | Imediato | Recrutador fora da plataforma |
| **Email** | Média e Alta | Até 5 min | Resumo diário / eventos importantes |
| **Teams** | Alta e Crítica | Imediato | Canal preferido do recrutador (NOT-007) |

### 11.3 Mapeamento de Eventos — LIA / AI (🤖)

| # | Evento | Trigger | Prioridade | Canais | Template da Mensagem | Informação Estratégica | Ação do Recrutador | Deep Link | Épico Origem |
|---|--------|---------|-----------|--------|---------------------|----------------------|-------------------|-----------|-------------|
| 1 | **Enriquecimento de JD concluído** | LIA termina enriquecimento da descrição da vaga | Alta | Bell, Push | "LIA enriqueceu a JD de **{vaga}** com {N} sugestões: {N_skills} competências, {N_resp} responsabilidades e análise salarial de mercado." | Quantas sugestões, WSI Quality Score atual, gap para meta | Revisar e aceitar/rejeitar sugestões | /wizard/{job_id}/jd-enrichment | Épico 2 |
| 2 | **Insight de padrão de decisão** | LIA detecta padrão em aprovações/reprovações | Média | Bell | "📊 Padrão detectado: nos últimos 30 dias, **{X}%** dos reprovados para **{vaga}** tinham menos de {Y} anos de experiência. Quer ajustar o filtro de busca?" | % do padrão, número de decisões analisadas, sugestão de ajuste | Aceitar sugestão de ajuste | /dashboard/insights | Épico 7 (GAT-008) |
| 3 | **Sugestão de competência** | LIA sugere competência baseada em vagas similares | Baixa | Bell | "💡 Vagas similares a **{vaga}** incluem a competência **{skill}** em {X}% dos casos. Considere adicionar." | % de vagas similares, fonte (mercado/empresa) | Aceitar/ignorar | /wizard/{job_id}/competencies | Épico 2 |
| 4 | **Benchmark salarial atualizado** | Dados de mercado atualizados para a vaga | Baixa | Bell | "📈 O benchmark salarial para **{cargo}** em **{região}** foi atualizado: faixa de R$ {min} a R$ {max} (mediana R$ {med})." | Faixa anterior vs atual, delta % | Revisar salário da vaga | /wizard/{job_id}/salary | Épico 2 |
| 5 | **Feedback de reprovação gerado** | LIA gera feedback personalizado para candidato | Média | Bell | "✍️ Feedback pronto para **{candidato}** ({vaga}). Motivo: {motivo}. Aguardando sua aprovação para envio." | Motivo resumido, score WSI do candidato | Aprovar ou regenerar feedback | /candidates/{id}/feedback | Épico 7 (GAT-004) |
| 6 | **Análise de candidato concluída** | LIA termina análise multimodal (CV, vídeo) | Alta | Bell, Push | "📄 Análise do CV de **{candidato}** concluída. Score: **{score}/100**. Top skills: {skills}. {N} alertas detectados." | Score, top skills, alertas, compatibilidade com vaga | Revisar análise | /candidates/{id}/analysis | Épico 15 |

### 11.4 Mapeamento de Eventos — Sistema (⚙️)

| # | Evento | Trigger | Prioridade | Canais | Template da Mensagem | Informação Estratégica | Ação do Recrutador | Deep Link | Épico Origem |
|---|--------|---------|-----------|--------|---------------------|----------------------|-------------------|-----------|-------------|
| 7 | **Busca de candidatos concluída** | Engine de busca termina mapeamento | Alta | Bell, Push, Teams | "🔍 Busca para **{vaga}** concluída: **{N} candidatos** encontrados. Top match: **{candidato}** ({score}%). {N_high} com score acima de {threshold}%." | Total encontrados, top 3, distribuição de scores, tempo de busca | Revisar candidatos | /jobs/{id}/search | Épico 3 |
| 8 | **Score WSI calculado** | Sistema calcula score final do candidato | Alta | Bell, Push, Teams | "📊 Score WSI de **{candidato}** para **{vaga}**: **{score}/100**. Bloco mais forte: {bloco_forte}. Bloco mais fraco: {bloco_fraco}." | Score por bloco WSI, comparação com média da vaga, posição no ranking | Revisar score e decidir gate | /candidates/{id}/wsi-score | Épico 6 |
| 9 | **Candidato movido no pipeline** | Candidato avança/retrocede de etapa | Baixa | Bell | "📋 **{candidato}** movido para **{etapa}** em **{vaga}**. {motivo_se_automatico}." | Etapa anterior → nova, quem moveu (LIA/recrutador), tempo na etapa anterior | Nenhuma (informativo) | /kanban/{job_id} | Épico 11 |
| 10 | **SLA de etapa estourando** | Candidato preso em etapa por mais de X dias | Alta | Bell, Push, Email, Teams | "⏰ **{candidato}** está há **{N} dias** na etapa **{etapa}** de **{vaga}**. SLA de {sla_dias} dias ultrapassado. Ação necessária." | Dias na etapa, SLA configurado, ação sugerida | Tomar ação no candidato | /kanban/{job_id}?highlight={candidate_id} | Épico 11 |
| 11 | **Vaga com poucos candidatos** | Pipeline tem menos de X candidatos ativos | Média | Bell, Email | "⚠️ A vaga **{vaga}** tem apenas **{N} candidatos ativos** no pipeline. Considere ampliar a busca ou ajustar critérios." | Total ativos, total reprovados, taxa de conversão, sugestão | Ampliar busca ou ajustar | /jobs/{id}/search | Épico 3 |
| 12 | **Entrevista agendada** | Sistema confirma agendamento | Alta | Bell, Push, Teams | "📅 Entrevista agendada: **{candidato}** para **{vaga}** em **{data}** às **{hora}**. Link: {link_reuniao}." | Data, hora, link, formato (presencial/remoto), duração | Preparar-se para entrevista | /interviews/{id} | Épico 9 |
| 13 | **Entrevista cancelada** | Candidato ou sistema cancela | Alta | Bell, Push, Teams | "❌ Entrevista com **{candidato}** ({vaga}) cancelada. Motivo: {motivo}. {sugestao_reagendar}." | Motivo, quem cancelou, sugestão de reagendamento | Reagendar ou tomar ação | /interviews/{id} | Épico 9 |
| 14 | **Vaga próxima do deadline** | Vaga com prazo de fechamento próximo | Alta | Bell, Push, Email, Teams | "🗓️ A vaga **{vaga}** vence em **{N} dias** ({data}). Pipeline atual: {N_candidatos} candidatos, {N_etapa_final} na etapa final." | Dias restantes, status do pipeline, candidatos na etapa final | Priorizar ações na vaga | /jobs/{id}/overview | Épico 2 |
| 15 | **Resumo diário de vagas** | Cron job diário (8h) | Baixa | Email | "📬 Resumo diário — Suas vagas ativas: {N_vagas}. Novos candidatos: {N_novos}. Pendentes de decisão: {N_pendentes}. Entrevistas hoje: {N_entrevistas}." | Vagas ativas, novos candidatos, pendências, entrevistas do dia | Planejar o dia | /dashboard | Todos |

### 11.5 Mapeamento de Eventos — Agentes (🔄)

| # | Evento | Trigger | Prioridade | Canais | Template da Mensagem | Informação Estratégica | Ação do Recrutador | Deep Link | Épico Origem |
|---|--------|---------|-----------|--------|---------------------|----------------------|-------------------|-----------|-------------|
| 16 | **Triagem batch concluída** | Agente finaliza triagem em lote | Alta | Bell, Push, Teams | "✅ Triagem em lote concluída para **{vaga}**: **{N_triados}/{N_total}** candidatos triados. {N_aprovados} acima do threshold ({threshold}%). Tempo: {tempo}." | Triados/total, aprovados/reprovados, tempo total, média de score | Revisar resultados | /jobs/{id}/screening-results | Épico 5 (KAN-NEW1) |
| 17 | **Triagem individual concluída** | Agente termina triagem de um candidato | Média | Bell | "📋 Triagem de **{candidato}** para **{vaga}** concluída. Score preliminar: **{score}**. Duração: {tempo}. {N_perguntas} perguntas respondidas." | Score, duração, completude, alertas | Revisar transcrição | /candidates/{id}/activities | Épico 5 |
| 18 | **Agente WSI gerou perguntas** | Geração de perguntas WSI concluída | Média | Bell | "🎯 **{N} perguntas WSI** geradas para **{vaga}** cobrindo {N_blocos} blocos. WSI Quality Score: **{score}%**. {alertas_se_houver}." | N perguntas, blocos cobertos, quality score, gaps | Revisar e ajustar perguntas | /jobs/{id}/wsi-questions | Épico 4 |
| 19 | **Busca de similares concluída** | Agente encontra candidatos similares | Média | Bell, Push | "🔗 **{N} candidatos similares** a **{candidato_ref}** encontrados para **{vaga}**. Similaridade média: {sim}%. Top: {top_candidato} ({top_sim}%)." | N encontrados, top 3, similaridade média | Revisar similares | /candidates/{id}/similar | Épico 3 (KAN-NEW3) |

### 11.6 Mapeamento de Eventos — Candidato (👤)

| # | Evento | Trigger | Prioridade | Canais | Template da Mensagem | Informação Estratégica | Ação do Recrutador | Deep Link | Épico Origem |
|---|--------|---------|-----------|--------|---------------------|----------------------|-------------------|-----------|-------------|
| 20 | **Candidato respondeu WhatsApp** | Mensagem recebida via webhook | Média | Bell | "💬 **{candidato}** respondeu no WhatsApp ({vaga}). Última mensagem: \"{preview_msg}\"." | Preview da mensagem, contexto (triagem/abordagem), tempo de resposta | Monitorar (se fora de triagem automática) | /candidates/{id}/activities | Épico 5 |
| 21 | **Candidato aceitou consentimento LGPD** | Candidato responde SIM ao approach_consent | Média | Bell | "✅ **{candidato}** aceitou o consentimento LGPD para **{vaga}**. Triagem pode ser iniciada." | Tempo de resposta, vaga associada | Iniciar triagem (se não automática) | /candidates/{id}/activities | Épico 5 (TPL-001) |
| 22 | **Candidato recusou consentimento** | Candidato responde NÃO ao approach_consent | Alta | Bell, Push, Teams | "🚫 **{candidato}** recusou o consentimento LGPD para **{vaga}**. Candidato não pode ser triado." | Motivo (se informado), impacto no pipeline | Registrar e buscar substituto | /candidates/{id} | Épico 5 (TPL-001) |
| 23 | **Incidente reportado por candidato** | Candidato digita "AJUDA" na triagem | Crítica | Bell, Push, Email, Teams | "🚨 **INCIDENTE:** Candidato **{candidato}** reportou problema durante triagem de **{vaga}**. Descrição: \"{preview}\". SLA: 24h. Encaminhado ao time WeDo Talent." | Descrição, etapa da triagem, histórico de mensagens | Nenhuma (direcionado ao time WeDo Talent) — recrutador informado para contexto | /incidents/{id} | Épico 5 (TRI-013) |
| 24 | **Candidato não respondeu (timeout)** | Timeout de resposta na triagem | Média | Bell | "⏳ **{candidato}** não respondeu há **{N} horas** na triagem de **{vaga}**. Retentativa #{N_retry} será enviada automaticamente." | Tempo sem resposta, número de retentativas, próxima ação automática | Monitorar | /candidates/{id}/activities | Épico 5 |
| 25 | **Candidato confirmou entrevista** | Candidato aceita horário proposto | Alta | Bell, Push, Teams | "✅ **{candidato}** confirmou entrevista para **{vaga}** em **{data}** às **{hora}**. Tudo certo!" | Data, hora, link da reunião, formato | Preparar entrevista | /interviews/{id} | Épico 9 |

### 11.7 Mapeamento de Eventos — Plataforma (🏢)

| # | Evento | Trigger | Prioridade | Canais | Template da Mensagem | Informação Estratégica | Ação do Recrutador | Deep Link | Épico Origem |
|---|--------|---------|-----------|--------|---------------------|----------------------|-------------------|-----------|-------------|
| 26 | **Limite de consumo LLM atingido** | Uso de Gemini atinge threshold (50%, 80%, 100%) | Alta (80%+) | Bell, Email, Teams | "⚠️ Consumo de IA em **{threshold}%** do limite mensal da empresa **{empresa}**. Gasto atual: R$ {gasto}. Limite: R$ {limite}. Estimativa de fim: {data_estimada}." | Gasto atual, limite, projeção, top consumers | Notificar gestor / otimizar uso | /admin/ai-consumption | Épico 14 (INT-LLM-005/007) |
| 27 | **Template WhatsApp aprovado pelo Meta** | Polling detecta aprovação | Média | Bell | "✅ Template WhatsApp **\"{nome_template}\"** foi **aprovado** pelo Meta. Já disponível para uso." | Nome, tipo, data de submissão, tempo de aprovação | Nenhuma (informativo) | /settings/templates | Épico 8 (TPL-008) |
| 28 | **Template WhatsApp rejeitado pelo Meta** | Polling detecta rejeição | Alta | Bell, Push, Teams | "❌ Template WhatsApp **\"{nome_template}\"** foi **rejeitado** pelo Meta. Motivo: {motivo}. Sugestão: {sugestao_correcao}." | Motivo da rejeição, sugestão de correção | Corrigir e resubmeter | /settings/templates/{id}/edit | Épico 8 (TPL-008) |
| 29 | **Manutenção programada** | Admin agenda manutenção | Baixa | Bell, Email | "🔧 Manutenção programada para **{data}** das **{hora_ini}** às **{hora_fim}**. A plataforma ficará indisponível. Salve seu trabalho." | Data, duração, impacto | Salvar trabalho | /dashboard | Admin |
| 30 | **Novo usuário adicionado ao tenant** | Admin adiciona recrutador | Baixa | Bell | "👤 Novo membro **{nome}** adicionado à equipe **{empresa}**. Perfil: {role}." | Nome, role, data | Nenhuma (informativo) | /admin/users | Épico 1 (AUTH) |

### 11.8 Cobertura dos Tipos Originais (NOT-001)

> Os 5 tipos de notificação definidos originalmente no NOT-001 estão cobertos e expandidos neste mapeamento:

| Tipo Original (NOT-001) | Eventos que Cobrem | IDs |
|--------------------------|-------------------|-----|
| `candidato_triado` | Triagem individual concluída, Triagem batch concluída | #17, #16 |
| `entrevista_confirmada` | Entrevista agendada, Candidato confirmou entrevista | #12, #25 |
| `entrevista_cancelada` | Entrevista cancelada | #13 |
| `mensagem_whatsapp` | Candidato respondeu WhatsApp, Candidato aceitou LGPD, Candidato recusou LGPD, Candidato não respondeu (timeout) | #20, #21, #22, #24 |
| `sistema` | Manutenção programada, Novo usuário, Limite LLM, SLA estourando, Vaga deadline, Resumo diário | #29, #30, #26, #10, #14, #15 |
| **(NOVOS — não existiam)** | Enriquecimento JD, Insight padrão, Sugestão competência, Benchmark salarial, Feedback gerado, Análise candidato, Busca concluída, Score WSI, Pipeline move, Poucos candidatos, Perguntas WSI, Similares, Incidente, Templates Meta | #1-6, #7-9, #11, #18-19, #23, #27-28 |

### 11.9 Regra de Canais por Prioridade

> **Regra geral:** Todo evento de prioridade **Alta** ou **Crítica** inclui Teams. Exceções devem ser documentadas.

| Prioridade | Bell | Push | Email | Teams | Total Eventos |
|-----------|------|------|-------|-------|---------------|
| **Crítica** | ✅ | ✅ | ✅ | ✅ | 1 (incidente TRI-013) |
| **Alta** | ✅ | ✅ | Seletivo | ✅ | 12 |
| **Média** | ✅ | Seletivo | ❌ | ❌ | 10 |
| **Baixa** | ✅ | ❌ | Seletivo | ❌ | 7 |
| **TOTAL** | **30** | **~16** | **~8** | **~13** | **30 eventos** |

### 11.10 Template de Mensagem — Estrutura Padrão

```yaml
Estrutura de cada notificação:
  - icon: Ícone da categoria (🤖/⚙️/🔄/👤/🏢)
  - title: Título curto e objetivo (max 80 chars)
  - body: Mensagem com dados interpolados ({variáveis})
  - strategic_info: Informação que ajuda o recrutador a TOMAR DECISÃO
  - action_label: Texto do botão de ação (ex: "Revisar", "Aprovar", "Ver detalhes")
  - action_url: Deep link para o contexto na plataforma
  - priority: critical | high | medium | low
  - channels: [bell, push, email, teams]
  - grouping: Agrupar notificações similares em 5 min (ex: "5 candidatos triados" em vez de 5 notificações separadas)
  - expiry: Tempo até expirar (24h para críticas, 7d para médias, 30d para baixas)
```

### 11.11 Regras de Agrupamento e Anti-Spam

```yaml
Regras:
  1. Janela de agrupamento: 5 minutos
     - Se 5 candidatos forem triados em 5 min → 1 notificação: "5 candidatos triados para {vaga}"
  2. Limite diário por canal:
     - Bell: sem limite (feed infinito)
     - Push: máximo 20/dia (prioridade alta+ apenas)
     - Email: 1 resumo diário + notificações críticas
     - Teams: máximo 30/dia (rate limit da API)
  3. Horário de silêncio (configurável):
     - Default: 22h-7h (sem push/Teams)
     - Email: sem restrição
     - Bell: sem restrição
  4. Preferências do recrutador (NOT-003):
     - Toggle por tipo de evento E por canal
     - Ex: "Quero triagem por Bell e Push, mas NÃO por email"
```

### 11.12 Ações Pendentes para Implementação

- [ ] **NOT-MAP-001:** Validar este mapeamento com Anderson (feedback sobre quais eventos são mais valiosos para ele)
- [ ] **NOT-MAP-002:** Definir prioridade relativa dos 30 eventos para order de implementação
- [ ] **NOT-MAP-003:** Criar Adaptive Card templates para Teams (NOT-007) para cada evento de prioridade alta+
- [ ] **NOT-MAP-004:** Definir formato do email de resumo diário (evento #15)
- [ ] **NOT-MAP-005:** Especificar regras de agrupamento para cada tipo de evento
- [ ] **NOT-MAP-006:** Atualizar NOT-001 no Jira com os 30 tipos de evento (substituir os 5 originais)
- [ ] **NOT-MAP-007:** Definir métricas de sucesso: taxa de abertura, taxa de ação, tempo até ação
