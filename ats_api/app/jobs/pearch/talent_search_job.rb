module Pearch
  class TalentSearchJob
    include Sidekiq::Job

    sidekiq_options queue: :sourcing_search, retry: 2

    def perform(account_id, user_id, sourcing_id, query, params_json)
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.info "🌍 [PearchSearchJob] STARTING GLOBAL SEARCH"
      Rails.logger.info "   account_id: #{account_id}"
      Rails.logger.info "   user_id: #{user_id}"
      Rails.logger.info "   sourcing_id: #{sourcing_id}"
      Rails.logger.info "   query: #{query}"
      Rails.logger.info "   params_json: #{params_json}"
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

      account = Account.find(account_id)
      user = User.find(user_id)
      params = parse_params(params_json)

      Current.user = user
      Current.account = account

      Rails.logger.info "[PearchSearchJob] Parsed params: #{params.inspect}"

      Apartment::Tenant.switch!(account.tenant)
      Rails.logger.info "[PearchSearchJob] Switched to tenant: #{account.tenant}"

      sourcing = Sourcing.find(sourcing_id)
      Rails.logger.info "[PearchSearchJob] Found sourcing: #{sourcing.inspect}"

      sourcing.update!(status: "processing")
      broadcast_sourcing_started(sourcing)
      Rails.logger.info "[PearchSearchJob] Sourcing status updated to 'processing'"

      result = execute_search(user, query, params, sourcing)
      Rails.logger.info "[PearchSearchJob] Search executed. Success: #{result[:success]}"
      Rails.logger.info "[PearchSearchJob] Result: #{result.inspect}"

      update_sourcing_with_result(sourcing, result)
      broadcast_sourcing_completed(sourcing, result)

      Rails.logger.info "🌍 [PearchSearchJob] ✅ GLOBAL SEARCH COMPLETED"
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    rescue => e
      Rails.logger.error "🌍 [PearchSearchJob] ❌ ERROR: #{e.message}"
      Rails.logger.error e.backtrace.join("\n")
      handle_error(account_id, sourcing_id, e)
    end

    private

    def parse_params(params_json)
      JSON.parse(params_json, symbolize_names: true)
    rescue JSON::ParserError
      {}
    end

    def execute_search(user, query, params, sourcing)
      params = params.deep_dup
      if params[:offset].to_i.zero?
        params[:limit] = Sourcings::FirstBatchPageSize.for_sourcing(sourcing)
      end
      params_with_sourcing = params.merge(sourcing_id: sourcing.id)

      Rails.logger.info "[PearchSearchJob] Calling TalentSearchExecutorService with:"
      Rails.logger.info "  user_id: #{user.id}"
      Rails.logger.info "  query length: #{query&.length || 0} chars"
      Rails.logger.info "  sourcing_id: #{params_with_sourcing[:sourcing_id]}"

      service = TalentSearchExecutorService.new(
        user: user,
        query: query,
        params: params_with_sourcing
      )

      result = service.call

      Rails.logger.info "[PearchSearchJob] TalentSearchExecutorService returned:"
      Rails.logger.info "  success: #{result[:success]}"
      Rails.logger.info "  data keys: #{result[:data]&.keys}"
      Rails.logger.info "  search_results count: #{result[:data]&.[](:search_results)&.size || 0}"

      result
    end

    def update_sourcing_with_result(sourcing, result)
      unless result[:success]
        Rails.logger.warn "[PearchSearchJob] ⚠️ Search was not successful, skipping update"
        Rails.logger.warn "[PearchSearchJob] Error: #{result[:error]}"
        return
      end

      data = result[:data]
      results_count = (data[:search_results] || []).size

      Rails.logger.info "[PearchSearchJob] Updating sourcing #{sourcing.id} with #{results_count} results"

      sourcing.update!(
        external_id: data[:uuid],
        thread_id: data[:thread_id],
        duration: data[:duration],
        total_estimate: data[:total_estimate],
        total_estimate_is_lower_bound: data[:total_estimate_is_lower_bound] || false,
        results_count: results_count,
        credits_used: data[:credits_used],
        response_metadata: data.except(:search_results),
        status: "done"
      )

      Rails.logger.info "[PearchSearchJob] ✅ Sourcing updated successfully"

      enqueue_profile_processing(sourcing, data)
    end

    def enqueue_profile_processing(sourcing, data)
      return unless data[:search_results]&.any?

      ProcessSourcingJob.perform_async(
        sourcing.account_id,
        sourcing.user_id,
        sourcing.query,
        data.to_json,
        sourcing.parameters.to_json,
        sourcing.id
      )
    end

    def broadcast_sourcing_started(sourcing)
      serialized = SourcingSerializer.new(sourcing).serializable_hash[:data][:attributes]

      SourcingChannel.broadcast_to(
        "#{sourcing.user_id}_sourcing_#{sourcing.id}",
        {
          type: "sourcing_started",
          sourcing: serialized
        }
      )
    end

    def broadcast_sourcing_completed(sourcing, result)
      serialized = SourcingSerializer.new(sourcing).serializable_hash[:data][:attributes]

      SourcingChannel.broadcast_to(
        "#{sourcing.user_id}_sourcing_#{sourcing.id}",
        {
          type: "sourcing_completed",
          sourcing: serialized,
          success: result[:success],
          error: result[:error]
        }
      )
    end

    def handle_error(account_id, sourcing_id, exception)
      Rails.logger.error("[TalentSearchJob] Failed: #{exception.message}")
      Rails.logger.error(exception.backtrace.join("\n"))

      account = Account.find(account_id)
      Apartment::Tenant.switch!(account.tenant)

      sourcing = Sourcing.find_by(id: sourcing_id)
      return unless sourcing

      sourcing.update(status: "failed")
      serialized = SourcingSerializer.new(sourcing).serializable_hash[:data][:attributes]

      SourcingChannel.broadcast_to(
        "#{sourcing.user_id}_sourcing_#{sourcing.id}",
        {
          type: "sourcing_failed",
          sourcing: serialized,
          error: exception.message
        }
      )
    end
  end
end
