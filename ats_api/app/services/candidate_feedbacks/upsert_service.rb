# frozen_string_literal: true

module CandidateFeedbacks
  class UpsertService
    def self.call(**args)
      new(**args).call
    end

    def initialize(sourcing_id: nil, apply_id: nil, candidate_id: nil, sourced_profile_sourcing_id: nil, user:, feedback_type:, job_id: nil, reference_type: nil, reference_id: nil, reason: nil, skip_agent_sync: false)
      @sourcing_id = sourcing_id
      @apply_id = apply_id
      @candidate_id = candidate_id
      @sourced_profile_sourcing_id = sourced_profile_sourcing_id
      @user = user
      @feedback_type = feedback_type
      @job_id = job_id
      @reference_type = reference_type
      @reference_id = reference_id
      @reason = reason
      @skip_agent_sync = skip_agent_sync
      @errors = []
    end

    def call
      return error_result("User is required") if @user.blank?
      return error_result("Account ID is required") if @user.account_id.blank?
      return error_result("At least one context must be present") if all_contexts_blank?
      return error_result("Invalid feedback type") unless valid_feedback_type?

      validation_error = validate_contexts
      return validation_error if validation_error

      existing_feedback = find_existing_feedback
      return process_existing_feedback(existing_feedback) if existing_feedback.present?

      create_new_feedback
    rescue StandardError => e
      error_result("Error processing feedback: #{e.message}")
    end

    private

    def all_contexts_blank?
      @sourcing_id.blank? && @apply_id.blank? && @candidate_id.blank? && @sourced_profile_sourcing_id.blank?
    end

    def valid_feedback_type?
      %w[like dislike].include?(@feedback_type.to_s.downcase)
    end

    def validate_contexts
      validations = [
        -> { validate_sourcing_context if @sourcing_id.present? },
        -> { validate_apply_context if @apply_id.present? },
        -> { validate_candidate_context if @candidate_id.present? },
        -> { validate_sourced_profile_sourcing_context if @sourced_profile_sourcing_id.present? }
      ]

      validations.each do |validation|
        error = validation.call
        return error if error
      end

      nil
    end

    def validate_sourcing_context
      @sourcing = find_record(Sourcing, @sourcing_id)
      return error_result("Sourcing not found") unless @sourcing

      nil
    end

    def validate_apply_context
      @apply = find_record(Apply, @apply_id)
      return error_result("Apply not found") unless @apply

      @candidate_id ||= @apply.candidate_id
      @job_id ||= @apply.job_id
      nil
    end

    def validate_candidate_context
      @candidate = find_record(Candidate, @candidate_id)
      return error_result("Candidate not found") unless @candidate

      nil
    end

    def validate_sourced_profile_sourcing_context
      @sourced_profile_sourcing = find_record(SourcedProfileSourcing, @sourced_profile_sourcing_id)
      return error_result("SourcedProfileSourcing not found") unless @sourced_profile_sourcing

      @sourcing_id ||= @sourced_profile_sourcing.sourcing_id
      @candidate_id ||= @sourced_profile_sourcing.candidate&.id
      nil
    end

    def find_record(model, id)
      model.find_by(id: id, account_id: @user.account_id, is_deleted: false)
    end

    def find_existing_feedback
      CandidateFeedback.find_existing(
        sourcing_id: @sourcing_id,
        apply_id: @apply_id,
        candidate_id: @candidate_id,
        sourced_profile_sourcing_id: @sourced_profile_sourcing_id,
        user_id: @user.id
      )
    end

    def process_existing_feedback(feedback)
      return toggle_off_feedback(feedback) if feedback.feedback_type == @feedback_type

      update_feedback_type(feedback)
    end

    def toggle_off_feedback(feedback)
      feedback.soft_delete!
      remove_agent_feedback(feedback)
      success_result(feedback, :removed)
    end

    def update_feedback_type(feedback)
      feedback.update!(
        feedback_type: @feedback_type,
        reference_type: @reference_type,
        reference_id: @reference_id,
        reason: @reason,
        search_query_snapshot: build_search_query_snapshot,
        candidate_score_snapshot: build_candidate_score_snapshot
      )

      sync_to_background_agent(feedback)
      success_result(feedback, :updated)
    end

    def create_new_feedback
      feedback = CandidateFeedback.create!(
        sourcing_id: @sourcing_id,
        apply_id: @apply_id,
        candidate_id: @candidate_id,
        sourced_profile_sourcing_id: @sourced_profile_sourcing_id,
        user_id: @user.id,
        account_id: @user.account_id,
        job_id: @job_id,
        reference_type: @reference_type,
        reference_id: @reference_id,
        reason: @reason,
        feedback_type: @feedback_type,
        search_query_snapshot: build_search_query_snapshot,
        candidate_score_snapshot: build_candidate_score_snapshot,
        is_deleted: false
      )

      sync_to_background_agent(feedback)
      success_result(feedback, :created)
    rescue ActiveRecord::RecordInvalid => e
      error_result("Validation error: #{e.message}")
    end

    def sync_to_background_agent(feedback)
      return if @skip_agent_sync

      sps = feedback.sourced_profile_sourcing
      return unless sps&.search_source == "background_agent"

      cycle = sps.sourcing.agent_cycles.delivered.or(sps.sourcing.agent_cycles.reviewed).recent.first
      return unless cycle

      agent = cycle.background_agent
      return unless agent

      action = feedback.feedback_type == "like" ? "approved" : "rejected"

      BackgroundAgents::ProcessFeedbackService.new(
        background_agent: agent,
        feedbacks: [{
          sourced_profile_sourcing_id: sps.id,
          agent_cycle_id: cycle.id,
          action: action,
          reason: feedback.reason
        }]
      ).call
    rescue StandardError => e
      Rails.logger.warn "[CandidateFeedbacks::UpsertService] sync_to_background_agent failed: #{e.message}"
    end

    def remove_agent_feedback(feedback)
      sps = feedback.sourced_profile_sourcing
      return unless sps

      AgentFeedback.where(sourced_profile_sourcing_id: sps.id).destroy_all
    rescue StandardError => e
      Rails.logger.warn "[CandidateFeedbacks::UpsertService] remove_agent_feedback failed: #{e.message}"
    end

    def build_search_query_snapshot
      return {} if @sourcing.blank?

      {
        query: @sourcing.query,
        provider: @sourcing.provider,
        parameters: @sourcing.parameters,
        searched_at: @sourcing.searched_at,
        results_count: @sourcing.results_count
      }
    rescue StandardError => e
      Rails.logger.warn "[#{self.class.name}] Error building query snapshot: #{e.message}"
      {}
    end

    def build_candidate_score_snapshot
      snapshot = {}
      add_sourcing_scores(snapshot)
      add_apply_scores(snapshot)
      snapshot
    rescue StandardError => e
      Rails.logger.warn "[#{self.class.name}] Error building score snapshot: #{e.message}"
      {}
    end

    def add_sourcing_scores(snapshot)
      sourcing_profile = find_sourcing_profile
      return unless sourcing_profile

      snapshot[:sourcing_score] = sourcing_profile.score
      snapshot[:search_source] = sourcing_profile.search_source
      snapshot[:search_score] = sourcing_profile.search_score
    end

    def find_sourcing_profile
      return @sourced_profile_sourcing if @sourced_profile_sourcing.present?
      return nil unless @sourcing_id.present? && @candidate_id.present?

      sourced_profile_id = find_sourced_profile_id
      return nil unless sourced_profile_id

      SourcedProfileSourcing.find_by(
        sourcing_id: @sourcing_id,
        sourced_profile_id: sourced_profile_id
      )
    end

    def add_apply_scores(snapshot)
      return unless @apply.present?

      snapshot[:cv_match] = @apply.cv_match if @apply.respond_to?(:cv_match)
      snapshot[:total_score] = @apply.total_score if @apply.respond_to?(:total_score)
    end

    def find_sourced_profile_id
      return nil if @candidate_id.blank?

      sourced_profile = SourcedProfile.find_by(candidate_id: @candidate_id, account_id: @user.account_id)
      sourced_profile&.id
    end

    def success_result(feedback, action)
      {
        success: true,
        feedback: feedback,
        action: action,
        message: action_message(action)
      }
    end

    def error_result(message)
      {
        success: false,
        feedback: nil,
        action: :error,
        errors: message
      }
    end

    def action_message(action)
      {
        created: "Feedback created successfully",
        updated: "Feedback updated successfully",
        removed: "Feedback removed successfully"
      }[action]
    end
  end
end
