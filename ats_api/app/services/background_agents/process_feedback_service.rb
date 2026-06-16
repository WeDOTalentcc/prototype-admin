# frozen_string_literal: true

module BackgroundAgents
  class ProcessFeedbackService
    def initialize(background_agent:, feedbacks:)
      @agent = background_agent
      @feedbacks = feedbacks
    end

    def call
      return error("No feedbacks provided") if @feedbacks.blank?

      processed = create_feedbacks
      update_counters(processed)
      update_calibration
      check_auto_mode

      @agent.update!(last_interaction_at: Time.current)

      cycle = @agent.current_cycle
      mark_cycle_reviewed(cycle) if cycle && all_reviewed?(cycle)

      {
        success: true,
        processed: processed.size,
        calibration_state: @agent.calibration_state,
        mode: @agent.mode
      }
    rescue StandardError => e
      Rails.logger.error "[BackgroundAgents::ProcessFeedbackService] #{e.message}"
      error(e.message)
    end

    private

    def create_feedbacks
      @feedbacks.filter_map do |feedback_data|
        cycle_id = feedback_data[:agent_cycle_id] || @agent.current_cycle&.id
        next unless cycle_id

        agent_feedback = AgentFeedback.create!(
          background_agent: @agent,
          agent_cycle_id: cycle_id,
          sourced_profile_sourcing_id: feedback_data[:sourced_profile_sourcing_id],
          action: feedback_data[:action],
          reason: feedback_data[:reason]
        )

        sync_candidate_feedback(agent_feedback)
        agent_feedback
      rescue ActiveRecord::RecordNotUnique
        nil
      end
    end

    def update_counters(processed)
      approved = processed.count { |f| f.action == "approved" }
      rejected = processed.count { |f| f.action == "rejected" }
      return if approved.zero? && rejected.zero?

      BackgroundAgent.where(id: @agent.id).update_all(
        [
          "total_approved = total_approved + ?, total_rejected = total_rejected + ?",
          approved, rejected
        ]
      )
      @agent.reload
    end

    def update_calibration
      return if @agent.calibrated?

      total = @agent.total_approved + @agent.total_rejected
      if total >= BackgroundAgent::CALIBRATION_THRESHOLD
        @agent.update!(calibration_state: "calibrated")
        BackgroundAgents::ExtractPreferencesJob.perform_async(@agent.id, @agent.account_id)
        return
      end

      @agent.update!(calibration_state: "learning") if @agent.calibration_state == "pending"
    end

    def check_auto_mode
      return unless @agent.calibrated?
      return if @agent.mode == "auto_add"

      recent = @agent.agent_feedbacks.order(created_at: :desc).limit(10)
      consecutive = count_consecutive_approvals(recent)

      @agent.update!(consecutive_approvals: consecutive)
    end

    def count_consecutive_approvals(feedbacks)
      count = 0
      feedbacks.each do |f|
        break unless f.action == "approved"
        count += 1
      end
      count
    end

    def all_reviewed?(cycle)
      cycle.candidates_delivered > 0 &&
        cycle.agent_feedbacks.count >= cycle.candidates_delivered
    end

    def mark_cycle_reviewed(cycle)
      cycle.mark_reviewed!

      BackgroundAgentChannel.broadcast_to(
        "#{@agent.user_id}_agent_#{@agent.id}",
        { type: "cycle_reviewed", cycle_id: cycle.id, cycle_number: cycle.cycle_number }
      )
    end

    def sync_candidate_feedback(agent_feedback)
      feedback_type = agent_feedback.action == "approved" ? "like" : "dislike"

      CandidateFeedbacks::UpsertService.call(
        sourced_profile_sourcing_id: agent_feedback.sourced_profile_sourcing_id,
        user: @agent.user,
        feedback_type: feedback_type,
        reason: agent_feedback.reason,
        skip_agent_sync: true
      )
    rescue StandardError => e
      Rails.logger.warn "[ProcessFeedbackService] sync_candidate_feedback failed: #{e.message}"
    end

    def error(message)
      { success: false, error: message }
    end
  end
end
