# Especificação Técnica: Sistema de Integrações ATS

**Versão**: 1.0  
**Data**: 24 Novembro 2025  
**Autor**: LIA Development Team

---

## 1. VISÃO GERAL

Sistema multi-tenant de integração com ATS (Applicant Tracking Systems) que combina:
- **Merge.dev**: Conector multi-ATS universal (Greenhouse, Lever, Workable, BambooHR, etc.)
- **Custom Connectors**: ATS brasileiros (Gupy, Pandapé)
- **Admin Module**: Interface para WedoTalent gerenciar integrações por cliente

---

## 2. CAMPOS DE CANDIDATOS - MAPEAMENTO COMPLETO

### 2.1 Campos Padrão (Merge.dev Unified Schema)

```typescript
// Campos já implementados na tabela `candidates`
✅ id: UUID
✅ name: string
✅ email: string
✅ phone: string
✅ linkedin_url: string
✅ github_url: string
✅ portfolio_url: string
✅ current_title: string
✅ current_company: string
✅ seniority_level: string
✅ years_of_experience: integer
✅ technical_skills: string[]
✅ soft_skills: string[]
✅ languages: jsonb ({"english": "fluent", "portuguese": "native"})
✅ certifications: string[]
✅ location_city: string
✅ location_state: string
✅ location_country: string
✅ is_remote: boolean
✅ willing_to_relocate: boolean
✅ desired_salary_min: numeric
✅ desired_salary_max: numeric
✅ salary_currency: string
✅ work_model_preference: string
✅ contract_type_preference: string
✅ resume_url: string
✅ resume_text: text
✅ cover_letter: text
✅ lia_score: numeric
✅ lia_insights: jsonb
✅ skills_match_percentage: numeric
✅ status: string
✅ is_active: boolean
✅ is_blacklisted: boolean
✅ blacklist_reason: text
✅ preferred_contact_method: string
✅ best_time_to_contact: string
✅ communication_consent: boolean
✅ tags: string[]
✅ notes: text
✅ additional_data: jsonb
✅ created_at: timestamp
✅ updated_at: timestamp
✅ last_contacted_at: timestamp
✅ last_activity_at: timestamp
```

### 2.2 Campos FALTANDO (ATS Integration - ALTA PRIORIDADE)

```typescript
// Campos críticos para integração ATS
❌ ats_identifiers: jsonb  // {"greenhouse": "cand_123", "gupy": "456", "pandape": "789"}
❌ application_metadata: jsonb  // {job_id, job_title, pipeline_stage, applied_at, etc.}
❌ diversity_fields: jsonb  // {gender, race, disability, lgbtq+, veteran, etc.}
❌ gdpr_lgpd_consent: jsonb  // {opted_in_at, consent_type, ip_address, etc.}
❌ source_metadata: jsonb  // {source_type, source_timestamp, referrer, campaign, etc.}
❌ raw_ats_payload: jsonb  // Payload completo do ATS para preservar dados não mapeados
```

### 2.3 Campos Específicos - ATS Brasileiros (Gupy, Pandapé)

```typescript
// Campos específicos do Brasil (compliance LGPD)
❌ cpf: string (encrypted)  // Brazilian tax ID
❌ rg: string (encrypted)  // Brazilian ID document
❌ birth_date: date
❌ pcd: boolean  // Pessoa com Deficiência (PCD law compliance)
❌ pcd_details: string
❌ race_ethnicity: string  // For diversity tracking (optional per LGPD)
❌ address: jsonb  // {street, number, complement, neighborhood, city, state, zip, country}
```

### 2.4 Merge.dev Standard Fields (Not Yet Implemented)

```typescript
// Merge.dev normalized fields
❌ first_name: string (separated from `name`)
❌ last_name: string (separated from `name`)
❌ phone_numbers: jsonb  // [{"type": "mobile", "phone": "+55..."}, {"type": "work", "phone": ...}]
❌ social_links: jsonb  // [{"type": "linkedin", "url": ...}, {"type": "github", "url": ...}]
❌ hired_at: timestamp
❌ avatar_url: string
❌ custom_fields: jsonb  // Merge.dev passthrough fields
❌ unified_custom_fields: jsonb  // Merge.dev normalized custom fields
```

---

## 3. ARQUITETURA DE INTEGRAÇÃO

### 3.1 Tabelas do Banco de Dados

#### **Tabela: `ats_systems`** (Catálogo de ATS)
```sql
CREATE TABLE ats_systems (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(100) NOT NULL,  -- "Greenhouse", "Gupy", "Pandape", etc.
  slug VARCHAR(50) UNIQUE NOT NULL,  -- "greenhouse", "gupy", "pandape"
  region VARCHAR(50),  -- "global", "brazil", "latam"
  auth_type VARCHAR(50),  -- "api_key", "oauth2", "basic_auth"
  capabilities JSONB,  -- {"webhooks": true, "custom_fields": true, "bulk_import": true}
  supports_webhooks BOOLEAN DEFAULT false,
  api_base_url VARCHAR(255),
  documentation_url VARCHAR(255),
  connector_type VARCHAR(50),  -- "merge", "custom"
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

#### **Tabela: `customer_ats_connections`** (Conexões por Cliente)
```sql
CREATE TABLE customer_ats_connections (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id UUID NOT NULL,  -- FK para tabela companies
  ats_system_id UUID NOT NULL REFERENCES ats_systems(id),
  connection_name VARCHAR(100),  -- "Greenhouse Production", "Gupy Hiring"
  status VARCHAR(50) DEFAULT 'active',  -- 'active', 'paused', 'error', 'setup'
  sync_mode VARCHAR(50) DEFAULT 'pull',  -- 'pull', 'push', 'bidirectional'
  sync_frequency VARCHAR(50) DEFAULT '15min',  -- '15min', '1hour', 'webhook'
  default_job_board BOOLEAN DEFAULT false,
  last_sync_at TIMESTAMP,
  last_sync_status VARCHAR(50),  -- 'success', 'partial', 'failed'
  error_message TEXT,
  configuration JSONB,  -- {"pull_candidates": true, "push_applications": false}
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_customer_ats_company ON customer_ats_connections(company_id);
CREATE INDEX idx_customer_ats_status ON customer_ats_connections(status);
```

#### **Tabela: `ats_credentials`** (Credenciais Criptografadas)
```sql
CREATE TABLE ats_credentials (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  connection_id UUID NOT NULL REFERENCES customer_ats_connections(id) ON DELETE CASCADE,
  credential_type VARCHAR(50),  -- 'api_key', 'oauth_token', 'basic_auth'
  
  -- Secrets armazenados via Replit Secrets (NÃO em plaintext!)
  secret_reference VARCHAR(255),  -- Reference to Replit secret key
  
  -- OAuth specific
  oauth_access_token_ref VARCHAR(255),
  oauth_refresh_token_ref VARCHAR(255),
  oauth_expires_at TIMESTAMP,
  oauth_scopes TEXT[],
  
  -- Metadata
  is_valid BOOLEAN DEFAULT true,
  last_validated_at TIMESTAMP,
  rotation_metadata JSONB,  -- {"last_rotated": ..., "next_rotation": ...}
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_ats_creds_connection ON ats_credentials(connection_id);
```

#### **Tabela: `ats_field_mappings`** (Mapeamento de Campos Customizados)
```sql
CREATE TABLE ats_field_mappings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id UUID NOT NULL,
  ats_system_id UUID NOT NULL REFERENCES ats_systems(id),
  
  lia_field VARCHAR(100) NOT NULL,  -- "technical_skills", "years_of_experience"
  external_field VARCHAR(100) NOT NULL,  -- "skills[]", "yearsExp", "custom_field_123"
  
  field_type VARCHAR(50),  -- 'string', 'array', 'number', 'date', 'boolean'
  transform VARCHAR(50),  -- 'none', 'split_comma', 'join_comma', 'parse_int', 'date_format'
  direction VARCHAR(50) DEFAULT 'pull',  -- 'pull', 'push', 'bidirectional'
  
  is_required BOOLEAN DEFAULT false,
  default_value TEXT,
  validation_rules JSONB,  -- {"min": 0, "max": 50, "regex": "..."}
  
  created_by VARCHAR(100),  -- "wedotalent_admin" or "auto_discovery"
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  
  UNIQUE(company_id, ats_system_id, lia_field, external_field)
);

CREATE INDEX idx_field_mapping_company ON ats_field_mappings(company_id);
CREATE INDEX idx_field_mapping_ats ON ats_field_mappings(ats_system_id);
```

#### **Tabela: `ats_sync_jobs`** (Histórico de Sincronizações)
```sql
CREATE TABLE ats_sync_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  connection_id UUID NOT NULL REFERENCES customer_ats_connections(id),
  
  job_type VARCHAR(50) NOT NULL,  -- 'pull_candidates', 'push_application', 'pull_jobs'
  trigger_type VARCHAR(50),  -- 'scheduled', 'manual', 'webhook'
  
  status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'running', 'completed', 'failed', 'partial'
  
  started_at TIMESTAMP,
  finished_at TIMESTAMP,
  duration_ms INTEGER,
  
  -- Stats
  total_items INTEGER DEFAULT 0,
  successful_items INTEGER DEFAULT 0,
  failed_items INTEGER DEFAULT 0,
  skipped_items INTEGER DEFAULT 0,
  
  error_summary TEXT,
  metadata JSONB,  -- {"cursor": "...", "page": 5, "filters": {...}}
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_sync_jobs_connection ON ats_sync_jobs(connection_id);
CREATE INDEX idx_sync_jobs_status ON ats_sync_jobs(status);
CREATE INDEX idx_sync_jobs_created ON ats_sync_jobs(created_at DESC);
```

#### **Tabela: `ats_sync_items`** (Itens Sincronizados)
```sql
CREATE TABLE ats_sync_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sync_job_id UUID NOT NULL REFERENCES ats_sync_jobs(id) ON DELETE CASCADE,
  
  entity_type VARCHAR(50),  -- 'candidate', 'application', 'job'
  entity_id UUID,  -- LIA internal ID (nullable for failed items)
  external_id VARCHAR(255),  -- ATS external ID
  
  outcome VARCHAR(50),  -- 'created', 'updated', 'skipped', 'failed'
  error_message TEXT,
  error_payload JSONB,
  
  raw_data JSONB,  -- Original ATS payload
  transformed_data JSONB,  -- After field mapping
  
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_sync_items_job ON ats_sync_items(sync_job_id);
CREATE INDEX idx_sync_items_entity ON ats_sync_items(entity_type, entity_id);
CREATE INDEX idx_sync_items_external ON ats_sync_items(external_id);
```

#### **Tabela: `ats_webhook_events`** (Webhooks Recebidos)
```sql
CREATE TABLE ats_webhook_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  connection_id UUID NOT NULL REFERENCES customer_ats_connections(id),
  
  event_name VARCHAR(100),  -- "candidate.created", "application.status_changed"
  payload JSONB NOT NULL,
  headers JSONB,
  
  processed_at TIMESTAMP,
  processing_status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'processed', 'failed'
  processing_error TEXT,
  
  retry_count INTEGER DEFAULT 0,
  
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_webhooks_connection ON ats_webhook_events(connection_id);
CREATE INDEX idx_webhooks_status ON ats_webhook_events(processing_status);
CREATE INDEX idx_webhooks_created ON ats_webhook_events(created_at DESC);
```

---

## 4. FLUXO DE DADOS

### 4.1 Initial Setup Flow
```
1. WedoTalent Admin → Admin UI → Enable ATS Connection
2. Enter Credentials → Validate Connection → Store in ats_credentials
3. Auto-discover Fields → Create ats_field_mappings (auto or manual)
4. Test Connection → Trigger initial backfill sync job
5. Monitor sync progress → Review errors → Activate connection
```

### 4.2 Ongoing Sync Flow (Pull Mode)
```
WEBHOOK-BASED (Preferred):
ATS Event → Webhook Receiver → ats_webhook_events → Queue → Process → Update candidates

POLLING-BASED (Fallback):
Cron (15min) → Create sync_job → Fetch updated_at > last_sync → Transform → Update candidates → Record sync_items
```

### 4.3 Conflict Resolution
```
Multiple ATS Sources:
- Match by email/phone
- Merge data (latest ATS timestamp wins)
- Record conflicts in ats_sync_items for manual review
- Maintain ats_identifiers JSONB for multi-source tracking
```

---

## 5. ESTRUTURA DE PASTAS (Backend)

```
lia-agent-system/
├── app/
│   ├── connectors/                    # NEW
│   │   ├── __init__.py
│   │   ├── base.py                    # BaseATSConnector interface
│   │   ├── merge_connector.py         # Merge.dev unified
│   │   ├── gupy_connector.py          # Gupy custom
│   │   └── pandape_connector.py       # Pandape custom
│   │
│   ├── services/
│   │   └── ats_integration_service.py # NEW - Facade service
│   │
│   ├── models/
│   │   ├── ats_system.py              # NEW - 7 novos modelos
│   │   └── candidate.py               # UPDATE - add missing fields
│   │
│   ├── schemas/
│   │   └── ats_integration.py         # NEW - Pydantic schemas
│   │
│   └── api/
│       └── v1/
│           └── admin/                 # NEW
│               ├── __init__.py
│               └── integrations.py    # Admin routes
```

---

## 6. ADMIN MODULE - ESPECIFICAÇÃO

### 6.1 Backend Routes

```python
# /api/v1/admin/integrations/*

GET    /systems                    # List available ATS systems
GET    /connections                # List customer connections (filter by company_id)
POST   /connections                # Create new connection
PUT    /connections/{id}           # Update connection (enable/disable, config)
DELETE /connections/{id}           # Delete connection
POST   /connections/{id}/test      # Test connection
POST   /connections/{id}/sync      # Trigger manual sync

GET    /field-mappings             # Get field mappings (by company, ats)
POST   /field-mappings             # Create/update mapping
DELETE /field-mappings/{id}        # Remove mapping

GET    /sync-history               # List sync jobs (pagination, filters)
GET    /sync-jobs/{id}             # Sync job details
GET    /sync-jobs/{id}/items       # Sync items (success/errors)

POST   /webhooks/receive           # Webhook receiver endpoint
```

### 6.2 Permissões

```typescript
// Role-based access
wedotalent_admin: Full access (manage all companies)
company_admin: Read-only (view own connections, sync status)
recruiter: No access
```

### 6.3 Frontend UI (plataforma-lia)

**Nova Seção no Menu Principal**: "Integrações ATS" (ícone: `Plug` do lucide-react)

**Páginas:**
1. **Conexões Ativas** (Lista de integrações)
   - Card por ATS: Status, última sync, erros
   - Botões: Enable/Disable, Configure, Test Connection, Manual Sync

2. **Configurar Nova Integração**
   - Select ATS System
   - Enter Credentials (API Key, OAuth)
   - Test Connection
   - Configure Sync Mode (Pull/Push/Bidirectional)
   - Set Frequency (Webhook / 15min / 1hour)

3. **Mapeamento de Campos**
   - Tabela: LIA Field ↔ ATS Field
   - Auto-discovery + Manual Override
   - Transform Rules (split, join, parse, format)

4. **Histórico de Sincronizações**
   - Tabela: Date, Type, Status, Total/Success/Failed
   - Drill-down: View failed items, error messages

---

## 7. PRIORIZAÇÃO DE IMPLEMENTAÇÃO

### Fase 1: Schema & Basic Infrastructure (CURRENT)
- ✅ Criar 7 tabelas de integração
- ✅ Atualizar tabela `candidates` com campos faltantes
- ✅ Migrations via `npm run db:push`

### Fase 2: Base Connector (NEXT)
- ⬜ Implementar `BaseATSConnector` interface
- ⬜ Merge.dev connector básico (list candidates)
- ⬜ `AtsIntegrationService` facade

### Fase 3: Admin Backend API
- ⬜ CRUD endpoints para connections
- ⬜ Field mapping endpoints
- ⬜ Sync job triggers
- ⬜ Role-based auth (wedotalent_admin)

### Fase 4: Custom Connectors (Gupy, Pandapé)
- ⬜ Gupy API connector
- ⬜ Pandapé API connector

### Fase 5: Admin Frontend UI
- ⬜ Página "Integrações ATS" no menu
- ⬜ Connection management UI
- ⬜ Field mapping UI
- ⬜ Sync history dashboard

### Fase 6: Webhooks & Real-time Sync
- ⬜ Webhook receiver
- ⬜ Queue/worker for async processing
- ⬜ Real-time sync monitoring

---

## 8. DECISÕES TÉCNICAS

✅ **Credentials**: Usar Replit Secrets (não armazenar plaintext)  
✅ **Merge.dev**: Usar para ATS internacionais (Greenhouse, Lever, etc.)  
✅ **Custom Connectors**: Implementar para Gupy e Pandapé  
✅ **Webhooks**: Preferir webhooks, fallback para polling 15min  
✅ **Conflict Resolution**: Latest ATS timestamp wins  
✅ **Field Mapping**: Auto-discovery + manual override  
✅ **Admin Only**: Apenas WedoTalent admin gerencia integracõ

es  
✅ **Queue**: Usar para processar syncs async (considerar Celery ou FastAPI BackgroundTasks)

---

## 9. PRÓXIMOS PASSOS IMEDIATOS

1. **Criar migrations** para 7 novas tabelas
2. **Atualizar modelo `Candidate`** com campos faltantes
3. **Implementar `BaseATSConnector`** interface
4. **Criar admin routes** básicos (CRUD connections)
5. **Testar Merge.dev** com credenciais de teste

---

**Documento mantido por**: LIA Development Team  
**Última atualização**: 24 Nov 2025
