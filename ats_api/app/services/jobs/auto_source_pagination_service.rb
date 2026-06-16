# frozen_string_literal: true

module Jobs
  class AutoSourcePaginationService
    MAX_PAGES_PER_RUN = 4
    CANDIDATES_PER_PAGE = 30

    def self.call(job:, user:, target_count:, min_score_threshold:, sources: [ "local" ], reset: false)
      new(job, user, target_count, min_score_threshold, sources, reset).call
    end

    def initialize(job, user, target_count, min_score_threshold, sources, reset)
      @job = job
      @user = user
      @account = user.account
      @target_count = target_count
      @min_score_threshold = min_score_threshold
      @sources = Array(sources).presence || [ "local" ]
      @reset = reset
    end

    def call
      reset_metadata_if_needed

      metadata = @job.auto_source_metadata || {}
      current_page = (metadata["last_page"] || 0) + 1
      pages_to_search = calculate_pages_needed(current_page)

      return target_already_reached_result(metadata) if pages_to_search.zero?

      query = Candidates::SuggestionService.generate_concise_query_from_job(@job)

      sourcing = create_sourcing(query, current_page, pages_to_search)

      broadcast_auto_source_started(sourcing, current_page, pages_to_search, metadata)

      enqueue_paginated_search(sourcing, query, current_page, pages_to_search)

      create_success_result(sourcing, current_page, pages_to_search)
    end

    private

    def reset_metadata_if_needed
      return force_reset_metadata if @reset

      metadata = @job.auto_source_metadata || {}
      last_title = metadata["last_title"]
      last_description = metadata["last_description"]

      title_changed = last_title.present? && last_title != @job.title
      description_changed = last_description.present? && last_description != @job.description

      return unless title_changed || description_changed

      Rails.logger.info "🔄 [AutoSourcePagination] Job #{@job.id} changed - resetting metadata"
      Rails.logger.info "   Title changed: #{title_changed}" if title_changed
      Rails.logger.info "   Description changed: #{description_changed}" if description_changed

      force_reset_metadata
    end

    def force_reset_metadata
      Rails.logger.info "🔄 [AutoSourcePagination] Resetting metadata for job #{@job.id} (reset=#{@reset})"

      @job.update!(
        auto_source_metadata: {
          last_title: @job.title,
          last_description: @job.description,
          last_page: 0,
          total_searched: 0,
          total_added: 0,
          reset_at: Time.current.iso8601
        }
      )
    end

    def calculate_pages_needed(current_page)
      metadata = @job.auto_source_metadata || {}
      total_added = metadata["total_added"] || 0

      remaining = @target_count - total_added
      return 0 if remaining <= 0

      estimated_pages = (remaining.to_f / expected_qualified_per_page).ceil

      [ estimated_pages, MAX_PAGES_PER_RUN ].min
    end

    def expected_qualified_per_page
      (@min_score_threshold >= 80) ? 5 : 10
    end

    def create_sourcing(query, start_page, num_pages)
      @account.sourcings.create!(
        user: @user,
        uid: SecureRandom.uuid,
        provider: @sources.include?("global") ? "hybrid" : "local",
        query: query,
        parameters: {
          sources: @sources,
          auto_add_job_id: @job.id,
          min_score_threshold: @min_score_threshold,
          pagination: {
            start_page: start_page,
            num_pages: num_pages,
            target_count: @target_count
          }
        },
        status: "processing",
        searched_at: Time.current
      )
    end

    def enqueue_paginated_search(sourcing, query, start_page, num_pages)
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.info "🚀 [AutoSourcePagination] Starting paginated search"
      Rails.logger.info "   Job: #{@job.id} - #{@job.title}"
      Rails.logger.info "   Sources: #{@sources.join(', ')}"
      Rails.logger.info "   Pages: #{start_page} to #{start_page + num_pages - 1}"
      Rails.logger.info "   Target: #{@target_count} candidates"
      Rails.logger.info "   Min Score: #{@min_score_threshold}%"
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

      @sources.each do |source|
        Sourcings::JobEnqueuerService.new(
          user: @user,
          sourcing: sourcing,
          query: query,
          params: {
            source: source,
            max_pages: num_pages,
            limit: CANDIDATES_PER_PAGE
          }
        ).call
      end
    end

    def create_success_result(sourcing, current_page, pages_to_search)
      {
        success: true,
        sourcing_id: sourcing.id,
        uid: sourcing.uid,
        status: sourcing.status,
        pagination: {
          current_page: current_page,
          pages_to_search: pages_to_search,
          max_page: current_page + pages_to_search - 1
        }
      }
    end

    def target_already_reached_result(metadata)
      total_added = metadata["total_added"] || 0

      {
        success: false,
        error: "Target already reached. Job already has #{total_added} candidates from Auto Source. " \
               "Send reset=true to start a fresh search, or increase the limit above #{total_added}.",
        metadata: metadata
      }
    end

    def broadcast_auto_source_started(sourcing, current_page, pages_to_search, metadata)
      total_added = metadata["total_added"] || 0
      remaining = @target_count - total_added

      SourcingChannel.broadcast_to(
        "#{@user.id}_sourcing_#{sourcing.id}",
        {
          type: "auto_source_started",
          sourcing_id: sourcing.id,
          job_id: @job.id,
          job_title: @job.title,
          status: "searching",
          phase: "search",
          message: "Searching for qualified candidates...",
          progress: {
            current_page: current_page,
            pages_this_batch: pages_to_search,
            max_page: current_page + pages_to_search - 1,
            candidates_found: 0,
            candidates_added: total_added,
            target: @target_count,
            remaining: remaining,
            percentage: total_added > 0 ? ((total_added.to_f / @target_count) * 100).round : 0
          },
          timestamp: Time.current.iso8601
        }
      )

      Rails.logger.info "📢 [AutoSourcePagination] Broadcasted 'auto_source_started' for job #{@job.id}"
    end
  end
end
