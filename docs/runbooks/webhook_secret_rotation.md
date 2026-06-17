# Runbook — Webhook Secret Rotation (per-tenant)

> **Task #1146** — Multi-tenant Ownership · Webhook ownership validators
> **Owner:** Plataforma / Security · **Severity on miss:** SEV-1
> **Related:** [`tenant-context-history.md`](../architecture/tenant-context-history.md), [`operational-flags.md`](./operational-flags.md), `lia-agent-system/app/shared/security/webhook_ownership.py`

## Why this runbook exists

Até a Task #1146 os 6 webhooks externos (Teams, OpenMic, Merge, Twilio,
WhatsApp, Mailgun) validavam HMAC com **uma única secret global por
provedor**. Quem comprometesse a secret podia acionar qualquer tenant — e
quem conhecesse o formato do payload podia forjar `X-Company-ID` / `metadata.
company_id` e mover candidatos de outra empresa.

A task entregou:

- Tabela `company_webhook_secrets` (migration `131_company_webhook_secrets`),
  com RLS, encriptação Fernet (mesma key de `REDIS_ENCRYPTION_KEY`) e estados
  `active | rotating | revoked`.
- Helper canônico `app.shared.security.webhook_ownership.verify_webhook_owner`
  que (a) tenta a secret per-tenant, (b) faz dual-validate com a secret global
  durante 90d, (c) cross-checa `candidate_id` / `job_id` contra o tenant
  resolvido (RLS), (d) grava 1 linha em `audit_logs`
  (`action=webhook_ownership_verified`), (e) incrementa
  `lia_webhook_ownership_outcome_total{provider,outcome}`, (f) emite log
  com fingerprint `WEBHOOK_OWNERSHIP_MISMATCH` no Sentry.
- Suíte red-team `tests/security/test_webhook_ownership_crossvalidation.py`
  (4 cenários × 6 webhooks = 24 testes).

Este runbook explica o **rollout faseado de 90 dias** que clientes precisam
seguir para re-emitir secrets nos provedores externos sem derrubar webhooks.

## Timeline canônica

| Marco | Quando | O que acontece |
|---|---|---|
| **D+0** | Deploy da migration 131 | `verify_webhook_owner(dual_validate=True)` ativo. Aceita secret per-tenant **OU** global. Nenhum cliente impactado. Métrica `lia_webhook_ownership_outcome_total{outcome=ok,secret_source=global}` deve cobrir 100% do tráfego. |
| **D−30** | 60 dias antes do cutoff | E-mail #1 + banner in-app no painel admin do tenant: "Gere sua secret per-tenant em `Configurações → Integrações → Webhooks`". Audit log filtrado por `secret_source=global` alimenta o relatório de adoção. |
| **D−15** | | E-mail #2 (lembrete). Suporte recebe playbook de FAQ (ver §5). |
| **D−7**  | | E-mail #3 (urgência) + alerta amarelo no painel admin. Listar nome + e-mail do owner técnico do tenant no e-mail. |
| **D−1**  | | E-mail #4 (último aviso) + alerta vermelho no painel admin. |
| **D+90** | Flip global-off | Deploy que vira `dual_validate=False` por default (`LIA_WEBHOOK_DUAL_VALIDATE=off`). Webhooks de tenants que NÃO emitiram secret per-tenant passam a falhar com `403 signature_invalid`. Métrica de canary: `outcome=signature_invalid` jumps. |
| **D+97** | Remoção do código | Após uma semana estável sem regressão, abrir PR removendo o branch `dual_validate=True` do helper, removendo os `_GLOBAL_SECRET_ENV` e arquivando as env vars globais (`TEAMS_WEBHOOK_SECRET`, `MERGE_WEBHOOK_SECRET`, ...). |

## 1. Pre-flight checklist (antes do deploy D+0)

1. **Migration 131** aplicada em prod (`alembic upgrade head`).
2. `REDIS_ENCRYPTION_KEY` configurado em prod (a mesma key encripta a secret
   per-tenant — sem a key, o helper grava em plaintext e loga warning).
3. Endpoint Admin `POST /api/v1/admin/webhook-secrets/{provider}/rotate`
   ativo (recebe `secret` no body, criptografa, faz `UPSERT` na
   `company_webhook_secrets` com `status='active'`).
4. Banner in-app + página de docs publicados.
5. Métrica `lia_webhook_ownership_outcome_total` registrada no
   Prometheus + dashboard no Grafana com 6 painéis (1 por provedor).
6. Sentry alert: fingerprint `WEBHOOK_OWNERSHIP_MISMATCH` com severity-1
   ligado ao PagerDuty rotation.

## 2. Templates de e-mail (CS)

### D−30 — Aviso de mudança

> **Assunto:** Ação necessária — Nova secret de webhook para [Provider] (90 dias)
>
> Olá [Owner Técnico],
>
> Para fortalecer a segurança multi-tenant da Plataforma LIA, estamos
> migrando os webhooks de **[Provider]** para uma secret HMAC dedicada por
> empresa. Até **[DATA D+90]** todos os webhooks da sua conta precisam
> usar a nova secret.
>
> **O que fazer:**
> 1. Acesse `Configurações → Integrações → Webhooks` no painel da LIA.
> 2. Clique em "Gerar nova secret" para [Provider]. Copie o valor exibido
>    (só será mostrado uma vez).
> 3. Cole essa secret no painel do [Provider] (ver doc anexa) e salve.
> 4. Confirme em até 7 dias que webhooks continuam sendo entregues
>    (status `200` no painel da LIA).
>
> Após **[DATA D+90]**, webhooks assinados com a secret antiga (global)
> serão rejeitados com `HTTP 403`.
>
> Equipe Plataforma LIA

### D−15 / D−7 / D−1

Iguais ao D−30 com escalada de urgência no assunto:
- D−15: "Lembrete · 45 dias restantes"
- D−7:  "Urgente · 7 dias restantes — sua integração [Provider] pode parar"
- D−1:  "Último aviso · Amanhã webhooks com a secret antiga serão rejeitados"

## 3. Banner in-app

Renderizado no painel admin (`/configuracoes/integracoes/webhooks`) sempre que
o tenant ainda **não** tem linha `active` em `company_webhook_secrets` para
algum provedor onde já consumiu webhook nos últimos 30 dias:

> ⚠️ **Ação necessária:** sua conta ainda usa a secret global de webhook do
> [Provider]. A partir de [DATA D+90] essa secret será descontinuada. Clique
> aqui para gerar a nova secret dedicada.

Cor do banner:
- D−30 → D−8: amarelo (`bg-amber-100`)
- D−7  → D−1: vermelho (`bg-red-100`)
- D+0  →     : vermelho + bloqueio do botão "Salvar configurações" até o
  cliente concluir a rotação.

## 4. Script de suporte — "Meu webhook parou de funcionar"

1. Confirmar provider + tenant id afetado.
2. Verificar `lia_webhook_ownership_outcome_total{provider=..., outcome=signature_invalid, company_id=...}` no dashboard
   (filtrar últimos 15min). Se contador subiu → confirma que é rotação.
3. Conferir `audit_logs` filtrando `action='webhook_ownership_verified'` +
   `company_id=...` (últimas 50 linhas):
   - `decision=signature_invalid` + `secret_source=tenant` → cliente rotacionou
     a secret em só um dos lados (LIA ou provedor); pedir para gerar nova
     secret e propagar pros dois.
   - `decision=signature_invalid` + `secret_source=global` (pós D+90) →
     cliente ainda não migrou; passo-a-passo do banner.
   - `decision=owner_mismatch` → payload referencia candidato/vaga de outro
     tenant: ESCALAR para security (possível tentativa de cross-tenant).
4. Se cliente precisa de janela emergencial, **NÃO ligar
   `LIA_ALLOW_NON_COMPLIANT_AGENTS`** (essa flag é p/ agentes, não webhooks).
   Use o endpoint admin `POST /api/v1/admin/webhook-secrets/{provider}/rotate`
   para gravar a secret antiga como nova entrada `active` da tabela (preserva
   ownership cross-check e re-estabelece a integração imediatamente).

## 5. Compromise / chave vazada

Se uma secret vazou:

1. Setar `status='revoked'` da linha em `company_webhook_secrets`
   (`UPDATE company_webhook_secrets SET status='revoked', rotated_at=now()
   WHERE company_id=$1 AND provider=$2`).
2. Forçar geração de nova secret (script CS abre o endpoint admin).
3. Auditar últimos 30d em `audit_logs WHERE action='webhook_ownership_verified'
   AND company_id=$1 AND secret_source='tenant'` — qualquer outcome `ok`
   posterior ao incidente precisa ser investigado.
4. Se o compromisso for da secret global (pré-D+90), abrir incidente SEV-1 e
   antecipar o flip `dual_validate=False` para o tenant afetado via override
   por empresa.

## 6. Sentinels e validações automáticas

- `tests/security/test_webhook_ownership_crossvalidation.py` (24 cenários)
  é gating de CI — qualquer PR que quebre o contrato bloqueia merge.
- Canary diário: alerta se `sum(rate(lia_webhook_ownership_outcome_total
  {outcome=~"signature_invalid|owner_mismatch"}[15m])) > 0.05` em qualquer
  provedor.
- Eval gate sugerido (Task downstream "Sealing"):
  `eval/golden/webhook_ownership_no_cross_tenant.jsonl` cobrindo 6 cenários
  (1 por provedor) provando que `owner_mismatch` nunca retorna `ok`.

## 7. Pós-D+97 — limpeza definitiva

Quando o flip global-off completar uma semana sem regressão:

1. Remover `_GLOBAL_SECRET_ENV` de `webhook_ownership.py`.
2. Remover branch `dual_validate=True` do helper (deixar default `False`).
3. Arquivar env vars globais nas secrets do Replit Deploy.
4. Atualizar `tenant-context-history.md` adicionando §T-G "Webhook
   ownership selado" referenciando este runbook.
