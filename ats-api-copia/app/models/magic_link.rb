# frozen_string_literal: true

class MagicLink < ApplicationRecord
  belongs_to :user

  PURPOSES = %w[onboarding login].freeze
  EXPIRY_DURATION = 72.hours
  MAX_PER_USER_PER_DAY = 3

  validates :token_digest, presence: true, uniqueness: true
  validates :purpose, inclusion: { in: PURPOSES }
  validates :expires_at, presence: true

  scope :valid, -> { where(used_at: nil).where("expires_at > ?", Time.current) }
  scope :for_user, ->(uid) { where(user_id: uid) }

  def expired?
    expires_at < Time.current
  end

  def used?
    used_at.present?
  end

  def valid_for_use?
    !expired? && !used?
  end

  def consume!(ip: nil, agent: nil)
    raise "Magic link already used" if used?
    raise "Magic link expired" if expired?

    update!(
      used_at: Time.current,
      ip_address: ip,
      user_agent: agent&.truncate(500)
    )
  end
end
