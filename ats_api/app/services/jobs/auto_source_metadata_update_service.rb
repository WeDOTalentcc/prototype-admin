# frozen_string_literal: true

module Jobs
  class AutoSourceMetadataUpdateService
    def self.call(job:, sourcing:, added_count:)
      new(job, sourcing, added_count).call
    end

    def initialize(job, sourcing, added_count)
      @job = job
      @sourcing = sourcing
      @added_count = added_count
    end

    def call
      metadata = @job.auto_source_metadata || {}
      pagination = @sourcing.parameters.dig("pagination") || {}

      current_page = pagination["start_page"] || 1
      num_pages = pagination["num_pages"] || 1
      target_count = pagination["target_count"] || 0
      min_score = @sourcing.parameters.dig("min_score_threshold") || 70.0

      new_metadata = metadata.merge(
        last_title: @job.title,
        last_description: @job.description,
        last_page: current_page + num_pages - 1,
        total_searched: (metadata["total_searched"] || 0) + (num_pages * 30),
        total_added: (metadata["total_added"] || 0) + @added_count,
        last_sourcing_id: @sourcing.id,
        last_sourcing_min_score: min_score,
        sources: @sourcing.parameters.dig("sources") || [ "local" ],
        updated_at: Time.current.iso8601
      )

      @job.update!(auto_source_metadata: new_metadata)

      Rails.logger.info "✅ [AutoSourceMetadataUpdate] Updated job #{@job.id} metadata"
      Rails.logger.info "   Pages searched: #{current_page} to #{current_page + num_pages - 1}"
      Rails.logger.info "   Added this run: #{@added_count}"
      Rails.logger.info "   Total added: #{new_metadata['total_added']}"
      Rails.logger.info "   Target: #{target_count}"

      will_continue = check_and_trigger_next_batch(new_metadata, target_count)
      broadcast_batch_completed(new_metadata, target_count, will_continue)
    end

    private

    def check_and_trigger_next_batch(metadata, target_count)
      return false if target_count.zero?

      total_added = metadata["total_added"] || 0
      remaining = target_count - total_added

      return false if remaining <= 0

      Rails.logger.info "🔄 [AutoSourceMetadataUpdate] Need #{remaining} more candidates, checking if should continue..."

      last_page = metadata["last_page"] || 0
      return false if last_page >= 10

      Rails.logger.info "🚀 [AutoSourceMetadataUpdate] Triggering next batch search"

      Jobs::AutoSourceContinuationJob.perform_async(@job.id, target_count, @sourcing.user_id)
      true
    end

    def broadcast_batch_completed(metadata, target_count, will_continue)
      total_added = metadata["total_added"] || 0
      total_searched = metadata["total_searched"] || 0
      remaining = target_count - total_added
      percentage = target_count > 0 ? ((total_added.to_f / target_count) * 100).round : 0

      target_reached = remaining <= 0
      max_pages_reached = (metadata["last_page"] || 0) >= 10

      status = if target_reached
        "completed"
      elsif max_pages_reached
        "completed_partial"
      elsif will_continue
        "continuing"
      else
        "completed"
      end

      message = if target_reached
        "✅ Target reached! Added #{total_added} candidates."
      elsif max_pages_reached
        "⚠️ Max pages reached. Added #{total_added} of #{target_count} candidates."
      elsif will_continue
        "🔄 Batch complete. Found #{total_added}/#{target_count}, continuing search..."
      else
        "✅ Search complete. Added #{total_added} candidates."
      end

      SourcingChannel.broadcast_to(
        "#{@sourcing.user_id}_sourcing_#{@sourcing.id}",
        {
          type: "auto_source_batch_completed",
          sourcing_id: @sourcing.id,
          job_id: @job.id,
          status: status,
          phase: will_continue ? "continuing" : "completed",
          message: message,
          progress: {
            candidates_searched: total_searched,
            candidates_added: total_added,
            target: target_count,
            remaining: remaining,
            percentage: percentage,
            last_page: metadata["last_page"],
            max_pages: 10
          },
          completion: {
            target_reached: target_reached,
            max_pages_reached: max_pages_reached,
            will_continue: will_continue,
            can_request_more: !max_pages_reached && !target_reached
          },
          timestamp: Time.current.iso8601
        }
      )

      Rails.logger.info "📢 [AutoSourceMetadataUpdate] Broadcasted 'batch_completed' - status: #{status}"
    end
  end
end
