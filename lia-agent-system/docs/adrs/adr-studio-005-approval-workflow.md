# ADR-Studio-005: Workflow obrigatório de aprovação de admin antes de agente ir para ACTIVE

**Status:** ACCEPTED  
**Data:** 2026-06-14  
**Origem:** Auditoria ultracode Agent Studio

---

## Contexto

Agentes customizados do Agent Studio executam com ferramentas reais de alto impacto: enviar e-mail, rejeitar candidato, publicar vaga, disparar notificações em massa. Um agente malicioso ou mal-configurado instalado por um tenant pode causar danos irreversíveis a candidatos e à reputação da empresa. Adicionalmente, o EU AI Act Art. 12 exige rastreabilidade e supervisão humana para sistemas de IA de alto impacto que tomem ou auxiliem decisões sobre pessoas, e a LGPD Art. 20 garante ao titular o direito de revisão de decisões automatizadas significativas. Antes do P0-2 do Onda 0 (corrigido em 2026-06-12), agentes instalados do marketplace entravam em execução imediatamente após a instalação, sem nenhum gate de revisão. Qualquer tenant podia instalar um agente do marketplace e executá-lo contra candidatos reais sem que a WeDOTalent soubesse ou aprovasse. O audit P0-3 de 2026-05-21 também revelou que o ciclo de vida inteiro do Agent Studio (criar, atualizar, deletar, executar, publicar, instalar, revisar, aprovar) não gerava nenhum registro em audit_logs, violando os dois marcos regulatórios acima. O contexto técnico é: agentes do marketplace têm um MarketplaceListingRecord associado (campo marketplace_listing na entidade CustomAgent); agentes criados diretamente pelo tenant não têm esse registro e não passam pelo gate de aprovação do marketplace.

## Decisão

Todo agente instalado a partir do marketplace fica com o status do listing em pending_review imediatamente após a instalação. A execução desse agente — tanto pelo endpoint REST POST /custom-agents/{agent_id}/execute quanto pelo caminho de domínio em domain.py — é bloqueada com HTTP 403 (erro agent_pending_review) enquanto o listing permanecer em pending_review. A desbloqueio só ocorre quando um usuário com role wedotalent_admin chama POST /admin/agent-marketplace/review/{listing_id} com action=approve, o que muda o status do listing para active. Toda ação do ciclo de vida (criação, atualização, instalação, execução, teste, aprovação, rejeição, desinstalação) gera um registro canônico em audit_logs via studio_audit(), wrapper de AuditService.log_decision, com campos padronizados: company_id (sempre do JWT, nunca do payload), action, decision, reasoning[], actor_user_id, target_id e target_type. O gate é implementado em dois pontos defensivos independentes: no endpoint FastAPI (custom_agents.py:525) e na camada de domínio (domain.py:631), garantindo defesa em profundidade. Agentes criados diretamente pelo tenant (sem marketplace_listing) não passam por esse gate — podem executar em qualquer status active ou draft.

## Alternativas Consideradas

1. Ativação imediata no momento da instalação — agente vai direto para ACTIVE sem revisão. Rejeitada: elimina toda supervisão humana sobre ferramentas de alto impacto; viola EU AI Act Art. 12 e requisito de procurement enterprise.
2. Ativação por cota — tenant pode ativar até N agentes por mês sem revisão manual. Rejeitada: não garante revisão de conteúdo/ferramentas; cota protege contra volume mas não contra agentes mal-intencionados ou mal-configurados.
3. Revisão apenas pela equipe WeDOTalent (staff interno) — sem gate no execute endpoint, confiando que a publicação no marketplace já foi curada. Rejeitada: o audit P0-2 confirmou que agentes instalados podiam executar antes de qualquer revisão no caminho de produção; curadoria de publicação não substitui gate de execução por tenant.
4. Sem qualquer gate — execução livre de qualquer agente instalado. Rejeitada: P0-2 original antes de 2026-06-12; risco regulatório e reputacional inaceitável.

## Consequências

### Positivas
- Governança enterprise: clientes corporativos têm controle formal sobre quais agentes rodam em produção antes de qualquer execução real.
- Trilha de auditoria EU AI Act Art. 12: todo evento do ciclo de vida (create/install/approve/reject/execute) gera registro canônico em audit_logs com actor, reasoning e timestamp, satisfazendo o requisito de registro de decisões por 6 meses.
- Prevenção de agentes rogue: agente mal-configurado ou injetado via marketplace não executa ferramentas reais (send_email, reject_candidate, publish_job) até aprovação explícita.
- Requisito de procurement enterprise: gate de aprovação documentado é diferencial formal em processos de compra de grandes contas que exigem evidência de controle de IA.
- Defesa em profundidade: gate duplicado em endpoint REST e em camada de domínio garante que nenhum caminho de invocação (chat SSE, API direta, domain tool) bypassa a revisão.
- LGPD Art. 20: decisões automatizadas sobre candidatos geradas por agentes do marketplace têm trilha de aprovação humana prévia, reforçando o direito de revisão.

### Negativas / Trade-offs
- Fricção para times pequenos: empresas que criam agentes internamente (sem marketplace) não sofrem o gate, mas times que dependem de agentes do marketplace precisam aguardar aprovação de admin WeDOTalent.
- Gargalo de aprovação: se o admin WeDOTalent estiver indisponível, agentes instalados ficam bloqueados indefinidamente; não há SLA de aprovação nem mecanismo de escalada automatizada implementado.
- Gap residual — agentes draft executam: o gate atual verifica apenas o status do marketplace_listing; agentes criados pelo próprio tenant em status draft ainda podem executar (linha 522 de custom_agents.py: status in ('active', 'draft')), o que cria uma superfície não coberta pelo gate de revisão.
- Gap residual — agentes tenant sem listing não têm revisão: by design, agentes criados diretamente pelo tenant ficam fora do fluxo de aprovação; isso é coerente com o modelo de responsabilidade (tenant assume responsabilidade pelo próprio agente), mas significa que a trilha de aprovação cobre apenas o vetor marketplace.
- studio_audit é best-effort: falhas no AuditService.log_decision são logadas em WARNING mas não bloqueiam a operação; em condições de degradação do banco de dados, ações de alto impacto podem ocorrer sem registro.

## Sensores

- lia-agent-system/tests/contract/test_agent_studio_review_gate.py — 5 testes de contrato que validam: existência das constantes REVIEW_STATUS_PENDING='pending_review' e REVIEW_STATUS_ACTIVE='active' em custom_agent_runtime.py; bloqueio de execução para listing em pending_review; permissão de execução para listing aprovado (active); permissão de execução para agente sem listing (criado pelo tenant).
- studio_audit() em app/domains/agent_studio/_audit_helper.py — chamado em todos os eventos de ciclo de vida (create, update, delete, execute, test, publish, install, uninstall, review, clone, generate); falhas são capturadas e logadas em WARNING para monitoramento de drift.
- require_admin Depends em endpoints /admin/agent-marketplace/pending-reviews e /admin/agent-marketplace/review/{listing_id} — gate de role enforçado pelo FastAPI antes de qualquer operação de revisão.

## Arquivos Canônicos

- `lia-agent-system/app/api/v1/custom_agents.py — gate P0-2 no endpoint execute (linha 525) e endpoints admin de revisão (pending-reviews + review/{listing_id})`
- `lia-agent-system/app/domains/agent_studio/domain.py — gate P0-2 na camada de domínio (linha 631), defesa em profundidade`
- `lia-agent-system/app/domains/agent_studio/custom_agent_runtime.py — constantes REVIEW_STATUS_PENDING e REVIEW_STATUS_ACTIVE (linhas 41-42)`
- `lia-agent-system/app/domains/agent_studio/_audit_helper.py — helper canônico studio_audit(), wrapper de AuditService.log_decision para todos os eventos de ciclo de vida`
- `lia-agent-system/app/domains/agent_studio/services/agent_marketplace_service.py — review_listing(), get_pending_reviews(), install_agent() que define o status inicial pending_review`
- `lia-agent-system/tests/contract/test_agent_studio_review_gate.py — sensor de contrato (5 testes)`
