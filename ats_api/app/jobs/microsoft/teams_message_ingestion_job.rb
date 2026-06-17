# frozen_string_literal: true

module Microsoft
  class TeamsMessageIngestionJob
    include Sidekiq::Job

    sidekiq_options queue: :default, retry: 2

    DEDUP_TTL = 30

    def perform(chat_id, tenant, teams_message_id = nil)
      lock_suffix = teams_message_id || chat_id
      lock_key = "teams_ingestion:#{chat_id}:#{lock_suffix}"
      locked = Sidekiq.redis { |conn| conn.set(lock_key, "1", nx: true, ex: DEDUP_TTL) }
      return unless locked

      Apartment::Tenant.switch(tenant) do
        subscription = TeamsChatSubscription.find_by(chat_id: chat_id, status: "active")
        return unless subscription

        MicrosoftService::TeamsMessageIngestionService.call(subscription)
      end
    end
  end
end
