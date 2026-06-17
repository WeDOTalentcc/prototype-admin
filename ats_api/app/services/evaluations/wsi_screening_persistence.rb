# frozen_string_literal: true

module Evaluations
  class WsiScreeningPersistence
    def self.call(evaluation_candidate:)
      new(evaluation_candidate: evaluation_candidate).call
    end

    def initialize(evaluation_candidate:)
      @evaluation_candidate = evaluation_candidate
    end

    def call
      decision = Wsi::ScreeningDecisionService.call(evaluation_candidate: @evaluation_candidate)
      flags = Wsi::RedFlagDetector.call(evaluation_candidate: @evaluation_candidate)

      payload = decision.merge(decided_at: Time.current.iso8601)
      @evaluation_candidate.update!(
        wsi_decision: payload.deep_stringify_keys,
        wsi_red_flags: flags.map { |h| h.deep_stringify_keys }
      )
    rescue StandardError => e
      Rails.logger.error("❌ [WsiScreeningPersistence] evaluation_candidate #{@evaluation_candidate&.id}: #{e.class} #{e.message}")
    end
  end
end
