# ADR-Studio-005: Approval workflow obrigatório de admin antes de agente ir para ACTIVE

**Status:** ACCEPTED  
**Data:** 2026-06-14  
**Origem:** Auditoria ultracode Agent Studio

---

## Contexto

Agentes customizados do Agent Studio executam com ferramentas reais que produzem side-effects irreversíveis: enviar e-mails para candidatos, publicar vagas publicamente, rejeitar candidatos formalmente, enviar propostas com comprometimento jurídico. Em um ambiente enterprise com múltiplos recrutadores criando agentes, não há garantia de que um agente criado por um usuário foi revisado antes de entrar em produção.

Adicionalmente, o EU AI Act Art. 12 exige supervisão humana de sistemas de IA de alto impacto. Clientes enterprise têm requisitos de procurement que exigem trilha de auditoria de aprovação para qualquer sistema automatizado que afete decisões sobre pessoas.

Sem um gate de aprovação, qualquer usuário com permissão de criar agente poderia colocar um agente com prompt problemático (por exemplo, com viés de contratação ou instruções discriminatórias) em produção imediatamente.

## Decisão

Todo agente customizado deve passar por um workflow de aprovação explícito antes de transicionar de `draft` para `active`:

1. Criador submete via `POST /api/v1/custom-agents/{id}/request-approval`
2. Cria `AgentApprovalRequest(status="pending")` e seta `agent.status = "pending_approval"`
3. Admin da empresa (role `admin`) revisa e aprova/rejeita via `POST /api/v1/agent-approvals/{id}/review`
4. Aprovação seta `agent.status = "active"`. Rejeição retorna a `"draft"`.
5. O endpoint `execute` verifica `status in ("active", "draft")` — agentes `pending_approval` não podem executar.
6. `studio_audit(action="studio_agent_review")` registra a decisão com trilha EU AI Act Art. 12.

## Alternativas Consideradas

1. **Ativação imediata após criação (sem workflow)** — descartada: risco de agentes com viés ou prompt problemático em produção sem revisão humana.
2. **Quota-based activation (ativa automaticamente se dentro do plano)** — descartada: não atende requisito de governance enterprise nem EU AI Act.
3. **Revisão exclusiva da staff WeDOTalent** — descartada: bottleneck operacional; cliente enterprise deve ter autonomia de governance interno.
4. **Draft pode executar sem restrições** — mitigação parcial: draft executa em test/dry-run, mas o gate de execute aceita draft também (ver GAP abaixo).

## Consequências

### Positivas

- **Governance enterprise:** empresa controla explicitamente quais agentes rodam em produção.
- **Conformidade EU AI Act Art. 12:** supervisão humana documentada via `studio_audit()`.
- **Requisito de procurement:** trilha de aprovação é exigência comum em RFPs enterprise e due diligence de segurança.
- **Previne prompts problemáticos:** agentes com viés, jailbreak, ou instruções discriminatórias não chegam a produção sem revisão humana.
- **Audit trail completo:** `AgentApprovalRequest` registra quem aprovou, quando e com qual razão.

### Negativas / Trade-offs

- **Fricção para times pequenos:** aprovação obrigatória adiciona passo mesmo para casos triviais.
- **Bottleneck de admin:** se o admin estiver indisponível, agente fica bloqueado. Workaround: dry-run disponível sem aprovação.
- **GAP — draft executa em produção:** endpoint `/execute` aceita `status in ("active", "draft")`; agentes em draft conseguem executar, o que é um bypass parcial do approval gate. A aprovação só é bloqueante para `pending_approval`, não para `draft`.
- **Dois workflows independentes:** aprovação interna (admin da empresa) e aprovação do marketplace (staff WeDOTalent) são separadas — para agentes publicados no marketplace, ambas são necessárias.

## Sensores

- `tests/contract/test_agent_studio_review_gate.py` — verifica que agente com `marketplace_listing.status == "pending_review"` é bloqueado; verifica constantes `REVIEW_STATUS_PENDING` / `REVIEW_STATUS_ACTIVE`.
- `studio_audit(action="studio_agent_review")` — audit trail obrigatório em toda revisão, referência EU AI Act Art. 12.
- Gate no endpoint `execute` (`app/api/v1/custom_agents.py:508`): status check + gate P0-2.

## Arquivos Canônicos

- `app/api/v1/custom_agents.py` — endpoints `request_approval`, `review_approval`, gate no `execute`
- `app/domains/agent_studio/services/agent_marketplace_service.py` — transições de status
- `tests/contract/test_agent_studio_review_gate.py` — sensores de contrato
- `libs/models/lia_models/custom_agent.py` — `AgentApprovalRequest` model + status enum
