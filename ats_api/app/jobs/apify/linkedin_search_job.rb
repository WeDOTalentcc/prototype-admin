# frozen_string_literal: true

module Apify
  class LinkedinSearchJob
    include Sidekiq::Job

    sidekiq_options queue: :sourcing_search, retry: 2

    def perform(account_id, user_id, sourcing_id, params_json)
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.info "🔍 [LinkedinSearchJob] STARTING LINKEDIN SEARCH"
      Rails.logger.info "   account_id: #{account_id}"
      Rails.logger.info "   sourcing_id: #{sourcing_id}"
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

      account = Account.find(account_id)
      user = User.find(user_id)

      Current.user = user
      Current.account = account

      Apartment::Tenant.switch!(account.tenant)

      sourcing = Sourcing.find(sourcing_id)
      sourcing.update!(status: "processing")
      broadcast_status(sourcing, "sourcing_started")

      params = parse_params(params_json)
      result = Apify::LinkedinSearchExecutorService.new(user: user, sourcing: sourcing, params: params).call

      broadcast_status(sourcing.reload, result[:success] ? "sourcing_completed" : "sourcing_failed", result)

      Rails.logger.info "🔍 [LinkedinSearchJob] #{result[:success] ? '✅' : '❌'} LINKEDIN SEARCH #{result[:success] ? 'COMPLETED' : 'FAILED'}"
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    rescue StandardError => e
      Rails.logger.error "🔍 [LinkedinSearchJob] ❌ ERROR: #{e.message}"
      Rails.logger.error e.backtrace.first(10).join("\n")
      handle_error(account_id, sourcing_id, e)
    end

    private

    def parse_params(params_json)
      JSON.parse(params_json, symbolize_names: true)
    rescue JSON::ParserError
      {}
    end

    def broadcast_status(sourcing, event_type, result = {})
      serialized = SourcingSerializer.new(sourcing).serializable_hash[:data][:attributes]

      SourcingChannel.broadcast_to(
        "#{sourcing.user_id}_sourcing_#{sourcing.id}",
        { type: event_type, sourcing: serialized, success: result[:success], error: result[:error] }.compact
      )
    end

    def handle_error(account_id, sourcing_id, exception)
      account = Account.find_by(id: account_id)
      return unless account

      Apartment::Tenant.switch!(account.tenant)
      sourcing = Sourcing.find_by(id: sourcing_id)
      return unless sourcing

      sourcing.update(status: "failed")
      broadcast_status(sourcing, "sourcing_failed", { success: false, error: exception.message })
    end
  end
end
