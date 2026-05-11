# ADR-LGPD-002 — Retention de conversation state em LangGraph checkpoints

**Data:** 2026-05-10
**Status:** Decisão registrada (rollout faseado)
**Contexto:** PLAN_FIX_wizard_memory_loss · Onda 4.D2

## Contexto

Auditoria 2026-05-10 detectou que a tabela LangGraph `checkpoints` no
Postgres canonical não tem TTL nem cleanup automatizado. Conversation
state do wizard (e outros agents — WSI, interview_scheduling) acumula
indefinidamente, podendo reter PII em campos livres:

- Descrição da vaga (livre — pode mencionar candidatos por nome).
- Contexto do recrutador (livre — comentários internos).
- Mensagens conversacionais cruas (`conversation_messages` array).

Isso viola:
- **LGPD Art. 16** — limitação de armazenamento (dados pessoais armazenados
  apenas pelo período necessário).
- **LGPD Art. 18** — direito à eliminação (sem mecanismo de erasure cascade
  para conversation state).
- **ANPD Guia de Anonimização §3** — agregados destrutivos sobre dados
  conversacionais não anonimizam o state cru subjacente.

## Decisão

1. **TTL default: 90 dias** para checkpoints sem atividade recente.
2. **Script canonical**: `scripts/cleanup_checkpoints_retention.py`
   - Apaga checkpoints expirados em batch.
   - Fallback conservador quando `track_commit_timestamp` indisponível
     (modo Replit atual): não apaga nada até detecção segura de idade.
   - `--dry-run` lista alvos; `--apply` executa.
3. **Cron sugerido**: semanal, domingos 03:00 UTC.
4. **Mascaramento de output** (já implementado): `mask_pii` aplicado em
   `agent_chat_ws.py:900,916,1043` e `agent_chat_sse.py:369,405`. Output
   ao cliente está sanitizado.
5. **Mascaramento de checkpoint write** (gap identificado): state cru no
   `checkpoint jsonb` NÃO é mascarado — é necessário para o LLM continuar
   contexto. Mitigação via retention + erasure cascade quando candidato
   solicita deleção (Art. 18).

## Fases de implementação

| Fase | Escopo | Status |
|---|---|---|
| **0** (Onda 4.D2, 2026-05-10) | Script canonical + tests + ADR registrada. Modo fallback conservador. | Pronto |
| **1** (próximo sprint) | Ativar `track_commit_timestamp = on` no Postgres canonical (Replit + staging). Permite identificação real de threads aged. | Planejado |
| **2** (sprint+1) | Cron scheduler no Replit/staging executando `--apply` semanal. Métrica Prometheus de threads deletados. | Planejado |
| **3** (sprint+2) | Erasure cascade: endpoint `/api/v1/data-subject/erasure/{candidate_id}` que apaga checkpoints contendo o candidato. Requer indexação reversa candidate_id → thread_id. | Planejado |
| **4** (futuro) | `PostgresSaverWithPII` wrapper opcional para mask antes de `saver.put()`. Trade-off: pode quebrar continuidade conversacional se PII mascarado for relevante para LLM. | Avaliar |

## Track commit timestamp — configuração necessária

```sql
-- Habilitar via postgresql.conf ou ALTER SYSTEM (requires restart):
ALTER SYSTEM SET track_commit_timestamp = on;
SELECT pg_reload_conf();  -- não basta — precisa restart do server
```

Em ambientes managed (Replit, Render), abrir ticket com o provider.

## Consequências

**Positivas:**
- Aderência LGPD Art. 16 + 18.
- Mitiga acúmulo indefinido de state com PII.
- Auditável via logs do cron + métricas.

**Negativas / riscos:**
- Em Fase 0 (atual), retention real não roda — apenas script + tests +
  documentação. Sensor seguro garante que --apply não apaga sem evidência.
- Threads HITL pendentes podem ser apagados se idle > 90 dias. Mitigação:
  HITL approval deve ser resolvido em < 30 dias (already enforced no UX).
- Erasure cascade (Fase 3) requer reindexação cara — vai aceitar latência
  na operação de "esquecer candidato".

## Referências

- `PLAN_FIX_wizard_memory_loss.md` Onda 4.D2
- `scripts/cleanup_checkpoints_retention.py`
- `tests/unit/test_cleanup_checkpoints_retention.py`
- CLAUDE.md → ADR-LGPD-001 (precedente; agregados de candidatos)
