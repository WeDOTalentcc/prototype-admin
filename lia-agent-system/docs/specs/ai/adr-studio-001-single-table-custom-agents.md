# ADR-Studio-001: Design de tabela única para custom_agents (agentes first-party + agentes de tenant)

**Status:** ACCEPTED  
**Data:** 2026-06-14  
**Origem:** Auditoria ultracode Agent Studio

---

## Contexto

O Agent Studio da WeDOTalent precisa expor dois tipos de agentes na mesma interface:

1. **Agentes first-party (WeDO global):** criados e mantidos pela WeDOTalent, disponíveis para todos os tenants sem vínculo com nenhuma empresa específica. Exemplos incluem agentes de sourcing padrão, agentes de triagem e agentes de analytics provisionados pela WeDOTalent.

2. **Agentes custom (por tenant):** criados pelo recrutador dentro de uma empresa específica, restritos ao escopo daquele tenant. Têm  obrigatório e não devem cruzar fronteiras de multi-tenancy.

Antes da Fase A do Agent Studio (2026-06-09), a tabela  exigia  — portanto, todos os agentes eram estritamente por-tenant. Quando surgiu a necessidade de agentes globais WeDO, o schema precisou evoluir. A migração 254 () tornou  nullable e adicionou a coluna discriminadora  (enum , default ) para distinguir os dois tipos na mesma tabela.

Esse mesmo arquivo também adiciona a coluna  (JSONB) para escopo de domínios cobertos pelo agente (preenchido na Fase B). A migração anterior 224 () havia adicionado FK  para agentes de tenant — necessitando que a política de FK fosse compatível com  para agentes first-party (o FK ainda aceita NULL em PostgreSQL por definição da norma SQL).

A migração 223 () removeu o índice duplicado  (gerado automaticamente por  na coluna), mantendo apenas o índice explícito  definido em  — tornando este o único índice no campo .

## Decisão

Usar **uma única tabela**  para todos os agentes do Agent Studio, diferenciando o tipo via coluna discriminadora  (enum PostgreSQL  com valores  e ).

A invariante central é: ** implica ** e ** implica  (enforçado em application-level)**.

O modelo SQLAlchemy () declara  com documentação inline explicando a dualidade:



O repositório canônico () bifurca explicitamente o comportamento:
- Métodos ,  chamam  (fail-closed) e filtram por .
- Métodos  e  são marcados  e **não** chamam , filtrando apenas por .
- O método  implementa a política de precedência: agentes de tenant ganham sobre agentes first-party; first-party são retornados apenas como fallback quando .

O repositório  também implementa um bypass explícito: ao atribuir um agente a um pool, o guard de cross-tenant é pulado quando , permitindo que qualquer tenant adicione agentes globais ao seu pool.

## Alternativas Consideradas

1. Tabelas separadas (custom_agents + first_party_agents): manteria isolamento completo de multi-tenancy e eliminaria o NULL em company_id, mas duplicaria toda a lógica de runtime, canais (voice/voip/whatsapp/triagem_invite), marketplace e métricas. A API de listagem unificada exigiria UNION ou JOIN artificial. Rejeitado por custo de manutenção e por violar o princípio DRY do codebase.
2. Herança de classe (Class Table Inheritance / SQLAlchemy concrete ou joined): tabela base com campos comuns e subtabelas para cada tipo. Aumenta complexidade de queries (JOINs obrigatórios mesmo para campos que existem em ambos os tipos), e o SQLAlchemy com PostgreSQL JSONB/ARRAY torna isso verboso sem ganho real. Rejeitado por overhead de query sem benefício de integridade adicional.
3. Discriminador via coluna JSONB config (flag dentro do campo config existente): evitaria nova coluna, mas tornaria a discriminação invisível para queries SQL, impossibilitando índices eficientes (ex: idx_custom_agents_agent_type criado na migration 254) e forçando leitura de JSONB em toda query de filtragem. Rejeitado por não ser indexável e dificultar auditoria.
4. Campo booleano is_first_party em vez de enum agent_type: mais simples inicialmente, mas não extensível caso um terceiro tipo seja necessário no futuro (ex: marketplace_agent instalado). O enum permite evolução sem ALTER TABLE disruptivo. Rejeitado em favor do enum que já sinaliza extensibilidade.

## Consequências

### Positivas
- API de listagem unificada: um único endpoint retorna tanto agentes first-party quanto agentes de tenant sem UNION. O método list_active_for_context do repositório encapsula a política de precedência (tenant ganha sobre global) em um único ponto.
- Zero duplicação de schema: canais (voice_enabled, voip_enabled, whatsapp_enabled, triagem_invite_enabled), métricas (runtime_metrics, total_executions, avg_confidence), configuração (allowed_tools, max_steps, temperature, model_override) e marketplace (is_marketplace_published) existem uma única vez.
- FK ON DELETE CASCADE preservada para agentes de tenant: quando um tenant é desligado (LGPD erasure), a cascata remove automaticamente seus agentes custom. Agentes first-party com company_id=NULL não são afetados pela cascata por definição SQL.
- Índice eficiente em agent_type: migration 254 cria idx_custom_agents_agent_type, permitindo queries globais de first-party sem full-scan da tabela.
- Evolução retrocompatível: server_default=custom garante que todos os agentes existentes (pré-Fase A) continuam funcionando como custom sem migration de dados.

### Negativas / Trade-offs
- NULL em company_id requer atenção em CADA novo método de repositório: todo método público que opera sobre agentes de tenant DEVE chamar _require_company_id() antes de qualquer query. A ausência desse guard em um método novo é uma violação silenciosa de multi-tenancy que não será capturada em nível de banco.
- O guard _require_company_id() no CustomAgentRepository rejeita None e string vazia — portanto métodos de first-party NÃO podem reutilizar a mesma assinatura de método. A bifurcação de código (métodos separados para tenant vs global) é necessária e permanente.
- O campo company_id nullable quebra a invariante simples do ADR-001 (todo método público de repositório chama _require_company_id). Os métodos TENANT-FREE são exceções documentadas que precisam de revisão explícita em code review.
- ai_consumption.studio_agent_id é uma referência polimórfica (varchar, sem FK) que referencia custom_agents.id para agent_type=custom_agent mas também sourcing_agent_id e digital_twins.id — a tabela única não resolve essa polimorfismo downstream, documentado explicitamente na migration 224 como decisão permanente.
- Testes de multi-tenancy precisam cobrir explicitamente o caso first_party (company_id=None) para garantir que novos métodos não apliquem o guard incorretamente sobre agentes globais.

## Sensores

- tests/unit/test_agent_studio_first_party_model.py: suite TDD de Fase A com 4 classes de teste. Verifica que (1) company_id=None + agent_type=first_party é construível sem violação de constraint Python-level; (2) agente first-party persiste em SQLite in-memory com company_id=NULL; (3) agente first-party aparece em listagem global sem filtro por company_id; (4) agent_type default permanece custom para agentes novos sem agent_type explícito — garantindo retrocompatibilidade.
- tests/contract/test_custom_agent_repository.py: verifica (classe TestTenantIsolation) que get_by_id levanta ValueError quando company_id é None ou string vazia, e que update_channel_flag também rejeita company_id inválido. Garante que o fail-closed guard _require_company_id() permanece ativo em todos os métodos de tenant.
- app/domains/agent_studio/repositories/pool_agent_assignment_repository.py: guard inline no método de atribuição de pool — se agent.agent_type != AgentType.first_party e agent.company_id != company_id levanta CrossTenantError. Garante que agentes custom não cruzam fronteiras de tenant mesmo quando o chamador tenta atribuí-los a um pool de outra empresa.
- alembic/versions/254_add_agent_type_and_domains_to_custom_agents.py: a própria migration é um sensor estrutural — qualquer tentativa de tornar company_id NOT NULL novamente ou remover o enum agenttypeenum quebraria o downgrade desta migration.
- Comentário canônico # TENANT-FREE nas docstrings de list_first_party_agents e update_first_party_manifest: serve como marcador de revisão explícita. Todo code review em CustomAgentRepository deve verificar que métodos sem _require_company_id estão marcados TENANT-FREE e filtram por agent_type == AgentType.first_party.

## Arquivos Canônicos

- 
- 
- 
- 
- 
- 
- 
- 
