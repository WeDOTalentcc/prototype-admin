# frozen_string_literal: true

# JWT Blacklist — Redis-backed token revocation.
#
# Tokens are blacklisted on logout. Each entry expires when the
# original token would have expired (TTL = token exp - now),
# so Redis auto-cleans stale entries.
#
# Fail-open: if Redis is unavailable, the token is NOT rejected
# (availability > security for non-critical flows). A warning is logged.
#
# Item: PX08-063 — Sprint 9, item 9.5

class JwtBlacklist
  REDIS_PREFIX = "jwt_blacklist:"

  # Revoke a token by adding it to the blacklist.
  # @param token_payload [Hash] decoded JWT payload (must have 'exp')
  def self.revoke!(token_payload)
    jti = extract_jti(token_payload)
    ttl = compute_ttl(token_payload)
    return if ttl <= 0 # already expired, no point blacklisting

    REDIS.setex("#{REDIS_PREFIX}#{jti}", ttl, "1")
    Rails.logger.info "[JwtBlacklist] Revoked token jti=#{jti} ttl=#{ttl}s"
  rescue Redis::BaseError => e
    Rails.logger.warn "[JwtBlacklist] Redis error on revoke: #{e.message}"
  end

  # Check if a token has been revoked.
  # @param token_payload [Hash] decoded JWT payload
  # @return [Boolean] true if token is blacklisted
  def self.revoked?(token_payload)
    jti = extract_jti(token_payload)
    REDIS.exists?("#{REDIS_PREFIX}#{jti}")
  rescue Redis::BaseError => e
    # Fail-open: if Redis is down, allow the request through
    Rails.logger.warn "[JwtBlacklist] Redis unavailable, fail-open: #{e.message}"
    false
  end

  # Extract or generate a unique identifier for the token.
  # Uses 'jti' claim if present, otherwise SHA256 of the payload.
  def self.extract_jti(token_payload)
    token_payload["jti"] || Digest::SHA256.hexdigest(token_payload.to_json)[0..15]
  end

  # Compute TTL: time remaining until token expiry.
  def self.compute_ttl(token_payload)
    exp = token_payload["exp"].to_i
    [exp - Time.now.to_i, 0].max
  end

  private_class_method :extract_jti, :compute_ttl
end
