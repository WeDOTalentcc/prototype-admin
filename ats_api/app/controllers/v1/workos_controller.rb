# frozen_string_literal: true

require "cgi"

module V1
  class WorkosController < ApplicationController
    skip_before_action :authorize_request, only: [ :callback, :login_url, :webhook, :sso_options ], raise: false

    PROVIDER_NAMES = {
      "microsoft_entra_id" => "Microsoft",
      "google_oauth" => "Google",
      "okta" => "Okta",
      "azure_ad" => "Azure AD",
      "adfs" => "AD FS",
      "saml" => "SAML",
      "testsaml" => "Test SAML"
    }.freeze

    def login_url
      return render_error("WorkOS não configurado") unless workos_configured?

      provider = params[:provider] || "microsoft_entra_id"
      return render_error("Provider inválido") unless PROVIDER_NAMES.key?(provider)

      redirect_uri = workos_callback_url
      state = jwt_encode_state({ action: "login", provider: provider, timestamp: Time.current.to_i }, 10.minutes.from_now)

      account_for_sso = @current_user&.account || find_account_for_sso

      Rails.logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
      Rails.logger.info("🚀 [WorkOS::Controller] Generating authorization URL")
      Rails.logger.info("   Provider: #{provider}")
      Rails.logger.info("   Callback: #{redirect_uri}")
      Rails.logger.info("   Account: #{account_for_sso&.name || 'none'}")
      Rails.logger.info("   Connection: #{account_for_sso&.workos_connection_id || 'none'}")
      Rails.logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

      authorize_url = workos_auth_service.authorize_url(
        redirect_uri: redirect_uri,
        state: state,
        provider: provider,
        connection_id: account_for_sso&.workos_connection_id,
        organization_id: account_for_sso&.workos_organization_id,
        login_hint: params[:email].presence
      )

      return render_error("Falha ao gerar URL de autorização") unless authorize_url

      render json: { url: authorize_url, provider: provider }
    end

    def callback
      return handle_callback_error("Estado inválido") unless valid_state?

      return handle_callback_error("Código de autorização não fornecido") unless params[:code].present?

      if params[:error].present?
        return handle_callback_error("Erro de autorização: #{params[:error_description] || params[:error]}")
      end

      handle_successful_callback
    rescue => e
      Rails.logger.error("[WorkOS::Controller] Callback error: #{e.message}")
      Rails.logger.error(e.backtrace.first(5).join("\n"))
      handle_callback_error("Erro interno do servidor")
    end

    def sso_options
      account = find_account_for_sso
      email_hint = params[:email]

      options = {
        sso_enabled: false,
        providers: [],
        login_traditional_enabled: account&.password_login_enabled? != false
      }

      return render json: options unless workos_configured?

      if account&.sso_active?
        options[:sso_enabled] = true
        options[:providers] = build_providers_list(account, email_hint: email_hint)
        options[:login_traditional_enabled] = account.password_login_enabled? && !account.sso_enforced?
      end

      render json: options
    end

    def find_account_for_sso
      return @current_user&.account if @current_user

      email = params[:email]
      return nil unless email.present?

      user = User.find_by("LOWER(email) = ?", email.downcase)
      return user.account if user&.account&.sso_active?

      email_domain = email.split("@").last&.downcase
      return nil unless email_domain

      account = Account.find_by("LOWER(domain) = ? AND workos_enabled = ?", email_domain, true)
      return account if account&.sso_active?

      account = Account.where(workos_enabled: true)
                       .where("? = ANY(allowed_domains)", email_domain)
                       .first
      return account if account&.sso_active?

      nil
    end

    def build_providers_list(account, email_hint: nil)
      account.available_sso_providers.map do |provider_id|
        {
          id: provider_id,
          name: PROVIDER_NAMES[provider_id] || provider_id.titleize,
          login_url: build_sso_url(provider_id, account, email_hint: email_hint)
        }
      end
    end

    def build_sso_url(provider, account, email_hint: nil)
      return nil unless workos_configured?

      state = jwt_encode_state({ action: "login", provider: provider, timestamp: Time.current.to_i }, 30.minutes.from_now)

      Rails.logger.info "[WorkOS] Building SSO URL: provider=#{provider}, connection=#{account.workos_connection_id}, org=#{account.workos_organization_id}, hint=#{email_hint}"

      workos_auth_service.authorize_url(
        redirect_uri: workos_callback_url,
        state: state,
        provider: provider,
        connection_id: account.workos_connection_id,
        organization_id: account.workos_organization_id,
        login_hint: email_hint
      )
    end

    def webhook
      return head :unauthorized unless valid_webhook_signature?

      event = JSON.parse(request.body.read)
      handle_webhook_event(event)

      head :ok
    rescue => e
      Rails.logger.error("[WorkOS::Controller] Webhook error: #{e.message}")
      head :unprocessable_entity
    end

    private

    def workos_auth_service
      @workos_auth_service ||= Workos::AuthService.new
    end

    def valid_state?
      return false unless params[:state].present?

      payload = jwt_decode_state(params[:state])
      return false unless payload

      @state_payload = payload
      true
    end

    def handle_successful_callback
      redirect_uri = workos_callback_url

      Rails.logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
      Rails.logger.info("🔄 [WorkOS::Controller] Processing callback")
      Rails.logger.info("   Code: #{params[:code][0..15]}...")
      Rails.logger.info("   Action: #{@state_payload['action']}")
      Rails.logger.info("   Provider: #{@state_payload['provider']}")
      Rails.logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

      result = begin
        workos_auth_service.exchange_code(code: params[:code], redirect_uri: redirect_uri)
      rescue Workos::AuthService::TokenError => e
        Rails.logger.error("[WorkOS::Controller] Token exchange failed: #{e.message}")
        return handle_callback_error("Falha na autenticação com WorkOS: #{e.message}")
      end

      return handle_callback_error("Falha na troca de tokens") unless result

      is_login = @state_payload["action"] == "login"

      if is_login
        handle_login(result)
      else
        handle_integration(result)
      end
    end

    def handle_login(result)
      workos_user = result[:user]
      return handle_callback_error("Dados do usuário não encontrados") unless workos_user

      email = extract_email(workos_user)
      return handle_callback_error("Email não encontrado") unless email

      user = find_or_create_user(workos_user, result)
      return handle_callback_error("Usuário não encontrado") unless user

      update_user_tokens(user, result)

      provider = @state_payload["provider"] || "microsoft_entra_id"
      log_sso_login_audit(user, provider)

      session_token = JsonWebToken.encode(user_id: user.id)

      Rails.logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
      Rails.logger.info("✅ [WorkOS::Controller] Login successful")
      Rails.logger.info("   User: #{user.name} (#{user.email})")
      Rails.logger.info("   Microsoft Graph connected: #{user.microsoft_connected?}")
      Rails.logger.info("   Rendering HTML redirect to frontend")
      Rails.logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

      session_data = { token: session_token, user: user_payload(user) }

      if provider == "microsoft_entra_id" && !user.microsoft_connected?
        session_data[:graph_auth_url] = build_graph_auth_url(user)
        Rails.logger.info("   graph_auth_url included for Microsoft Graph consent")
      end

      render html: close_popup_html(success: true, session_data: session_data)
    end

    def handle_integration(result)
      return handle_callback_error("Usuário não autenticado") unless @current_user

      workos_user = result[:user]
      return handle_callback_error("Dados do usuário não encontrados") unless workos_user

      update_user_tokens(@current_user, result)

      render html: close_popup_html(success: true)
    end

    def find_or_create_user(workos_user, result)
      return nil unless workos_user

      workos_user_id = workos_user.respond_to?(:id) ? workos_user.id : workos_user["id"]
      organization_id = workos_user.respond_to?(:organization_id) ? workos_user.organization_id : workos_user["organization_id"]

      user = User.find_by(workos_user_id: workos_user_id)
      return user if user

      email = extract_email(workos_user)
      return nil unless email

      account = Account.find_by(workos_organization_id: organization_id)
      return nil unless account

      name = workos_user.respond_to?(:first_name) ? workos_user.first_name : workos_user["first_name"]
      name ||= email

      workos_auth_service.find_or_create_user(
        workos_user_id: workos_user_id,
        email: email,
        name: name,
        organization_id: organization_id
      )
    rescue Workos::AuthService::AuthenticationError => e
      Rails.logger.warn "[WorkOS::Controller] Authentication error: #{e.message}"
      nil
    end

    def extract_email(workos_user)
      return nil unless workos_user

      workos_user.email || workos_user.raw_attributes&.dig("email") || workos_user["email"]
    end

    def log_sso_login_audit(user, provider)
      Workos::AuditService.log(
        action: "workos#callback",
        user: user,
        metadata: {
          login_method: "sso",
          provider: provider,
          ip_address: request.remote_ip,
          user_agent: request.user_agent
        },
        request: request
      )
    rescue => e
      Rails.logger.error("[WorkOS::Controller] Failed to log SSO login audit: #{e.message}")
    end

    def update_user_tokens(user, result)
      return unless result[:user]

      workos_user = result[:user]
      workos_user_id = workos_user.respond_to?(:id) ? workos_user.id : workos_user["id"]
      organization_id = workos_user.respond_to?(:organization_id) ? workos_user.organization_id : workos_user["organization_id"]

      expires_at = Time.current + 1.hour

      user.update!(
        workos_user_id: workos_user_id,
        workos_organization_id: organization_id,
        workos_access_token: result[:access_token],
        workos_refresh_token: result[:refresh_token],
        workos_expires_at: expires_at
      )
    end

    def handle_webhook_event(event)
      event_type = event["event"]
      return unless event_type

      case event_type
      when "connection.activated"
        handle_connection_activated(event)
      when "connection.deactivated"
        handle_connection_deactivated(event)
      when "user.created", "user.updated"
        handle_user_event(event)
      when "organization.created", "organization.updated"
        handle_organization_event(event)
      end
    end

    def handle_connection_activated(event)
      org_id = event.dig("data", "organization_id")
      connection_type = event.dig("data", "connection_type")

      return unless org_id

      account = Account.find_by(workos_organization_id: org_id)
      return unless account

      account.update!(workos_enabled: true)

      Rails.logger.info "[WorkOS::Webhook] SSO connection activated for #{account.name} (#{connection_type})"

      Workos::AuditService.log(
        action: "sso.connection_activated",
        user: account.users.first,
        metadata: {
          organization_id: org_id,
          connection_type: connection_type
        }
      )
    rescue => e
      Rails.logger.error "[WorkOS::Webhook] Failed to handle connection activated: #{e.message}"
    end

    def handle_connection_deactivated(event)
      org_id = event.dig("data", "organization_id")
      connection_type = event.dig("data", "connection_type")

      return unless org_id

      account = Account.find_by(workos_organization_id: org_id)
      return unless account

      Rails.logger.warn "[WorkOS::Webhook] SSO connection deactivated for #{account.name} (#{connection_type})"

      Workos::AuditService.log(
        action: "sso.connection_deactivated",
        user: account.users.first,
        metadata: {
          organization_id: org_id,
          connection_type: connection_type
        }
      )
    rescue => e
      Rails.logger.error "[WorkOS::Webhook] Failed to handle connection deactivated: #{e.message}"
    end

    def handle_user_event(event)
      user_data = event["data"]
      return unless user_data

      user = User.find_by(workos_user_id: user_data["id"])
      return unless user

      user.update(
        email: user_data["email"],
        name: user_data["first_name"] || user_data["email"]
      )
    end

    def handle_organization_event(event)
      org_data = event["data"]
      return unless org_data

      account = Account.find_by(workos_organization_id: org_data["id"])
      return unless account

      account.update(
        workos_organization_id: org_data["id"],
        workos_enabled: true
      )
    end

    def valid_webhook_signature?
      return false unless ENV["WORKOS_WEBHOOK_SECRET"].present?

      signature = request.headers["WorkOS-Signature"]
      return false unless signature

      body = request.body.read
      request.body.rewind

      ::WorkOS::Webhooks.verify_header(
        payload: body,
        sig_header: signature,
        secret: ENV["WORKOS_WEBHOOK_SECRET"]
      )
      true
    rescue => e
      Rails.logger.error("[WorkOS::Controller] Webhook signature validation error: #{e.message}")
      false
    end

    def workos_configured?
      ENV["WORKOS_API_KEY"].present? && ENV["WORKOS_CLIENT_ID"].present?
    end

    def workos_callback_url
      base = if Rails.env.development?
        "http://localhost:8080"
      else
        host = ENV["domain_name"].presence || ENV["APP_HOST"]
        host = host.sub(%r{^https?://}, "") if host
        "https://#{host}"
      end
      base + "/v1/workos/callback"
    end

    def workos_sso_url(provider)
      account = @current_user&.account
      return nil unless account&.workos_organization_id

      build_sso_url(provider, account.workos_organization_id)
    end

    def handle_callback_error(message)
      render html: close_popup_html(success: false, error: message)
    end

    def close_popup_html(success:, error: nil, session_data: nil)
      message = if success && session_data
        { success: true, session: session_data }
      elsif success
        { success: true }
      else
        { success: false, error: error }
      end

      render_to_string(
        template: "v1/workos/oauth_popup",
        layout: false,
        locals: { message: message }
      ).html_safe
    end

    def jwt_encode_state(payload, exp = 24.hours.from_now)
      payload[:exp] = exp.to_i
      JWT.encode(payload, Rails.application.secret_key_base, 'HS256')
    end

    def jwt_decode_state(token)
      decoded = JWT.decode(token, Rails.application.secret_key_base, true, algorithm: 'HS256').first
      HashWithIndifferentAccess.new(decoded)
    rescue JWT::DecodeError => e
      Rails.logger.error "[WorkOS] State decode failed: #{e.message}"
      nil
    end

    def user_payload(user)
      {
        id: user.id,
        name: user.name,
        email: user.email,
        is_admin: user.is_admin?,
        workos_connected: user.workos_connected?,
        microsoft_connected: user.microsoft_connected?,
        first_access: user.first_access
      }
    end

    def render_error(message, status: :unprocessable_entity)
      render json: { error: message }, status: status
    end

    def build_graph_auth_url(user)
      state_token = jwt_encode_state({ user_id: user.id }, 10.minutes.from_now)

      host = ENV["domain_name"].presence || ENV["APP_HOST"]
      host = host.sub(%r{\Ahttps?://}, "") if host
      callback_base = Rails.env.development? ? "http://localhost:8080" : "https://#{host}"
      redirect_uri = "#{callback_base}/v1/auth/microsoft_graph_auth/callback"

      url  = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize?"
      url += "client_id=#{CGI.escape(ENV.fetch('AZURE_APP_ID', ''))}&"
      url += "redirect_uri=#{CGI.escape(redirect_uri)}&"
      url += "response_type=code&"
      url += "scope=#{CGI.escape(V1::Users::MicrosoftAuthsController::GRAPH_SCOPES)}&"
      url += "state=#{state_token}"
      url
    end
  end
end
