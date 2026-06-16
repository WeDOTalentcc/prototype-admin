# frozen_string_literal: true

class MagicLinkService
  class RateLimitExceeded < StandardError; end
  class InvalidToken < StandardError; end
  class ExpiredToken < StandardError; end
  class AlreadyUsed < StandardError; end

  # Generate a magic link for a user
  # Returns: { token: raw_token, magic_link: MagicLink, url: full_url }
  def self.generate(user:, purpose: "onboarding")
    # Rate limit: max 3 per user per 24h
    recent_count = MagicLink.for_user(user.id)
                            .where("created_at > ?", 24.hours.ago)
                            .count
    raise RateLimitExceeded, "Maximum #{MagicLink::MAX_PER_USER_PER_DAY} magic links per 24h" if recent_count >= MagicLink::MAX_PER_USER_PER_DAY

    # Generate cryptographically secure random token (256 bits)
    raw_token = SecureRandom.urlsafe_base64(32)
    token_digest = BCrypt::Password.create(raw_token)

    magic_link = MagicLink.create!(
      user: user,
      token_digest: token_digest,
      purpose: purpose,
      expires_at: MagicLink::EXPIRY_DURATION.from_now
    )

    # Build full URL
    base_url = ENV.fetch("FRONTEND_URL", "https://app.wedotalent.com")
    url = "#{base_url}/auth/magic?token=#{raw_token}&uid=#{user.id}"

    { token: raw_token, magic_link: magic_link, url: url }
  end

  # Validate and consume a magic link. Returns JWT + user data.
  # Raises: InvalidToken, ExpiredToken, AlreadyUsed
  def self.verify(token:, user_id:, ip: nil, user_agent: nil)
    user = User.find_by(id: user_id)
    raise InvalidToken, "User not found" unless user

    # Find all valid (unexpired, unused) magic links for this user
    candidates = MagicLink.valid.for_user(user.id)
    raise InvalidToken, "No valid magic link found" if candidates.empty?

    # Compare bcrypt hash against each candidate
    matched = candidates.find { |ml| BCrypt::Password.new(ml.token_digest) == token }
    raise InvalidToken, "Token does not match" unless matched

    # Consume the magic link
    matched.consume!(ip: ip, agent: user_agent)

    # Update user activation state
    # Check both first_login_at AND activation_state to handle re-onboarding
    is_first_login = user.first_login_at.nil? || user.activation_state.in?(%w[pending invited])
    if is_first_login
      user.update!(
        activation_state: "onboarding",
        first_login_at: user.first_login_at || Time.current
      )
    end

    # Update last_login_at
    user.update!(last_login_at: Time.current)

    # Generate JWT (same pattern as SessionsController)
    payload = { user_id: user.id, exp: 24.hours.from_now.to_i }
    jwt = JWT.encode(payload, Rails.application.secret_key_base)

    # Find active onboarding session
    session = OnboardingSession.for_user(user.id).active.first

    {
      token: jwt,
      user: {
        id: user.id,
        email: user.email,
        name: user.name,
        activation_state: user.activation_state
      },
      first_login: is_first_login,
      onboarding_session_id: session&.id
    }
  end
end
