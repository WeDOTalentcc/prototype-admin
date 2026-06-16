#!/usr/bin/env python3
"""Evolve Rails handlers from log-only to real side-effects.

Uses existing Rails tables:
- audit_logs (for execution tracking)
- notifications (for admin notifications)
"""
import os

BASE_RB = "/home/runner/workspace/ats-api-copia"

worker_path = os.path.join(BASE_RB, "app/workers/lia_events_worker.rb")
with open(worker_path) as f:
    content = f.read()

# Find the 6 existing placeholder handlers and replace with evolved versions
old_handlers = '''  # Phase 5: Agent Studio event handlers
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
  end'''

new_handlers = '''  # Phase 5: Agent Studio event handlers
  # Evolved with real side-effects:
  # - AuditLog entries for execution tracking
  # - Notification entries for admins
  # All handlers are fail-safe: side-effect errors don't block event acknowledgment.

  def handle_agent_execution_completed(payload, company_id)
    agent_name = payload["agent_name"].to_s
    agent_id = payload["agent_id"].to_s
    latency_ms = payload["execution_time_ms"].to_i
    tokens_total = payload["tokens_input"].to_i + payload["tokens_output"].to_i
    confidence = payload["confidence"].to_f

    Rails.logger.info(
      "[AgentStudio] execution.completed: agent=#{agent_name} " \\
      "id=#{agent_id} latency_ms=#{latency_ms} tokens=#{tokens_total} company=#{company_id}"
    )

    begin
      AuditLog.create!(
        company_id: company_id,
        agent_name: agent_name,
        agent_used: agent_id,
        decision_type: "studio_execution",
        action: "agent.execution.completed",
        decision: "completed",
        score: confidence,
        confidence: confidence,
        reasoning: { latency_ms: latency_ms, tokens_total: tokens_total },
        session_id: payload["deployment_id"].to_s,
        output_text: payload["response"].to_s.first(1000),
        created_at: Time.current,
      )
    rescue StandardError => e
      Rails.logger.warn("[AgentStudio] audit_log create failed: #{e.message}")
    end
  end

  def handle_agent_execution_failed(payload, company_id)
    agent_name = payload["agent_name"].to_s
    error_msg = payload["error"].to_s.first(500)

    Rails.logger.warn(
      "[AgentStudio] execution.failed: agent=#{agent_name} error=#{error_msg} company=#{company_id}"
    )

    begin
      AuditLog.create!(
        company_id: company_id,
        agent_name: agent_name,
        agent_used: payload["agent_id"].to_s,
        decision_type: "studio_execution",
        action: "agent.execution.failed",
        decision: "failed",
        reasoning: { error: error_msg },
        output_text: error_msg,
        created_at: Time.current,
      )

      # Notify all admins of this company about the failure
      admin_user_ids = User.where(company_id: company_id, role: "admin", active: true).pluck(:id)
      admin_user_ids.each do |uid|
        Notification.create!(
          user_id: uid.to_s,
          company_id: company_id,
          notification_type: "agent_studio_failure",
          title: "Falha em agent do Studio",
          message: "Agent \\"#{agent_name}\\" falhou: #{error_msg.first(200)}",
          priority: "high",
          action_url: "/agent-studio?agent=#{payload['agent_id']}",
          metadata: { agent_id: payload["agent_id"], error: error_msg },
        )
      end
    rescue StandardError => e
      Rails.logger.warn("[AgentStudio] side-effect failed: #{e.message}")
    end
  end

  def handle_agent_deployment_created(payload, company_id)
    Rails.logger.info(
      "[AgentStudio] deployment.created: agent_id=#{payload['agent_id']} " \\
      "target=#{payload['target_type']}/#{payload['target_id']} " \\
      "trigger=#{payload['trigger_mode']} company=#{company_id}"
    )

    begin
      AuditLog.create!(
        company_id: company_id,
        agent_name: payload["agent_name"].to_s,
        agent_used: payload["agent_id"].to_s,
        decision_type: "studio_deployment",
        action: "agent.deployment.created",
        decision: "created",
        job_vacancy_id: payload["target_type"] == "job" ? payload["target_id"].to_s : nil,
        reasoning: {
          target_type: payload["target_type"],
          target_id: payload["target_id"],
          trigger_mode: payload["trigger_mode"],
        },
        created_at: Time.current,
      )
    rescue StandardError => e
      Rails.logger.warn("[AgentStudio] audit_log create failed: #{e.message}")
    end
  end

  def handle_agent_deployment_paused(payload, company_id)
    Rails.logger.info(
      "[AgentStudio] deployment.paused: deployment_id=#{payload['deployment_id']} company=#{company_id}"
    )

    begin
      AuditLog.create!(
        company_id: company_id,
        agent_used: payload["agent_id"].to_s,
        decision_type: "studio_deployment",
        action: "agent.deployment.paused",
        decision: "paused",
        reasoning: { deployment_id: payload["deployment_id"] },
        created_at: Time.current,
      )
    rescue StandardError => e
      Rails.logger.warn("[AgentStudio] audit_log create failed: #{e.message}")
    end
  end

  def handle_agent_approval_requested(payload, company_id)
    agent_id = payload["agent_id"].to_s
    requested_by = payload["requested_by"].to_s

    Rails.logger.info(
      "[AgentStudio] approval.requested: agent_id=#{agent_id} requested_by=#{requested_by} company=#{company_id}"
    )

    begin
      # Notify all admins — action required
      admin_user_ids = User.where(company_id: company_id, role: "admin", active: true).pluck(:id)
      admin_user_ids.each do |uid|
        Notification.create!(
          user_id: uid.to_s,
          company_id: company_id,
          notification_type: "agent_studio_approval",
          title: "Aprovacao pendente de agent",
          message: "Revise o agent solicitado por #{requested_by}.",
          priority: "high",
          action_url: "/agent-studio?pending_approvals=1",
          metadata: { agent_id: agent_id, requested_by: requested_by, approval_id: payload["approval_id"] },
        )
      end
    rescue StandardError => e
      Rails.logger.warn("[AgentStudio] approval notification failed: #{e.message}")
    end
  end

  def handle_agent_approval_reviewed(payload, company_id)
    agent_id = payload["agent_id"].to_s
    action_taken = payload["action"].to_s  # "approve" | "reject"
    reviewer_id = payload["reviewer_id"].to_s

    Rails.logger.info(
      "[AgentStudio] approval.reviewed: agent_id=#{agent_id} " \\
      "action=#{action_taken} reviewer=#{reviewer_id} company=#{company_id}"
    )

    begin
      AuditLog.create!(
        company_id: company_id,
        agent_used: agent_id,
        decision_type: "studio_approval",
        action: "agent.approval.reviewed",
        decision: action_taken,
        human_reviewed_by: reviewer_id,
        human_reviewed_at: Time.current,
        reasoning: { approval_id: payload["approval_id"], notes: payload["review_notes"] },
        created_at: Time.current,
      )
    rescue StandardError => e
      Rails.logger.warn("[AgentStudio] audit_log create failed: #{e.message}")
    end
  end'''

if old_handlers in content:
    content = content.replace(old_handlers, new_handlers)
    with open(worker_path, "w") as f:
        f.write(content)
    print("OK: handlers evolved with real side-effects")
else:
    print("ERROR: old handlers block not found exactly — need manual verification")
    print("Lines with 'handle_agent_':")
    for i, line in enumerate(content.split("\n"), 1):
        if "handle_agent_" in line and "def " in line:
            print(f"  line {i}: {line.strip()}")
