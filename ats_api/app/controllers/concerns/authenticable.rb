module Authenticable
  extend ActiveSupport::Concern

  def authorize_request
    token = request.headers["Authorization"]&.split(" ")&.last

    begin
      decoded = JsonWebToken.decode(token)
      return render_unauthorized("Token inválido ou expirado") unless decoded

      @jwt_payload = decoded

      role = decoded[:role].to_s
      return render_unauthorized("Tipo de token desconhecido: #{role}") if role == "one_time_token"
      return authorize_service(decoded) if role == "service"
      return authorize_user(decoded) if decoded[:user_id]

      render_unauthorized("Tipo de token desconhecido: #{role}")

    rescue JWT::DecodeError => e
      render_unauthorized("Erro na decodificação do JWT: #{e.message}")
    end
  end

  private

  def authorize_service(payload)
    account = Account.find_by(id: payload[:account_id])
    return render_unauthorized("Conta inválida especificada no token") unless account

    Current.account = account

    if payload[:user_id].present?
      @current_user = User.find_by(id: payload[:user_id])
      return render_unauthorized("Usuário do token não encontrado") unless @current_user

      Current.user = @current_user
    end

    Apartment::Tenant.switch!(account.tenant)
  end

  def authorize_user(payload)
    user_id = payload[:user_id]
    user = Rails.cache.fetch("auth:user:#{user_id}", expires_in: 30.seconds) do
      User.find_by(id: user_id)
    end
    return render_unauthorized("Usuário do token não encontrado") unless user

    @current_user = user
    Current.user = @current_user
    account = Rails.cache.fetch("auth:account:#{user.account_id}", expires_in: 30.seconds) do
      user.account
    end
    Current.account = account
    Apartment::Tenant.switch!(account.tenant)
  end

  def render_unauthorized(msg)
    response.set_header("X-Auth-Debug", msg.to_s)
    render(json: { error: msg }, status: :unauthorized)
  end

  def render_forbidden(msg)    = render(json: { error: msg }, status: :forbidden)
  def render_conflict(msg)     = render(json: { error: msg }, status: :conflict)
  def jwt_decode(token)        = JsonWebToken.decode(token)
end
