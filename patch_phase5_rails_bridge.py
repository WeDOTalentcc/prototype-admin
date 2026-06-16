#!/usr/bin/env python3
"""
Phase 5: Rails Bridge for Agent Studio events

Both sides:
  Python: register 6 new event types in rails_event_schemas + emit in webhook_dispatcher
  Rails: register 6 events in EventRegistry + add 6 handlers in LiaEventsWorker
"""
import os

BASE_PY = "/home/runner/workspace/lia-agent-system"
BASE_RB = "/home/runner/workspace/ats-api-copia"


def read_file(base, rel):
    with open(os.path.join(base, rel)) as f:
        return f.read()


def patch_file(base, rel, old, new, label=""):
    full = os.path.join(base, rel)
    content = read_file(base, rel)
    if old not in content:
        print(f"  SKIP: {label}")
        return False
    content = content.replace(old, new, 1)
    with open(full, "w") as f:
        f.write(content)
    print(f"  OK: {label}")
    return True


# ============================================================
# 1. PYTHON: Register Studio events in rails_event_schemas.py
# ============================================================
print("\n=== 1. Python: register 6 Studio events in EVENT_VERSIONS ===")

# Find EVENT_VERSIONS dict
content = read_file(BASE_PY, "app/shared/messaging/rails_event_schemas.py")
print(f"  File has EVENT_VERSIONS: {'EVENT_VERSIONS' in content}")

# Use simpler patch — find dict start and end
import re
match = re.search(r'EVENT_VERSIONS\s*[:=]?\s*[^=]*=\s*\{([^}]*)\}', content)
if match:
    print(f"  Found EVENT_VERSIONS dict at offset {match.start()}")
    existing_block = match.group(0)
    inner = match.group(1)
    # Add new entries before the closing }
    new_entries = '''
    "agent.execution.completed": "1.0",
    "agent.execution.failed": "1.0",
    "agent.deployment.created": "1.0",
    "agent.deployment.paused": "1.0",
    "agent.approval.requested": "1.0",
    "agent.approval.reviewed": "1.0",
'''
    if "agent.execution.completed" in inner:
        print("  SKIP: events already registered")
    else:
        # Insert new entries at end of dict (before closing brace)
        new_block = existing_block.rstrip("}").rstrip() + new_entries + "}"
        content = content.replace(existing_block, new_block, 1)
        with open(os.path.join(BASE_PY, "app/shared/messaging/rails_event_schemas.py"), "w") as f:
            f.write(content)
        print("  OK: 6 events added to EVENT_VERSIONS")
else:
    print("  ERROR: EVENT_VERSIONS dict not found via regex")


# ============================================================
# 2. PYTHON: Hook Rails event publish in webhook_dispatcher.dispatch()
# ============================================================
print("\n=== 2. Python: webhook_dispatcher publishes to Rails too ===")
patch_file(
    BASE_PY,
    "app/services/webhook_dispatcher.py",
    '''    async def dispatch(
        self, db: AsyncSession, company_id: str, event: str, payload: dict
    ) -> int:
        """Dispatch event to all subscribed webhooks. Returns count of queued deliveries."""
        webhooks = await self.find_subscribers(db, company_id, event)
        queued = 0
        for wh in webhooks:
            try:
                # Lazy import to avoid circular dep
                from app.jobs.webhook_tasks import deliver_webhook_task
                deliver_webhook_task.delay(
                    webhook_id=str(wh.id),
                    url=wh.url,
                    secret=wh.secret,
                    event=event,
                    payload=payload,
                )
                queued += 1
            except Exception as exc:
                logger.warning("[Webhook] dispatch enqueue failed: %s", exc)
        if queued > 0:
            logger.info(
                "[Webhook] dispatched event=%s to %d webhook(s) for company=%s",
                event, queued, company_id,
            )
        return queued''',
    '''    async def dispatch(
        self, db: AsyncSession, company_id: str, event: str, payload: dict
    ) -> int:
        """Dispatch event to all subscribed external webhooks AND Rails internal bus.

        Returns count of queued external webhook deliveries (Rails publish is fire-and-forget).
        """
        # External webhooks (P2.5b)
        webhooks = await self.find_subscribers(db, company_id, event)
        queued = 0
        for wh in webhooks:
            try:
                from app.jobs.webhook_tasks import deliver_webhook_task
                deliver_webhook_task.delay(
                    webhook_id=str(wh.id),
                    url=wh.url,
                    secret=wh.secret,
                    event=event,
                    payload=payload,
                )
                queued += 1
            except Exception as exc:
                logger.warning("[Webhook] dispatch enqueue failed: %s", exc)
        if queued > 0:
            logger.info(
                "[Webhook] dispatched event=%s to %d webhook(s) for company=%s",
                event, queued, company_id,
            )

        # Phase 5: Rails internal bus (non-blocking, fire-and-forget)
        try:
            from app.shared.messaging.unified_event_publisher import unified_event_publisher
            await unified_event_publisher.publish(
                event_type=event,
                payload=payload,
                company_id=company_id,
            )
        except Exception as rails_exc:
            logger.warning(
                "[RailsBridge] publish failed for event=%s company=%s: %s",
                event, company_id, rails_exc,
            )

        return queued''',
    "webhook_dispatcher publishes to Rails",
)


# ============================================================
# 3. RAILS: Register 6 events in EventRegistry
# ============================================================
print("\n=== 3. Rails: register 6 Studio events in EventRegistry ===")
patch_file(
    BASE_RB,
    "app/services/lia_events/event_registry.rb",
    '''    EVENT_VERSIONS = {
      "screening.completed" => "1.0",
      "interview.scheduled" => "1.0",
      "interview.completed" => "1.0",
      "offer.sent"          => "1.0",
      "candidate.enriched"  => "1.0",
      "pipeline.moved"      => "1.0",
    }.freeze''',
    '''    EVENT_VERSIONS = {
      "screening.completed" => "1.0",
      "interview.scheduled" => "1.0",
      "interview.completed" => "1.0",
      "offer.sent"          => "1.0",
      "candidate.enriched"  => "1.0",
      "pipeline.moved"      => "1.0",
      # Phase 5: Agent Studio events (mirrors lia-agent-system/app/shared/messaging/rails_event_schemas.py)
      "agent.execution.completed" => "1.0",
      "agent.execution.failed"    => "1.0",
      "agent.deployment.created"  => "1.0",
      "agent.deployment.paused"   => "1.0",
      "agent.approval.requested"  => "1.0",
      "agent.approval.reviewed"   => "1.0",
    }.freeze''',
    "EventRegistry add 6 Studio events",
)


# ============================================================
# 4. RAILS: Add 6 handlers in LiaEventsWorker
# ============================================================
print("\n=== 4. Rails: add 6 handlers ===")

# Find a good insertion point — after the last existing handler
worker_content = read_file(BASE_RB, "app/workers/lia_events_worker.rb")

# Insert before the final `end` of the class
# Find handle_pipeline_moved as anchor
old_handler = '''  def handle_pipeline_moved(payload, company_id)'''

if old_handler in worker_content:
    # Find the end of handle_pipeline_moved method
    # Look for the next "  def" or class-level "end"
    lines = worker_content.split("\n")
    pm_idx = None
    for i, line in enumerate(lines):
        if "def handle_pipeline_moved" in line:
            pm_idx = i
            break

    if pm_idx is not None:
        # Find the matching `end` for this method (next "  end" at same indent)
        end_idx = None
        for j in range(pm_idx + 1, len(lines)):
            stripped = lines[j].rstrip()
            # Method end is "  end" (2 spaces indent) — class end is "end" (0 spaces)
            if stripped == "  end":
                end_idx = j
                break

        if end_idx is not None:
            # Insert 6 new handlers after this end
            new_handlers = '''
  # Phase 5: Agent Studio event handlers
  # These handlers react to Studio events emitted from the Python LIA backend.
  # Currently only logging — extend with side-effects (ActivityLog, notifications, badges)
  # as ATS product requirements evolve.

  def handle_agent_execution_completed(payload, company_id)
    Rails.logger.info(
      "[AgentStudio] execution.completed: agent=#{payload['agent_name']} " \\
      "agent_id=#{payload['agent_id']} latency_ms=#{payload['execution_time_ms']} " \\
      "tokens=#{payload['tokens_input'].to_i + payload['tokens_output'].to_i} company=#{company_id}"
    )
    # TODO (product): create ActivityLog entry on related job
    # TODO (product): increment "automated executions today" counter
  end

  def handle_agent_execution_failed(payload, company_id)
    Rails.logger.warn(
      "[AgentStudio] execution.failed: agent=#{payload['agent_name']} " \\
      "error=#{payload['error']} company=#{company_id}"
    )
    # TODO (product): notify admins via existing notification infra
  end

  def handle_agent_deployment_created(payload, company_id)
    Rails.logger.info(
      "[AgentStudio] deployment.created: agent_id=#{payload['agent_id']} " \\
      "target=#{payload['target_type']}/#{payload['target_id']} " \\
      "trigger=#{payload['trigger_mode']} company=#{company_id}"
    )
    # TODO (product): tag visual on related job/pool ("agent ativo")
  end

  def handle_agent_deployment_paused(payload, company_id)
    Rails.logger.info(
      "[AgentStudio] deployment.paused: deployment_id=#{payload['deployment_id']} company=#{company_id}"
    )
    # TODO (product): remove visual tag, log to deployment history
  end

  def handle_agent_approval_requested(payload, company_id)
    Rails.logger.info(
      "[AgentStudio] approval.requested: agent_id=#{payload['agent_id']} " \\
      "requested_by=#{payload['requested_by']} company=#{company_id}"
    )
    # TODO (product): internal notification to ATS admins
  end

  def handle_agent_approval_reviewed(payload, company_id)
    Rails.logger.info(
      "[AgentStudio] approval.reviewed: agent_id=#{payload['agent_id']} " \\
      "action=#{payload['action']} reviewer=#{payload['reviewer_id']} company=#{company_id}"
    )
    # TODO (product): log to agent approval history table
  end
'''
            # Insert after line end_idx
            lines.insert(end_idx + 1, new_handlers)
            new_content = "\n".join(lines)
            with open(os.path.join(BASE_RB, "app/workers/lia_events_worker.rb"), "w") as f:
                f.write(new_content)
            print(f"  OK: 6 handlers inserted after line {end_idx + 1}")
        else:
            print("  ERROR: could not find end of handle_pipeline_moved")
    else:
        print("  ERROR: handle_pipeline_moved not found in lines")
else:
    print("  SKIP: handle_pipeline_moved anchor not found")


# ============================================================
# Verify
# ============================================================
print("\n=== Verify ===")
import ast

# Python files
for f in [
    "app/shared/messaging/rails_event_schemas.py",
    "app/services/webhook_dispatcher.py",
]:
    try:
        ast.parse(read_file(BASE_PY, f))
        print(f"  OK Python: {f}")
    except SyntaxError as e:
        print(f"  ERROR: {f}: {e}")

# Ruby files — basic check (count methods)
worker = read_file(BASE_RB, "app/workers/lia_events_worker.rb")
agent_handlers = worker.count("def handle_agent_")
print(f"  Rails worker has {agent_handlers} agent handler(s) (expected 6)")

registry = read_file(BASE_RB, "app/services/lia_events/event_registry.rb")
agent_events = registry.count('"agent.')
print(f"  Rails EventRegistry has {agent_events} agent event(s) (expected 6)")

print("\nPhase 5 complete!")
