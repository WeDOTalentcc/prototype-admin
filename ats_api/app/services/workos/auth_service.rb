module Workos
  class AuthService
    class AuthenticationError < StandardError; end
    class TokenError < StandardError; end

    OAUTH_PROVIDERS = {
      "google_oauth"       => "GoogleOAuth",
      "microsoft_entra_id" => "MicrosoftOAuth",
      "github_oauth"       => "GitHubOAuth",
      "apple_oauth"        => "AppleOAuth"
    }.freeze

    def initialize(account_id: nil)
      @account_id = account_id
    end

    def authorize_url(redirect_uri:, state: nil, provider: nil, organization_id: nil, connection_id: nil, login_hint: nil)
      raise AuthenticationError, "WorkOS not configured" unless configured?

      params = build_auth_params(redirect_uri: redirect_uri, state: state, login_hint: login_hint)

      return connection_authorization_url(params, connection_id, login_hint) if connection_id
      return organization_authorization_url(params, organization_id, login_hint) if organization_id

      workos_provider = OAUTH_PROVIDERS[provider]
      return oauth_authorization_url(params, provider, workos_provider, login_hint) if workos_provider

      Rails.logger.error("[Workos::AuthService] No valid provider, connection_id, or organization_id")
      nil
    end

    def exchange_code(code:, redirect_uri: nil)
      return nil unless configured?

      Rails.logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
      Rails.logger.info("🔄 [Workos::AuthService] Exchanging code for token")
      Rails.logger.info("   Client ID present: #{api_client_id.present?}")
      Rails.logger.info("   API Key present: #{api_key.present?}")
      Rails.logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

      response = ::WorkOS::SSO.profile_and_token(
        code: code,
        client_id: api_client_id
      )
      return nil unless response

      Rails.logger.info("[Workos::AuthService] ✅ Token exchange successful")
      Rails.logger.info("   Profile ID: #{response.profile&.id}")
      Rails.logger.info("   Organization ID: #{response.profile&.organization_id}")

      {
        user: response.profile,
        access_token: response.access_token,
        refresh_token: extract_refresh_token(response)
      }
    rescue => e
      Rails.logger.error("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
      Rails.logger.error("❌ [Workos::AuthService] Exchange code FAILED")
      Rails.logger.error("   Error class: #{e.class}")
      Rails.logger.error("   Error message: #{e.message}")
      Rails.logger.error("   Client ID: #{api_client_id}")
      Rails.logger.error("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
      raise TokenError, "Failed to exchange code: #{e.message}"
    end

    def get_user(access_token:)
      return nil unless configured?
      return nil if access_token.blank?

      ::WorkOS::SSO.get_profile(access_token: access_token)
    rescue => e
      Rails.logger.error("[Workos::AuthService] Get user error: #{e.message}")
      nil
    end

    def refresh_token(refresh_token:)
      return nil unless configured?
      return nil if refresh_token.blank?

      ::WorkOS::SSO.refresh_access_token(refresh_token: refresh_token, client_id: api_client_id)
    rescue => e
      Rails.logger.error("[Workos::AuthService] Refresh token error: #{e.message}")
      raise TokenError, "Failed to refresh token: #{e.message}"
    end

    def find_or_create_user(workos_user_id:, email:, name:, organization_id:)
      user = User.find_by(workos_user_id: workos_user_id)
      return user if user

      account = find_account_by_organization(organization_id)
      validate_user_access(account, email)

      sync_or_create_user_in_tenant(account, workos_user_id, email, name, organization_id)
    end

    private

    attr_reader :account_id

    def configured?
      api_key.present? && api_client_id.present?
    end

    def api_key
      ENV["WORKOS_API_KEY"]
    end

    def api_client_id
      ENV["WORKOS_CLIENT_ID"]
    end

    def find_organization_id
      account = account_id ? Account.find_by(id: account_id) : Account.find_by(tenant: "public")
      account&.workos_organization_id
    end

    def build_auth_params(redirect_uri:, state:, login_hint:)
      params = {
        client_id: api_client_id,
        redirect_uri: redirect_uri,
        state: state
      }
      params[:login_hint] = login_hint if login_hint.present?
      params
    end

    def oauth_authorization_url(params, provider, workos_provider, login_hint)
      log_hint = login_hint ? " (hint: #{login_hint})" : ""
      Rails.logger.info("[Workos::AuthService] OAuth flow: #{provider} → #{workos_provider}#{log_hint}")

      ::WorkOS::SSO.authorization_url(**params, provider: workos_provider)
    end

    def connection_authorization_url(params, connection_id, login_hint)
      log_hint = login_hint ? " (hint: #{login_hint})" : ""
      Rails.logger.info("[Workos::AuthService] Connection-based SSO flow: conn=#{connection_id}#{log_hint}")

      ::WorkOS::SSO.authorization_url(**params, connection: connection_id)
    end

    def organization_authorization_url(params, organization_id, login_hint)
      log_hint = login_hint ? " (hint: #{login_hint})" : ""
      Rails.logger.info("[Workos::AuthService] Organization-based SSO flow (fallback): org=#{organization_id}#{log_hint}")

      ::WorkOS::SSO.authorization_url(**params, organization: organization_id)
    end

    def extract_refresh_token(response)
      response.respond_to?(:refresh_token) ? response.refresh_token : nil
    end

    def find_account_by_organization(organization_id)
      account = Account.find_by(workos_organization_id: organization_id)
      raise AuthenticationError, "Organization not found" unless account

      account
    end

    def validate_user_access(account, email)
      raise AuthenticationError, "Email domain not allowed" unless account.email_domain_allowed?(email)
      raise AuthenticationError, "Account tenant not configured" if account.tenant.blank?
    end

    def sync_or_create_user_in_tenant(account, workos_user_id, email, name, organization_id)
      Apartment::Tenant.switch(account.tenant) do
        existing_user = User.find_by("LOWER(email) = ?", email.downcase)

        return link_existing_user(existing_user, workos_user_id, organization_id) if existing_user

        create_new_user(account, workos_user_id, email, name, organization_id)
      end
    end

    def link_existing_user(user, workos_user_id, organization_id)
      user.update!(
        workos_user_id: workos_user_id,
        workos_organization_id: organization_id
      )
      Rails.logger.info "[Workos::AuthService] Linked existing user #{user.id} to WorkOS"
      user
    end

    def create_new_user(account, workos_user_id, email, name, organization_id)
      raise AuthenticationError, "Just-in-time provisioning disabled for this organization" unless account.jit_provisioning_enabled?

      User.create!(
        workos_user_id: workos_user_id,
        workos_organization_id: organization_id,
        email: email,
        name: name,
        account_id: account.id,
        password: SecureRandom.hex(16)
      )
    end
  end
end
