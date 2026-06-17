# frozen_string_literal: true

module V1
  module Webhooks
    module MicrosoftTeams
      class TeamsWebhookController < ApplicationController
        CHAT_ID_PATTERN = %r{chats[/(]'?([^)']+)'?\)?/messages}
        TENANT_CACHE_TTL = 1.hour

        def create
          return handle_validation if params[:validationToken].present?
          return head(:ok) if params[:value].blank?

          Array(params[:value]).each { |notification| process_notification(notification) }
          head :accepted
        end

        private

        def handle_validation
          render plain: params[:validationToken], status: :ok
        end

        def process_notification(notification)
          return handle_lifecycle_event(notification) if notification[:lifecycleEvent].present?

          chat_id = extract_chat_id(notification[:resource])
          return if chat_id.blank?

          subscription_id = notification[:subscriptionId] || notification["subscriptionId"]
          tenant = resolve_tenant_for_chat(subscription_id, chat_id)
          return if tenant.blank?

          teams_message_id = notification.dig(:resourceData, :id) || notification.dig("resourceData", "id")
          Microsoft::TeamsMessageIngestionJob.perform_async(chat_id, tenant, teams_message_id)
        rescue StandardError => e
          Rails.logger.error "[TeamsWebhook] #{e.message}"
        end

        def handle_lifecycle_event(notification)
          tenant = resolve_tenant_for_subscription(notification[:subscriptionId])
          return if tenant.blank?

          Apartment::Tenant.switch(tenant) do
            record = TeamsChatSubscription.find_by(subscription_id: notification[:subscriptionId])
            return unless record

            lia_user = User.find_by(id: record.lia_user_id)
            return unless lia_user

            MicrosoftService::TeamsSubscriptionService.create_or_renew(lia_user, record.chat_id)
          end
        rescue StandardError => e
          Rails.logger.error "[TeamsWebhook] Lifecycle error: #{e.message}"
        end

        def resolve_tenant_for_chat(subscription_id, chat_id)
          cache_key = "teams_sub_tenant:#{subscription_id}"
          cached = Rails.cache.read(cache_key)
          return cached if cached

          tenant = search_tenant_for_chat(chat_id)
          Rails.cache.write(cache_key, tenant, expires_in: TENANT_CACHE_TTL) if tenant
          tenant
        end

        def resolve_tenant_for_subscription(subscription_id)
          return if subscription_id.blank?

          cache_key = "teams_sub_tenant:#{subscription_id}"
          cached = Rails.cache.read(cache_key)
          return cached if cached

          tenant = search_tenant_for_subscription(subscription_id)
          Rails.cache.write(cache_key, tenant, expires_in: TENANT_CACHE_TTL) if tenant
          tenant
        end

        def search_tenant_for_chat(chat_id)
          Account.pluck(:tenant).each do |tenant|
            Apartment::Tenant.switch(tenant) do
              next unless ActiveRecord::Base.connection.table_exists?(:teams_chat_subscriptions)
              return tenant if TeamsChatSubscription.exists?(chat_id: chat_id)
            end
          end
          nil
        end

        def search_tenant_for_subscription(subscription_id)
          Account.pluck(:tenant).each do |tenant|
            Apartment::Tenant.switch(tenant) do
              next unless ActiveRecord::Base.connection.table_exists?(:teams_chat_subscriptions)
              return tenant if TeamsChatSubscription.exists?(subscription_id: subscription_id)
            end
          end
          nil
        end

        def extract_chat_id(resource)
          return if resource.blank?

          resource.match(CHAT_ID_PATTERN)&.[](1)
        end
      end
    end
  end
end
