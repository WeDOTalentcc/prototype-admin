# frozen_string_literal: true

require "sneakers"
require "json"

# LIA-E03 (Rails mirror): Consumer for LIA Python events with version validation
#
# Consumes from `lia_events_queue` bound to exchange `lia_python_events`.
# Validates event_version before processing — drops incompatible events to log/DLQ.
#
# Mirrors app/shared/messaging/rails_crud_consumer.py in the LIA Python repo.
class LiaEventsWorker
  include Sneakers::Worker

  from_queue "lia_events_queue",
             ack: true,
             threads: 2,
             prefetch: 4,
             timeout_job_after: 30

  def work(raw_message)
    event = JSON.parse(raw_message)
    event_type = event["event_type"]
    event_version = event["event_version"] || "1.0"
    company_id = event["company_id"]

    unless LiaEvents::EventRegistry.validate_version(event_type, event_version)
      Rails.logger.warn(
        "[LIA-E03] Incompatible event version: type=#{event_type} " \
        "received=#{event_version} expected_major=#{LiaEvents::EventRegistry.current_version(event_type)} " \
        "company=#{company_id}"
      )
      # Reject and route to DLQ for manual analysis (do not requeue)
      return :reject
    end

    Rails.logger.info(
      "[LIA-E03] Event received: type=#{event_type} version=#{event_version} company=#{company_id}"
    )

    # Dispatch to appropriate handler based on event_type
    handler_method = "handle_#{event_type.tr('.', '_')}"
    if respond_to?(handler_method, true)
      send(handler_method, event["payload"], company_id)
    else
      Rails.logger.info("[LIA-E03] No handler for #{event_type}, event acknowledged")
    end

    :ack
  rescue JSON::ParserError => e
    Rails.logger.error("[LIA-E03] JSON parse error: #{e.message}")
    :reject
  rescue StandardError => e
    Rails.logger.error("[LIA-E03] Handler error: type=#{event_type} err=#{e.message}")
    # Requeue once for transient failures; Sneakers will DLQ after retry exhaustion
    :requeue
  end

  private

  # Handler stubs — implement business logic per event type
  # Method name convention: handle_<event_type_with_dots_as_underscores>

  def handle_screening_completed(payload, company_id)
    Rails.logger.info("[LIA-E03] handle_screening_completed: payload=#{payload.inspect}")
    # TODO: update Apply/Candidate records with screening result
  end

  def handle_interview_scheduled(payload, company_id)
    Rails.logger.info("[LIA-E03] handle_interview_scheduled: payload=#{payload.inspect}")
    # TODO: create/update Interview record
  end

  def handle_interview_completed(payload, company_id)
    Rails.logger.info("[LIA-E03] handle_interview_completed: payload=#{payload.inspect}")
    # TODO: update Interview status + trigger downstream
  end

  def handle_offer_sent(payload, company_id)
    Rails.logger.info("[LIA-E03] handle_offer_sent: payload=#{payload.inspect}")
    # TODO: create Offer record
  end

  def handle_candidate_enriched(payload, company_id)
    Rails.logger.info("[LIA-E03] handle_candidate_enriched: payload=#{payload.inspect}")
    # TODO: update Candidate enrichment fields
  end

  def handle_pipeline_moved(payload, company_id)
    Rails.logger.info("[LIA-E03] handle_pipeline_moved: payload=#{payload.inspect}")
    # TODO: update Apply pipeline_stage
  end

  # Phase 5: Agent Studio event handlers
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
      "[AgentStudio] execution.completed: agent=#{agent_name} " \
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
          message: "Agent \"#{agent_name}\" falhou: #{error_msg.first(200)}",
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
      "[AgentStudio] deployment.created: agent_id=#{payload['agent_id']} " \
      "target=#{payload['target_type']}/#{payload['target_id']} " \
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
      "[AgentStudio] approval.reviewed: agent_id=#{agent_id} " \
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
  end

end
