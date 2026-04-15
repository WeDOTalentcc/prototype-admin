class ApplicationController < ActionController::Base
  
  def authorize_request
    header = request.headers['Authorization']
    token = header.split(' ').last if header

    decoded = jwt_decode(token)

    if decoded
      if JwtBlacklist.revoked?(decoded)
        return render json: { error: 'Token revogado' }, status: :unauthorized
      end

      @current_user = User.find_by(id: decoded[:user_id])
      render json: { error: 'Not Authorized' }, status: :unauthorized unless @current_user
    else
      render json: { error: 'Token missing or invalid' }, status: :unauthorized
    end
  end

  def jwt_encode(payload, exp = 24.hours.from_now)
    payload[:exp] = exp.to_i
    JWT.encode(payload, Rails.application.secret_key_base)
  end

  def jwt_decode(token)
    decoded = JWT.decode(token, Rails.application.secret_key_base)[0]
    HashWithIndifferentAccess.new decoded
  rescue StandardError => e
    Rails.logger.error "JWT Decode Error: #{e.message}"
    nil
  end
end
