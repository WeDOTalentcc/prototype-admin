# frozen_string_literal: true

module MicrosoftService
  class TeamsSubscriptionResetService
    def self.reset_all_subscriptions(force_delete_ms: false, verbose: false)
      new(force_delete_ms, verbose).call
    end

    def self.nuke_and_recreate(verbose: true)
      new(true, verbose, nuke: true).call
    end

    def initialize(force_delete_ms = false, verbose = false, nuke: false)
      @force_delete_ms = force_delete_ms
      @verbose = verbose
      @nuke = nuke
      @results = { total: 0, recreated: 0, failed: 0, deleted_from_ms: 0, errors: [] }
    end

    def call
      log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      log "🔄 [TeamsSubscriptionReset] Starting subscription reset"
      log "   Force delete from MS: #{@force_delete_ms}"
      log "   Nuke mode: #{@nuke}"
      log "   Webhook URL: #{current_webhook_url}"
      log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

      purge_all_microsoft_subscriptions if @nuke

      each_tenant_with_subscriptions do |tenant|
        process_tenant_subscriptions(tenant)
      end

      print_summary
      @results
    end

    private

    def purge_all_microsoft_subscriptions
      log "🗑️  [Nuke] Listing ALL Microsoft Graph subscriptions..."

      lia_user = find_any_lia_user
      return log("❌ No LIA user with valid token found") unless lia_user

      response = MicrosoftService::Api.get("/subscriptions", lia_user)
      subs = response&.dig("value") || []

      log "   Found #{subs.size} subscriptions on Microsoft"

      subs.each do |sub|
        sub_id = sub["id"]
        resource = sub["resource"]
        expiry = sub["expirationDateTime"]
        log "   🔍 #{sub_id} → #{resource} (expires: #{expiry})"

        MicrosoftService::Api.delete("/subscriptions/#{sub_id}", lia_user)
        @results[:deleted_from_ms] += 1
        log "   🗑️  Deleted #{sub_id}"
      rescue StandardError => e
        log "   ⚠️  Failed to delete #{sub_id}: #{e.message}"
      end

      log "   ✅ Purged #{@results[:deleted_from_ms]} Microsoft subscriptions"
    rescue StandardError => e
      log "   ❌ Failed to list/purge MS subscriptions: #{e.message}"
    end

    def process_tenant_subscriptions(tenant)
      subs = TeamsChatSubscription.all.to_a
      return if subs.empty?

      log "\n📊 Tenant: #{tenant} (#{subs.size} subscriptions)"

      subs.each do |subscription|
        @results[:total] += 1

        lia_user = User.find_by(id: subscription.lia_user_id)
        unless lia_user&.ms_access_token.present?
          log "   ❌ #{subscription.chat_id.first(30)}: No valid token for lia_user_id=#{subscription.lia_user_id}"
          @results[:errors] << "#{tenant}/#{subscription.chat_id}: No valid token"
          @results[:failed] += 1
          next
        end

        if @force_delete_ms && !@nuke && subscription.subscription_id.present?
          delete_from_microsoft(subscription, lia_user)
        end

        reset_and_recreate(subscription, lia_user, tenant)
      end
    end

    def delete_from_microsoft(subscription, lia_user)
      MicrosoftService::Api.delete("/subscriptions/#{subscription.subscription_id}", lia_user)
      @results[:deleted_from_ms] += 1
      log "   🗑️  Deleted #{subscription.subscription_id} from Microsoft"
    rescue StandardError => e
      log "   ⚠️  Failed to delete from MS: #{e.message}"
    end

    def reset_and_recreate(subscription, lia_user, tenant)
      subscription.update!(
        subscription_id: nil,
        status: "expired",
        subscription_expires_at: nil
      )

      MicrosoftService::TeamsSubscriptionService.new(lia_user, subscription.chat_id).call

      subscription.reload
      if subscription.subscription_active?
        @results[:recreated] += 1
        log "   ✅ #{subscription.chat_id.first(30)}: Active (expires: #{subscription.subscription_expires_at})"
      else
        @results[:failed] += 1
        log "   ❌ #{subscription.chat_id.first(30)}: Failed to recreate (status: #{subscription.status})"
      end
    rescue StandardError => e
      @results[:failed] += 1
      error_msg = "#{tenant}/#{subscription.chat_id}: #{e.message}"
      @results[:errors] << error_msg
      log "   ❌ Error: #{error_msg}"
    end

    def print_summary
      log "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      log "📊 Summary"
      log "   Total subscriptions: #{@results[:total]}"
      log "   ✅ Recreated: #{@results[:recreated]}"
      log "   ❌ Failed: #{@results[:failed]}"
      log "   🗑️  Deleted from MS: #{@results[:deleted_from_ms]}"
      if @results[:errors].any?
        log "   Errors:"
        @results[:errors].each { |e| log "     - #{e}" }
      end
      log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    end

    def log(message)
      Rails.logger.info message
      puts message if @verbose
    end

    def current_webhook_url
      host = ENV.fetch("APP_HOST", "http://localhost:3000")
      return "#{host}/v1/webhooks/teams_chat" if host.start_with?("http://", "https://")

      "https://#{host}/v1/webhooks/teams_chat"
    end

    def find_any_lia_user
      each_tenant_with_subscriptions do |_tenant|
        TeamsChatSubscription.find_each do |sub|
          user = User.find_by(id: sub.lia_user_id)
          return user if user&.ms_access_token.present?
        end
      end
      nil
    end

    def each_tenant_with_subscriptions
      Account.pluck(:tenant).each do |tenant|
        Apartment::Tenant.switch(tenant) do
          next unless ActiveRecord::Base.connection.table_exists?(:teams_chat_subscriptions)

          yield tenant
        end
      end
    end
  end
end
