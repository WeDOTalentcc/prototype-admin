# frozen_string_literal: true

module Microsoft
  class TokenRefreshJob
    include Sidekiq::Job

    sidekiq_options queue: :default, retry: 3

    def perform
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.info "🔄 [TokenRefreshJob] Starting proactive token refresh"
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

      users_to_refresh = find_users_requiring_refresh

      Rails.logger.info "   Found #{users_to_refresh.count} users with tokens expiring soon"

      refreshed_count = 0
      failed_count = 0
      re_auth_required_count = 0

      users_to_refresh.find_each do |user|
        Apartment::Tenant.switch(user.account.tenant) do
          result = refresh_user_token(user)

          case result
          when :success
            refreshed_count += 1
          when :re_auth_required
            re_auth_required_count += 1
          when :failed
            failed_count += 1
          end
        end
      rescue => e
        Rails.logger.error "[TokenRefreshJob] Error processing user_id=#{user.id}: #{e.message}"
        failed_count += 1
      end

      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.info "✅ [TokenRefreshJob] Completed"
      Rails.logger.info "   Refreshed: #{refreshed_count}"
      Rails.logger.info "   Re-auth required: #{re_auth_required_count}"
      Rails.logger.info "   Failed: #{failed_count}"
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    end

    private

    def find_users_requiring_refresh
      refresh_threshold = 10.minutes.from_now

      User.where.not(ms_refresh_token: nil)
          .where("ms_expires_at IS NOT NULL")
          .where("ms_expires_at < ?", refresh_threshold)
          .where("ms_expires_at > ?", Time.current)
    end

    def refresh_user_token(user)
      Rails.logger.info "🔄 [TokenRefreshJob] Refreshing token for user_id=#{user.id}"

      MicrosoftService::Api.refresh_expires_at(user)

      Rails.logger.info "✅ [TokenRefreshJob] Successfully refreshed token for user_id=#{user.id}"
      :success
    rescue => e
      if e.message.include?("needs to re-authenticate")
        Rails.logger.warn "⚠️ [TokenRefreshJob] User #{user.id} needs re-authentication"
        notify_user_re_auth_required(user)
        :re_auth_required
      else
        Rails.logger.error "❌ [TokenRefreshJob] Failed to refresh token for user_id=#{user.id}: #{e.message}"
        :failed
      end
    end

    def notify_user_re_auth_required(user)
      Rails.logger.info "📧 [TokenRefreshJob] Should notify user_id=#{user.id} about re-authentication"
    end
  end
end
