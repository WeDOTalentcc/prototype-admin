module ApplicationCable
  class Connection < ActionCable::Connection::Base
    identified_by :current_user

    def connect
      self.current_user = find_verified_user
      logger.add_tags 'ActionCable', "User #{current_user.id}"
    end

    private

    def find_verified_user
      token = request.params[:auth_token]

      decoded = jwt_decode(token)
    
      if decoded
        user = User.find_by(id: decoded[:user_id])
        reject_unauthorized_connection unless user
        user
      else
        reject_unauthorized_connection
      end
    end

    def jwt_decode(token)
      decoded = JWT.decode(token, Rails.application.secret_key_base)[0]
      HashWithIndifferentAccess.new decoded
    rescue StandardError => e
      Rails.logger.error "JWT Decode Error: #{e.message}"
      nil
    end
  end
end
