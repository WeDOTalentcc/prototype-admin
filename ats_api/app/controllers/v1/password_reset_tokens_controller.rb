# frozen_string_literal: true

module V1
  class PasswordResetTokensController < ApplicationController
    include RenderDefault

    before_action :set_user_by_email, only: [ :create ]
    before_action :set_token, only: [ :show, :complete ]
    protect_from_forgery with: :null_session

    def create
      if @user.nil?
        return render_error_message("Email não encontrado")
      end

      PasswordResetToken.where(user: @user, used_at: nil).update_all(used_at: Time.current)

      @token = PasswordResetToken.new(
        user: @user,
        account: @user.account,
        ip_address: request.remote_ip,
        expires_at: 1.hour.from_now
      )

      if @token.save
        PasswordResetMailer.with(
          user: @user,
          token: @token.raw_token,
          reset_url: password_reset_url(@token.raw_token)
        ).reset_password_email.deliver_now

        render json: { message: "Email de redefinição de senha enviado com sucesso" }, status: :ok
      else
        render_error(@token)
      end
    end

    def show
      if @token.nil?
        return render_error_message("Token inválido ou expirado")
      end

      render json: {
        message: "Token válido",
        expires_at: @token.expires_at,
        user_email: @token.user.email
      }, status: :ok
    end

    def complete
      if @token.nil?
        return render_error_message("Token inválido ou expirado")
      end

      user = @token.user

      if user.update(password: params[:password], pepper_migrated: true)
        @token.mark_used!
        render json: { message: "Senha alterada com sucesso" }, status: :ok
      else
        render_error(user)
      end
    end

    private

    def set_user_by_email
      @user = User.find_by(email: params[:email])
    end

    def set_token
      return unless params[:token].present?
      @token = PasswordResetToken.find_valid(params[:token])
    end

    def password_reset_url(token)
      frontend_url = ENV.fetch("FRONT_URL", "http://localhost:3000")
      "#{frontend_url}/reset-password/#{token}"
    end
  end
end
