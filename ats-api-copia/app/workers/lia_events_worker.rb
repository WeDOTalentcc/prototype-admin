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
end
