# Relatório de Débitos Técnicos — WeDO Talent ATS

**Data:** 08/04/2026
**Escopo:** Análise completa do backend Rails API

---

## Resumo Executivo

| Severidade | Quantidade | Descrição |
|------------|-----------|-----------|
| 🔴 Crítico | 12 | SQL injection, `switch!` com block silencioso, `default_scope`, objetos Ruby no Sidekiq |
| 🟠 Alto | 85+ | `permit!` (7x), PII em logs, `switch!` sem block (40+), `sleep()` em jobs, dados sensíveis em serializers |
| 🟡 Médio | 120+ | Português no código, `Time.now`, `ENV[]` sem `fetch`, `as_json`, N+1 em serializers |
| 🔵 Baixo | 250+ | `frozen_string_literal` ausente (~230 arquivos), ordenação de blocos, comentários proibidos |

### Cobertura de Testes

| Camada | Total | Com Specs | Sem Specs | Cobertura |
|--------|-------|-----------|-----------|-----------|
| Models | 106 | 62 | 44 | **58%** |
| Services | 180 | 88 | 92 | **49%** |
| Controllers | 155 | ~95 | ~60 | **61%** |
| Jobs | 81 | 18 | 63 | **22%** |
| Workers | 9 | 1 | 8 | **11%** |

---

## 🔴 P0 — Crítico (Corrigir Imediatamente)

### 1. SQL Injection via Interpolação de `field_name` em Collection Jobs

**Risco:** Atacante pode executar SQL arbitrário via parâmetro `filter` do `select_all_params` (que usa `permit!`).

| Arquivo | Linha | Código Vulnerável |
|---------|-------|-------------------|
| `app/jobs/collection_job/applies_job/reject_collection_job.rb` | 40 | `where("#{field_name} ILIKE ?", "%#{field_value}%")` |
| `app/jobs/collection_job/applies_job/approve_collection_job.rb` | 41 | `where("#{field_name} ILIKE ?", "%#{field_value}%")` |
| `app/jobs/collection_job/applies_job/reject_feedback_collection_job.rb` | 88 | `where("#{field_name} ILIKE ?", "%#{field_value}%")` |

**Correção:** Validar `field_name` contra allowlist de colunas conhecidas antes de interpolar no SQL.

---

### 2. `Apartment::Tenant.switch!` com Block Silenciosamente Ignorado

`switch!` (com bang) **não aceita block**. O código abaixo executa FORA do tenant:

| Arquivo | Linha |
|---------|-------|
| `app/jobs/emails/delivery_job.rb` | 20 |
| `app/jobs/emails/orchestrator_job.rb` | 11 |

**Correção:** Trocar `switch!` por `switch` (sem bang) para usar block form.

---

### 3. `default_scope` em `SelectiveProcess`

| Arquivo | Linha | Código |
|---------|-------|--------|
| `app/models/selective_process.rb` | 7 | `default_scope { where(is_deleted: false) }` |

**Impacto:** Comportamento imprevisível em queries, força `unscoped` em todo lugar. Proibido pelas convenções do projeto.

**Correção:** Remover `default_scope`, adicionar `scope :active, -> { where(is_deleted: false) }` e atualizar todas as queries.

---

### 4. `CopyJob` Passa Objetos Ruby ao Sidekiq

| Arquivo | Linha | Código |
|---------|-------|--------|
| `app/jobs/copy_job.rb` | 8 | `perform(class_to_copy, class_relationships, attributes_overwrite)` |

**Impacto:** Falha na serialização do Sidekiq ou comportamento inesperado.

**Correção:** Passar apenas IDs e reconstruir objetos dentro do `perform`.

---

### 5. Jobs sem Tenant Switching (Acesso a Dados de Tenant sem `switch`)

| Arquivo | Modelos Acessados |
|---------|-------------------|
| `app/jobs/ats_sync/apply_job.rb` | `Apply.find` |
| `app/jobs/bulk_import_job.rb` | Delegação a importer service |
| `app/jobs/candidate_import_job.rb` | `DataFile`, `Candidate` |
| `app/jobs/candidate_import_preview_job.rb` | `DataFile`, `Candidate` |
| `app/jobs/copy_job.rb` | Duplicação de records |
| `app/jobs/department_import_job.rb` | Delegação a service |
| `app/jobs/list_relationship_job.rb` | `List`, `Apply`, `ListRelationship` |
| `app/jobs/message_job.rb` | `Message` |
| `app/jobs/collection_job/job_copy_by_amount_job.rb` | `JobService` |

**Correção:** Adicionar `account_id` como parâmetro e usar `Apartment::Tenant.switch(account.tenant) { }`.

---

### 6. Associação Duplicada em `SelectiveProcess`

| Arquivo | Linhas | Código |
|---------|--------|--------|
| `app/models/selective_process.rb` | 11, 14 | `has_many :applies` declarado 2x (sem `dependent:` na primeira, com `dependent: :nullify` na segunda) |

**Correção:** Remover linha 11, manter apenas `has_many :applies, dependent: :nullify`.

---

### 7. `has_many` sem `dependent:` em Entidades Core

| Arquivo | Linha | Associação |
|---------|-------|------------|
| `app/models/account.rb` | 6 | `has_many :candidates` |
| `app/models/evaluation.rb` | 13 | `has_many :evaluation_candidates` |
| `app/models/user.rb` | 21 | `has_many :user_roles` |
| `app/models/user.rb` | 24 | `has_many :data_files` |
| `app/models/user.rb` | 26 | `has_many :dispatches` |
| `app/models/user.rb` | 27 | `has_many :user_permissions` |
| `app/models/permission.rb` | 4, 6 | `has_many :role_permissions`, `has_many :user_permissions` |
| `app/models/state.rb` | 5 | `has_many :cities` |
| `app/models/workflow_template.rb` | 8 | `has_many :selective_processes` |
| `app/models/candidate.rb` | 24 | `has_many :sourced_profile` (também está no singular!) |

---

## 🟠 P1 — Alto (Corrigir Esta Sprint)

### 8. `permit!` — Mass Assignment em 7 Controllers

Todos os `select_all_params` usam `permit!` que permite qualquer atributo. Combinado com SQL injection nos collection jobs, cria exploit encadeado.

| Arquivo | Linha |
|---------|-------|
| `app/controllers/v1/users/application_controller.rb` | 188 |
| `app/controllers/v1/users/jobs_controller.rb` | 442 |
| `app/controllers/v1/users/sourced_profiles_controller.rb` | 124 |
| `app/controllers/v1/users/applies_controller.rb` | 144 |
| `app/controllers/v1/users/evaluation_candidates_controller.rb` | 81 |
| `app/controllers/v1/users/jobs/applies/applies_controller.rb` | 163 |
| `app/controllers/v1/users/lists/list_relationships_controller.rb` | 203 |

**Correção:** Substituir `permit!` por lista explícita de parâmetros permitidos.

---

### 9. `Apartment::Tenant.switch!` sem Block Form (40+ Jobs)

Se ocorrer exceção, o tenant nunca é resetado, causando leak de dados entre tenants.

**Arquivos afetados (amostra dos mais críticos):**

| Arquivo | Linha |
|---------|-------|
| `app/jobs/collection_job/applies_job/approve_collection_job.rb` | 13 |
| `app/jobs/collection_job/applies_job/reject_collection_job.rb` | 13 |
| `app/jobs/collection_job/applies_job/update_collection_job.rb` | 15 |
| `app/jobs/collection_job/applies_job/delete_collection_job.rb` | 15 |
| `app/jobs/apify/linkedin_search_job.rb` | 22 |
| `app/jobs/candidates/embedding_sync_job.rb` | 17 |
| `app/jobs/candidates/linkedin_enrichment_job.rb` | 31 |
| `app/jobs/process_sourcing_job.rb` | 17 |
| `app/jobs/dispatch_orchestrator_job.rb` | 11 |
| `app/jobs/pearch/talent_search_job.rb` | 26 |
| `app/workers/ms_graph_email_worker.rb` | 11 |
| `app/workers/evaluation_result_worker.rb` | 25 |
| `app/workers/message_worker/process_worker.rb` | 19 |
| *(+27 outros arquivos)* | |

**Correção:** `Apartment::Tenant.switch!(tenant)` → `Apartment::Tenant.switch(tenant) { ... }`

---

### 10. `sleep()` em Jobs/Workers (18 Ocorrências)

Bloqueia threads do Sidekiq, degradando performance de todo o sistema.

| Arquivo | Linha | Duração |
|---------|-------|---------|
| `app/jobs/phone_call_interviews/invite_notification_job.rb` | 54 | `sleep(10)` |
| `app/workers/scheduling/invite_notification_worker.rb` | 54 | `sleep(10)` |
| `app/jobs/collection_job/applies_job/delete_collection_job.rb` | 50 | `sleep(2)` |
| `app/jobs/collection_job/applies_job/update_collection_job.rb` | 49 | `sleep(2)` |
| `app/jobs/collection_job/applies_job/approve_collection_job.rb` | 77 | `sleep(1)` |
| `app/jobs/collection_job/applies_job/reject_collection_job.rb` | 81 | `sleep(1)` |
| `app/jobs/collection_job/jobs_job/archive_collection_job.rb` | 48 | `sleep(1)` |
| `app/services/jobs/copy_service.rb` | 57, 271 | `sleep(1)`, `sleep(0.5)` |
| `app/services/apify/linkedin_search_service.rb` | 80 | `sleep(5)` |
| `app/services/apify/linkedin_profile_parser_service.rb` | 157 | `sleep(5)` |
| `app/services/job_service/copy_job_collection.rb` | 12, 19 | `sleep(0.2)`, `sleep(0.3)` |

**Correção:** Usar `perform_in` / `set(wait:)` para agendar jobs com delay.

---

### 11. PII Exposta em Logs

| Arquivo | Linha | Dado Exposto |
|---------|-------|-------------|
| `app/services/ats_sync/candidate_service.rb` | 84 | `record.mobile_phone` |
| `app/services/ats_sync/candidate_service.rb` | 122 | `payload[:mobile_phone]` |
| `app/services/sourced_profiles/convert_to_candidate_service.rb` | 144 | `candidate.mobile_phone` |

**Correção:** Mascarar PII nos logs: `joao****@email.com`, `(11) ****-1234`.

---

### 12. Dados Sensíveis em Serializers (Expostos em List Views)

| Arquivo | Linha | Dado |
|---------|-------|------|
| `app/serializer/candidate_serializer.rb` | 28 | `:cpf` (CPF em todas as views) |
| `app/serializer/apply_serializer.rb` | 33 | `:cpf` |
| `app/serializer/sourced_profile_serializer.rb` | 29 | `:cpf` |
| `app/serializer/candidate_serializer.rb` | 40-41 | `:current_salary`, `:desired_salary` |
| `app/serializer/apply_serializer.rb` | 45-46 | `:current_salary`, `:desired_salary` |
| `app/serializer/account_serializer.rb` | 7-8 | `setup_token` (token de configuração!) |
| `app/serializer/account_serializer.rb` | 10-11 | `tenant`, `staging_tenant` (infraestrutura interna) |
| `app/serializer/account_serializer.rb` | 16-19 | `workos_organization_id`, `workos_connection_id` |

**Correção:** Remover CPF/salary de attributes padrão; condicionar via `params` para view de detalhe. Remover `setup_token` e dados internos do `AccountSerializer`.

---

### 13. Controllers Fat com Lógica de Negócio

| Arquivo | Linhas | Problema |
|---------|--------|----------|
| `app/controllers/v1/webhooks/meta_whatsapp/meta_whatsapp_controller.rb` | 20-165 | **145 linhas** de lógica de webhook no `create` |
| `app/controllers/v1/users/email_templates_controller.rb` | 230-300 | **70 linhas** no `send_email` |
| `app/controllers/v1/users/jobs/suggestions_controller.rb` | 83-130 | **100+ linhas** de lógica de normalização |
| `app/controllers/v1/users/jobs_controller.rb` | 53-90 | **40 linhas** no `update` com sync operations |
| `app/controllers/v1/users/microsoft_auths_controller.rb` | 60-115 | **60 linhas** no `callback` |
| `app/controllers/v1/users/candidates_controller.rb` | 72-88 | Cálculos de remuneração/benefícios no controller |
| `app/controllers/v1/users/dispatches_controller.rb` | 8-31 | Queries complexas direto no controller |

**Correção:** Extrair lógica para services dedicados.

---

### 14. `constantize` com Input do Usuário (Code Injection)

| Arquivo | Linha | Código |
|---------|-------|--------|
| `app/controllers/v1/users/application_controller.rb` | 199-207 | `class_valid?` chama `constantize` em input do usuário |

**Correção:** Validar contra allowlist de classes conhecidas.

---

### 15. N+1 em Serializers

| Arquivo | Problema | Impacto |
|---------|----------|---------|
| `app/serializer/dispatch_serializer.rb` | **5 queries** por dispatch (`sent_at`, `opened_count`, `delivered_count`, `failed_count`, `recipients`) | O(5N) em list views |
| `app/serializer/department_serializer.rb` | `department_relationships.managers` + `.count` por departamento | O(2N) |
| `app/serializer/job_status_serializer.rb` | `jobs.count` por status | O(N) |
| `app/serializer/skill_category_serializer.rb` | `skills.where(is_deleted: false).count` por categoria | O(N) |

**Correção:** Counter cache, preload no controller, ou `includes` nas queries.

---

### 16. `to_unsafe_h` Bypassa Strong Params

| Arquivo | Linha |
|---------|-------|
| `app/controllers/v1/users/jobs_controller.rb` | 387 |
| `app/controllers/v1/users/candidates_controller.rb` | 352 |
| `app/controllers/v1/users/talent_searches_controller.rb` | 140, 204 |
| `app/controllers/v1/webhooks/meta_whatsapp/meta_whatsapp_controller.rb` | 30, 74 |

---

### 17. Missing Rate Limiting em Endpoints Públicos

| Arquivo | Endpoint |
|---------|----------|
| `app/controllers/v1/password_reset_tokens_controller.rb` | `POST /password_reset` — sem rate limiting |

---

## 🟡 P2 — Médio (Próximas 2-3 Sprints)

### 18. Português no Código (~100+ Ocorrências)

**Regra do projeto:** Todo código deve ser em inglês.

**Models (16+ ocorrências):**

| Arquivo | Exemplo |
|---------|---------|
| `app/models/user.rb` | `STATUSES = ["Inativo", "Ativo", "Pendente"]` |
| `app/models/company.rb` | `message: "Empresa já cadastrada"` |
| `app/models/job.rb` | `"Title ou Description deve estar presente"`, `"Erro ao sincronizar departamento"` |
| `app/models/candidate_feedback.rb` | `"deve ser 'like' ou 'dislike'"`, `"já possui feedback neste contexto"` |
| `app/models/skill_relationship.rb` | `EXPERIENCE_TIMES`, `SKILL_LEVELS` com strings em português |
| `app/models/language_relationship.rb` | `LEVELS = %w[básico intermediário avançado...]` |
| `app/models/sector_relationship.rb` | `"já possui relacionamento com esta referência"` |
| `app/models/approver.rb` | `"já é aprovador para este tipo/departamento"` |
| `app/models/occupation.rb` | `"Ocupação já existe"` |
| `app/models/behavioral_skill.rb` | `"Nome já existe para esta conta"` |

**Controllers (50+ ocorrências):**

| Arquivo | Exemplos |
|---------|----------|
| `app/controllers/v1/sessions_controller.rb` | `"Token MFA inválido"`, `"Usuário não encontrado"`, `"Código inválido ou expirado"` |
| `app/controllers/v1/users/jobs_controller.rb` | `"Gere uma busca booleana..."`, `"As vagas estão sendo arquivadas"`, `"Atualização em lote iniciada"` |
| `app/controllers/v1/users/applies_controller.rb` | `"candidate não encontrado"`, `"job não encontrado"`, `"são obrigatórios"` |
| `app/controllers/v1/evaluations/evaluation_candidates_controller.rb` | `"Avaliação já foi finalizada"`, `"Você recusou a avaliação"` |
| `app/controllers/v1/password_reset_tokens_controller.rb` | `"Email não encontrado"`, `"Senha alterada com sucesso"` |
| `app/controllers/v1/users/email_templates_controller.rb` | `"text não pode estar em branco"`, `"(cópia)"` |
| `app/controllers/v1/users/sourced_profiles_controller.rb` | `"Candidato importado"`, `"Conversão em lote iniciada"` |
| `app/controllers/v1/users/businesses_controller.rb` | `"Falha ao gerar perfil Big Five"` |
| `app/controllers/v1/setups/` (vários) | `"Convite de configuração inválido"`, `"Este convite expirou"` |

**Jobs/Workers (30+ ocorrências):**

| Arquivo | Exemplos |
|---------|----------|
| `app/jobs/candidate_import_job.rb` | `"Candidato Importado"`, `"Iniciando importação"`, `"Erro ao processar"` |
| `app/jobs/evaluations/decline_notification_job.rb` | `"movido para 'Reprovados'"`, `"Candidato recusou participar"` |
| `app/jobs/evaluations/completion_notification_job.rb` | `"concluiu a avaliação"` |
| `app/jobs/evaluations/escalation_job.rb` | `"Erro no tenant"`, `"Candidato não participou"` |
| `app/workers/evaluation_result_worker.rb` | `"Resposta recebida"`, `"Desculpe"` |
| `app/workers/job_import_worker.rb` | `"Job sem title"`, `"Job salvo"`, `"Erro ao salvar"` |
| Collection jobs (todos) | `"Processando"`, `"aprovados"`, `"rejeitados"` |

---

### 19. `Time.now` em vez de `Time.current` (13 Ocorrências)

| Arquivo | Linha(s) |
|---------|----------|
| `app/models/account.rb` | 183 |
| `app/controllers/v1/users/application_controller.rb` | 211-245 (6x) |
| `app/controllers/v1/setups/setups_controller.rb` | 40 |
| `app/mailers/evaluation_mailer.rb` | 35-81 (3x) |
| `app/services/schema_clone_service.rb` | 59, 76 |

---

### 20. `ENV[]` sem `ENV.fetch` (Secrets Expostos)

| Arquivo | Variáveis |
|---------|-----------|
| `app/services/microsoft_service/auth.rb` | `ENV['AZURE_APP_ID']`, `ENV['AZURE_APP_SECRET']` |
| `app/services/whatsapp_service/whatsapp_twilio_service.rb` | `ENV['TWILIO_ACCOUNT_SID']`, `ENV['TWILIO_AUTH_TOKEN']` |
| `app/services/workos/auth_service.rb` | `ENV["WORKOS_API_KEY"]`, `ENV["WORKOS_CLIENT_ID"]` |
| `app/services/workos/audit_service.rb` | `ENV["WORKOS_API_KEY"]` |
| `app/services/meta/whatsapp_service.rb` | `ENV["WHATSAPP_ALLOW_SEND"]` |
| `app/services/mfa_service.rb` | `ENV["REDIS_URL"]` |
| `app/services/internal_api.rb` | `ENV["APP_INTERNAL_PORT"]` |

**Correção:** `ENV.fetch("KEY", "default")` ou `Rails.application.credentials`.

---

### 21. `puts`/`p` para Debug (em vez de `Rails.logger`)

| Arquivo | Ocorrências |
|---------|-------------|
| `app/services/candidates/search/console_debug.rb` | **17 `puts`** — arquivo inteiro é debug com `puts` |
| `app/workers/evaluation_result_worker.rb` | Múltiplos `puts` |
| `app/services/rabbit_mq_publisher.rb` | `puts` para logging |
| `app/services/microsoft_service/teams_subscription_diagnostic_service.rb` | **~20 `puts`** |
| `app/services/microsoft_service/teams_subscription_reset_service.rb` | `puts` verbose |

---

### 22. `as_json` em vez de Serializer

| Arquivo | Linha |
|---------|-------|
| `app/controllers/v1/evaluations/evaluation_candidates_controller.rb` | 27-40 (5 chamadas) |
| `app/controllers/v1/users/talent_searches_controller.rb` | 128 |
| `app/controllers/v1/users/sourcings_controller.rb` | 241 |
| `app/controllers/v1/users/sourced_profile_sourcings_controller.rb` | 216 |
| `app/controllers/v1/users/jobs/matches_controller.rb` | 31 |
| `app/controllers/v1/admin/search_credits_controller.rb` | 127 |
| `app/controllers/concerns/favoritable.rb` | 17 |
| `app/controllers/concerns/pinnable.rb` | 23 |
| `api/v1/llm_usages_controller.rb` | 19 |

---

### 23. CORS Permite localhost em Produção

| Arquivo | Linha | Problema |
|---------|-------|---------|
| `config/initializers/cors.rb` | 4-7 | `localhost:3000` e `localhost:3001` permitidos em todos os ambientes |

**Correção:** Condicionar origins de localhost a `Rails.env.development?`.

---

### 24. N+1 em `search_data` dos Models

| Arquivo | Problema |
|---------|----------|
| `app/models/candidate.rb` | `search_data` chama `skill_relationships_data`, `language_relationships_data`, `educations_summary_data`, `experiences_summary_data` |
| `app/models/job.rb` | `search_data` faz joins em múltiplas tabelas individualmente |
| `app/models/list_relationship.rb` | `reference_search_data` faz `constantize` + `find_by` por record |
| `app/models/skill_category.rb` | `skills.where(is_deleted: false).count` no `search_data` |

---

### 25. Issuer/Audience Inconsistente entre JWT e MFA

| Serviço | Issuer | Audience |
|---------|--------|----------|
| `JsonWebToken` | `wedo-ats-api` | `wedo-agent` |
| `MfaService` | `ats-api` | `ats-client` |

**Nota:** MFA usa decode próprio, então funciona, mas a inconsistência pode causar confusão.

---

### 26. Jobs sem `sidekiq_options` Explícito (27 Arquivos)

Sem `queue` e `retry` definidos, usam defaults que podem não ser adequados.

**Amostra:**
- `app/jobs/candidates/embedding_sync_job.rb`
- `app/jobs/candidates/embedding_delete_job.rb`
- `app/jobs/evaluations/completion_notification_job.rb`
- `app/jobs/evaluations/decline_notification_job.rb`
- `app/jobs/save_interview_result_job.rb`
- `app/jobs/list_relationship_job.rb`
- `app/jobs/dispatch_orchestrator_job.rb`

---

### 27. Callbacks Pesados em Models

| Arquivo | Callbacks | Problema |
|---------|-----------|---------|
| `app/models/job.rb` | 6 `after_create` + 3 `after_commit` | `copy_field_requirements_from_template`, `create_job_journeys_from_template`, sync operations |
| `app/models/evaluation_candidate.rb` | 8 callbacks | Inclui operações LLM (`get_ai_feedback`) |
| `app/models/message.rb` | 4 `after_create_commit`/`after_update_commit` | Broadcasting + side effects |
| `app/models/sourced_profile.rb` | `before_save` + 2 `after_update` | Normalização + sync |

**Correção:** Extrair para services ou jobs assíncronos.

---

### 28. Specs em Português (30+ Arquivos)

| Arquivo | Problema |
|---------|---------|
| `spec/services/pearch/search_profiles_builder_has_email_spec.rb` | Contexts em português (`quando`, `não`, `está`) |
| `spec/services/pearch/search_profiles_builder_has_phone_spec.rb` | Idem |
| `spec/services/pearch/search_profiles_builder_reveal_spec.rb` | Idem |
| `spec/channels/message_channel_spec.rb` | Comentários em português |
| `spec/jobs/candidate_import_job_spec.rb` | Descrições em português |
| `spec/services/jobs/publish_service_spec.rb` | Idem |
| *(+24 outros)* | |

---

## 🔵 P3 — Baixo (Cleanup Contínuo)

### 29. `frozen_string_literal: true` Ausente (~230 Arquivos)

| Camada | Arquivos sem pragma |
|--------|-------------------|
| Models | ~55 |
| Controllers | ~30 |
| Services | ~108 |
| Jobs/Workers | ~24 |
| Serializers | ~65 |
| Specs | ~89 |

**Correção:** Script batch: `find app spec -name '*.rb' -exec grep -L 'frozen_string_literal' {} \;` + inserir pragma.

---

### 30. Comentários Proibidos no Código

| Arquivo | Linha | Comentário |
|---------|-------|-----------|
| `app/models/candidate.rb` | 41 | `# Callbacks` |
| `app/models/sourced_profile.rb` | 67 | `# Score moved to SourcedProfileSourcing` |
| `app/models/data_file.rb` | 1 | `# app/models/data_file.rb` |
| `app/models/sector.rb` | 14, 19, 28 | `# Validações`, `# Scopes`, `# Callbacks` |
| `app/models/selective_process.rb` | 85-95 | Bloco de código comentado |
| `app/models/api_client.rb` | 10-11 | Comentário descritivo |
| `app/models/candidate.rb` | 155-171 | Múltiplos comentários `#` |
| `app/controllers/v1/users/jobs_controller.rb` | 12 | `# before_action :ensure_owner` — código comentado |
| `app/controllers/v1/webhooks/meta_whatsapp/meta_whatsapp_controller.rb` | 24-32 | `# === LOG COMPLETO ===` |

---

### 31. Ordenação de Blocos Violada em Models Principais

| Arquivo | Problema |
|---------|---------|
| `app/models/account.rb` | Constants após methods; callbacks após constants; `belongs_to` separado |
| `app/models/user.rb` | Associations em 2 blocos com validations no meio; constants após associations |
| `app/models/job.rb` | Constants após callbacks (devem vir antes de associations) |
| `app/models/candidate.rb` | Constants após callbacks |
| `app/models/apply.rb` | Enum após bloco de associations |

**Ordem correta:** concerns → enums → constants → associations → validations → scopes → callbacks → class methods → instance methods → private

---

### 32. Enum com Syntax Inconsistente

| Arquivo | Problema |
|---------|---------|
| `app/models/search_archetype.rb` | `enum :seniority, { ... }` (Rails 7 syntax) vs convenção `enum seniority: { ... }` |
| `app/models/approval_request.rb` | `enum :status, STATUSES` (Rails 7 syntax) |
| `app/models/pearch_credit_transaction.rb` | Enum com values string em vez de integer |
| `app/models/evaluation_candidate.rb` | `enum session_status` com values string (`"active"`, `"timeout"`) |

---

### 33. Models sem Validações

| Arquivo | Problema |
|---------|---------|
| `app/models/role_permission.rb` | Model vazio — sem associations nem validations |
| `app/models/address.rb` | Sem validações apesar de múltiplos `belongs_to` |
| `app/models/user_role.rb` | Sem validação de unicidade `user_id` + `role_id` |
| `app/models/user_permission.rb` | Sem validação de unicidade `user_id` + `permission_id` |

---

### 34. `rescue => e` Engolindo Erros

| Arquivo | Linha | Problema |
|---------|-------|---------|
| `app/models/job.rb` | 347 | `rescue => e` em `copy_field_requirements_from_template` — engole silenciosamente |
| `app/models/list_relationship.rb` | 46 | `rescue StandardError => e` retorna `{}` silenciosamente |
| `app/models/whatsapp_tenant_mapping.rb` | 27 | `rescue => e` retorna nil |

---

### 35. Singular `has_many :sourced_profile` em Candidate

| Arquivo | Linha | Código |
|---------|-------|--------|
| `app/models/candidate.rb` | 24 | `has_many :sourced_profile` → deveria ser `has_many :sourced_profiles` |

---

## 📊 Gaps de Cobertura de Testes (Mais Críticos)

### Models sem Specs (Entidades Core)

| Model | Criticidade |
|-------|------------|
| `sourced_profile` | 🔴 Core sourcing |
| `sourcing` | 🔴 Core sourcing |
| `selective_process` | 🔴 Core pipeline |
| `meeting` | 🟠 Scheduling |
| `calendar_event` | 🟠 Scheduling |
| `department` | 🟠 Org structure |
| `team` / `team_member` | 🟠 Org structure |
| `message` | 🟠 Messaging |
| `approval_request` / `approver` | 🟡 Workflow |

### Services sem Specs (Críticos)

| Service | Criticidade |
|---------|------------|
| `gemini_client.rb` | 🔴 LLM principal — ZERO testes |
| `public/create_candidate_and_apply_service.rb` | 🔴 Fluxo público de aplicação |
| `candidate_importer_service.rb` | 🔴 Importação de candidatos |
| `microsoft_service/` (7 arquivos) | 🟠 Integração Microsoft |
| `meta/whatsapp_service.rb` | 🟠 Integração WhatsApp |
| `workos/auth_service.rb` | 🟠 SSO |
| `matching/candidate_for_job.rb` | 🟠 Match AI |
| `evaluations/unified_invite_service.rb` | 🟠 Convites de avaliação |

### Jobs sem Specs (63/81 = 78% sem testes)

**Mais críticos:**
- `create_tenant_job` — Provisionamento de tenant
- `dispatch_orchestrator_job` — Orquestação de email
- `emails/orchestrator_job`, `emails/delivery_job`
- Todos 7 `collection_job/applies_job/*`
- Todos 4 `evaluations/*` notification jobs
- `candidates/embedding_sync_job`, `candidates/resume_parser_job`

### Factories Ausentes (20 Models)

`api_client`, `approval_request`, `approver`, `audit_log`, `behavioral_skill`, `behavioral_skill_relationship`, `calendar_event_attendee`, `department_relationship`, `issue`, `job_analytics_snapshot`, `job_field_template`, `meeting_relationship`, `pearch_credit_transaction`, `pearch_search_log`, `request_key`, `sourced_profile_activity`, `sourcing_filter`, `teams_chat_subscription`, `whatsapp_configuration`, `whatsapp_tenant_mapping`

---

## 📋 Roadmap de Correção Sugerido

### Sprint 1 — Segurança (P0)
- [ ] Fix SQL injection nos collection jobs (validar `field_name` contra allowlist)
- [ ] Fix `switch!` → `switch` em `Emails::DeliveryJob` e `OrchestratorJob`
- [ ] Remover `default_scope` de `SelectiveProcess`
- [ ] Fix `CopyJob` para passar IDs em vez de objetos
- [ ] Adicionar tenant switching nos 9 jobs sem ele
- [ ] Substituir `permit!` por permit lists explícitas (7 controllers)
- [ ] Fix `constantize` com input do usuário

### Sprint 2 — Segurança + Estabilidade (P1)
- [ ] Converter 40+ jobs de `switch!` para `switch` block form
- [ ] Remover `sleep()` de todos os jobs (usar `perform_in`)
- [ ] Mascarar PII nos logs
- [ ] Remover CPF/salary/setup_token de serializers padrão
- [ ] Adicionar rate limiting no password reset
- [ ] Extrair lógica de controllers fat para services
- [ ] Fix N+1 no `DispatchSerializer`

### Sprint 3 — Qualidade (P2)
- [ ] Traduzir strings em português para inglês (~100+ ocorrências)
- [ ] Substituir `Time.now` por `Time.current` (13 ocorrências)
- [ ] Substituir `ENV[]` por `ENV.fetch` (20+ ocorrências)
- [ ] Substituir `puts` por `Rails.logger` (5 arquivos)
- [ ] Substituir `as_json` por serializers (9 controllers)
- [ ] Fix CORS localhost em produção
- [ ] Adicionar `sidekiq_options` nos 27 jobs sem ele

### Sprint 4 — Standards + Testes (P3)
- [ ] Adicionar `frozen_string_literal: true` (~230 arquivos — script batch)
- [ ] Remover comentários proibidos
- [ ] Corrigir ordenação de blocos nos models principais
- [ ] Fix `has_many :sourced_profile` → `:sourced_profiles`
- [ ] Fix associação duplicada em `SelectiveProcess`
- [ ] Adicionar `dependent:` nas ~10 associações faltantes
- [ ] Specs para models core sem testes (9 models)
- [ ] Specs para services críticos sem testes (8 services)
- [ ] Specs para jobs críticos sem testes (15+ jobs)
- [ ] Criar 20 factories ausentes
