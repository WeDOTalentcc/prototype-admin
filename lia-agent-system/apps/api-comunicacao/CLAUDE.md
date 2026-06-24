# CLAUDE.md — api-comunicacao

Micro-app de comunicação outbound da LIA.
Domínio: Email, WhatsApp, Voz, Multi-canal, Digest, Notificações, Alertas.
Porta padrão: `8004`.

## Regra Auth — OBRIGATÓRIA em todos os novos endpoints

Todo endpoint **novo** neste sub-app DEVE usar `get_auth_context_dependency`:

```python
from app.shared.auth.auth_provider import AuthContext, get_auth_context_dependency

@router.get("/endpoint")
async def meu_endpoint(auth: AuthContext = Depends(get_auth_context_dependency())):
    company_id = auth.company_id
```

**PROIBIDO** em novos endpoints: `get_current_active_user`, `get_current_user`

**Endpoints legados existentes são PERM-EXEMPT** — NÃO reescrever em massa.

## LGPD — Outbound communication

Todo envio outbound (email/WhatsApp/voz) DEVE verificar consentimento via
`ConsentCheckerService` antes de disparar. Regra ADR-LGPD-001 aplicável.

CONSENT_QUESTION em plugins de voz é HARDCODED — nunca parametrizar com ai_name
(ver seção "Voice plugins — LGPD wording canonical" no CLAUDE.md raiz).

## Domínio

Rotas: email, WhatsApp, voz, multi-canal, digest, notificações, alertas.
Scaling: alto volume, async-heavy, deps externas (Twilio, Mailgun, WhatsApp API).

## Rotas incluídas

| Módulo | Tags | Notas |
|---|---|---|
| `communication` | communication | geral outbound |
| `communications` | communications | histórico/listagem |
| `communication_settings` | communication_settings | config por tenant |
| `communication_matrix` | communication_matrix | matriz de canais |
| `communication_optout` | communication_optout | LGPD opt-out |
| `email` | email | envio email |
| `email_templates` | email_templates | templates |
| `email_tracking` | email_tracking | opens/clicks |
| `whatsapp` | whatsapp | envio WhatsApp |
| `whatsapp_webhook` | whatsapp_webhook | webhook inbound |
| `voice` | voice | voz genérica |
| `lia_voice` | lia_voice | plugin LIA voz |
| `twilio_voice` | twilio_voice | Twilio provider |
| `gemini_voice` | gemini_voice | Gemini Live provider |
| `voice_stream` | voice_stream | streaming áudio |
| `voice_screening` | voice_screening | triagem por voz |
| `multi_channel` | multi_channel | roteamento multi-canal |
| `digest` | digest | digest recorrente |
| `digest_schedule` | digest_schedule | agendamento digest |
| `notifications` | notifications | notificações push/in-app |
| `alerts` | alerts | alertas de pipeline |
| `alert_rule_templates` | alert_rule_templates | templates de regras |
| `conversations` | conversations | histórico conversas |
| `mailgun_webhooks` | mailgun_webhooks | webhook Mailgun |
| `openmic_webhook` | openmic_webhook | webhook OpenMic |
