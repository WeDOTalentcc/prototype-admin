# Merge API - Referência de Campos de Integração

> **Documento para acelerar implementações de clientes**  
> Última atualização: Janeiro 2026

---

## Sumário

1. [Visão Geral](#visão-geral)
2. [ATSs Suportados](#atss-suportados)
3. [Campos ATS por Objeto](#campos-ats-por-objeto)
4. [Comparativo por ATS](#comparativo-por-ats)
5. [HRISs Suportados](#hriss-suportados)
6. [Campos HRIS por Objeto](#campos-hris-por-objeto)
7. [Operações de Escrita](#operações-de-escrita)
8. [Passthrough Requests](#passthrough-requests)
9. [Webhooks Disponíveis](#webhooks-disponíveis)

---

## Visão Geral

### Base URLs

| Região | ATS | HRIS |
|--------|-----|------|
| US | `https://api.merge.dev/api/ats/v1` | `https://api.merge.dev/api/hris/v1` |
| EU | `https://api-eu.merge.dev/api/ats/v1` | `https://api-eu.merge.dev/api/hris/v1` |
| APAC | `https://api-ap.merge.dev/api/ats/v1` | `https://api-ap.merge.dev/api/hris/v1` |

### Autenticação

```
Authorization: Bearer {API_KEY}
X-Account-Token: {LINKED_ACCOUNT_TOKEN}
```

### Rate Limits

| Plano | Limite |
|-------|--------|
| Launch | 100/min por Linked Account |
| Professional | 400/min por Linked Account |
| Enterprise | 600/min por Linked Account |

---

## ATSs Suportados

### Tier 1 (Principais - Brasil e Global)

| ATS | Mercado | Notas |
|-----|---------|-------|
| **Greenhouse** | Global | Mais completo, todos os campos |
| **Lever** | Global | Excelente cobertura |
| **Gupy** | Brasil | Via StackOne ou direto |
| **Pandapé** | Brasil | Via StackOne ou direto |
| **Oracle Taleo** | Enterprise | Grandes empresas |
| **Workday Recruiting** | Enterprise | Grandes empresas |
| **SAP SuccessFactors** | Enterprise | Grandes empresas |
| **SmartRecruiters** | Global | Boa cobertura |

### Tier 2 (Populares)

| ATS | Mercado |
|-----|---------|
| Ashby | Tech/Startups |
| BambooHR | PME |
| Bullhorn | Staffing |
| iCIMS | Enterprise |
| JazzHR | PME |
| Jobvite | Mid-market |
| Workable | PME/Mid |

### Lista Completa (60+ ATSs)

ApplicantStack, Ashby, Avature, BambooHR, Breezy, Bullhorn, CATS, ClayHR, Clockwork, Comeet, Cornerstone TalentLink, Crelate, Dayforce, d.Vinci, Easycruit, EngageATS, Eploy, Flatchr, Fountain, Freshteam, Gem, Greenhouse, Harbour ATS, Homerun, HR Cloud, iCIMS, Infinite BrassRing, JazzHR, JobAdder, JobDiva, JobScore, Jobsoid, Jobvite, Join, Lano, Lever, Manatal, Occupop, Onlyfy, Oracle Fusion Recruiting, Oracle Taleo, Personio, Pinpoint, Polymer, Recruiterflow, Recruitive, Sage HR, SAP SuccessFactors, SmartRecruiters, Taleez, TalentLyft, TalentReef, Teamtailor, Tellent Recruitee, Traffit, Tribepad, UKG Pro Recruiting, Welcome to the Jungle, Workable, Workday, Zoho Recruit

---

## Campos ATS por Objeto

### 1. Candidate (Candidato)

| Campo | Tipo | Descrição | Uso LIA |
|-------|------|-----------|---------|
| `id` | UUID | ID interno Merge | Referência |
| `remote_id` | String | ID no ATS do cliente | Sync |
| `first_name` | String | Nome | Personalização |
| `last_name` | String | Sobrenome | Personalização |
| `company` | String | Empresa atual | Contexto |
| `title` | String | Cargo atual | Matching |
| `email_addresses` | EmailAddress[] | Lista de emails | Comunicação |
| `phone_numbers` | PhoneNumber[] | Lista de telefones | WhatsApp |
| `urls` | Url[] | LinkedIn, Portfolio, GitHub | Enriquecimento |
| `locations` | String[] | Localizações | Filtro geográfico |
| `tags` | UUID[] | Tags de categorização | Segmentação |
| `applications` | UUID[] | Candidaturas vinculadas | Histórico |
| `attachments` | UUID[] | CVs e arquivos | Análise |
| `is_private` | Boolean | Candidato confidencial | ACL |
| `can_email` | Boolean | Pode receber email | Comunicação |
| `last_interaction_at` | DateTime | Última interação | Engajamento |
| `remote_created_at` | DateTime | Criado no ATS | Antiguidade |
| `remote_updated_at` | DateTime | Atualizado no ATS | Atividade |

**Endpoints:**
- `GET /candidates` - Listar
- `GET /candidates/{id}` - Detalhe
- `POST /candidates` - Criar
- `PATCH /candidates/{id}` - Atualizar

---

### 2. Application (Candidatura)

| Campo | Tipo | Descrição | Uso LIA |
|-------|------|-----------|---------|
| `id` | UUID | ID Merge | Referência |
| `remote_id` | String | ID no ATS | Sync |
| `candidate` | UUID | Candidato vinculado | Contexto |
| `job` | UUID | Vaga vinculada | Contexto |
| `current_stage` | UUID | **Etapa atual no pipeline** | **Sync de status** |
| `source` | String | Origem (LinkedIn, Referral, etc.) | **ROI de canais** |
| `credited_to` | UUID | Recrutador responsável | Atribuição |
| `applied_at` | DateTime | Data de candidatura | Time-to-hire |
| `rejected_at` | DateTime | Data de rejeição | Métricas |
| `reject_reason` | UUID | Motivo de rejeição | Análise |
| `screening_question_answers` | ScreeningQuestionAnswer[] | **Respostas de triagem** | **Input WSI** |
| `attachments` | UUID[] | Anexos da candidatura | CV |

**Endpoints:**
- `GET /applications` - Listar
- `GET /applications/{id}` - Detalhe
- `POST /applications` - Criar
- `PATCH /applications/{id}` - Atualizar stage

---

### 3. Job (Vaga)

| Campo | Tipo | Descrição | Uso LIA |
|-------|------|-----------|---------|
| `id` | UUID | ID Merge | Referência |
| `remote_id` | String | ID no ATS | Sync |
| `name` | String | Título da vaga | Display |
| `description` | String | **Job Description completo** | **Parsing requisitos** |
| `code` | String | Código da vaga | Referência |
| `status` | Enum | OPEN, CLOSED, DRAFT, ARCHIVED, PENDING | **Status sync** |
| `confidential` | Boolean | Vaga confidencial | ACL |
| `departments` | UUID[] | Departamentos | Organização |
| `offices` | UUID[] | Locais/Escritórios | Filtro |
| `hiring_managers` | UUID[] | Gestores | Responsáveis |
| `recruiters` | UUID[] | Recrutadores | Atribuição |
| `remote_created_at` | DateTime | Criada no ATS | Antiguidade |
| `remote_updated_at` | DateTime | Atualizada no ATS | Atividade |

**Status Enum:**
- `OPEN` - Aberta
- `CLOSED` - Fechada
- `DRAFT` - Rascunho
- `ARCHIVED` - Arquivada
- `PENDING` - Pendente aprovação

**Endpoints:**
- `GET /jobs` - Listar
- `GET /jobs/{id}` - Detalhe

---

### 4. ScheduledInterview (Entrevista Agendada)

| Campo | Tipo | Descrição | Uso LIA |
|-------|------|-----------|---------|
| `id` | UUID | ID Merge | Referência |
| `remote_id` | String | ID no ATS | Sync |
| `application` | UUID | Candidatura | Contexto |
| `job_interview_stage` | UUID | Etapa da entrevista | Tipo |
| `organizer` | UUID | Quem agendou | Responsável |
| `interviewers` | UUID[] | **Lista de entrevistadores** | **Briefing** |
| `location` | String | Local ou link | Acesso |
| `start_at` | DateTime | Início | Scheduling |
| `end_at` | DateTime | Fim | Duração |
| `status` | Enum | Status da entrevista | **Trigger automação** |

**Status Enum:**
- `SCHEDULED` - Agendada
- `AWAITING_FEEDBACK` - Aguardando feedback
- `COMPLETE` - Concluída

**Endpoints:**
- `GET /interviews` - Listar
- `GET /interviews/{id}` - Detalhe
- `POST /interviews` - Criar

---

### 5. Scorecard (Feedback de Entrevista) ⭐

| Campo | Tipo | Descrição | Uso LIA |
|-------|------|-----------|---------|
| `id` | UUID | ID Merge | Referência |
| `remote_id` | String | ID no ATS | Sync |
| `application` | UUID | Candidatura | Contexto |
| `interview` | UUID | Entrevista específica | Vínculo |
| `interviewer` | UUID | **Quem deu o feedback** | Atribuição |
| `submitted_at` | DateTime | Quando submetido | Timing |
| `overall_recommendation` | Enum | **Recomendação geral** | **Input WSI** |

**Recommendation Enum:**
- `DEFINITELY_NO` - Definitivamente não
- `NO` - Não
- `YES` - Sim
- `STRONG_YES` - Fortemente sim
- `NO_DECISION` - Sem decisão

**Endpoints:**
- `GET /scorecards` - Listar
- `GET /scorecards/{id}` - Detalhe

---

### 6. Activity (Notas e Histórico) ⭐

| Campo | Tipo | Descrição | Uso LIA |
|-------|------|-----------|---------|
| `id` | UUID | ID Merge | Referência |
| `remote_id` | String | ID no ATS | Sync |
| `candidate` | UUID | Candidato | Vínculo |
| `user` | UUID | Quem criou | Auditoria |
| `activity_type` | Enum | Tipo de atividade | Classificação |
| `subject` | String | Assunto | Contexto |
| `body` | String | **Conteúdo da nota/email** | **Histórico** |
| `visibility` | Enum | Visibilidade | ACL |
| `remote_created_at` | DateTime | Criada no ATS | Timing |

**Activity Type Enum:**
- `NOTE` - Nota
- `EMAIL` - Email
- `COMMENT` - Comentário
- `OTHER` - Outro

**Endpoints:**
- `GET /activities` - Listar
- `GET /activities/{id}` - Detalhe
- `POST /activities` - Criar nota

---

### 7. Attachment (Arquivos/CVs)

| Campo | Tipo | Descrição | Uso LIA |
|-------|------|-----------|---------|
| `id` | UUID | ID Merge | Referência |
| `remote_id` | String | ID no ATS | Sync |
| `file_name` | String | Nome do arquivo | Display |
| `file_url` | String | **URL para download** | **Parsing CV** |
| `attachment_type` | Enum | Tipo de anexo | Classificação |
| `candidate` | UUID | Candidato | Vínculo |

**Attachment Type Enum:**
- `RESUME` - Currículo
- `COVER_LETTER` - Carta de apresentação
- `OFFER_LETTER` - Carta de oferta
- `OTHER` - Outro

**Endpoints:**
- `GET /attachments` - Listar
- `GET /attachments/{id}` - Detalhe
- `POST /attachments` - Upload

---

### 8. JobInterviewStage (Etapas do Pipeline)

| Campo | Tipo | Descrição | Uso LIA |
|-------|------|-----------|---------|
| `id` | UUID | ID Merge | Referência |
| `remote_id` | String | ID no ATS | Sync |
| `name` | String | Nome da etapa | Mapeamento |
| `job` | UUID | Vaga específica (ou null) | Contexto |
| `stage_order` | Integer | **Ordem no pipeline** | Progressão |

**Endpoints:**
- `GET /job-interview-stages` - Listar

---

### 9. Offer (Proposta)

| Campo | Tipo | Descrição | Uso LIA |
|-------|------|-----------|---------|
| `id` | UUID | ID Merge | Referência |
| `remote_id` | String | ID no ATS | Sync |
| `application` | UUID | Candidatura | Contexto |
| `creator` | UUID | Quem criou | Atribuição |
| `status` | Enum | Status da oferta | **Conversão** |
| `start_date` | DateTime | Data de início | Planejamento |
| `sent_at` | DateTime | Quando enviada | Métricas |
| `closed_at` | DateTime | Quando fechada | Time-to-offer |

**Status Enum:**
- `DRAFT` - Rascunho
- `APPROVED` - Aprovada
- `SENT` - Enviada
- `ACCEPTED` - Aceita
- `DECLINED` - Recusada

**Endpoints:**
- `GET /offers` - Listar
- `GET /offers/{id}` - Detalhe

---

### 10. ScreeningQuestion (Perguntas de Triagem)

| Campo | Tipo | Descrição | Uso LIA |
|-------|------|-----------|---------|
| `id` | UUID | ID Merge | Referência |
| `remote_id` | String | ID no ATS | Sync |
| `job` | UUID | Vaga associada | Contexto |
| `title` | String | Texto da pergunta | Display |
| `description` | String | Descrição | Contexto |
| `type` | Enum | Tipo de resposta | Validação |
| `required` | Boolean | Obrigatória | Fluxo |
| `options` | ScreeningQuestionOption[] | Opções | Renderização |

**Type Enum:**
- `DATE` - Data
- `FILE` - Arquivo
- `SINGLE_SELECT` - Seleção única
- `MULTI_SELECT` - Seleção múltipla
- `SINGLE_LINE_TEXT` - Texto curto
- `MULTI_LINE_TEXT` - Texto longo
- `NUMERIC` - Numérico
- `BOOLEAN` - Sim/Não

---

### 11. RemoteUser (Usuários do ATS)

| Campo | Tipo | Descrição | Uso LIA |
|-------|------|-----------|---------|
| `id` | UUID | ID Merge | Referência |
| `remote_id` | String | ID no ATS | Sync |
| `first_name` | String | Nome | Display |
| `last_name` | String | Sobrenome | Display |
| `email` | String | Email | Comunicação |
| `disabled` | Boolean | Ativo/Inativo | Filtro |
| `access_role` | Enum | Permissão no ATS | ACL |
| `remote_created_at` | DateTime | Criado no ATS | Antiguidade |

**Endpoints:**
- `GET /users` - Listar
- `GET /users/{id}` - Detalhe
- `POST /users` - Criar

---

### 12. EEOC (Dados de Diversidade - EUA)

| Campo | Tipo | Descrição | Uso LIA |
|-------|------|-----------|---------|
| `id` | UUID | ID Merge | Referência |
| `candidate` | UUID | Candidato | Vínculo |
| `race` | Enum | Raça declarada | Compliance |
| `gender` | Enum | Gênero | Compliance |
| `veteran_status` | Enum | Status veterano | Compliance |
| `disability_status` | Enum | Status PcD | Compliance |
| `submitted_at` | DateTime | Quando submetido | Timing |

---

### 13. Department (Departamento)

| Campo | Tipo | Descrição | Uso LIA |
|-------|------|-----------|---------|
| `id` | UUID | ID Merge | Referência |
| `remote_id` | String | ID no ATS | Sync |
| `name` | String | Nome do departamento | Display |
| `parent_department` | UUID | Departamento pai | Hierarquia |

---

### 14. Office (Escritório/Local)

| Campo | Tipo | Descrição | Uso LIA |
|-------|------|-----------|---------|
| `id` | UUID | ID Merge | Referência |
| `remote_id` | String | ID no ATS | Sync |
| `name` | String | Nome do escritório | Display |
| `location` | String | Endereço | Filtro geográfico |

---

### 15. RejectReason (Motivo de Rejeição)

| Campo | Tipo | Descrição | Uso LIA |
|-------|------|-----------|---------|
| `id` | UUID | ID Merge | Referência |
| `remote_id` | String | ID no ATS | Sync |
| `name` | String | Nome do motivo | Análise |

---

### 16. Tag (Tags)

| Campo | Tipo | Descrição | Uso LIA |
|-------|------|-----------|---------|
| `id` | UUID | ID Merge | Referência |
| `remote_id` | String | ID no ATS | Sync |
| `name` | String | Nome da tag | Segmentação |

---

### 17. JobPosting (Publicação de Vaga)

| Campo | Tipo | Descrição | Uso LIA |
|-------|------|-----------|---------|
| `id` | UUID | ID Merge | Referência |
| `remote_id` | String | ID no ATS | Sync |
| `job` | UUID | Vaga vinculada | Contexto |
| `title` | String | Título publicado | SEO |
| `content` | String | Conteúdo publicado | Análise |
| `is_internal` | Boolean | Publicação interna | Filtro |
| `status` | Enum | PUBLISHED, CLOSED, DRAFT | Status |
| `job_posting_urls` | Url[] | URLs onde está publicada | Monitoramento |
| `remote_created_at` | DateTime | Criada no ATS | Timing |
| `remote_updated_at` | DateTime | Atualizada no ATS | Atividade |

---

## Comparativo por ATS

### Greenhouse vs Lever vs Taleo vs SmartRecruiters

| Objeto/Campo | Greenhouse | Lever | Taleo | SmartRecruiters |
|--------------|------------|-------|-------|-----------------|
| **Candidates** | ✅ Full | ✅ Full | ✅ Full | ✅ Full |
| `first_name` | ✅ R/W | ✅ R/W | ✅ R | ✅ R |
| `last_name` | ✅ R/W | ✅ R/W | ✅ R | ✅ R |
| `company` | ✅ R/W | ✅ R | ✅ R | ✅ R |
| `title` | ✅ R/W | ❌ | ✅ R | ✅ R |
| `email_addresses` | ✅ R/W | ✅ R/W | ✅ R | ✅ R |
| `phone_numbers` | ✅ R/W | ✅ R/W | ✅ R | ✅ R |
| `urls` | ✅ R | ✅ R | ✅ R | ✅ R |
| `locations` | ❌ | ✅ R | ❌ | ✅ R |
| `tags` | ✅ R/W | ✅ R | ❌ | ✅ R |
| **Applications** | ✅ Full | ✅ Full | ✅ Full | ✅ Full |
| `current_stage` | ✅ R/W | ✅ R/W | ✅ R/W | ✅ R/W |
| `source` | ✅ R | ✅ R | ✅ R | ✅ R |
| `screening_answers` | ✅ R | ✅ R | ✅ R | ✅ R |
| **Interviews** | ✅ Full | ✅ Full | ✅ Parcial | ✅ Full |
| `interviewers` | ❌ | ✅ R | ❌ | ✅ R |
| `status` | ✅ R | ❌ | ✅ R | ✅ R |
| **Scorecards** | ✅ Full | ✅ Full | ✅ Parcial | ✅ Full |
| `overall_recommendation` | ✅ R | ✅ R | ✅ R | ✅ R |
| **Activities** | ✅ Full | ✅ Full | ✅ Parcial | ✅ Full |
| `body` | ✅ R | ✅ R | ✅ R | ✅ R |
| `visibility` | ✅ R | ❌ | ❌ | ❌ |
| **Attachments** | ✅ Full | ✅ Full | ✅ Full | ✅ Full |
| `file_url` | ✅ R | ✅ R | ✅ R | ✅ R |
| `attachment_type` | ✅ R | ❌ | ✅ R | ✅ R |
| **EEOC** | ✅ Full | ❌ | ✅ Full | ✅ Full |
| **Offers** | ✅ Full | ✅ Full | ✅ Parcial | ✅ Full |

**Legenda:** ✅ R = Leitura, ✅ R/W = Leitura e Escrita, ❌ = Não disponível

---

## HRISs Suportados

### Tier 1 (Principais)

| HRIS | Mercado | Notas |
|------|---------|-------|
| **Workday** | Enterprise | Muito completo |
| **SAP SuccessFactors** | Enterprise | Grandes empresas |
| **ADP Workforce Now** | Enterprise/Mid | Popular EUA |
| **BambooHR** | PME | Muito popular |
| **Gusto** | PME/Startups | EUA |
| **Rippling** | Mid/Tech | Crescendo rápido |
| **Personio** | PME Europa | Forte na Alemanha |
| **Hibob** | Mid/Tech | Moderno |

### Tier 2 (Populares)

| HRIS | Mercado |
|------|---------|
| Deel | Remote/Global |
| Remote | Remote/Global |
| Paylocity | Mid-market |
| UKG Pro | Enterprise |
| Namely | Mid-market |
| Lattice HRIS | Tech |
| Factorial | PME Europa |
| Freshteam | PME |

### Lista Completa (80+ HRISs)

7shifts, ADP DECIDIUM, ADP Next Gen, ADP RUN, ADP Workforce Now, AllianceHCM, Altera Payroll, BambooHR, Breathe, Cezanne HR, Charlie, ChartHop, ClayHR, CoolCare, CyberArk, Darwinbox, Dayforce, Deel, Employment Hero, Factorial, Folks HR, Fourth, Freshteam, Google Workspace, Gusto, Hailey HR, Hibob, HR Cloud, HR Partner, HRWorks, Humaans, Humi, Insperity Premier, IntelliHR, IRIS Cascade, ISolved, JumpCloud, Justworks, Kallidus, Keka, Kenjo, Lano, Lattice HRIS, Leapsome, Lucca, Microsoft Entra ID, Namely, Nmbrs, Officient, Okta, OneLogin, Oracle Cloud HCM, OysterHR, PayCaptain, Paychex, Paycom, Paycor, PayFit, Paylocity, PeopleHR, Personio, PingOne, Planday, PrismHR, Proliant, Remote, Revolut People, Rippling, Sage HR, Sage People, SAP SuccessFactors, Sesame, Shapes, Simployer, Square Payroll, TriNet, UKG Pro, UKG Ready, Workday, Zelt, Zoho People

---

## Campos HRIS por Objeto

### 1. Employee (Funcionário)

| Campo | Tipo | Descrição | Uso LIA |
|-------|------|-----------|---------|
| `id` | UUID | ID Merge | Referência |
| `remote_id` | String | ID no HRIS | Sync |
| `employee_number` | String | Matrícula | Identificação |
| `first_name` | String | Nome | Display |
| `last_name` | String | Sobrenome | Display |
| `preferred_name` | String | Nome preferido | Personalização |
| `display_full_name` | String | Nome completo | Display |
| `username` | String | Username | Login |
| `work_email` | String | Email corporativo | Comunicação |
| `personal_email` | String | Email pessoal | Backup |
| `mobile_phone_number` | String | Celular | Comunicação |
| `company` | UUID | Empresa | Multi-tenant |
| `groups` | UUID[] | Grupos/Times | Organização |
| `employments` | Employment[] | Histórico de cargos | Carreira |
| `home_location` | UUID | Endereço residencial | Logística |
| `work_location` | UUID | Local de trabalho | Filtro |
| `manager` | UUID | Gestor direto | Hierarquia |
| `pay_group` | UUID | Grupo de pagamento | Payroll |
| `ssn` | String | CPF/SSN | Sensitivo |
| `gender` | Enum | Gênero | Diversidade |
| `ethnicity` | Enum | Etnia | Diversidade |
| `marital_status` | Enum | Estado civil | Benefícios |
| `date_of_birth` | DateTime | Data de nascimento | Compliance |
| `start_date` | DateTime | Data de início | Antiguidade |
| `employment_status` | Enum | ACTIVE, PENDING, INACTIVE | Filtro |
| `termination_date` | DateTime | Data de desligamento | Histórico |
| `avatar` | String | URL da foto | Display |
| `remote_created_at` | DateTime | Criado no HRIS | Timing |

**Employment Status Enum:**
- `ACTIVE` - Ativo
- `PENDING` - Pendente
- `INACTIVE` - Inativo

**Gender Enum:**
- `MALE` - Masculino
- `FEMALE` - Feminino
- `NON-BINARY` - Não-binário
- `OTHER` - Outro
- `PREFER_NOT_TO_DISCLOSE` - Prefiro não informar

---

### 2. Employment (Cargo/Posição)

| Campo | Tipo | Descrição | Uso LIA |
|-------|------|-----------|---------|
| `id` | UUID | ID Merge | Referência |
| `remote_id` | String | ID no HRIS | Sync |
| `employee` | UUID | Funcionário | Vínculo |
| `job_title` | String | Título do cargo | Display |
| `pay_rate` | Number | Salário | Confidencial |
| `pay_period` | Enum | Período (HOUR, MONTH, YEAR) | Cálculo |
| `pay_frequency` | Enum | Frequência de pagamento | Payroll |
| `pay_currency` | Enum | Moeda | Internac. |
| `pay_group` | UUID | Grupo de pagamento | Payroll |
| `flsa_status` | Enum | Status FLSA | Compliance EUA |
| `effective_date` | DateTime | Data efetiva | Histórico |
| `employment_type` | Enum | FULL_TIME, PART_TIME, CONTRACTOR | Classificação |

**Employment Type Enum:**
- `FULL_TIME` - Tempo integral
- `PART_TIME` - Meio período
- `INTERN` - Estagiário
- `CONTRACTOR` - Contratado
- `FREELANCE` - Freelancer

---

### 3. Company (Empresa)

| Campo | Tipo | Descrição | Uso LIA |
|-------|------|-----------|---------|
| `id` | UUID | ID Merge | Referência |
| `remote_id` | String | ID no HRIS | Sync |
| `legal_name` | String | Razão social | Documentos |
| `display_name` | String | Nome fantasia | Display |
| `eins` | String[] | CNPJ/EIN | Fiscal |
| `remote_created_at` | DateTime | Criada no HRIS | Timing |

---

### 4. Group (Grupos/Times)

| Campo | Tipo | Descrição | Uso LIA |
|-------|------|-----------|---------|
| `id` | UUID | ID Merge | Referência |
| `remote_id` | String | ID no HRIS | Sync |
| `name` | String | Nome do grupo | Display |
| `type` | Enum | TEAM, DEPARTMENT, COST_CENTER, etc. | Classificação |
| `parent_group` | UUID | Grupo pai | Hierarquia |

---

### 5. Location (Localização)

| Campo | Tipo | Descrição | Uso LIA |
|-------|------|-----------|---------|
| `id` | UUID | ID Merge | Referência |
| `remote_id` | String | ID no HRIS | Sync |
| `name` | String | Nome do local | Display |
| `phone_number` | String | Telefone | Contato |
| `street_1` | String | Endereço linha 1 | Logística |
| `street_2` | String | Endereço linha 2 | Logística |
| `city` | String | Cidade | Filtro |
| `state` | String | Estado | Filtro |
| `zip_code` | String | CEP | Logística |
| `country` | Enum | País | Filtro |
| `location_type` | Enum | HOME, OFFICE | Classificação |

---

### 6. Time Off (Férias/Licenças)

| Campo | Tipo | Descrição | Uso LIA |
|-------|------|-----------|---------|
| `id` | UUID | ID Merge | Referência |
| `remote_id` | String | ID no HRIS | Sync |
| `employee` | UUID | Funcionário | Vínculo |
| `approver` | UUID | Aprovador | Workflow |
| `status` | Enum | REQUESTED, APPROVED, DECLINED, CANCELLED | Status |
| `employee_note` | String | Nota do funcionário | Contexto |
| `units` | Enum | HOURS, DAYS | Unidade |
| `amount` | Number | Quantidade | Cálculo |
| `request_type` | Enum | VACATION, SICK, PERSONAL, etc. | Classificação |
| `start_time` | DateTime | Início | Período |
| `end_time` | DateTime | Fim | Período |

---

### 7. Time Off Balance (Saldo de Férias)

| Campo | Tipo | Descrição | Uso LIA |
|-------|------|-----------|---------|
| `id` | UUID | ID Merge | Referência |
| `employee` | UUID | Funcionário | Vínculo |
| `balance` | Number | Saldo disponível | Display |
| `used` | Number | Utilizado | Histórico |
| `policy_type` | Enum | Tipo de política | Classificação |

---

### 8. Payroll Run (Folha de Pagamento)

| Campo | Tipo | Descrição | Uso LIA |
|-------|------|-----------|---------|
| `id` | UUID | ID Merge | Referência |
| `remote_id` | String | ID no HRIS | Sync |
| `run_state` | Enum | PAID, DRAFT, APPROVED, etc. | Status |
| `run_type` | Enum | REGULAR, OFF_CYCLE, CORRECTION | Classificação |
| `start_date` | DateTime | Início do período | Período |
| `end_date` | DateTime | Fim do período | Período |
| `check_date` | DateTime | Data de pagamento | Pagamento |

---

### 9. Employee Payroll Run (Holerite)

| Campo | Tipo | Descrição | Uso LIA |
|-------|------|-----------|---------|
| `id` | UUID | ID Merge | Referência |
| `employee` | UUID | Funcionário | Vínculo |
| `payroll_run` | UUID | Folha vinculada | Contexto |
| `gross_pay` | Number | Salário bruto | Confidencial |
| `net_pay` | Number | Salário líquido | Confidencial |
| `start_date` | DateTime | Início do período | Período |
| `end_date` | DateTime | Fim do período | Período |
| `check_date` | DateTime | Data de pagamento | Pagamento |
| `earnings` | Earning[] | Proventos | Detalhes |
| `deductions` | Deduction[] | Descontos | Detalhes |
| `taxes` | Tax[] | Impostos | Detalhes |

---

### 10. Benefit (Benefícios)

| Campo | Tipo | Descrição | Uso LIA |
|-------|------|-----------|---------|
| `id` | UUID | ID Merge | Referência |
| `employee` | UUID | Funcionário | Vínculo |
| `provider_name` | String | Nome do provedor | Display |
| `benefit_plan_type` | String | Tipo do plano | Classificação |
| `employee_contribution` | Number | Contribuição funcionário | Financeiro |
| `company_contribution` | Number | Contribuição empresa | Financeiro |

---

### 11. Dependent (Dependentes)

| Campo | Tipo | Descrição | Uso LIA |
|-------|------|-----------|---------|
| `id` | UUID | ID Merge | Referência |
| `employee` | UUID | Funcionário | Vínculo |
| `first_name` | String | Nome | Display |
| `last_name` | String | Sobrenome | Display |
| `date_of_birth` | DateTime | Data de nascimento | Benefícios |
| `relationship` | Enum | CHILD, SPOUSE, DOMESTIC_PARTNER | Classificação |
| `gender` | Enum | Gênero | Compliance |
| `ssn` | String | CPF/SSN | Sensitivo |

---

## Operações de Escrita

### ATS - Operações Suportadas

| Operação | Endpoint | Suporte |
|----------|----------|---------|
| Criar candidato | `POST /candidates` | Greenhouse, Lever, SmartRecruiters |
| Atualizar candidato | `PATCH /candidates/{id}` | Greenhouse, Lever |
| Criar candidatura | `POST /applications` | Greenhouse, Lever, SmartRecruiters |
| **Mover stage** | `PATCH /applications/{id}` | Greenhouse, Lever, Taleo, SmartRecruiters |
| Criar entrevista | `POST /interviews` | Greenhouse, Lever |
| Criar nota/activity | `POST /activities` | Greenhouse, Lever |
| Upload attachment | `POST /attachments` | Greenhouse |
| Criar tag | `POST /tags` | Greenhouse |
| Criar usuário | `POST /users` | Greenhouse, Lever |

### HRIS - Operações Suportadas

| Operação | Endpoint | Suporte |
|----------|----------|---------|
| Criar funcionário | `POST /employees` | BambooHR, Gusto, alguns outros |
| Atualizar funcionário | `PATCH /employees/{id}` | Limitado |
| Criar time off | `POST /time-off` | Alguns HRISs |

---

## Passthrough Requests

Para acessar campos não normalizados ou fazer operações específicas do ATS:

```python
import requests

response = requests.request(
    method="POST",
    url="https://api.merge.dev/api/ats/v1/passthrough",
    headers={
        "Authorization": "Bearer {API_KEY}",
        "X-Account-Token": "{ACCOUNT_TOKEN}",
        "Content-Type": "application/json"
    },
    json={
        "method": "GET",  # ou POST, PATCH, PUT, DELETE
        "path": "/v1/scorecards/123",  # Endpoint nativo do ATS
        "data": {},  # Body para POST/PATCH
        "headers": {}  # Headers adicionais
    }
)
```

### Casos de Uso Passthrough

1. **Campos customizados**: Acessar campos que o cliente criou
2. **Scorecards detalhados**: Notas por competência (não normalizadas)
3. **Escrever campo customizado**: Salvar WSI Score no ATS
4. **Endpoints não suportados**: Funcionalidades específicas do ATS

---

## Webhooks Disponíveis

### ATS Webhooks

| Evento | Descrição |
|--------|-----------|
| `Candidate.created` | Novo candidato criado |
| `Candidate.changed` | Candidato atualizado |
| `Application.created` | Nova candidatura |
| `Application.changed` | Candidatura atualizada (inclui mudança de stage) |
| `Interview.created` | Entrevista agendada |
| `Interview.changed` | Entrevista atualizada |
| `Offer.created` | Oferta criada |
| `Offer.changed` | Oferta atualizada |
| `Job.created` | Nova vaga |
| `Job.changed` | Vaga atualizada |

### HRIS Webhooks

| Evento | Descrição |
|--------|-----------|
| `Employee.created` | Novo funcionário |
| `Employee.changed` | Funcionário atualizado |
| `Employment.created` | Nova posição/cargo |
| `Employment.changed` | Posição atualizada |
| `TimeOff.created` | Solicitação de férias |
| `TimeOff.changed` | Férias atualizadas |

### Configuração de Webhook

```json
{
  "target_url": "https://api.plataforma-lia.com/webhooks/merge",
  "is_active": true,
  "events": ["Candidate.changed", "Application.changed"]
}
```

---

## Referências

- **Documentação Merge ATS**: https://docs.merge.dev/ats/
- **Documentação Merge HRIS**: https://docs.merge.dev/hris/
- **Campos suportados ATS**: https://docs.merge.dev/integrations/ats/supported-fields/
- **Campos suportados HRIS**: https://docs.merge.dev/integrations/hris/supported-fields/
- **Postman Collection**: https://www.postman.com/mergeapi/workspace/merge-public-workspace

---

## Changelog

| Data | Versão | Alteração |
|------|--------|-----------|
| 2026-01-19 | 1.0 | Documento inicial |
