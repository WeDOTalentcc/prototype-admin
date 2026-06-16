# frozen_string_literal: true

module MicrosoftService
  class TeamsSubscriptionDiagnosticService
    def self.run
      new.call
    end

    def self.call
      run
    end

    def call
      puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      puts "🔍 [TeamsSubscriptionDiagnostic] Running diagnostics"
      puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

      check_webhook_url
      check_subscriptions_status
      check_tokens
      check_microsoft_connectivity

      puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    end

    private

    def check_webhook_url
      host = ENV.fetch("APP_HOST", "http://localhost:3000")
      webhook_url = if host.start_with?("http://", "https://")
        "#{host}/v1/webhooks/teams_chat"
      else
        "https://#{host}/v1/webhooks/teams_chat"
      end

      puts "📍 Webhook URL: #{webhook_url}"

      if webhook_url.include?("ngrok")
        puts "⚠️  Using ngrok - URL may change on tunnel restart"
      elsif webhook_url.include?("localhost")
        puts "❌ Using localhost - won't work with Microsoft"
      else
        puts "✅ Using production URL"
      end
    end

    def check_subscriptions_status
      total = 0
      active_count = 0
      failed_count = 0
      expired_count = 0
      expiring_soon_count = 0

      each_tenant_with_subscriptions do |tenant|
        subs = TeamsChatSubscription.all
        next if subs.empty?

        total += subs.count
        active_count += TeamsChatSubscription.active.count
        failed_count += TeamsChatSubscription.failed.count
        expired_count += TeamsChatSubscription.where(status: "expired").count
        expiring_soon_count += TeamsChatSubscription.expiring_soon.count

        puts "📊 Tenant: #{tenant}"
        puts "   Total: #{subs.count}"
        puts "   ✅ Active: #{TeamsChatSubscription.active.count}"
        puts "   ❌ Failed: #{TeamsChatSubscription.failed.count}"
        puts "   ⏰ Expired: #{TeamsChatSubscription.where(status: 'expired').count}"
        puts "   ⚠️  Expiring Soon: #{TeamsChatSubscription.expiring_soon.count}"

        subs.each do |sub|
          status_icon = case sub.status
          when "active" then "✅"
          when "failed" then "❌"
          when "expired" then "⏰"
          else "❓"
          end

          expires_in = if sub.subscription_expires_at
            distance = (sub.subscription_expires_at - Time.current) / 60
            "#{distance.round}min"
          else
            "N/A"
          end

          puts "   #{status_icon} Chat: #{sub.chat_id.first(30)}..."
          puts "      Status: #{sub.status}, Expires in: #{expires_in}"
          puts "      SubID: #{sub.subscription_id&.first(20)}#{sub.subscription_id ? '...' : 'nil'}"
        end
      end

      if total.zero?
        puts "⚠️  No subscriptions found in any tenant"
      elsif failed_count > 0
        puts "❌ #{failed_count} failed subscriptions need attention"
      elsif active_count == total
        puts "✅ All subscriptions are active"
      end
    end

    def check_tokens
      no_token_users = []

      each_tenant_with_subscriptions do |tenant|
        TeamsChatSubscription.find_each do |sub|
          lia_user = User.find_by(id: sub.lia_user_id)
          unless lia_user&.ms_access_token.present?
            no_token_users << "#{tenant}/User##{sub.lia_user_id}"
          end
        end
      end

      if no_token_users.any?
        puts "❌ Users without MS token:"
        no_token_users.each { |u| puts "   - #{u}" }
      else
        puts "✅ All LIA users have MS tokens"
      end
    end

    def check_microsoft_connectivity
      sample_sub = nil
      sample_tenant = nil

      each_tenant_with_subscriptions do |tenant|
        sub = TeamsChatSubscription.first
        if sub
          sample_sub = sub
          sample_tenant = tenant
          break
        end
      end

      return puts "⚠️  No subscriptions to test MS connectivity" unless sample_sub

      lia_user = User.find_by(id: sample_sub.lia_user_id)
      return puts "❌ Sample user has no token" unless lia_user&.ms_access_token

      Apartment::Tenant.switch(sample_tenant) do
        response = MicrosoftService::Api.get("/me", lia_user)
        if response&.dig("displayName")
          puts "✅ Microsoft Graph API: Connected (#{response['displayName']})"
        else
          puts "❌ Microsoft Graph API: Failed to connect"
        end
      end
    rescue StandardError => e
      puts "❌ Microsoft Graph API: #{e.message}"
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
