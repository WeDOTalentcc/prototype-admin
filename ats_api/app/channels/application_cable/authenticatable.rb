# frozen_string_literal: true

module ApplicationCable
  module Authenticatable
    extend ActiveSupport::Concern

    private

    def authenticate_user!
      return true if connection.current_user

      token = params[:auth_token]
      decoded = jwt_decode(token)

      if decoded
        user = User.find_by(id: decoded[:user_id])
        if user
          connection.current_user = user
          return true
        end
      end

      reject
      false
    end

    def jwt_decode(token)
      decoded = JWT.decode(token, Rails.application.secret_key_base)[0]
      HashWithIndifferentAccess.new(decoded)
    rescue StandardError => e
      Rails.logger.error "[Authenticatable] JWT Decode Error: #{e.message}"
      nil
    end
  end
end
