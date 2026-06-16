# Build-Spec — Granularidade de Visibilidade de PII por Papel/Usuário (instrução técnica auto-contida)

> **Para uma sessão NOVA executar do zero.** Objetivo: poder marcar, por **papel** (gerente/gestor-da-vaga/recrutador) e/ou por **usuário específico**, quais campos sensíveis (CPF, email, telefone, endereço, remuneração) cada um **pode ou não ver** — configurável na tela de cadastro de usuário, aplicado em TODAS as superfícies, auditável (LGPD).
> Escrito 2026-06-06. Fonte da verdade: Replit `ssh replit-wedo-0405` → `/home/runner/workspace/` (`lia-agent-system/` backend, `plataforma-lia/` frontend), branch `feat/benefits-prv-canonical`.

---

## 0. CONSTRAINTS (CLAUDE.md — ler ANTES)
- Replit é a única fonte; sem `git push`/`gh`; commit atômico `git commit -- <paths>` (nunca `git add .`); branch `feat/benefits-prv-canonical`.
- TDD Red→Green + sensor por mudança. Multi-tenancy: `company_id` do JWT. LGPD: minimização + auditabilidade. Computacional > inferencial.
- Frontend: hooks no topo, design tokens, i18n next-intl (key em pt-BR.json E en.json). Editar via heredoc `<<'PYEOF'`/sed (rg corrompe tokens; Python longo dropa SSH).

## 1. OBJETIVO
Matriz de visibilidade: `{papel|usuário → {campo_PII → ver|ocultar}}`. Default por papel (company-level) + override por usuário (tela de cadastro). Aplicada em TODA superfície que mostra PII (chat, API de candidato, funil, kanban, perfil, exports). Mascaramento é opt-in (default = ver, decisão Paulo 2026-06-06: recrutador vê por padrão).

## 2. ESTADO ATUAL (verificado 2026-06-06)
### 2.1 Papéis (`ClientUserRole` em `libs/models/lia_models/client_user.py`)
- `admin` (Administrador — acesso total), `manager` (Gerente — "gerenciar vagas e equipe" = o "recruiting manager/gestor"), `recruiter` (Recrutador). + `wedotalent_admin` (staff).
- **Gestor DA VAGA específico:** `job_vacancies.manager` / `manager_email` (o gestor atribuído àquela vaga). `recruiter`/`recruiter_email` = o recrutador. → dá pra mirar por PAPEL (todo manager) OU pelo gestor específico de uma vaga.
- **Hook de config JÁ EXISTE:** `client_users` tem `role` + **`permissions`** (campo). É o lugar natural pro override por usuário.

### 2.2 Campos PII do candidato (`candidates`)
`cpf`, `email`, `secondary_email`, `phone`, `mobile_phone`, `secondary_phone`, `date_of_birth`, `address_street`, `address_number`, `address_district`, `address_zip`, `address_complement`, **`current_salary`, `salary_currency`, `desired_salary_min`** (salário DO CANDIDATO). 
> Vaga tem `salary` / `salary_range` (remuneração DA VAGA — conceito diferente, ver §3).

### 2.3 O que o masking detecta hoje (`app/shared/pii_masking.py`)
- Regex (determinístico): **CPF** (`CPF_PATTERN`→`***CPF***`), **email** (`EMAIL_PATTERN`), **telefone** (`PHONE_BR_PATTERN`), **RG** (`_RG_PATTERN`), **CNPJ** (`_CNPJ_PATTERN`).
- Presidio (NER, opt-in `LLM_PROMPT_PRESIDIO_ENABLED`): **PERSON** (nome), **LOCATION** (endereço/cidade) — inferencial, pode errar.
- **NÃO existe:** masking de **salário/remuneração** (nem candidato nem vaga). **Endereço** só via Presidio (sem regex). **date_of_birth** não mascarado.

### 2.4 Mecanismos que já existem (mas NÃO são granularidade-por-campo-por-papel)
- `mask_pii_outbound(text)` (pii_masking.py, criado 2026-06-06) — saída do chat do recrutador; HOJE é flag GLOBAL (`LIA_RECRUITER_CHAT_MASK_PII`), default preserva. **É o HOOK pra plugar a matriz.**
- `_filter_candidates_by_dept_scope` (candidates_crud.py) — scoping de QUAIS CANDIDATOS o manager vê (hierarquia). Controla RECORDS, **não CAMPOS**. (Complementar, não substitui.)
- `client_users.permissions` — campo existente, subutilizado; hospeda o override por usuário.

### 2.5 GAP central
**NÃO existe** field-level PII-visibility por papel/usuário. `mask_pii_outbound` é global. A PII é servida crua em TODAS as superfícies (API de candidato, funil, etc.) — esconder só no chat NÃO basta.

## 3. DISTINÇÃO IMPORTANTE — 2 classes de dado
1. **PII do candidato** (cpf, emails, phones, date_of_birth, endereço, salário-do-candidato): mascarável via masking de candidato (`mask_pii_outbound` + serialização da API de candidato).
2. **Remuneração DA VAGA** (`job_vacancies.salary`/`salary_range`): NÃO é PII de candidato — é dado da vaga/oferta. Esconder do gestor é gatear ESSE campo por papel na serialização da vaga (mecanismo separado).
> A matriz deve cobrir AMBOS, mas a aplicação difere (candidate-serialization vs vacancy-serialization).

## 4. TARGET (definição de PRONTO)
1. Matriz `{role|user_id → {campo → ver|ocultar}}` persistida (company default por papel + override por usuário).
2. Aplicada em TODAS as superfícies (§7), não só no chat.
3. Campos cobertos: cpf, email(s), telefone(s), endereço, date_of_birth, salário-do-candidato, salário-da-vaga.
4. Default = ver (decisão Paulo); ocultar é opt-in por config.
5. Determinístico (regex/field-level), não inferencial onde possível. Endereço/nome via Presidio só como complemento.
6. Auditável: toda ocultação/decisão logada (LGPD). Multi-tenancy: company-scoped.

## 5. PLANO DE IMPLEMENTAÇÃO (fases — cada uma TDD + commit atômico)
### Fase A — Modelo de config (a matriz)
- **Defaults por papel (company-level):** novo campo JSONB em `company_hiring_policy` ou `admin_settings` (ex: `pii_visibility_defaults = {manager: {cpf: hide, salary: hide, ...}, recruiter: {...}}`). Migration alembic (verificar próximo número: `ls lia-agent-system/alembic/versions/ | grep -oE '^[0-9]+' | sort -un | tail -3`).
- **Override por usuário:** usar `client_users.permissions` (JSONB existente) — chave `pii_visibility = {cpf: hide, ...}`.
- **Resolução:** efetivo = override do usuário ⟶ default do papel ⟶ "ver" (fail-open pro recrutador, decisão Paulo).
- **UI:** tela de cadastro/edição de usuário (plataforma-lia, settings/usuários) — toggles por campo. i18n + design tokens.
- Sensor: teste da resolução (user override > role default > ver).

### Fase B — Enforcement no CHAT (já tem o hook)
- `mask_pii_outbound(text, user_id=...)` (pii_masking.py): trocar a flag global por: lê a matriz efetiva do `user_id` (o SSE/WS já têm user_id) → mascara campo a campo. Para mascarar SÓ os campos marcados, precisa de masking POR CAMPO (não tudo-ou-nada): aplicar só os patterns dos campos "ocultar".
- **Adicionar patterns que faltam:** salário (R$/número + `current_salary`/`desired_salary`/`salary_range`), endereço (regex de CEP/logradouro + Presidio LOCATION), date_of_birth.
- Sensor: dado um user com `{cpf: hide, email: show}`, a saída mascara CPF mas mantém email.

### Fase C — Enforcement nas OUTRAS superfícies (o ponto CRÍTICO)
A PII vaza na TELA se só o chat for tratado. Aplicar a matriz na SERIALIZAÇÃO da API de candidato (o produtor único):
- `app/api/v1/candidates/candidates_crud.py` (list + get), `candidates_metadata.py` — onde o candidato é serializado pro FE. Criar um helper canônico `apply_pii_visibility(candidate_dict, current_user)` que zera/mascara os campos "ocultar" ANTES de retornar. (Produtor único — não no FE, senão drift.)
- Exports (CSV/Excel de candidatos) — mesmo helper.
- Sensor: contract test — GET /candidates com user role=manager + matriz {cpf: hide} → resposta sem cpf.

### Fase D — Remuneração (candidato + vaga)
- Candidato (`current_salary`/`desired_salary`): via o helper da Fase C (campo do candidato).
- Vaga (`salary`/`salary_range`): gatear na serialização da VAGA (`app/api/v1/job_vacancies/`) por papel — mecanismo separado (não é candidate-PII).

### Fase E — Auditoria + LGPD
- Log de cada ocultação (AuditService) + o trail de QUEM configurou a matriz. Citar base legal (minimização Art. 6 III, finalidade Art. 6 I).

## 6. CAMPOS × COMO MASCARAR
| Campo | Hoje | Ação |
|---|---|---|
| CPF | regex ✅ | reusar |
| Email(s) | regex ✅ | reusar (cobrir secondary_email) |
| Telefone(s) | regex ✅ | reusar (mobile/secondary) |
| RG/CNPJ | regex ✅ | reusar |
| Endereço | só Presidio 🟡 | adicionar field-level (os campos address_* são estruturados → fácil zerar na serialização; regex de CEP no texto) |
| date_of_birth | ❌ | field-level (zerar na serialização) |
| Salário candidato | ❌ | field-level (current_salary/desired_salary) |
| Salário vaga | ❌ | gate na serialização da vaga (Fase D) |
| Nome | só Presidio 🟡 | em geral o recrutador VÊ nome (decisão Paulo); ocultar nome é raro |

## 7. SUPERFÍCIES ONDE APLICAR (exaustivo — senão vaza)
- Chat (SSE `agent_chat_sse.py` + WS `agent_chat_ws.py`) → `mask_pii_outbound` (Fase B).
- API de candidato: `candidates_crud.py` (list/get), `candidates_metadata.py` → helper `apply_pii_visibility` (Fase C).
- Funil/kanban (consomem a API de candidato → herdam o helper).
- Perfil de candidato (modal/página) → herda a API.
- Exports (CSV/Excel) → o helper.
- API de vaga (`job_vacancies/`) → gate salário (Fase D).
- Discovery: `grep -rln "cpf\|current_salary\|address_" plataforma-lia/src | head` pra achar surfaces do FE que renderizam PII direto (devem só consumir a API tratada, não ter cópia).

## 8. TESTES/SENSORES
1. Resolução da matriz (user > role > ver).
2. mask_pii_outbound por campo (oculta só os marcados).
3. Contract: GET /candidates por papel respeita a matriz (sem cpf quando hide).
4. Serialização da vaga oculta salary quando o papel não pode.
5. Multi-tenancy: matriz é company-scoped.
6. Audit: ocultação logada.

## 9. ARQUIVOS-CHAVE
- `app/shared/pii_masking.py` — patterns + `mask_pii_outbound` (hook).
- `app/api/v1/candidates/candidates_crud.py` + `candidates_metadata.py` — serialização (Fase C).
- `app/api/v1/job_vacancies/` — serialização da vaga (salário, Fase D).
- `libs/models/lia_models/client_user.py` — `role` + `permissions` (override por usuário).
- `libs/models/lia_models/company_hiring_policy.py` / `admin_settings.py` — defaults por papel (company).
- `app/api/v1/agent_chat_sse.py` / `agent_chat_ws.py` — chat (passa user_id ao masking).
- FE: tela de cadastro/edição de usuário (toggles) — `plataforma-lia/src/components/settings/` (achar a tela de usuários).

## 10. DISCOVERY COMMANDS
```
# campos PII do candidato:
psql "$DATABASE_URL" -tA -c "SELECT column_name FROM information_schema.columns WHERE table_name='candidates';"
# papéis + permissions:
sed -n '1,60p' lia-agent-system/libs/models/lia_models/client_user.py
# patterns de PII atuais:
grep -nE "_PATTERN|PII_PATTERNS|_PRESIDIO_ENTITIES" lia-agent-system/app/shared/pii_masking.py
# onde a API serializa candidato:
grep -rln "cpf\|mobile_phone\|current_salary" lia-agent-system/app/api/v1/candidates/
# próximo número de migration:
ls lia-agent-system/alembic/versions/ | grep -oE '^[0-9]+' | sort -un | tail -3
```

## 11. DECISÕES ABERTAS (Paulo)
1. **Default por papel:** o que cada papel vê por padrão? (Recomendo: recrutador vê tudo; gerente/gestor — você define; admin tudo.)
2. **Por-papel vs por-usuário:** começar só por papel (mais simples) ou já com override por usuário? (`client_users.permissions` suporta os dois.)
3. **Salário do candidato** (current/desired) — ocultar de quem? E o **salário da vaga** — quem não pode ver?
4. **Nome:** alguém deve NÃO ver o nome? (raro; afeta identificação.)
5. **Escopo de superfícies:** todas de uma vez, ou chat + API de candidato primeiro (e funil/kanban herdam)?
6. **Interação com dept-scope** (visibilidade de RECORDS) — a matriz é ortogonal (campos), mas decidir se um papel sem acesso a um campo ainda vê o record.

---
**Resumo:** Fase A (modelo de config: defaults por papel + override por usuário em `client_users.permissions` + UI) → Fase B (chat: `mask_pii_outbound` lê a matriz + add patterns salário/endereço/dob) → Fase C (API de candidato: helper `apply_pii_visibility` no produtor único — o ponto crítico) → Fase D (salário candidato + vaga) → Fase E (audit/LGPD). TDD + commit atômico, sem push. Default = ver (decisão Paulo); ocultar é opt-in.
