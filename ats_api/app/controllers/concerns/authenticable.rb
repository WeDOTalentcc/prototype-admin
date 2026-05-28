module Authenticable
  extend ActiveSupport::Concern

  GENERIC_AUTH_ERROR = "Não autorizado".freeze

  def authorize_request
    token = request.headers["Authorization"]&.split(" ")&.last

    begin
      decoded = JsonWebToken.decode(token)
      unless decoded
        Rails.logger.warn("[auth] Token inválido ou expirado")
        return render_unauthorized
      end

      @jwt_payload = decoded

      role = decoded[:role].to_s
      if role == "one_time_token"
        Rails.logger.warn("[auth] Tipo de token desconhecido: #{role}")
        return render_unauthorized
      end
      return authorize_service(decoded) if role == "service"
      return authorize_user(decoded) if decoded[:user_id]

      Rails.logger.warn("[auth] Tipo de token desconhecido: #{role}")
      render_unauthorized

    rescue JWT::DecodeError => e
      Rails.logger.warn("[auth] Erro na decodificação do JWT: #{e.message}")
      render_unauthorized
    end
  end

  private

  def authorize_service(payload)
    account = Account.find_by(id: payload[:account_id])
    unless account
      Rails.logger.warn("[auth] Conta inválida especificada no token (account_id=#{payload[:account_id].inspect})")
      return render_unauthorized
    end

    Current.account = account

    if payload[:user_id].present?
      @current_user = User.find_by(id: payload[:user_id])
      unless @current_user
        Rails.logger.warn("[auth] Usuário do token não encontrado (user_id=#{payload[:user_id].inspect})")
        return render_unauthorized
      end

      Current.user = @current_user
    end

    Apartment::Tenant.switch!(account.tenant)
  end

  def authorize_user(payload)
    user_id = payload[:user_id]
    user = Rails.cache.fetch("auth:user:#{user_id}", expires_in: 30.seconds) do
      User.find_by(id: user_id)
    end
    unless user
      Rails.logger.warn("[auth] Usuário do token não encontrado (user_id=#{user_id.inspect})")
      return render_unauthorized
    end

    @current_user = user
    Current.user = @current_user
    account = Rails.cache.fetch("auth:account:#{user.account_id}", expires_in: 30.seconds) do
      user.account
    end
    Current.account = account
    Apartment::Tenant.switch!(account.tenant)
  end

  def render_unauthorized
    render(json: { error: GENERIC_AUTH_ERROR }, status: :unauthorized)
  end

  def render_forbidden(msg)    = render(json: { error: msg }, status: :forbidden)
  def render_conflict(msg)     = render(json: { error: msg }, status: :conflict)
  def jwt_decode(token)        = JsonWebToken.decode(token)
end
