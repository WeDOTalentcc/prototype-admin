# frozen_string_literal: true

module V1
  class SessionsController < ApplicationController
    before_action :authorize_request, except: [ :create ]
    protect_from_forgery with: :null_session

    def create
      if AccountLockout.locked?(params[:email])
        remaining = AccountLockout.remaining_seconds(params[:email])
        return render json: {
          error: "Conta temporariamente bloqueada. Tente novamente em #{(remaining / 60.0).ceil} minutos."
        }, status: :too_many_requests
      end

      @user = User.find_by(email: params[:email])

      if @user&.authenticate(params[:password])
        AccountLockout.clear(params[:email])
        token = jwt_encode(user_id: @user.id)
        render json: { user: user_payload(@user), token: }, status: :ok
      else
        AccountLockout.record_failure(params[:email])
        render json: { error: "Invalid email or password" }, status: :unauthorized
      end
    end

    def me
      render json: { user: user_payload(@current_user) }
    end

    def logout
      header = request.headers["Authorization"]
      token = header.split(" ").last if header
      decoded = jwt_decode(token)
      JwtBlacklist.revoke!(decoded) if decoded
      render json: { message: "Logged out" }
    end

    private

    def user_payload(user)
      {
        id: user.id,
        email: user.email
        # Removed 'name: user.name' as the User instance does not have a 'name' attribute.
        # If 'name' is required, ensure your User model has a 'name' column
        # and your FactoryBot definition for User creates a 'name'.
      }
    end

    def jwt_encode(payload, exp = 24.hours.from_now)
      payload[:exp] = exp.to_i
      JWT.encode(payload, Rails.application.secret_key_base)
    end

    def jwt_decode(token)
      decoded = JWT.decode(token, Rails.application.secret_key_base)[0]
      HashWithIndifferentAccess.new decoded
    rescue StandardError => e # Added StandardError for better error handling
      Rails.logger.error "JWT Decode Error: #{e.message}" # Log the error
      nil
    end

    def authorize_request
      header = request.headers["Authorization"]
      token = header.split(" ").last if header

      decoded = jwt_decode(token)

      if decoded
        if JwtBlacklist.revoked?(decoded)
          return render json: { error: "Token revogado" }, status: :unauthorized
        end

        @current_user = User.find_by(id: decoded[:user_id])
        Current.user = @current_user
        render json: { error: "Invalid token" }, status: :unauthorized unless @current_user
      else
        render json: { error: "Token missing or invalid" }, status: :unauthorized
      end
    end
  end
end
