# frozen_string_literal: true

require "cgi"

module V1
  module Users
    class MicrosoftAuthsController < V1::Users::ApplicationController
      skip_before_action :authorize_request, only: [ :callback, :login_url ]

      GRAPH_SCOPES = [
        "openid", "profile", "email", "offline_access",
        "User.Read", "Mail.Read", "Mail.ReadWrite", "Mail.Send",
        "MailboxSettings.Read", "Calendars.ReadWrite",
        "OnlineMeetings.ReadWrite", "Tasks.ReadWrite",
        "Chat.ReadWrite", "Chat.Create"
      ].join(" ").freeze

      def login_url
        state_token = jwt_encode({ action: "login", timestamp: Time.current.to_i }, 10.minutes.from_now)

        authorize_url = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize?"
        authorize_url += "client_id=#{ENV['AZURE_APP_ID']}&"
        authorize_url += "redirect_uri=#{CGI.escape(login_callback_url)}&"
        authorize_url += "response_type=code&"
        authorize_url += "scope=#{CGI.escape(microsoft_oauth_scopes)}&"
        authorize_url += "state=#{state_token}"

        render json: { url: authorize_url }
      end

      def status
        auth_url = @current_user.microsoft_connected? ? nil : build_auth_url(@current_user)

        render json: {
          connected: @current_user.microsoft_connected?,
          status: @current_user.microsoft_connection_status,
          expires_at: @current_user.ms_expires_at,
          auth_url: auth_url
        }
      end

      def url
        return render json: { error: "Usuário não autenticado" }, status: :unauthorized unless @current_user

        state_token = jwt_encode({ user_id: @current_user.id }, 10.minutes.from_now)

        authorize_url = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize?"
        authorize_url += "client_id=#{ENV['AZURE_APP_ID']}&"
        authorize_url += "redirect_uri=#{CGI.escape(callback_url)}&"
        authorize_url += "response_type=code&"
        authorize_url += "scope=#{CGI.escape(microsoft_oauth_scopes)}&"
        authorize_url += "state=#{state_token}"

        render json: { url: authorize_url }
      end

      def callback
        state_token = params[:state].to_s
        payload = JWT.decode(state_token, Rails.application.secret_key_base, true, algorithm: "HS256").first rescue nil

        if payload.blank?
          Rails.logger.error("MS OAuth callback: Invalid state token")
          return render html: close_popup_html(success: false, error: "Estado inválido")
        end

        is_login = payload["action"] == "login"
        user_id = payload["user_id"]

        if !is_login && user_id.blank?
          Rails.logger.error("MS OAuth callback: Invalid state token - missing user_id for integration")
          return render html: close_popup_html(success: false, error: "Estado inválido")
        end

        if !is_login
          user = User.find_by(id: user_id)
          unless user
            Rails.logger.error("MS OAuth callback: User not found for id=#{user_id}")
            return render html: close_popup_html(success: false, error: "Usuário não encontrado")
          end
        end

        if params[:error].present?
          Rails.logger.error("MS OAuth callback: OAuth error=#{params[:error]} description=#{params[:error_description]}")
          error_message = case params[:error]
          when "access_denied"
            "Acesso negado pelo usuário"
          when "invalid_request"
            "Requisição inválida"
          when "unsupported_response_type"
            "Tipo de resposta não suportado"
          else
            "Erro de autorização: #{params[:error_description] || params[:error]}"
          end
          return render html: close_popup_html(success: false, error: error_message)
        end

        unless params[:code].present?
          Rails.logger.error("MS OAuth callback: No authorization code provided")
          return render html: close_popup_html(success: false, error: "Código de autorização não fornecido")
        end

        Rails.logger.info(
          "MS OAuth callback start: is_login=#{is_login} user_id=#{user_id} state_valid=#{payload.present?} has_code=#{params[:code].present?}"
        )

        redirect_uri = is_login ? login_callback_url : callback_url
        token_resp = MicrosoftService::Auth.token(
          params[:code],
          redirect_uri: redirect_uri
        )

        if token_resp.respond_to?(:code) && token_resp.code.to_i >= 400
          Rails.logger.error("MS token exchange failed: status=#{token_resp.code}")
          return render html: close_popup_html(success: false, error: "Falha na troca de tokens de autorização")
        end

        me = MicrosoftService::Auth.get_me(token_resp["access_token"]) if token_resp["access_token"].present?

        Rails.logger.info("MS OAuth: Token exchange successful, access_token present: #{token_resp["access_token"].present?}")

        if token_resp["access_token"].present?
          MicrosoftService::Auth.debug_token(token_resp["access_token"])

          me = MicrosoftService::Auth.get_me(token_resp["access_token"])
        else
          me = nil
        end

        Rails.logger.info("MS Graph /me fetched: #{me.present?}")

        if is_login
          handle_direct_login(token_resp, me)
        else
          handle_user_integration(user, token_resp)
        end

      rescue => error
        Rails.logger.error("Microsoft OAuth callback error: #{error.class} #{error.message}")
        Rails.logger.error(error.backtrace&.first(5)&.join("\n"))
        Rails.logger.error("Params keys: #{params.keys}")

        render html: close_popup_html(success: false, error: "Erro interno do servidor")
      end

      private

      def microsoft_oauth_scopes
        GRAPH_SCOPES
      end

      def handle_direct_login(token_resp, me)
        Rails.logger.info("Handle direct login: me=#{me.present?}")

        unless me && (me["mail"].present? || me["userPrincipalName"].present?)
          Rails.logger.error("MS OAuth login: No email found in Microsoft profile")
          return render html: close_popup_html(success: false, error: "Email não encontrado no perfil Microsoft")
        end

        email = (me["mail"] || me["userPrincipalName"]).downcase

        user = User.find_by(email: email)

        unless user
          Rails.logger.error("MS OAuth login: User not found for provided email")
          return render html: close_popup_html(success: false, error: "Usuário não encontrado com este email")
        end

        expires_at = Time.current + token_resp["expires_in"].to_i.seconds - 5.minutes
        user.update!(
          ms_access_token: token_resp["access_token"],
          ms_refresh_token: token_resp["refresh_token"],
          ms_expires_at: expires_at
        )

        session_token = jwt_encode(user_id: user.id)

        Rails.logger.info("MS OAuth login successful: user_id=#{user.id}")

        render html: close_popup_html(
          success: true,
          session_data: {
            token: session_token,
            user: user_payload(user)
          }
        )
      end

      def handle_user_integration(user, token_resp)
        expires_at = Time.current + token_resp["expires_in"].to_i.seconds - 5.minutes
        user.update!(
          ms_access_token: token_resp["access_token"],
          ms_refresh_token: token_resp["refresh_token"],
          ms_expires_at: expires_at
        )

        Rails.logger.info("MS OAuth integration success: user_id=#{user.id}, redirecting to frontend")

        front_url = ENV.fetch("FRONT_URL", "http://localhost:3000")
        redirect_to "#{front_url}/user/candidates", allow_other_host: true
      end

      def login_callback_url
        base = if Rails.env.development?
          "http://localhost:8080"
        else
          host = ENV["domain_name"].presence || ENV["APP_HOST"]
          host = host.sub(%r{\Ahttps?://}, "") if host
          "https://#{host}"
        end
        base + "/v1/auth/microsoft_graph_auth/callback"
      end

      def callback_url
        base = if Rails.env.development?
          "http://localhost:8080"
        else
          host = ENV["domain_name"].presence || ENV["APP_HOST"]
          host = host.sub(%r{\Ahttps?://}, "") if host
          "https://#{host}"
        end
        base + "/v1/auth/microsoft_graph_auth/callback"
      end

      def close_popup_html(success:, error: nil, session_data: nil)
        @success = success
        @error = error
        @session_data = session_data
        @message = if success && session_data
          { success: true, session: session_data }
        elsif success
          { success: true }
        else
          { success: false, error: error }
        end

        render_to_string(
          template: "v1/users/microsoft_auths/oauth_popup",
          layout: false
        ).html_safe
      end

      def build_auth_url(user)
        state_token = jwt_encode({ user_id: user.id }, 10.minutes.from_now)
        host = ENV["domain_name"].presence || ENV["APP_HOST"]
        host = host.sub(%r{\Ahttps?://}, "") if host
        base = Rails.env.development? ? "http://localhost:8080" : "https://#{host}"
        redirect_uri = "#{base}/v1/auth/microsoft_graph_auth/callback"

        url  = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize?"
        url += "client_id=#{CGI.escape(ENV.fetch('AZURE_APP_ID', ''))}&"
        url += "redirect_uri=#{CGI.escape(redirect_uri)}&"
        url += "response_type=code&"
        url += "scope=#{CGI.escape(GRAPH_SCOPES)}&"
        url += "state=#{state_token}"
        url
      end

      def jwt_encode(payload, exp = 24.hours.from_now)
        payload[:exp] = exp.to_i
        JWT.encode(payload, Rails.application.secret_key_base)
      end

      def user_payload(user)
        {
          id: user.id,
          name: user.name,
          email: user.email,
          is_admin: user.is_admin?,
          microsoft_connected: user.microsoft_connected?
        }
      end
    end
  end
end
