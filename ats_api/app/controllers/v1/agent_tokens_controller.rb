# frozen_string_literal: true

class V1::AgentTokensController < ActionController::API
  include RenderDefault

  SERVICE_TOKEN_TTL = 30.minutes

  def exchange
    ott = params[:one_time_token] || params.dig(:agent_token, :one_time_token)
    client_id = params[:client_id].presence || params.dig(:agent_token, :client_id).presence

    if ott.blank?
      Rails.logger.error "❌ [OTT_EXCHANGE] OTT is blank. params_keys=#{params.keys.join(', ')}"
      return render_unauthorized("Missing one-time token")
    end

    payload = JsonWebToken.decode(ott)
    ott_preview = "#{ott[0..7]}...#{ott[-8..]}"

    unless payload
      Rails.logger.error "❌ [OTT_EXCHANGE] JWT decode returned nil — token is invalid or expired"
      Rails.logger.error "   [OTT_EXCHANGE] ott_preview=#{ott_preview} ott_length=#{ott.length}"
      Rails.logger.error "   [OTT_EXCHANGE] Possible causes: expired token, wrong SECRET_KEY_BASE, issuer/audience mismatch"
      return render_unauthorized("Invalid or expired one-time token")
    end

    unless payload[:role] == "one_time_token"
      Rails.logger.error "❌ [OTT_EXCHANGE] Wrong role in payload. expected=one_time_token got=#{payload[:role]}"
      Rails.logger.error "   [OTT_EXCHANGE] account_id=#{payload[:account_id]} user_id=#{payload[:user_id]} jti=#{payload[:jti]}"
      return render_unauthorized("Invalid or expired one-time token")
    end

    unless RequestKey.claim!("ott:#{payload[:jti]}", ttl: 10.minutes)
      Rails.logger.error "❌ [OTT_EXCHANGE] OTT already claimed jti=#{payload[:jti]} account_id=#{payload[:account_id]}"
      return render_conflict("One-time token already used")
    end

    if client_id
      client = ApiClient.find_by(client_id: client_id, account_id: payload[:account_id])
      Rails.logger.warn("[OTT_EXCHANGE] Unknown client_id=#{client_id} for account=#{payload[:account_id]}") unless client
    end

    ttl = SERVICE_TOKEN_TTL
    token = JsonWebToken.encode_service_token(
      account_id: payload[:account_id],
      user_id: payload[:user_id],
      exp: ttl.from_now
    )
    Rails.logger.info "✅ [OTT_EXCHANGE] Service token issued account_id=#{payload[:account_id]} user_id=#{payload[:user_id]} ttl=#{ttl.to_i}s"
    render json: { access_token: token, token_type: "Bearer", expires_in: ttl.to_i, user_id: payload[:user_id] }
  end

  def refresh
    auth_header = request.headers["Authorization"]&.split(" ")&.last
    return render_unauthorized("Missing token") if auth_header.blank?

    payload = JsonWebToken.decode(auth_header)
    unless payload
      payload = decode_expired_token(auth_header)
      return render_unauthorized("Token invalid") unless payload
    end

    unless payload[:role].to_s == "service"
      return render_unauthorized("Invalid token role for refresh")
    end

    ttl = SERVICE_TOKEN_TTL
    new_token = JsonWebToken.encode_service_token(
      account_id: payload[:account_id],
      user_id: payload[:user_id],
      exp: ttl.from_now
    )

    Rails.logger.info "🔄 [TOKEN_REFRESH] Token refreshed account_id=#{payload[:account_id]} user_id=#{payload[:user_id]} ttl=#{ttl.to_i}s"
    render json: { access_token: new_token, token_type: "Bearer", expires_in: ttl.to_i }
  end

  private

  def decode_expired_token(token)
    opts = { algorithm: "HS256", verify_exp: false }
    decoded = JWT.decode(token, JsonWebToken::SECRET, true, opts)
    payload = decoded.first.with_indifferent_access

    expired_at = Time.at(payload[:exp].to_i)
    grace_period = 30.seconds
    return nil if expired_at < grace_period.ago

    jti = payload[:jti]
    return nil if jti.present? && !RequestKey.claim!("refresh:#{jti}", ttl: 2.minutes)

    payload
  rescue JWT::DecodeError
    nil
  end

  def render_unauthorized(msg) = render(json: { error: msg }, status: :unauthorized)
  def render_conflict(msg)     = render(json: { error: msg }, status: :conflict)
end
