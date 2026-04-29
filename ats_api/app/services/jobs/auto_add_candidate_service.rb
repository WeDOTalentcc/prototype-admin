# frozen_string_literal: true

module Jobs
  class AutoAddCandidateService
    def self.call(sourced_profile_sourcing:, job_id:, account:, user:)
      new(sourced_profile_sourcing, job_id, account, user).call
    end

    def initialize(sourced_profile_sourcing, job_id, account, user)
      @sps = sourced_profile_sourcing
      @job_id = job_id
      @account = account
      @user = user
    end

    def call
      job = Job.find_by(id: @job_id)
      return unless job

      candidate = @sps.sourced_profile.candidate
      return unless candidate

      selective_process = job.selective_processes.order(:position).first
      return unless selective_process

      apply = Apply.find_or_create_apply(
        candidate_id: candidate.id,
        job_id: @job_id,
        account_id: @account.id,
        selective_process_id: selective_process.id,
        selective_process_status: selective_process.name,
        user_id: @user.id
      )

      broadcast_candidate_added(apply)
      broadcast_to_kanban(apply, selective_process)

      Rails.logger.info "✅ [AutoAddCandidateService] Added candidate #{candidate.id} to job #{@job_id} via auto_source"
    rescue => e
      Rails.logger.error "[AutoAddCandidateService] Failed for sourced_profile_sourcing #{@sps.id}: #{e.message}"
    end

    private

    def broadcast_candidate_added(apply)
      SourcingChannel.broadcast_to(
        "#{@sps.sourcing.user_id}_sourcing_#{@sps.sourcing_id}",
        {
          type: "candidate_added_to_job",
          sourcing_id: @sps.sourcing_id,
          job_id: @job_id,
          candidate_id: apply.candidate_id,
          apply_id: apply.id,
          sourced_profile_sourcing_id: @sps.id,
          score: @sps.score
        }
      )
    rescue => e
      Rails.logger.error "[AutoAddCandidateService] Broadcast failed: #{e.message}"
    end

    def broadcast_to_kanban(apply, selective_process)
      ApplyCollectionChannel.broadcast_to(
        apply_collection_stream_id,
        {
          type: "item_completed",
          timestamp: Time.current.iso8601,
          apply_id: apply.id,
          candidate_id: apply.candidate_id,
          selective_process_id: selective_process.id,
          apply: serialize_apply(apply),
          source: "auto_source",
          score: @sps.score
        }
      )

      Rails.logger.info "📢 [AutoAddCandidateService] Broadcasted to kanban (ApplyCollectionChannel)"
    rescue => e
      Rails.logger.error "[AutoAddCandidateService] Kanban broadcast failed: #{e.message}"
    end

    def apply_collection_stream_id
      parts = [ @user.id, "apply_collection", @job_id ]
      parts << selective_process.id if selective_process.present?
      parts.join("_")
    end

    def selective_process
      @selective_process ||= SelectiveProcess.find_by(
        job_id: @job_id,
        position: 1
      )
    end

    def serialize_apply(apply)
      ApplySerializer.new(apply).serializable_hash.dig(:data, :attributes)
    end
  end
end
