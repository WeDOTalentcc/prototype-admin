# frozen_string_literal: true

class MfaService
  ISSUER = ENV.fetch("JWT_ISSUER", "ats-api")
  AUDIENCE = ENV.fetch("JWT_AUDIENCE", "ats-client")
  SECRET = Rails.application.secret_key_base
  OTP_TTL = 300
  VERIFY_ATTEMPTS_TTL = 900
  MAX_VERIFY_ATTEMPTS = 5

  def initialize
    @redis = Redis.new(url: ENV["REDIS_URL"])
  end

  def generate_otp(user)
    code = SecureRandom.random_number(10**6).to_s.rjust(6, "0")
    redis.setex(otp_key(user.id), OTP_TTL, code)
    Rails.logger.info "[MFA] OTP generated for user #{user.id} (expires in #{OTP_TTL}s)"
    code
  end

  def verify_otp(user, code)
    return false if rate_limited?(user)

    stored_code = redis.get(otp_key(user.id))
    return false unless stored_code

    increment_attempts(user)

    if stored_code == code.to_s.strip
      redis.del(otp_key(user.id))
      redis.del(attempts_key(user.id))
      Rails.logger.info "[MFA] OTP verified successfully for user #{user.id}"
      return true
    end

    Rails.logger.warn "[MFA] Invalid OTP attempt for user #{user.id}"
    false
  end

  def generate_mfa_token(user)
    payload = {
      role: "mfa_pending",
      user_id: user.id,
      iss: ISSUER,
      aud: AUDIENCE
    }
    exp = 10.minutes.from_now
    payload[:exp] = exp.to_i
    JWT.encode(payload, SECRET, "HS256")
  end

  def decode_mfa_token(token)
    return nil unless token.present?

    decoded = JWT.decode(
      token,
      SECRET,
      true,
      algorithm: "HS256",
      verify_iss: true,
      iss: ISSUER,
      verify_aud: true,
      aud: AUDIENCE,
      verify_exp: true
    )
    decoded.first.with_indifferent_access
  rescue JWT::DecodeError => e
    Rails.logger.warn "[MFA] Failed to decode MFA token: #{e.message}"
    nil
  end

  def rate_limited?(user)
    attempts = redis.get(attempts_key(user.id)).to_i
    attempts >= MAX_VERIFY_ATTEMPTS
  end

  def attempts_remaining(user)
    attempts = redis.get(attempts_key(user.id)).to_i
    [ MAX_VERIFY_ATTEMPTS - attempts, 0 ].max
  end

  private

  attr_reader :redis

  def otp_key(user_id)
    "mfa:otp:#{user_id}"
  end

  def attempts_key(user_id)
    "mfa:attempts:#{user_id}"
  end

  def increment_attempts(user)
    current = redis.get(attempts_key(user.id)).to_i
    redis.setex(attempts_key(user.id), VERIFY_ATTEMPTS_TTL, current + 1)
  end
end
