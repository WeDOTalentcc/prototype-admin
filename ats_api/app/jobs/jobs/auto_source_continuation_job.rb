# frozen_string_literal: true

module Jobs
  class AutoSourceContinuationJob
    include Sidekiq::Job

    sidekiq_options queue: :default, retry: 2

    def perform(job_id, target_count, user_id)
      @job = Job.find_by(id: job_id)
      return unless @job

      @user = User.find_by(id: user_id)
      return unless @user

      Apartment::Tenant.switch(@user.account.tenant) do
        execute_continuation(target_count)
      end
    rescue => e
      Rails.logger.error "[AutoSourceContinuationJob] Failed for job #{job_id}: #{e.message}"
    end

    private

    def execute_continuation(target_count)
      metadata = @job.auto_source_metadata || {}
      total_added = metadata["total_added"] || 0
      remaining = target_count - total_added

      return if remaining <= 0

      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.info "🔄 [AutoSourceContinuation] Continuing auto source"
      Rails.logger.info "   Job: #{@job.id} - #{@job.title}"
      Rails.logger.info "   Added so far: #{total_added}"
      Rails.logger.info "   Still need: #{remaining}"
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

      min_score = metadata.dig("last_sourcing_min_score") || 70.0
      sources = metadata["sources"] || [ "local" ]

      result = ::Jobs::AutoSourcePaginationService.call(
        job: @job,
        user: @user,
        target_count: target_count,
        min_score_threshold: min_score,
        sources: sources
      )

      if result[:success]
        Rails.logger.info "✅ [AutoSourceContinuation] Next batch enqueued (sourcing #{result[:sourcing_id]})"
      else
        Rails.logger.warn "⚠️  [AutoSourceContinuation] No more pages to search: #{result[:error]}"
        broadcast_auto_source_finished(metadata, target_count, result[:error])
      end
    end

    def broadcast_auto_source_finished(metadata, target_count, error_reason)
      total_added = metadata["total_added"] || 0
      last_sourcing_id = metadata["last_sourcing_id"]

      return unless last_sourcing_id

      sourcing = Sourcing.find_by(id: last_sourcing_id)
      return unless sourcing

      SourcingChannel.broadcast_to(
        "#{@user.id}_sourcing_#{sourcing.id}",
        {
          type: "auto_source_finished",
          sourcing_id: sourcing.id,
          job_id: @job.id,
          status: "completed",
          phase: "finished",
          message: "Auto Source finished. Added #{total_added} of #{target_count} candidates (#{error_reason})",
          progress: {
            candidates_added: total_added,
            target: target_count,
            percentage: target_count > 0 ? ((total_added.to_f / target_count) * 100).round : 0
          },
          completion: {
            reason: error_reason,
            can_request_more: false
          },
          timestamp: Time.current.iso8601
        }
      )

      Rails.logger.info "📢 [AutoSourceContinuation] Broadcasted 'auto_source_finished'"
    end
  end
end
