# frozen_string_literal: true

class JsonWebToken
  ISSUER   = ENV.fetch('JWT_ISSUER', 'wedo-ats-api')
  AUDIENCE = ENV.fetch('JWT_AUDIENCE', 'wedo-agent')
  # Prefere RAILS_JWT_SECRET_KEY (compartilhado com FastAPI) — fallback para secret_key_base.
  SECRET   = ENV['RAILS_JWT_SECRET_KEY'].presence || Rails.application.secret_key_base

  def self.encode(payload, exp = 24.hours.from_now)
    claims = payload.dup
    claims[:iss] = ISSUER
    claims[:aud] = AUDIENCE
    claims[:exp] = exp.to_i
    JWT.encode(claims, SECRET, "HS256")
  end

  def self.encode_service_token(account_id:, user_id: nil, scope: nil, exp: 5.minutes.from_now)
    payload = {
      iss: ISSUER,
      aud: AUDIENCE,
      exp: exp.to_i,
      jti: SecureRandom.uuid,
      role: "service",
      account_id: account_id,
      user_id: user_id,
      scope: scope
    }
    payload.compact!
    JWT.encode(payload, SECRET, "HS256")
  end

  def self.decode(token)
    decoded = JWT.decode(token, SECRET, true, { algorithm: "HS256", verify_exp: true })
    decoded.first.with_indifferent_access
  rescue JWT::DecodeError => e
    Rails.logger.error "[JWT] Decode failed: #{e.class} #{e.message}"
    nil
  end

  def self.encode_ott(account_id:, user_id:, exp: 5.minutes.from_now)
    jti = SecureRandom.uuid
    payload = {
      iss: ISSUER,
      aud: AUDIENCE,
      exp: exp.to_i,
      jti: jti,
      role: "one_time_token",
      account_id: account_id,
      user_id: user_id
    }
    token = JWT.encode(payload, SECRET, "HS256")
    Rails.logger.info "🔑 [JWT] OTT encoded account_id=#{account_id} user_id=#{user_id} jti=#{jti} exp=#{exp.utc.iso8601} ttl=600s token_length=#{token.length} iss=#{ISSUER} aud=#{AUDIENCE}"
    token
  end
end
