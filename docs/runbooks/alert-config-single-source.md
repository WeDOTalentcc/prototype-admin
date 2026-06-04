# Alertas proativos — fonte-única-da-verdade de config (Task #1295)

## Resumo

O que o recrutador configura em **Configurações → Comunicação & Alertas**
(liga/desliga, threshold, canais) agora **governa de verdade** os alertas
proativos. Antes, cada gerador decidia sozinho: o `ProactiveDetectorService`
sobrepunha um gate quebrado de `communication_settings` e o `MonitoringLoop`
usava constantes hardcoded e canais fixos `["bell","chat"]`, ignorando o tenant.

## Canônico

`AlertPreference` (tabela `alert_preferences`, escrita pela tela via
`POST /alerts/preferences`) é a **única** fonte de verdade para
enable/threshold/cooldown/canais de alerta. O leitor canônico é
`app/shared/services/alert_config_resolver.py`:

- `resolve_alert_config(db, company_id, alert_type) -> AlertConfigResolution`
  — lê `AlertPreference`; sem row cai no default canônico (`source="default"`);
  erro de DB é **fail-loud** (`source="error"`, WARNING/metric), nunca mascara
  config existente como ausente.
- `ALERT_CONFIG_DEFAULTS` — registro **único** de defaults, espelha 1-1 o
  catálogo da UI (`DEFAULT_ALERT_PREFERENCES` em `app/api/v1/alerts.py`). Tanto
  o detector (`_DEFAULT_TENANT_OVERRIDE` via `_build_default_tenant_overrides`)
  quanto o `MonitoringLoop` derivam daqui.
- `channels_to_list(dict) -> list[str]` — converte o dict canônico
  `{email,bell,teams,whatsapp}` em lista ordenada para os dispatchers.

`communication_settings` mantém SÓ seu papel real (janela de envio / assinatura
/ cooldown LGPD), **nunca** o enable/canal dos alertas.

## Matriz de alinhamento (regra ↔ detector ↔ alert_type ↔ default)

| Regra (UI) | Gerador | detector.name | alert_type | enable/threshold/cooldown default | canais default |
|---|---|---|---|---|---|
| Perfil da Empresa Incompleto | detector | `company_profile_completion` | `company_profile_incomplete` | on / 80% / 168h | bell |
| Solicitação LGPD Vencendo | detector | `dsr_overdue` | `dsr_overdue` | on / 24h / 12h | email, bell |
| Candidato Sem Interação | detector | `candidate_stale` | `candidate_no_interaction` | on / 5d / 24h | email, bell |
| Plano de Workforce Desatualizado | detector | `workforce_plan_stale` | `workforce_plan_stale` | on / 30d / 336h | bell |
| Créditos IA Baixos | detector | `ai_credits_low` | `credits_low` | on / 20% / 12h | email, bell, teams |
| Candidatos Estagnados | detector | `pipeline_stuck` | `candidates_stagnant` | on / 10 / 48h | email, bell |
| SLA Próximo do Vencimento | detector + MonitoringLoop `_check_sla_risks` | `sla_near_expiration` | `sla_near_expiration` | on / 80% / 12h | email, bell, teams |
| Taxa de Conversão Baixa | detector | `conversion_rate_low` | `conversion_rate_low` | on / 2% / 48h | email, bell |
| Entrevista Não Confirmada | detector | `interview_not_confirmed` | `interview_not_confirmed` | on / 24h / 12h | email, bell, teams, whatsapp |
| Feedback Pendente | detector | `feedback_pending` | `feedback_pending` | **off** / 48h / 24h | email, bell |
| Proposta Sem Resposta | detector | `offers_pending_long` | `offers_pending_long` | on / 72h / 24h | email, bell, teams, whatsapp |
| Tarefas Atrasadas | detector | `tasks_overdue` | `tasks_overdue` | on / 5 (contagem) / 8h | email, bell, teams |
| Entrega de Email Baixa | detector | `email_delivery_low` | `email_delivery_low` | on / 80% / 24h | bell |
| Candidato Ideal Encontrado | detector | `ideal_candidate_found` | `ideal_candidate_found` | on / 90% / 0h | email, bell, teams, whatsapp |
| Falha de Sincronização ATS | detector | `ats_sync_failed` | `ats_sync_failed` | on / 3 (contagem) / 2h | email, bell, teams |
| Candidato Sem Interação | MonitoringLoop `_check_stale_candidates` | — | `candidate_no_interaction` | on / 5d / 24h | email, bell |

> **Cobertura 15/15 (Task #1296):** todas as 15 regras do catálogo da UI têm
> gerador real. As 9 antes órfãs ganharam detector canônico em
> `proactive_detector_service.py` (ver `_DETECTOR_ALERT_TYPE_MAP`). O sentinel
> `test_catalog_alert_types_have_generator` trava o reaparecimento de qualquer
> ghost setting.

**Notas de semântica:**
- `conversion_rate_low`: conversão = `hired / total` de `VacancyCandidate` na
  janela de 90 dias; exige amostra mínima (≥20) para não alertar em funil vazio.
- `sla_near_expiration` (detector): vinculação preditiva — o SLA vem de
  `RecruitmentStage.sla_hours` (config real por etapa/tenant, **não** constante);
  alerta candidatos entre `threshold%` e 100% do prazo na etapa atual.
- `interview_not_confirmed`: `Interview.confirmation_status=='pending'` com
  `start_time` nas próximas `threshold` horas.
- `feedback_pending`: entrevistas com `end_time` há `threshold`+ horas, sem
  `InterviewFeedback` e com `feedback` JSON vazio (default **off** espelha a UI).
- `offers_pending_long`: `OfferProposal.sent_at` há `threshold`+ horas sem
  `accepted_at`/`declined_at`.
- `tasks_overdue`: threshold é **contagem mínima** de tarefas atrasadas
  (`due_date < now` & status `PENDING`), não dias — evita 1 alerta por tarefa.
- `email_delivery_low`: taxa `(sent+delivered)/processados` de `MessageQueue`
  (`channel='email'`) na janela de 7 dias; exige amostra mínima (≥10).
- `ideal_candidate_found`: `VacancyCandidate.match_percentage >= threshold` em
  candidatos ativos atualizados nos últimos 7 dias.
- `ats_sync_failed`: `ATSSyncJob.status==FAILED` na janela de 24h, escopado por
  `company_id` via join em `ATSConnection` (o job não tem `company_id` direto);
  threshold é contagem mínima de falhas.
- `ai_credits_low` (vinculação preditiva): além do gate de saldo, projeta a
  **data de esgotamento** a partir do burn rate de `AiConsumption` (14 dias);
  fail-defensive — sem histórico, o hint segue sem forecast (nunca inventa data).
- `MonitoringLoop._check_sla_risks` honra **enable + canais** de
  `sla_near_expiration`. O threshold de **%** do SLA da UI não se aplica ao
  cálculo por **dias** desse check (semântica distinta — fora de escopo).
- `MonitoringLoop._check_stale_candidates` honra **enable + threshold (dias) +
  canais** de `candidate_no_interaction`; tiers de severidade escalam a partir
  do threshold (`×1` low, `×2` medium, `×3` high).
- Canais in-app: `_resolve_alert_channels` adiciona `chat` quando `bell` está
  ativo (briefing) e tem fail-safe `["bell","chat"]` se nada estiver marcado
  (a regra ainda está ENABLED nesse ponto, então não se perde o alerta).

## Reconciliação de `company_id` (sem migração)

A config legada vive sob o id string `demo_company` em `alert_rule_templates` /
`alert_configs`. Os geradores **nunca** consultam essas tabelas — só
`alert_preferences` por UUID. Lookup por UUID acha a config real do tenant;
as tabelas legadas ficam órfãs por design (sem migração nesta task). As 9 regras
órfãs do catálogo (sem detector) ganharam gerador canônico na Task #1296 — ver a
matriz 15/15 acima.

## Sentinelas

`tests/contract/test_alert_config_single_source.py` (14 testes):
1. `ALERT_CONFIG_DEFAULTS` espelha 1-1 o catálogo da UI.
2. `_DEFAULT_TENANT_OVERRIDE` deriva de `ALERT_CONFIG_DEFAULTS`.
3. resolver retorna default sem company / fail-safe em type desconhecido;
   `channels_to_list` ordenado.
4. consumer importa `CommunicationSettings` do módulo canônico (não do shim
   `observability` quebrado).
5. detector persiste `channels` em `suggested_action`; `MonitoringLoop`
   persiste `alert.channels` (não hardcoded).
6. `MonitoringLoop` retorna `[]` quando a regra está desabilitada (sem query).
7. **Cobertura 15/15 (Task #1296):** toda `alert_type` do catálogo da UI tem
   gerador real (`test_catalog_alert_types_have_generator`); os 9 detectores
   novos estão registrados em `ProactiveDetectorService.detectors`
   (`test_nine_orphan_detectors_registered`); e cada detector novo retorna `[]`
   antes de qualquer query quando a regra está desabilitada
   (`test_orphan_detectors_disabled_gate_returns_empty`).

O sensor AST `scripts/check_proactive_detectors_registered.py` (15 detectores
declarados ⇔ registrados) trava drift de registro fora do pytest.

Sentinelas existentes que continuam verdes: `test_alert_detector_uses_template.py`,
`test_alert_canonical_consolidation.py`.

## Como verificar

```bash
cd lia-agent-system
LIA_ENV=test python -m pytest \
  tests/contract/test_alert_config_single_source.py \
  tests/contract/test_alert_detector_uses_template.py \
  tests/contract/test_alert_canonical_consolidation.py \
  -o addopts="" -q
```
