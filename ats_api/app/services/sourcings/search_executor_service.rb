module Sourcings
  class SearchExecutorService
    Result = Struct.new(:success, :data, :error, :status, :current_balance, keyword_init: true)

    def initialize(user:, sourcing:, query:, params:)
      @user = user
      @account = user.account
      @sourcing = sourcing
      @query = query
      @params = params
    end

    def call
      return execute_local_search if @sourcing.local?
      execute_global_search
    end

    private

    def execute_local_search
      broadcast_search_started("local")

      service = Candidates::Search::HybridSearchService.new(
        account_id: @account.id,
        tenant: @account.tenant,
        sourcing_id: @sourcing.id,
        user_id: @user.id
      )

      result = service.search(
        @query,
        user_filters: build_user_filters,
        limit: @params[:limit]&.to_i || 10,
        debug: true
      )

      @sourcing.update!(
        search_metadata: result.metadata.merge(
          query: @query,
          filters: build_user_filters,
          params: @params
        ).to_json,
        search_explanation: result.explanation&.to_json,
        results_count: result.candidates.size,
        status: "done"
      )

      Result.new(
        success: true,
        data: {
          candidates: result.candidates.as_json,
          sourcing_id: @sourcing.id,
          metadata: result.metadata
        }
      )
    rescue => e
      @sourcing.update!(status: "error")
      Rails.logger.error("Local hybrid search failed: #{e.message}")

      Result.new(
        success: false,
        error: "Search failed: #{e.message}",
        status: :unprocessable_entity
      )
    end

    def execute_global_search
      broadcast_search_started("global")

      merged = @params.merge(sourcing_id: @sourcing.id)
      merged[:limit] = Sourcings::FirstBatchPageSize.for_sourcing(@sourcing) if merged[:offset].to_i.zero?

      Pearch::TalentSearchExecutorService.new(
        user: @user,
        query: @query,
        params: merged
      ).call
    end

    def broadcast_search_started(search_type)
      SourcingChannel.broadcast_to(
        "#{@user.id}_sourcing_#{@sourcing.id}",
        {
          type: "search_started",
          sourcing_id: @sourcing.id,
          search_type: search_type,
          timestamp: Time.current.iso8601,
          message: search_type == "local" ? "Iniciando busca local..." : "Iniciando busca global..."
        }
      )
    rescue => e
      Rails.logger.error("[SearchExecutorService] Failed to broadcast search_started: #{e.message}")
    end

    def build_user_filters
      filters = @params.slice(
        :city, :state, :remote_work, :position_level,
        :years_of_experience_min, :years_of_experience_max,
        :role_name, :skills, :languages
      ).to_h

      filters.merge(@params[:where] || {}).merge(@params[:filter] || {})
    end
  end
end
