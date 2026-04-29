module ApplicationCable
  class Connection < ActionCable::Connection::Base
    identified_by :current_user

    def connect
      token = request.params[:auth_token]

      if token.present?
        self.current_user = find_verified_user(token)
        logger.add_tags "ActionCable", "User #{current_user.id}" if current_user
      end
    end

    private

    def find_verified_user(token)
      decoded = jwt_decode(token)
      return unless decoded

      User.find_by(id: decoded[:user_id])
    end

    def jwt_decode(token)
      decoded = JWT.decode(token, Rails.application.secret_key_base)[0]
      HashWithIndifferentAccess.new(decoded)
    rescue StandardError => e
      Rails.logger.error "[ActionCable::Connection] JWT Decode Error: #{e.message}"
      nil
    end
  end
end
