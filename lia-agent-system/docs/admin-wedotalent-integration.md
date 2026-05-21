# Admin WeDOTalent Integration Contract

**Versão do contrato:** 1.0.0
**Endpoint canonical de versão:** `GET /api/v1/admin/persona/contract-version`
**Audiência:** time WeDOTalent que vai construir `admin2.wedotalent.cc` (Anderson + equipe)
**Registrado:** 2026-05-21 (E4-prep — pós-auditoria menu Configurações × inteligência dos agentes)

---

## Visão geral

A UI em `admin2.wedotalent.cc` precisa operar **per-tenant overrides de persona LIA** (YAML cru, audit history, rollback) que NÃO devem ficar acessíveis ao cliente final. Este documento descreve a API estável que `lia-agent-system` expõe pra esse propósito, junto com as garantias que vocês podem assumir sem replicar lógica.

**Princípio canonical:** todo o trabalho de validação, audit e enforcement de invariants de compliance vive no backend `lia-agent-system`. Vocês constroem a UI consumindo a API. Não precisam tocar:

- Validação de YAML (sintaxe, schema, semver)
- Enforcement de ethics invariants (LGPD / EU AI Act anti-bias)
- Multi-tenancy (gate por JWT + role)
- Audit log canonical
- Hot-reload pós-write
- PII scan

Tudo isso já vive no backend e é garantido por sensores contract (`tests/contract/test_wedotalent_admin_gate.py`).

---

## Autenticação

Endpoints sob `/api/v1/admin/prompts/tenant-overrides/*` e `/api/v1/admin/persona/*` exigem JWT com `role = "wedotalent_admin"`. Esse role é distinto de `admin` (que é admin de UM cliente). Concessão do role:

1. Login via WorkOS SSO ou JWT issuer (mesmo flow que customer-end users).
2. Backend de autenticação deve setar `role = "wedotalent_admin"` no payload do JWT.
3. Frontend `admin2.wedotalent.cc` envia `Authorization: Bearer <jwt>` em cada request.

**403 esperado** quando:
- JWT é de role `admin` / `recruiter` / `viewer` (tenta acessar surface de staff).
- JWT expirado.
- JWT inválido.

Implementação canonical: `app/auth/dependencies.py:require_wedotalent_admin` — não copie a lógica do lado de vocês, apenas chame os endpoints.

---

## Surfaces canonical

### 1. Health-check + versão do contrato

```
GET /api/v1/admin/persona/contract-version
Authorization: Bearer <jwt-wedotalent-admin>
```

**Response 200:**
```json
{
  "contract_version": "1.0.0",
  "major": 1,
  "minor": 0,
  "patch": 0,
  "surfaces": [
    "tenant_overrides_crud",
    "ethics_invariants_validation",
    "audit_trail_per_change"
  ],
  "docs_url_relative": "docs/admin-wedotalent-integration.md"
}
```

**Uso:** chame no boot do admin UI e antes de releases. Mismatch de `major` ⇒ pare e coordene com nosso time. Mismatch de `minor` ⇒ provavelmente compatível; novas features disponíveis.

### 2. Listar tenant overrides

```
GET /api/v1/admin/prompts/tenant-overrides
```

Retorna a lista de overrides ativos para o `company_id` resolvido via JWT (uma chamada por tenant; se admin precisar ver outro tenant, repassam o JWT com o `company_id` desejado).

**Response 200:**
```json
{
  "total": 2,
  "overrides": [
    {
      "path": "shared/lia_persona",
      "version": "1.0-tenant",
      "last_updated_at": "2026-05-21T14:30:00Z",
      "size_bytes": 4892
    },
    ...
  ]
}
```

### 3. Ler 1 override

```
GET /api/v1/admin/prompts/tenant-overrides/{path}
```

Onde `{path}` é o canonical path (e.g. `shared/lia_persona`). Retorna o YAML cru.

### 4. Criar/Atualizar override

```
PUT /api/v1/admin/prompts/tenant-overrides/{path}
Content-Type: application/json
Authorization: Bearer <jwt>

{
  "content": "metadata:\n  version: \"1.0-tenant\"\n  ...\nprompts:\n  ..."
}
```

**Comportamento canonical:**

1. **YAML syntax validation** — se `yaml.safe_load` falhar ⇒ 422 com detail `code: yaml_syntax_error`.
2. **metadata.version required** — se ausente ⇒ 422 com `code: version_missing`.
3. **Ethics invariants check** — se algum anchor crítico de compliance estiver ausente do conteúdo ⇒ 422 com `code: ethics_invariant_missing` e a lista de anchors faltantes + sugestão de fix.
4. **PII scan** — match de padrões (CPF / CNPJ / email / telefone) gera **warnings** (não bloqueia). Aparecem em `validation_warnings` no response 200.
5. **Write file + invalidate cache** — escreve em disco e zera o cache do `PromptLoader` para o tenant (hot-reload <30s).
6. **Audit log** — todo PUT gera row no `audit_logs` com `action="tenant_override_put"`, `actor_user_id`, `prev_hash`, `new_hash`, `pii_warnings_count`, `version`.

**Response 200 (aceito):**
```json
{
  "success": true,
  "path": "shared/lia_persona",
  "version": "1.0-tenant",
  "last_updated_at": "2026-05-21T14:30:00Z",
  "validation_warnings": [
    "Possível EMAIL no override (2 ocorrência(s))."
  ]
}
```

**Response 422 (rejeitado por ethics invariant):**
```json
{
  "detail": {
    "code": "persona_override_rejected",
    "message": "Override rejeitado por validador canonical.",
    "errors": [
      {
        "code": "ethics_invariant_missing",
        "message": "Override remove o invariant 'Bloco Diretrizes Éticas'. Esse bloco é imutável por compliance (LGPD / EU AI Act / anti-bias). Restaure antes de persistir.",
        "fix": "Preserve a seção 'Diretrizes Éticas (inegociáveis)' do persona canonical. Você pode reformular o texto mas não pode remover a seção.",
        "anchor": "Diretrizes Éticas"
      }
    ],
    "warnings": []
  }
}
```

Time admin WeDOTalent deve **renderizar os erros direto pro staff editor** — `errors[].fix` é actionable em português.

### 5. Deletar override

```
DELETE /api/v1/admin/prompts/tenant-overrides/{path}
```

Reverte pro persona canonical da WeDOTalent (`app/prompts/shared/lia_persona.yaml`).

**Audit:** `action="tenant_override_delete"` no log.

---

## Ethics invariants — o que NÃO pode ser removido de um override

A lista canonical vive em `app/domains/persona/services/tenant_persona_validator.py:ETHICS_INVARIANTS` e contém âncoras textuais que **devem aparecer em qualquer YAML aceito**. Cada anchor é uma frase ou termo curto referente a compliance obrigatório.

**Lista atual (versão 1.0.0):**

| Anchor | Bloco | Por que é imutável |
|---|---|---|
| `Diretrizes Éticas` | Seção "Diretrizes Éticas (inegociáveis)" | LGPD Art. 6º + EU AI Act anti-bias |
| `IGNORE COMPLETAMENTE` | Lista de fatores proibidos (nome, idade, foto, etc.) | Anti-discriminação CLT + LGPD |
| `Linguagem inclusiva` | Diretriz de linguagem neutra | Princípio de igualdade |
| `Transparência` | Bloco de registro de pareceres + critérios | EU AI Act Art. 13 (transparência) |

Se produto decidir mudar essa lista, é commit reviewable em `tenant_persona_validator.py` — **não é configuração de runtime**. Trade-off explícito: aceita reformulação superficial do texto, bloqueia remoção semântica.

---

## Audit trail

Toda mutação de override gera row em `audit_logs` com:

- `company_id` — tenant alvo
- `agent_name` — sempre `"admin_prompts"`
- `decision_type` — sempre `"admin_config_change"`
- `action` — `"tenant_override_put"` ou `"tenant_override_delete"`
- `actor_user_id` — id do staff WeDOTalent que fez a operação
- `reasoning[]` — array com `path=...`, `version=...`, `prev_hash=...`, `new_hash=...`, `pii_warnings=...`
- `criteria_used[]` — sempre `["yaml_syntax", "metadata_version", "ethics_invariants", "pii_scan"]`
- `human_review_required` — sempre `False` (mudanças WeDOTalent staff são autoritarivas)

**Como consumir o audit do lado admin:** endpoint dedicado de leitura ainda não existe (deferred para versão MINOR seguinte). Por enquanto, consultem via DB direto ou via `AuditService.list_by_action`.

---

## Webhook opcional (futuro)

Versão 1.x (planejada): backend dispara webhook outbound quando override muda — payload `{tenant_id, path, prev_hash, new_hash, actor}` para vocês fazerem post-actions (notificar CS, sync CRM). Endpoint de cadastro do webhook ainda não publicado; quando estiver, esse documento será atualizado + `contract-version` major bumpa pra 2.0.

---

## Sensores que protegem este contrato

Lista canonical em `lia-agent-system/tests/contract/`:

- `test_wedotalent_admin_gate.py` — gate role; 9 testes
- `test_tenant_persona_validator.py` — ethics invariants + YAML/version validation
- `test_admin_persona_contract.py` — `contract-version` endpoint estável

CI bloqueia merge se qualquer um desses falhar.

---

## FAQ

**P: Nosso admin pode listar overrides de TODOS os tenants de uma vez?**
R: Não diretamente nesta versão — cada GET é escopado ao `company_id` do JWT. Para varrer múltiplos tenants, fazer N requests com JWTs apropriados (idealmente via um service account WeDOTalent-staff que pode emitir tokens per-tenant).

**P: Se editarmos o YAML cru via SSH no servidor, isso passa pelo audit?**
R: NÃO. Audit log só dispara via API. Edição direta em disco é fora-do-contrato e quebra trilha de SOX/LGPD. Mantenham todo write via PUT.

**P: O cliente final pode acidentalmente disparar PUT?**
R: Não — `require_wedotalent_admin` retorna 403 pra qualquer role customer-end. Sensor `test_wedotalent_admin_gate.py` pin isso.

**P: O que acontece se a UI cliente tentar fazer GET via DevTools sniffing?**
R: O backend rejeita com 403. O front esconder a tab é defense-in-depth (UX), não segurança — o gate real está no backend.

---

## Contato

Mudanças neste contrato exigem PR no `lia-agent-system` com bump apropriado de `ADMIN_PERSONA_CONTRACT_VERSION` em `app/api/v1/admin_persona.py`. Coordenação prévia com time admin WeDOTalent é boa prática para qualquer bump MAJOR.

Document maintainer: equipe `lia-agent-system` (Paulo + time).
