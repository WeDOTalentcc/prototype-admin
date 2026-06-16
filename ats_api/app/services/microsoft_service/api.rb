# frozen_string_literal: true

module MicrosoftService
  class Api
    TIMEZONE = "America/Cuiaba"
    GRAPH_BASE = "https://graph.microsoft.com/v1.0"

    class << self
      # GET request to Microsoft Graph. `path_or_url` may be relative (e.g., "/me") or absolute.
      def get(path_or_url, user, params: {}, headers: {})
        user = ensure_user_token(user)
        url = absolute_url(path_or_url)
        with_retry_refresh(user) do |u|
          conn.get(url) do |req|
            req.headers.update(default_headers(u).merge(headers))
            req.params.update(params) if params.present?
          end
        end
      end

      def post(path_or_url, user, body: {}, params: {}, headers: {})
        user = ensure_user_token(user)
        url = absolute_url(path_or_url)
        with_retry_refresh(user) do |u|
          conn.post(url) do |req|
            req.headers.update(default_headers(u).merge(headers))
            req.params.update(params) if params.present?
            req.body = body if body.present?
          end
        end
      end

      def patch(path_or_url, user, body: {}, params: {}, headers: {})
        user = ensure_user_token(user)
        url = absolute_url(path_or_url)
        with_retry_refresh(user) do |u|
          conn.patch(url) do |req|
            req.headers.update(default_headers(u).merge(headers))
            req.params.update(params) if params.present?
            req.body = body if body.present?
          end
        end
      end

      def delete(path_or_url, user, body: nil, params: {}, headers: {})
        user = ensure_user_token(user)
        url = absolute_url(path_or_url)
        with_retry_refresh(user) do |u|
          conn.delete(url) do |req|
            req.headers.update(default_headers(u).merge(headers))
            req.params.update(params) if params.present?
            req.body = body if body.present?
          end
        end
      end

      # Ensures the user's Microsoft token is set and not expired; refreshes if needed.
      # Renews token 5 minutes before expiration as per security best practices.
      def ensure_user_token(user)
        return user unless user.ms_refresh_token.present?

        if user.ms_expires_at.nil?
          Rails.logger.info("[MicrosoftService] Token missing expiration, setting default to force refresh")
          user.ms_expires_at = 1.hour.ago
        end

        if user.ms_expires_at < Time.current
          Rails.logger.info("[MicrosoftService] Token expired or about to expire, refreshing for user_id=#{user.id}")
          user = refresh_expires_at(user)
        end

        user
      end

      def refresh_expires_at(user, retry_count: 0)
        max_retries = 3
        backoff_seconds = [ 2, 5, 10 ][retry_count] || 10

        resp = MicrosoftService::Auth.refresh_token(user.ms_refresh_token)

        if resp && resp["access_token"] && resp["expires_in"]
          new_refresh_token = resp["refresh_token"] || user.ms_refresh_token

          if resp["refresh_token"].blank?
            Rails.logger.warn("[MicrosoftService] Microsoft didn't return new refresh_token, keeping existing one")
          end

          user.update(
            ms_access_token: resp["access_token"],
            ms_refresh_token: new_refresh_token,
            ms_expires_at: Time.current + resp["expires_in"].to_i.seconds - 5.minutes
          )

          Rails.logger.info("[MicrosoftService] Token refreshed successfully for user_id=#{user.id}, expires_at=#{user.ms_expires_at}")
        else
          Rails.logger.error("[MicrosoftService] Token refresh failed for user_id=#{user.id}, invalid response")
        end

        user
      rescue MicrosoftService::Auth::AuthenticationError => e
        error_msg = e.message

        # Errors that are irrecoverable - don't retry
        if error_msg.include?("AADSTS700082") || # Refresh token expired due to inactivity
           error_msg.include?("AADSTS70000") ||  # Token revoked/expired family
           error_msg.include?("invalid_grant") && error_msg.include?("expired")

          Rails.logger.error("[MicrosoftService] Refresh token expired/revoked for user_id=#{user.id}")
          Rails.logger.error("[MicrosoftService] Error: #{error_msg}")

          user.update(
            ms_access_token: nil,
            ms_refresh_token: nil,
            ms_expires_at: nil
          )

          raise StandardError, "Microsoft refresh token expired. User needs to re-authenticate."
        end

        # Transient errors - can retry
        Rails.logger.error("[MicrosoftService] Token refresh authentication error for user_id=#{user.id}: #{error_msg}")

        if retry_count < max_retries
          Rails.logger.warn("[MicrosoftService] Retrying token refresh in #{backoff_seconds}s (attempt #{retry_count + 1}/#{max_retries})")
          sleep(backoff_seconds)
          return refresh_expires_at(user, retry_count: retry_count + 1)
        end

        raise StandardError, "Failed to refresh Microsoft token after #{max_retries} retries: #{error_msg}"
      rescue => e
        Rails.logger.error("[MicrosoftService] Unexpected error refreshing token for user_id=#{user.id}: #{e.class} #{e.message}")
        raise
      end

      private

      def conn
        @conn ||= Faraday.new do |f|
          f.request :json
          f.response :json, content_type: /json|\+json/
          f.adapter Faraday.default_adapter
        end
      end

      def default_headers(user)
        {
          "Authorization" => "Bearer #{user.ms_access_token}",
          "Content-Type" => "application/json",
          "Accept" => "application/json",
          "Prefer" => "outlook.timezone=\"#{TIMEZONE}\""
        }
      end

      def absolute_url(path_or_url)
        return path_or_url if path_or_url.to_s.start_with?("http://", "https://")
        GRAPH_BASE + path_or_url.to_s
      end

      # If a 401 occurs, try a one-time refresh using refresh_token and retry.
      def with_retry_refresh(user)
        resp = yield(user)
        if resp.status == 401 && user.ms_refresh_token.present?
          user = refresh_expires_at(user)
          resp = yield(user)
        end
        raise(StandardError, "Microsoft Graph error: #{resp.status} #{resp.body}") unless resp.success?
        resp.body
      end
    end
  end
end
