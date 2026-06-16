# Technical Debt Report - ATS API
**Data de Análise:** 2026-02-09  
**Linguagem:** Ruby on Rails 7.1.0  
**Total de Arquivos Ruby:** 1061  
**Total de Migrations:** 253  
**Total de Controllers:** 114  
**Total de Services:** 66  
**Total de Specs:** 149

---

## 📊 Visão Geral

Este relatório identifica débitos técnicos críticos e de alta prioridade que impactam manutenibilidade, performance e qualidade do código.

**Legenda de Prioridade:**
- 🔴 **Crítica**: Impacto severo em performance/segurança
- 🟡 **Alta**: Impacta manutenibilidade significativamente
- 🟢 **Média**: Melhoria de qualidade incremental

---

## 🔴 DÉBITOS CRÍTICOS

### DEBT-001: God Objects (Classes Gigantes)
**Título:** [REFACTOR] Quebrar Classes Gigantes (God Objects)  
**Tipo:** Refactoring  
**Área:** Backend - Models & Services  
**Prioridade:** 🔴 Crítica  
**Pontos:** 13  
**Epic:** EPIC-CODE-QUALITY

**Descrição:**
Classes com mais de 500 linhas violam Single Responsibility Principle e tornam manutenção impossível.

**Arquivos Identificados:**
```
983 linhas - app/models/job.rb
867 linhas - app/services/candidates/search/hybrid_search_service.rb
825 linhas - app/services/candidates/suggestion_service.rb
674 linhas - app/jobs/candidates/local_search_job.rb
655 linhas - app/services/sourced_profiles/profile_analyzer.rb
553 linhas - app/services/evaluations/ai_feedback_service.rb
528 linhas - app/models/sourced_profile.rb
517 linhas - app/services/candidates/linkedin_data_processor.rb
507 linhas - app/controllers/v1/users/sourcings_controller.rb
```

**Impacto Atual:**
- Impossível testar isoladamente
- Alta complexidade ciclomática
- Dificulta onboarding de novos devs
- Aumenta tempo de code review

**Plano de Ação:**
1. **Job Model (983 linhas)**
   - Extrair concerns: `Embeddable`, `StatusManageable`, `RemunerationManagement`
   - Extrair service: `Job::OrganizationalStructureService`
   - Extrair decorator: `JobPresenter` para lógica de apresentação

2. **HybridSearchService (867 linhas)**
   - Já está modularizado em estratégias
   - Extrair: `SearchOrchestrator`, `ResultMerger`, `ScoreCalculator`

3. **SuggestionService (825 linhas)**
   - Extrair: `PromptBuilder`, `ResponseParser`, `FilterExtractor`
   - Separar por tipo de suggestion (title, filters, chips)

4. **LocalSearchJob (674 linhas)**
   - Extrair: `SearchCoordinator`, `ProgressTracker`, `ErrorHandler`

**Regras de Negócio:**
1. Nenhuma classe deve ter mais de 300 linhas
2. Nenhum método deve ter mais de 20 linhas
3. Complexidade ciclomática máxima: 10

**Critérios de Aceitação:**
- [ ] Job.rb reduzido para < 300 linhas
- [ ] HybridSearchService < 300 linhas
- [ ] SuggestionService < 300 linhas
- [ ] Todos os testes passando
- [ ] Cobertura mantida/melhorada

**DoD:**
- [ ] Refactoring completo
- [ ] Testes unitários para classes extraídas
- [ ] Rubocop sem warnings de complexidade
- [ ] Documentação atualizada

---

### DEBT-002: ENV Variables Sem Fallback
**Título:** [SECURITY] Adicionar ENV.fetch com Fallback  
**Tipo:** Security Fix  
**Área:** Backend - Configuration  
**Prioridade:** 🔴 Crítica  
**Pontos:** 5  
**Epic:** EPIC-SECURITY

**Descrição:**
20+ locais usando `ENV['KEY']` ao invés de `ENV.fetch('KEY', default)`, causando crashes silenciosos em produção.

**Arquivos Impactados:**
```ruby
app/controllers/v1/users/microsoft_auths_controller.rb:13
app/controllers/v1/workos_controller.rb:311
app/controllers/v1/webhooks/meta_whatsapp/meta_whatsapp_controller.rb:10
app/workers/message_worker/process_worker.rb:199
app/serializer/business_serializer.rb:40
app/models/account.rb:101
```

**Impacto Atual:**
- Crashes silenciosos em produção quando ENV não definida
- Dificulta debugging
- Viola princípio fail-fast
- Não documentado quais ENVs são obrigatórias

**Plano de Ação:**
1. Criar `config/environment_variables.yml` documentando todas as ENVs
2. Substituir todos `ENV['KEY']` por `ENV.fetch('KEY', default)`
3. Criar initializer `config/initializers/environment_validator.rb`
4. Adicionar verificação em deploy

**Exemplo de Correção:**
```ruby
# ❌ ANTES
client_id = ENV['AZURE_APP_ID']

# ✅ DEPOIS
client_id = ENV.fetch('AZURE_APP_ID') { raise "AZURE_APP_ID não configurada" }

# OU com fallback seguro
api_url = ENV.fetch('API_URL', 'http://localhost:8080')
```

**Critérios de Aceitação:**
- [ ] 0 ocorrências de `ENV['KEY']` sem fetch
- [ ] Documentação de todas ENVs obrigatórias
- [ ] Environment validator criado
- [ ] README atualizado com lista completa

**DoD:**
- [ ] Todas as substituições feitas
- [ ] Testes de ambiente criados
- [ ] CI validando ENVs obrigatórias
- [ ] Deploy docs atualizados

---

### DEBT-003: Generic Rescue Blocks (175 ocorrências)
**Título:** [REFACTOR] Substituir Generic Rescue por Specific Exceptions  
**Tipo:** Error Handling  
**Área:** Backend - Global  
**Prioridade:** 🔴 Crítica  
**Pontos:** 8  
**Epic:** EPIC-ERROR-HANDLING

**Descrição:**
175 ocorrências de `rescue => e` capturam TODAS exceções (incluindo SystemExit, SignalException), mascarando bugs e dificultando debugging.

**Exemplo Problemático:**
```ruby
# ❌ RUIM - Captura TUDO
def process_data
  # código
rescue => e
  log_error(e)
  nil
end

# ✅ BOM - Específico
def process_data
  # código
rescue ActiveRecord::RecordNotFound => e
  Rails.logger.error "[Service] Record not found: #{e.message}"
  Result.error("Record not found")
rescue StandardError => e
  Rails.logger.error "[Service] Unexpected: #{e.message}"
  Sentry.capture_exception(e)
  raise
end
```

**Impacto Atual:**
- Bugs mascarados em produção
- Logs não informativos
- Dificulta troubleshooting
- Pode capturar signals do sistema

**Plano de Ação:**
1. Auditar todos os 175 casos
2. Categorizar por tipo de erro esperado
3. Substituir por rescue específico
4. Adicionar logging estruturado
5. Integrar com Sentry/error tracking

**Categorias de Erro Comuns:**
- Database: `ActiveRecord::RecordNotFound`, `ActiveRecord::RecordInvalid`
- Network: `Net::OpenTimeout`, `Faraday::Error`
- LLM: `Gemini::RateLimitError`, `Timeout::Error`
- Business: Custom errors (`InvalidSearchQuery`, etc)

**Critérios de Aceitação:**
- [ ] 0 ocorrências de `rescue => e` sem rescue StandardError
- [ ] Todos os rescues com logging adequado
- [ ] Custom exceptions criadas para business logic
- [ ] Error tracking configurado

**DoD:**
- [ ] Refactoring completo
- [ ] Error tracking integrado
- [ ] Runbook de errors criado
- [ ] Testes de error handling

---

## 🟡 DÉBITOS DE ALTA PRIORIDADE

### DEBT-004: Missing frozen_string_literal
**Título:** [PERFORMANCE] Adicionar frozen_string_literal: true  
**Tipo:** Performance  
**Área:** Backend - Global  
**Prioridade:** 🟡 Alta  
**Pontos:** 3  
**Epic:** EPIC-PERFORMANCE

**Descrição:**
Vários arquivos sem `# frozen_string_literal: true`, causando alocações desnecessárias de strings mutáveis.

**Impacto:**
- ~5-10% overhead de memória
- Garbage collector trabalhando mais
- Strings duplicadas na memória

**Plano de Ação:**
```bash
# Adicionar automaticamente
find app -name "*.rb" -exec sed -i '1s/^/# frozen_string_literal: true\n\n/' {} \;
```

**Critérios de Aceitação:**
- [ ] 100% dos arquivos .rb com frozen_string_literal
- [ ] CI bloqueando PRs sem frozen_string_literal
- [ ] Rubocop rule ativada

**DoD:**
- [ ] Todos os arquivos corrigidos
- [ ] Testes passando
- [ ] CI configurado

---

### DEBT-005: N+1 Queries em Controllers
**Título:** [PERFORMANCE] Eliminar N+1 Queries  
**Tipo:** Performance  
**Área:** Backend - Controllers  
**Prioridade:** 🟡 Alta  
**Pontos:** 8  
**Epic:** EPIC-PERFORMANCE

**Descrição:**
Controllers carregando associações sem `includes`/`preload`, gerando centenas de queries desnecessárias.

**Exemplos Identificados:**
```ruby
# app/controllers/v1/users/jobs_controller.rb
# ❌ N+1 ao iterar sobre jobs.each { |j| j.company.name }
@jobs = Job.where(account_id: account_id)

# ✅ Solução
@jobs = Job.where(account_id: account_id)
           .includes(:company, :job_status, :department)
           .preload(skill_relationships: :skill)
```

**Ferramentas para Detectar:**
1. Instalar `bullet` gem
2. Configurar em development
3. Revisar logs do bullet
4. Adicionar N+1 detection no CI

**Plano de Ação:**
1. Instalar e configurar `bullet` gem
2. Identificar todos os N+1s (rodar test suite)
3. Adicionar includes nos controllers
4. Criar custom scopes nos models
5. Adicionar indexes faltantes

**Exemplo de Scope:**
```ruby
class Job < ApplicationRecord
  scope :with_associations, -> { 
    includes(:company, :job_status, :department, :skills, :benefits)
  }
  
  scope :for_search, -> {
    includes(:company, :department)
    .preload(skill_relationships: :skill)
  }
end
```

**Critérios de Aceitação:**
- [ ] Bullet configurado e rodando
- [ ] 0 N+1 warnings em test suite
- [ ] Scopes criados para queries comuns
- [ ] Documentação de performance

**DoD:**
- [ ] Todos os N+1s eliminados
- [ ] Bullet no CI
- [ ] Query logs revisados
- [ ] Benchmarks de before/after

---

### DEBT-006: Missing Database Indexes
**Título:** [PERFORMANCE] Adicionar Índices Faltantes  
**Tipo:** Performance  
**Área:** Database  
**Prioridade:** 🟡 Alta  
**Pontos:** 5  
**Epic:** EPIC-PERFORMANCE

**Descrição:**
Foreign keys e colunas frequentemente filtradas sem índices, causando full table scans.

**Análise Necessária:**
```sql
-- Encontrar foreign keys sem índice
SELECT
  c.table_name,
  c.column_name,
  c.constraint_name
FROM information_schema.key_column_usage c
LEFT JOIN pg_indexes i 
  ON c.table_name = i.tablename 
  AND c.column_name = i.indexdef
WHERE c.table_schema = 'public'
  AND i.indexname IS NULL
  AND c.constraint_name LIKE '%fkey%';
```

**Índices a Criar (baseado em queries comuns):**
```ruby
# Candidates
add_index :candidates, [:account_id, :is_deleted], name: 'idx_candidates_active'
add_index :candidates, [:account_id, :created_at], name: 'idx_candidates_recent'
add_index :candidates, :email, where: "email IS NOT NULL"

# Jobs
add_index :jobs, [:account_id, :is_deleted, :job_status_id]
add_index :jobs, [:company_id, :created_at]

# Applies
add_index :applies, [:candidate_id, :job_id, :apply_status_id]
add_index :applies, [:job_id, :created_at]

# Composite para queries específicas
add_index :skill_relationships, [:reference_type, :reference_id, :skill_id]
```

**Critérios de Aceitação:**
- [ ] Análise de queries lentas completa
- [ ] Todos os FKs com índice
- [ ] Colunas de filtro indexadas
- [ ] Composite indexes para queries complexas

**DoD:**
- [ ] Migrations criadas e rodadas
- [ ] Query plan analisado (EXPLAIN)
- [ ] Benchmarks de before/after
- [ ] Documentação de índices

---

### DEBT-007: Test Coverage Baixo
**Título:** [QUALITY] Aumentar Cobertura de Testes  
**Tipo:** Testing  
**Área:** Backend - Tests  
**Prioridade:** 🟡 Alta  
**Pontos:** 13  
**Epic:** EPIC-QUALITY

**Descrição:**
149 specs para 66 services + 114 controllers é cobertura insuficiente. Services críticos sem testes.

**Análise:**
```
Total Services: 66
Total Service Specs: ~30-40 (estimado)
Cobertura: ~50-60%

Críticos sem testes:
- HybridSearchService (867 linhas)
- ProfileAnalyzer (655 linhas)
- AiFeedbackService (553 linhas)
```

**Prioridades de Testes:**
1. **Tier 1 - Crítico de Negócio:**
   - Search services (hybrid, elasticsearch, embedding)
   - AI services (feedback, suggestions)
   - Payment/credits services
   - Authentication/authorization

2. **Tier 2 - Importante:**
   - CRUD services
   - Background jobs
   - Serializers

3. **Tier 3 - Nice to have:**
   - Helpers
   - Decorators
   - Presenters

**Plano de Ação:**
1. Configurar SimpleCov com threshold mínimo
2. Adicionar badges de coverage no README
3. Bloquear PRs com cobertura < 80%
4. Criar testes para services Tier 1
5. Refatorar god objects antes de testar

**Template de Teste:**
```ruby
RSpec.describe Candidates::Search::HybridSearchService do
  subject(:service) { described_class.new(account_id: account.id) }
  
  let(:account) { create(:account) }
  
  describe '#search' do
    context 'quando query é simples' do
      it 'usa simple strategy' do
        # test
      end
    end
    
    context 'quando query é complexa' do
      it 'usa hybrid strategy' do
        # test
      end
    end
  end
end
```

**Critérios de Aceitação:**
- [ ] Cobertura global > 80%
- [ ] Services críticos > 90%
- [ ] Controllers > 85%
- [ ] Models > 90%
- [ ] SimpleCov configurado

**DoD:**
- [ ] Coverage threshold no CI
- [ ] Testes Tier 1 completos
- [ ] Badge no README
- [ ] Documentação de testes

---

### DEBT-008: Inconsistent Logging
**Título:** [OBSERVABILITY] Padronizar Logging Estruturado  
**Tipo:** Observability  
**Área:** Backend - Global  
**Prioridade:** 🟡 Alta  
**Pontos:** 5  
**Epic:** EPIC-OBSERVABILITY

**Descrição:**
Logging inconsistente dificulta debugging e observabilidade. Mix de `puts`, `Rails.logger`, e logs não estruturados.

**Problemas Atuais:**
1. Mix de `puts` e `Rails.logger`
2. Logs sem contexto (account_id, user_id, request_id)
3. Níveis inconsistentes (info vs debug)
4. Sem structured logging (JSON)

**Plano de Ação:**
1. **Criar LoggerService:**
```ruby
class ApplicationLogger
  def self.log(level:, message:, context: {})
    Rails.logger.public_send(level, {
      message: message,
      timestamp: Time.current.iso8601,
      account_id: Current.account_id,
      user_id: Current.user_id,
      request_id: Current.request_id,
      **context
    }.to_json)
  end
  
  def self.info(message, **context)
    log(level: :info, message: message, context: context)
  end
  
  def self.error(message, error: nil, **context)
    log(level: :error, message: message, context: context.merge(
      error: error&.message,
      backtrace: error&.backtrace&.first(5)
    ))
  end
end
```

2. **Substituir logs existentes:**
```ruby
# ❌ ANTES
Rails.logger.info "Processing candidate #{candidate.id}"
puts "Error: #{e.message}"

# ✅ DEPOIS
ApplicationLogger.info("Processing candidate", candidate_id: candidate.id)
ApplicationLogger.error("Processing failed", error: e, candidate_id: candidate.id)
```

3. **Configurar JSON logging:**
```ruby
# config/environments/production.rb
config.log_formatter = proc do |severity, datetime, progname, msg|
  { severity: severity, datetime: datetime, message: msg }.to_json + "\n"
end
```

**Critérios de Aceitação:**
- [ ] ApplicationLogger criado
- [ ] 0 `puts` em app/
- [ ] Todos os logs com contexto
- [ ] JSON logging em produção
- [ ] Log levels corretos

**DoD:**
- [ ] Logger service implementado
- [ ] Todos os logs migrados
- [ ] Log aggregation configurado
- [ ] Runbook de logs

---

## 🟢 DÉBITOS DE MÉDIA PRIORIDADE

### DEBT-009: Documentation Gaps
**Título:** [DOCS] Documentar Arquitetura e Fluxos  
**Tipo:** Documentation  
**Área:** Documentation  
**Prioridade:** 🟢 Média  
**Pontos:** 5  
**Epic:** EPIC-DOCUMENTATION

**Descrição:**
README.md genérico, sem documentação de arquitetura, fluxos de negócio, ou setup.

**O que criar:**
1. **README.md completo:**
   - Setup local
   - Variáveis de ambiente
   - Como rodar testes
   - Arquitetura overview

2. **ARCHITECTURE.md:**
   - Diagrama de componentes
   - Fluxo de dados
   - Padrões de design
   - Tech stack

3. **CONTRIBUTING.md:**
   - Code style guide
   - PR guidelines
   - Testing requirements

4. **API_DOCS.md:**
   - Endpoints principais
   - Autenticação
   - Rate limiting

**Critérios de Aceitação:**
- [ ] README completo e atualizado
- [ ] Diagramas de arquitetura
- [ ] Setup docs testados por novo dev
- [ ] API docs gerados automaticamente

**DoD:**
- [ ] Docs criados
- [ ] Diagramas incluídos
- [ ] Revisados por time
- [ ] Mantidos atualizados no CI

---

### DEBT-010: Sidekiq Job Monitoring
**Título:** [MONITORING] Adicionar Monitoring de Background Jobs  
**Tipo:** Monitoring  
**Área:** Backend - Jobs  
**Prioridade:** 🟢 Média  
**Pontos:** 3  
**Epic:** EPIC-OBSERVABILITY

**Descrição:**
43 jobs sem retry strategy clara, dead letter queue, ou alerting.

**Plano de Ação:**
1. Configurar retry strategies por job
2. Implementar dead letter queue
3. Adicionar alerting (Slack/PagerDuty)
4. Dashboard de jobs

**Exemplo:**
```ruby
class CriticalJob
  include Sidekiq::Job
  
  sidekiq_options queue: :critical,
                  retry: 5,
                  dead: true,
                  backtrace: 10
  
  sidekiq_retry_in do |count|
    10 * (count + 1) # Exponential backoff
  end
  
  sidekiq_retries_exhausted do |msg, exception|
    Sidekiq.logger.error("Job failed permanently", class: msg['class'], error: exception.message)
    AlertService.critical("Job #{msg['class']} failed after retries")
  end
end
```

**Critérios de Aceitação:**
- [ ] Retry strategies definidas
- [ ] Dead letter queue configurada
- [ ] Alerting integrado
- [ ] Dashboard de jobs

**DoD:**
- [ ] Configurações implementadas
- [ ] Alerting testado
- [ ] Runbook de jobs criado
- [ ] Dashboard configurado

---

### DEBT-011: Apartment Multi-Tenancy Complexity
**Título:** [REFACTOR] Simplificar Multi-Tenancy  
**Tipo:** Refactoring  
**Área:** Backend - Infrastructure  
**Prioridade:** 🟢 Média  
**Pontos:** 8  
**Epic:** EPIC-INFRASTRUCTURE

**Descrição:**
Apartment gem com 253 migrations duplicadas por tenant. Schema migration complexa e propensa a erros.

**Problemas:**
1. Migrations demoram horas em produção
2. Rollback complexo
3. Dificulta seeding de novos tenants
4. Inconsistências entre schemas

**Alternativas a Avaliar:**
1. **Row-level multi-tenancy:**
   - Tudo em um schema
   - account_id em todas as tabelas
   - RLS (Row Level Security) do Postgres
   
2. **Actasasportaltenant:**
   - Alternativa mais moderna ao Apartment

3. **Citus (sharding):**
   - Para grande escala

**Plano de Ação (se mantiver Apartment):**
1. Consolidar migrations antigas
2. Automatizar schema validation
3. Melhorar scripts de migração
4. Documentar processo

**Critérios de Aceitação:**
- [ ] Migrations < 30min em produção
- [ ] Schema validation automatizada
- [ ] Rollback testado e documentado
- [ ] Zero-downtime migrations

**DoD:**
- [ ] Solução implementada
- [ ] Testes de migração
- [ ] Documentação completa
- [ ] Runbook de tenants

---

## 📋 Resumo de Priorização

| ID | Título | Prioridade | Pontos | Epic |
|----|--------|------------|--------|------|
| DEBT-001 | God Objects | 🔴 Crítica | 13 | CODE-QUALITY |
| DEBT-002 | ENV Variables | 🔴 Crítica | 5 | SECURITY |
| DEBT-003 | Generic Rescue | 🔴 Crítica | 8 | ERROR-HANDLING |
| DEBT-004 | frozen_string_literal | 🟡 Alta | 3 | PERFORMANCE |
| DEBT-005 | N+1 Queries | 🟡 Alta | 8 | PERFORMANCE |
| DEBT-006 | Missing Indexes | 🟡 Alta | 5 | PERFORMANCE |
| DEBT-007 | Test Coverage | 🟡 Alta | 13 | QUALITY |
| DEBT-008 | Inconsistent Logging | 🟡 Alta | 5 | OBSERVABILITY |
| DEBT-009 | Documentation | 🟢 Média | 5 | DOCUMENTATION |
| DEBT-010 | Job Monitoring | 🟢 Média | 3 | OBSERVABILITY |
| DEBT-011 | Multi-Tenancy | 🟢 Média | 8 | INFRASTRUCTURE |

**Total de Pontos:** 76

---

## 🎯 Roadmap Sugerido

### Sprint 1 (Crítico - 26 pontos)
- DEBT-002: ENV Variables (5 pontos)
- DEBT-003: Generic Rescue (8 pontos) 
- DEBT-004: frozen_string_literal (3 pontos)
- DEBT-006: Missing Indexes (5 pontos)
- DEBT-008: Inconsistent Logging (5 pontos)

### Sprint 2 (Performance - 21 pontos)
- DEBT-005: N+1 Queries (8 pontos)
- DEBT-001: God Objects - Fase 1 (Job.rb + HybridSearch) (13 pontos)

### Sprint 3 (Quality - 18 pontos)
- DEBT-007: Test Coverage (13 pontos)
- DEBT-010: Job Monitoring (3 pontos)

### Sprint 4 (Long-term - 16 pontos)
- DEBT-009: Documentation (5 pontos)
- DEBT-011: Multi-Tenancy (8 pontos)

---

## 📈 Métricas de Sucesso

**Antes (Baseline):**
- Arquivos > 500 linhas: 9
- ENV sem fetch: 20+
- Generic rescue: 175
- Cobertura de testes: ~60%
- N+1 queries: Não medido

**Depois (Target):**
- Arquivos > 500 linhas: 0
- ENV sem fetch: 0
- Generic rescue: 0
- Cobertura de testes: > 80%
- N+1 queries: 0 (com bullet)

**KPIs de Acompanhamento:**
- Tempo médio de PR review
- Bugs em produção (por sprint)
- Tempo de onboarding de novos devs
- P95 response time de APIs
- Code Climate score

---

## 🔧 Ferramentas Recomendadas

### Para Implementar:
1. **bullet** - Detectar N+1 queries
2. **simplecov** - Cobertura de testes
3. **brakeman** - Security scanning (já instalado)
4. **rubocop-performance** - Performance linting
5. **reek** - Code smells

### Configurar Melhor:
1. **sidekiq** - Retry strategies e monitoring
2. **exception_notification** - Alerting estruturado
3. **rails-erd** - Diagramas de database

### CI/CD:
1. Adicionar coverage threshold
2. Rubocop como blocker
3. Bullet no CI
4. Security scanning automático

---

## 📝 Notas Finais

Este relatório foi gerado baseado em análise estática do código. Recomenda-se:

1. **Revisar com time técnico** prioridades e estimativas
2. **Criar cards no Jira** usando este template
3. **Estabelecer working agreement** de qualidade mínima
4. **Agendar tech debt sprints** regulares (20% do tempo)

**Próximos Passos:**
1. Apresentar relatório para lideranças técnicas
2. Definir ownership de cada débito
3. Criar milestones no GitHub/Jira
4. Começar com DEBT-002 (quick win de 5 pontos)

---

**Elaborado por:** GitHub Copilot CLI  
**Revisão Recomendada:** Tech Leads + CTO  
**Atualização:** Trimestral ou quando débito crítico for identificado
