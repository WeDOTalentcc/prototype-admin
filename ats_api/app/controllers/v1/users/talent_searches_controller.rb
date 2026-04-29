module V1
  module Users
    class TalentSearchesController < ApplicationController
      before_action :check_credits, only: [ :create ]

      def create
        return render_bad_request("Query parameter is required") if params[:query].blank?

        sources = parse_sources

        return handle_local_search if sources.include?("local") && !sources.include?("global") && !sources.include?("linkedin")
        return handle_linkedin_search if sources.include?("linkedin")
        return handle_global_search if sources.include?("global")

        render_bad_request("Invalid source. Use 'local', 'global', or 'linkedin'")
      end

      def credits
        render json: credits_service.statistics(start_date: parse_date(:start_date), end_date: parse_date(:end_date)), status: :ok
      rescue ArgumentError => e
        render json: { error: "Invalid date format: #{e.message}" }, status: :bad_request
      end

      def search_profiles
        render json: {
          profiles: Pearch::SearchProfiles.all,
          current_balance: @current_user.account.pearch_credits,
          notes: Pearch::SearchProfiles.cost_notes
        }, status: :ok
      end

      def transactions
        render json: transaction_response, status: :ok
      rescue ArgumentError => e
        render json: { error: "Invalid date format: #{e.message}" }, status: :bad_request
      end

      private

      def render_bad_request(error_message)
        render json: { error: error_message }, status: :bad_request
      end

      def render_payment_required(error_message, balance = 0)
        render json: { error: error_message, current_balance: balance }, status: :payment_required
      end

      def render_error(error_message, balance = nil, status = :unprocessable_entity)
        render json: { error: error_message, current_balance: balance }.compact, status: status
      end

      def render_success(data, status = :ok)
        render json: data, status: status
      end

      def render_accepted(sourcing, message)
        render json: {
          sourcing_id: sourcing.id,
          uid: sourcing.uid,
          status: sourcing.status,
          message: message
        }, status: :accepted
      end

      def parse_sources
        sources = params[:sources] || params[:source]
        return [ "global" ] if sources.blank?

        sources = [ sources ] unless sources.is_a?(Array)
        sources = sources.map(&:to_s).map(&:downcase).uniq
        sources & [ "local", "global", "linkedin" ]
      end

      def handle_local_search
        sourcing = create_sourcing("local")

        return execute_local_hybrid_search(sourcing) unless async_mode?

        enqueue_local_search(sourcing)
        render_accepted(sourcing, "Local search enqueued. Subscribe to sourcing_#{sourcing.id} channel for updates.")
      end

      def handle_global_search
        sourcing = create_sourcing("pearch")

        return execute_async_search(sourcing) if async_mode?

        result = execute_pearch_search(sourcing)
        return render_error(result[:error], result[:current_balance], result[:status]) unless result[:success]

        render_success(result[:data].merge(sourcing_id: sourcing.id))
      end

      def handle_linkedin_search
        sourcing = create_sourcing("linkedin")
        linkedin_params = build_linkedin_params

        ::Apify::LinkedinSearchJob.perform_async(
          @current_user.account.id,
          @current_user.id,
          sourcing.id,
          linkedin_params.to_json
        )

        render_accepted(sourcing, "LinkedIn search enqueued. Subscribe to sourcing_#{sourcing.id} channel for updates.")
      end

      def execute_local_hybrid_search(sourcing)
        service = Candidates::Search::HybridSearchService.new(
          account_id: @current_user.account_id,
          tenant: @current_user.account.tenant
        )

        result = service.search(
          params[:query],
          user_filters: build_user_filters,
          limit: params[:limit]&.to_i || 50
        )

        sourcing.update!(
          search_metadata: result.metadata.to_json,
          search_explanation: result.explanation&.to_json,
          results_count: result.candidates.size,
          status: "done"
        )

        render_success(
          candidates: result.candidates.as_json,
          sourcing_id: sourcing.id,
          metadata: result.metadata
        )
      rescue => e
        sourcing.update!(status: "error")
        Rails.logger.error("Local hybrid search failed: #{e.message}")
        render_error("Search failed: #{e.message}")
      end

      def build_user_filters
        filters = params.slice(:city, :state, :remote_work, :position_level, :years_of_experience_min,
                               :years_of_experience_max, :role_name, :skills, :languages).to_unsafe_h

        filters.merge(params[:where]&.to_unsafe_h || {}).merge(params[:filter]&.to_unsafe_h || {})
      end

      def async_mode?
        params[:async] == "true"
      end

      def create_sourcing(provider = "pearch")
        @current_user.account.sourcings.create!(
          user: @current_user,
          uid: SecureRandom.uuid,
          provider: provider,
          query: params[:query],
          parameters: filtered_params,
          status: "processing",
          searched_at: Time.current
        )
      end

      def enqueue_local_search(sourcing)
        max_pages = params[:max_pages]&.to_i || 1

        Candidates::LocalSearchJob.perform_async(
          @current_user.account.id,
          @current_user.id,
          sourcing.id,
          params[:query],
          (params[:where] || {}).to_json,
          (params[:filter] || {}).to_json,
          (params[:order] || {}).to_json,
          max_pages
        )
      end

      def execute_async_search(sourcing)
        enqueue_pearch_search_job(sourcing)
        render_accepted(sourcing, "Global search enqueued. Subscribe to sourcing_#{sourcing.id} channel for updates.")
      end

      def enqueue_pearch_search_job(sourcing)
        ::Pearch::TalentSearchJob.perform_async(
          @current_user.account.id,
          @current_user.id,
          sourcing.id,
          params[:query],
          filtered_params.to_json
        )
      end

      def execute_pearch_search(sourcing)
        ::Pearch::TalentSearchExecutorService.new(
          user: @current_user,
          query: params[:query],
          params: params.merge(sourcing_id: sourcing.id)
        ).call
      end

      def credits_service
        @credits_service ||= ::Pearch::CreditsService.new(@current_user.account)
      end

      def filtered_params
        params.except(:controller, :action, :query, :async, :sourcing_id).to_unsafe_h
      end

      def parse_date(key)
        return nil unless params[key]
        Date.parse(params[key])
      end

      def transaction_response
        {
          current_balance: credits_service.current_balance,
          total_consumed: credits_service.total_consumed,
          transactions: fetch_transactions.as_json(only: [
            :id, :transaction_type, :amount, :balance_before, :balance_after,
            :reason, :reference_id, :reference_type, :created_at
          ])
        }
      end

      def fetch_transactions
        credits_service.transaction_history(
          limit: [ params[:limit]&.to_i || 50, 100 ].min,
          start_date: parse_date(:start_date),
          end_date: parse_date(:end_date)
        )
      end

      def check_credits
        sources = parse_sources
        return if sources.include?("linkedin")
        return if @current_user.account.pearch_credits.positive?

        render_payment_required(
          "No credits available. Please contact support to purchase credits.",
          0
        )
      end

      def build_linkedin_params
        {
          query: params[:query],
          current_job_titles: params[:current_job_titles],
          past_job_titles: params[:past_job_titles],
          locations: params[:locations],
          current_companies: params[:current_companies],
          past_companies: params[:past_companies],
          schools: params[:schools],
          industries: params[:industries],
          years_of_experience: params[:years_of_experience],
          mode: params[:linkedin_mode] || "full_with_email",
          take_pages: params[:take_pages],
          max_items: params[:max_items]
        }.compact
      end
    end
  end
end
