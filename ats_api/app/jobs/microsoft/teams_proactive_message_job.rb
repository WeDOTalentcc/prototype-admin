# frozen_string_literal: true

module Microsoft
  class TeamsProactiveMessageJob
    include Sidekiq::Job

    sidekiq_options queue: :default, retry: 3

    def perform(lia_user_id, recruiter_id, account_id, custom_message = nil)
      account = Account.find_by(id: account_id)
      return unless account

      Apartment::Tenant.switch(account.tenant) do
        lia_user = User.find_by(id: lia_user_id)
        recruiter = User.find_by(id: recruiter_id)
        return unless lia_user && recruiter
        return if lia_user.email == recruiter.email

        ensure_lia_token!(lia_user)

        content = build_content(recruiter, custom_message)

        response = MicrosoftService::Teams.send_message(
          user: lia_user,
          content: content,
          content_type: "html",
          to: recruiter.email
        )

        register_subscription(lia_user, recruiter, account, response[:chat_id])

        Rails.logger.info "[TeamsProactiveMessage] ✅ Sent to recruiter_id=#{recruiter.id} chat=#{response[:chat_id]}"
      end
    rescue MicrosoftService::Teams::Error => e
      Rails.logger.error "[TeamsProactiveMessage] Teams error for recruiter_id=#{recruiter_id}: #{e.code} - #{e.message}"
    rescue StandardError => e
      Rails.logger.error "[TeamsProactiveMessage] Error: #{e.class} #{e.message}"
      raise
    end

    private

    def ensure_lia_token!(lia_user)
      if lia_user.ms_refresh_token.blank?
        Rails.logger.error "[TeamsProactiveMessage] ❌ LIA user_id=#{lia_user.id} has no refresh token — needs OAuth re-authentication"
        raise StandardError, "LIA user needs Microsoft OAuth re-authentication"
      end

      if lia_user.microsoft_token_needs_refresh?
        Rails.logger.info "[TeamsProactiveMessage] 🔄 Refreshing expired token for LIA user_id=#{lia_user.id}"
        MicrosoftService::Api.refresh_expires_at(lia_user)
        lia_user.reload
      end

      return if lia_user.ms_access_token.present?

      Rails.logger.error "[TeamsProactiveMessage] ❌ LIA user_id=#{lia_user.id} has no access token after refresh attempt"
      raise StandardError, "LIA user Microsoft token unavailable"
    end

    def build_content(recruiter, custom_message)
      return custom_message if custom_message.present?

      recruiter_name = recruiter.name || recruiter.email.split("@").first
      format(MicrosoftService::TeamsProactiveOutreachService::DEFAULT_GREETING, recruiter_name: CGI.escapeHTML(recruiter_name))
    end

    def register_subscription(lia_user, recruiter, account, chat_id)
      return if chat_id.blank?

      tenant = account.tenant

      TeamsChatSubscription.find_or_create_by!(
        lia_user_id: lia_user.id,
        recruiter_user_id: recruiter.id
      ) do |sub|
        sub.account_id = account.id
        sub.chat_id = chat_id
        sub.tenant = tenant
        sub.status = "active"
      end.tap do |sub|
        sub.update!(chat_id: chat_id, status: "active") if sub.chat_id != chat_id
      end

      MicrosoftService::TeamsSubscriptionService.create_or_renew(lia_user, chat_id)
    rescue StandardError => e
      Rails.logger.error "[TeamsProactiveMessage] Failed to register subscription: #{e.message}"
    end
  end
end
