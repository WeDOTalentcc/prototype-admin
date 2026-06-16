# frozen_string_literal: true

module V1
  class SessionsController < ApplicationController
    LOGIN_MAX_ATTEMPTS = 5
    LOGIN_WINDOW_SECONDS = 60

    before_action :authorize_request, except: [ :create, :logout, :verify_mfa, :resend_mfa ]
    before_action :check_login_rate_limit, only: [ :create ]

    def create
      @user = User.find_by(email: params[:email])

      unless @user
        increment_login_attempts
        return render json: { error: "Invalid email or password" }, status: :unauthorized
      end

      unless @user.account&.password_login_enabled?
        return render json: {
          error: "Password login is not enabled for this account",
          available_methods: @user.account&.available_auth_methods || []
        }, status: :forbidden
      end

      unless @user.authenticate_with_migration(params[:password])
        increment_login_attempts
        return render json: { error: "Invalid email or password" }, status: :unauthorized
      end

      @current_user = @user
      Current.user = @user

      # Check if MFA is required
      return handle_mfa_challenge(@user) if mfa_required?(@user)

      log_login_audit

      token = JsonWebToken.encode(user_id: @user.id)
      render json: { user: user_payload(@user), token: token }, status: :ok
    end

    def verify_mfa
      mfa_service = MfaService.new
      payload = mfa_service.decode_mfa_token(params[:mfa_token])

      unless payload && payload[:role] == "mfa_pending"
        return render json: { error: "Token MFA inválido ou expirado" }, status: :unauthorized
      end

      user = User.find_by(id: payload[:user_id])
      unless user
        return render json: { error: "Usuário não encontrado" }, status: :unauthorized
      end

      unless mfa_service.verify_otp(user, params[:code])
        remaining = mfa_service.attempts_remaining(user)

        if remaining == 0
          return render json: {
            error: "Limite de tentativas excedido. Faça login novamente.",
            rate_limited: true
          }, status: :too_many_requests
        end

        return render json: {
          error: "Código inválido ou expirado",
          attempts_remaining: remaining
        }, status: :unauthorized
      end

      @current_user = user
      Current.user = user
      log_login_audit

      token = JsonWebToken.encode(user_id: user.id)
      render json: { user: user_payload(user), token: token }, status: :ok
    end

    def resend_mfa
      mfa_service = MfaService.new
      payload = mfa_service.decode_mfa_token(params[:mfa_token])

      unless payload && payload[:role] == "mfa_pending"
        return render json: { error: "Token MFA inválido ou expirado" }, status: :unauthorized
      end

      user = User.find_by(id: payload[:user_id])
      unless user
        return render json: { error: "Usuário não encontrado" }, status: :unauthorized
      end

      # Rate limit resends
      resend_key = "mfa:resend:#{user.id}"
      redis = Redis.new(url: ENV["REDIS_URL"])
      resend_count = redis.get(resend_key).to_i

      if resend_count >= 3
        return render json: {
          error: "Limite de reenvios atingido. Tente fazer login novamente."
        }, status: :too_many_requests
      end

      redis.setex(resend_key, 600, resend_count + 1)

      code = mfa_service.generate_otp(user)
      MfaMailer.with(user: user, code: code).otp_email.deliver_now

      render json: {
        message: "Novo código enviado para #{mask_email(user.email)}",
        mfa_token: params[:mfa_token]
      }, status: :ok
    end

    def me
      payload = Rails.cache.fetch("user_payload:#{@current_user.id}", expires_in: 30.seconds) do
        user_payload(@current_user)
      end
      render json: { user: payload }
    end

    def logout
      render json: { message: "Logged out" }
    end

    def mark_welcomed
      @current_user.update!(first_access: false)
      render json: { user: user_payload(@current_user) }
    end

    private

    def mfa_required?(user)
      account = user.account
      return false unless account

      if account.mfa_enabled?
        return true if user.mfa_enabled?
        return true if user.is_admin? && account.mfa_required_for_admins?
      end

      false
    end

    def handle_mfa_challenge(user)
      mfa_service = MfaService.new
      code = mfa_service.generate_otp(user)
      mfa_token = mfa_service.generate_mfa_token(user)

      MfaMailer.with(user: user, code: code).otp_email.deliver_now

      Rails.logger.info "[MFA] Challenge initiated for user #{user.id}"

      render json: {
        mfa_required: true,
        mfa_token: mfa_token,
        message: "Código de verificação enviado para #{mask_email(user.email)}"
      }, status: :ok
    end

    def mask_email(email)
      local, domain = email.split("@")
      return email if local.length < 3

      masked_local = local[0..1] + ("*" * [ local.length - 3, 1 ].max) + local[-1]
      "#{masked_local}@#{domain}"
    end

    def user_payload(user)
      business = user.account_id ? Business.find_by(account_id: user.account_id) : nil
      account = Account.find_by(id: user.account_id)

      business_logo_url = if business&.logo&.attached?
        "#{ENV['API_URL'] || 'http://localhost:8080'}#{Rails.application.routes.url_helpers.rails_blob_url(business.logo, only_path: true)}"
      end

      {
        id: user.id,
        name: user.name,
        email: user.email,
        is_admin: user.is_admin?,
        microsoft_connected: user.microsoft_connected?,
        business_name: business&.name,
        business_logo: business_logo_url,
        account_id: user.account_id,
        role: user.role_name,
        sourcing_config: account&.sourcing_config,
        first_access: user.first_access
      }
    end


    def log_login_audit
      return unless @current_user

      Workos::AuditService.log(
        action: "sessions#create",
        user: @current_user,
        metadata: {
          login_method: "email_password",
          ip_address: request.remote_ip,
          user_agent: request.user_agent
        },
        request: request
      )
    rescue StandardError => e
      Rails.logger.error("[SessionsController] Failed to log audit: #{e.message}")
    end

    def check_login_rate_limit
      attempts = redis.get(login_rate_limit_key).to_i
      return if attempts < LOGIN_MAX_ATTEMPTS

      render json: {
        error: "Muitas tentativas de login. Tente novamente em 1 minuto.",
        rate_limited: true
      }, status: :too_many_requests
    end

    def increment_login_attempts
      key = login_rate_limit_key
      redis.multi do |tx|
        tx.incr(key)
        tx.expire(key, LOGIN_WINDOW_SECONDS)
      end
    end

    def login_rate_limit_key
      "login:rate_limit:#{request.remote_ip}"
    end

    def redis
      @redis ||= Redis.new(url: ENV["REDIS_URL"])
    end

    def authorize_request
      header = request.headers["Authorization"]
      token = header.split(" ").last if header

      decoded = JsonWebToken.decode(token)
      return render json: { error: "Token missing or invalid" }, status: :unauthorized unless decoded

      @current_user = User.find_by(id: decoded[:user_id])
      Current.user = @current_user
      render json: { error: "Invalid token" }, status: :unauthorized unless @current_user
    end
  end
end
