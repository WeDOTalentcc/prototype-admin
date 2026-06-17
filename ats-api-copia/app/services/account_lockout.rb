# frozen_string_literal: true

# Account Lockout — Redis-backed brute force protection.
#
# Tracks failed login attempts per email. After MAX_ATTEMPTS failures
# within WINDOW_SECONDS, the account is locked for LOCKOUT_SECONDS.
#
# Uses Redis with auto-expiring keys (no migration needed).
# Fail-open: if Redis is unavailable, login is allowed (with warning).
#
# Item: PX08-084 — Wave 6, item 6.10

class AccountLockout
  MAX_ATTEMPTS = 5
  WINDOW_SECONDS = 900      # 15 minutes
  LOCKOUT_SECONDS = 1800    # 30 minutes

  REDIS_PREFIX = "lockout:"
  LOCKED_PREFIX = "locked:"

  # Check if an account is currently locked.
  # @param email [String] user email
  # @return [Boolean] true if locked
  def self.locked?(email)
    key = normalize_key(email)
    REDIS.exists?("#{LOCKED_PREFIX}#{key}")
  rescue Redis::BaseError => e
    Rails.logger.warn "[AccountLockout] Redis unavailable (fail-open): #{e.message}"
    false
  end

  # Record a failed login attempt. Locks account if threshold exceeded.
  # @param email [String] user email
  def self.record_failure(email)
    key = normalize_key(email)
    attempts_key = "#{REDIS_PREFIX}#{key}"

    count = REDIS.incr(attempts_key)
    REDIS.expire(attempts_key, WINDOW_SECONDS) if count == 1

    if count >= MAX_ATTEMPTS
      REDIS.setex("#{LOCKED_PREFIX}#{key}", LOCKOUT_SECONDS, "1")
      REDIS.del(attempts_key)
      Rails.logger.warn "[AccountLockout] Locked email=#{key} after #{count} failed attempts"
    end
  rescue Redis::BaseError => e
    Rails.logger.warn "[AccountLockout] Redis error on record_failure: #{e.message}"
  end

  # Clear failed attempts on successful login.
  # @param email [String] user email
  def self.clear(email)
    key = normalize_key(email)
    REDIS.del("#{REDIS_PREFIX}#{key}")
  rescue Redis::BaseError => e
    Rails.logger.warn "[AccountLockout] Redis error on clear: #{e.message}"
  end

  # Remaining lockout time in seconds (0 if not locked).
  def self.remaining_seconds(email)
    key = normalize_key(email)
    ttl = REDIS.ttl("#{LOCKED_PREFIX}#{key}")
    [ttl, 0].max
  rescue Redis::BaseError
    0
  end

  def self.normalize_key(email)
    email.to_s.strip.downcase
  end

  private_class_method :normalize_key
end
