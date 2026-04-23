# frozen_string_literal: true

module MicrosoftService
  class TeamsSubscriptionService
    SUBSCRIPTION_EXPIRY_MINUTES = 55
    RESOURCE_TEMPLATE = "/chats/%s/messages"
    CHANGE_TYPE = "created"

    def self.create_or_renew(lia_user, chat_id)
      new(lia_user, chat_id).call
    end

    def self.renew_all_expiring
      each_tenant_with_subscriptions do |tenant|
        TeamsChatSubscription.expiring_soon.find_each do |record|
          lia_user = User.find_by(id: record.lia_user_id)
          unless lia_user&.ms_access_token.present?
            Rails.logger.warn "[TeamsSubscriptionService] No valid token for lia_user_id=#{record.lia_user_id} in #{tenant}"
            next
          end

          new(lia_user, record.chat_id).call
        rescue StandardError => e
          Rails.logger.error "[TeamsSubscriptionService] Renewal failed for #{record.chat_id} in #{tenant}: #{e.message}"
        end
      end
    end

    def self.renew_all_active
      each_tenant_with_subscriptions do |tenant|
        TeamsChatSubscription.active.find_each do |record|
          lia_user = User.find_by(id: record.lia_user_id)
          unless lia_user&.ms_access_token.present?
            Rails.logger.warn "[TeamsSubscriptionService] No valid token for lia_user_id=#{record.lia_user_id} in #{tenant}"
            next
          end

          record.update!(subscription_id: nil, status: "expired")
          new(lia_user, record.chat_id).call
          Rails.logger.info "[TeamsSubscriptionService] Recreated subscription for chat #{record.chat_id} in #{tenant}"
        rescue StandardError => e
          Rails.logger.error "[TeamsSubscriptionService] Recreation failed for #{record.chat_id} in #{tenant}: #{e.message}"
        end
      end
    end

    def self.retry_all_failed
      each_tenant_with_subscriptions do |tenant|
        TeamsChatSubscription.failed.find_each do |record|
          lia_user = User.find_by(id: record.lia_user_id)
          unless lia_user&.ms_access_token.present?
            Rails.logger.warn "[TeamsSubscriptionService] No valid token for lia_user_id=#{record.lia_user_id} in #{tenant}"
            next
          end

          record.update!(subscription_id: nil, status: "expired")
          new(lia_user, record.chat_id).call
          Rails.logger.info "[TeamsSubscriptionService] Retried failed subscription for chat #{record.chat_id} in #{tenant}"
        rescue StandardError => e
          Rails.logger.error "[TeamsSubscriptionService] Retry failed for #{record.chat_id} in #{tenant}: #{e.message}"
        end
      end
    end

    def self.each_tenant_with_subscriptions
      Account.pluck(:tenant).each do |tenant|
        Apartment::Tenant.switch(tenant) do
          next unless ActiveRecord::Base.connection.table_exists?(:teams_chat_subscriptions)

          yield tenant
        end
      end
    end

    def initialize(lia_user, chat_id)
      @lia_user = lia_user
      @chat_id = chat_id
    end

    def call
      record = TeamsChatSubscription.find_by(chat_id: @chat_id)
      return unless record

      return renew_subscription(record) if record.subscription_active?

      create_subscription(record)
    end

    private

    def create_subscription(record)
      expiration = SUBSCRIPTION_EXPIRY_MINUTES.minutes.from_now
      body = subscription_body(expiration)

      Rails.logger.info "[TeamsSubscriptionService] Creating subscription for chat #{@chat_id}"
      Rails.logger.info "[TeamsSubscriptionService] Webhook URL: #{build_webhook_url}"

      response = MicrosoftService::Api.post("/subscriptions", @lia_user, body: body)

      unless response&.dig("id")
        Rails.logger.error "[TeamsSubscriptionService] MS returned no subscription ID. Response: #{response.inspect}"
        return record.update!(status: "failed")
      end

      record.update!(
        subscription_id: response["id"],
        subscription_expires_at: expiration,
        status: "active"
      )

      Rails.logger.info "[TeamsSubscriptionService] ✅ Created subscription #{response['id']} for #{@chat_id}"
    rescue StandardError => e
      Rails.logger.error "[TeamsSubscriptionService] Failed to create subscription for #{@chat_id}: #{e.class} #{e.message}"
      Rails.logger.error "[TeamsSubscriptionService] #{e.backtrace&.first(3)&.join("\n")}"
      record.update!(status: "failed")
    end

    def renew_subscription(record)
      expiration = SUBSCRIPTION_EXPIRY_MINUTES.minutes.from_now
      body = { expirationDateTime: expiration.utc.iso8601 }

      MicrosoftService::Api.patch("/subscriptions/#{record.subscription_id}", @lia_user, body: body)
      record.update!(subscription_expires_at: expiration)
    rescue StandardError => e
      Rails.logger.error "[TeamsSubscriptionService] Renewal failed, recreating: #{e.message}"
      record.update!(subscription_id: nil, status: "expired")
      create_subscription(record)
    end

    def subscription_body(expiration)
      {
        changeType: CHANGE_TYPE,
        notificationUrl: build_webhook_url,
        resource: format(RESOURCE_TEMPLATE, @chat_id),
        expirationDateTime: expiration.utc.iso8601,
        clientState: Rails.application.credentials.secret_key_base.first(32)
      }
    end

    def build_webhook_url
      host = ENV.fetch("APP_HOST", "http://localhost:3000")
      return "#{host}/v1/webhooks/teams_chat" if host.start_with?("http://", "https://")

      "https://#{host}/v1/webhooks/teams_chat"
    end
  end
end
