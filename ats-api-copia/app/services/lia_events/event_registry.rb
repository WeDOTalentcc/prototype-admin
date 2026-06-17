# frozen_string_literal: true

# LIA-E03 (Rails mirror): Event version registry
#
# Must stay in sync with app/shared/messaging/rails_event_schemas.py in the LIA Python repo.
# Source of truth: https://github.com/WeDOTalentcc/wedotalent02202026/blob/main/app/shared/messaging/rails_event_schemas.py
#
# Compatibility rule: MAJOR version must match.
# Examples: 1.0 ↔ 1.1 = OK, 1.x ↔ 2.0 = NOT OK
module LiaEvents
  module EventRegistry
    EVENT_VERSIONS = {
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
    }.freeze

    # Check if received version is compatible with current schema.
    # @param event_type [String] Event type (e.g. "screening.completed")
    # @param received_version [String] Version received in event payload (e.g. "1.0")
    # @return [Boolean] true if compatible, false otherwise
    def self.validate_version(event_type, received_version)
      current = EVENT_VERSIONS[event_type]
      return false unless current && received_version && !received_version.to_s.strip.empty?

      current_major = current.split(".").first.to_i
      received_major = received_version.to_s.split(".").first.to_i
      current_major == received_major
    rescue StandardError => e
      Rails.logger.warn("[LIA-E03] validate_version error: #{e.message}")
      false
    end

    # Get the current version for an event type.
    # @param event_type [String] Event type
    # @return [String, nil] Current version or nil if event type unknown
    def self.current_version(event_type)
      EVENT_VERSIONS[event_type]
    end

    # Check if an event type is registered.
    # @param event_type [String] Event type
    # @return [Boolean] true if registered
    def self.known_event?(event_type)
      EVENT_VERSIONS.key?(event_type)
    end
  end
end
