"""
RabbitMQ Consumer — NOT YET WIRED (R-046: intentional stub)
====================================

R-046 EVALUATION (2026-05-25): KEEP — serves a different purpose than
app/shared/messaging/rabbitmq_consumer.py (which handles WS response routing
and IS live in production). THIS file is a placeholder for the future
Rails → lia-agent-system async channel via AMQP. The two files are NOT
duplicates. Activation checklist below.
TODO(RABBITMQ-INT): Implementar este módulo para ativar o canal Rails → lia-agent-system.

## Por que existe agora (mas não roda)

O `ContextAdapter.from_rabbitmq()` já está pronto e testado.
Este worker é a ponte que falta: ouve a fila, deserializa, chama o orchestrator,
publica a resposta.

Enquanto `AMQP_URL` não estiver configurada, o `start_consumer()` lança
`NotImplementedError` — sem impacto no canal REST/WS que já está em produção.

## Contrato de mensagem (Rails → queue → aqui)

```json
{
  "question":         "<mensagem do usuário>",
  "domain":           "<wizard | job_management | talent_funnel | general | ...>",
  "user_id":          "<uuid — validado contra JWT interno>",
  "company_id":       "<uuid — NUNCA confiar cegamente; validar contra INTERNAL_SERVICE_TOKEN>",
  "conversation_id":  "<uuid | null>",
  "sourcing_id":      "<uuid | null>",
  "job_id":           "<uuid | null>",
  "context_data": {
    "candidates":   [],
    "job_context":  {},
    "metadata": {
      "source":      "rail_a",
      "domain_hint": "<wizard | job_management | ...>",
      "card_id":     "panel_active:<panel_type>"
    }
  }
}
```

Formato publicado pelo Rails em `messages_controller.rb` via
`LiaJobsProducerService` (a implementar no Rails — ver ats-api-copia/).

## Checklist de ativação em produção

Antes de remover o `NotImplementedError` e ligar este worker:

- [ ] `AMQP_URL` env var configurada no Replit Secrets
      (ex: `amqp://user:pass@rabbitmq-host:5672/lia`)
- [ ] `INTERNAL_SERVICE_TOKEN` env var configurada (shared secret Rails↔Python)
- [ ] Exchange/queue criados no broker:
        exchange = "lia.exchange"  (type=direct)
        queue    = "lia.jobs"
        key      = "lia.chat"
- [ ] Rails `LiaJobsProducerService` implementado e publicando no formato acima
- [ ] Integration test: `tests/integration/test_rabbitmq_consumer.py`
      (pelo menos: publish → consume → assert orchestrator called)
- [ ] Smoke test manual: publicar 1 msg via CLI → verificar log
      `[rabbitmq_consumer] routed via ContextAdapter.from_rabbitmq`

## Referências cruzadas

- `ContextAdapter.from_rabbitmq`:  app/orchestrator/context_adapter.py  (já pronto)
- `MainOrchestrator`:              app/orchestrator/main_orchestrator.py
- `Rail A hint override`:          app/orchestrator/services/rail_a_hint_override.py
- AGENTS.md § Integrações Planejadas
- Audit Enterprise 2026-04-26:     ~/.claude/plans/chave-do-replit-para-linked-pie.md
"""
from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


async def start_consumer() -> None:  # pragma: no cover
    """
    Inicia o consumer AMQP assíncrono.

    TODO(RABBITMQ-INT): substituir o corpo deste stub pela implementação real.
    Esqueleto sugerido com aio-pika:

        import aio_pika
        connection = await aio_pika.connect_robust(os.environ["AMQP_URL"])
        channel = await connection.channel()
        queue = await channel.declare_queue("lia.jobs", durable=True)

        async with queue.iterator() as q:
            async for msg in q:
                async with msg.process():
                    payload = json.loads(msg.body)
                    ctx = ContextAdapter.from_rabbitmq(payload)
                    response = await orchestrator.process(ctx)
                    await _publish_response(channel, payload, response)

    Autenticação: validar `payload["_token"] == os.environ["INTERNAL_SERVICE_TOKEN"]`
    antes de processar (anti-spoofing entre serviços internos).
    """
    # Wave 4 Gap 1 (2026-05-22): RabbitMQ consumer is a separate process
    # tree from FastAPI -- if/when this stub becomes real, the LLM guards
    # MUST be installed in this process too or every orchestrator call from
    # a RabbitMQ-delivered request bypasses the universal credit gate.
    # install_llm_guards() is idempotent; safe to call here at startup.
    try:
        from app.shared.llm_bootstrap import install_llm_guards
        install_llm_guards(entrypoint='rabbitmq')
    except Exception:  # noqa: BLE001
        logger.exception(
            '[rabbitmq_consumer] install_llm_guards FAILED -- LLM gate '
            'bypassed in this process'
        )

    amqp_url = os.environ.get("AMQP_URL")
    if not amqp_url:
        raise NotImplementedError(
            "TODO(RABBITMQ-INT): AMQP_URL env var não configurada.\n"
            "Consulte a docstring de app/workers/rabbitmq_consumer.py para o checklist "
            "completo de ativação em produção."
        )
    raise NotImplementedError(
        "TODO(RABBITMQ-INT): Consumer não implementado ainda.\n"
        "AMQP_URL está configurada — agora implemente o corpo de start_consumer().\n"
        "Ver docstring do módulo para o contrato completo."
    )
