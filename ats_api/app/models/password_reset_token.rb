# app/models/password_reset_token.rb
class PasswordResetToken < ApplicationRecord
  include Searchable

  belongs_to :user
  belongs_to :account
  before_create :generate_token

  validates :ip_address, presence: true
  validates :expires_at, presence: true

  scope :valid_tokens, -> { where(used_at: nil).where("expires_at > ?", Time.current) }

  def generate_token
    raw = SecureRandom.urlsafe_base64(48)
    self.token_digest = Digest::SHA256.hexdigest(raw)
    @raw_token = raw
  end

  def raw_token
    @raw_token
  end

  def self.find_valid(token)
    digest = Digest::SHA256.hexdigest(token)
    valid_tokens.find_by(token_digest: digest)
  end

  def mark_used!
    update!(used_at: Time.current)
  end
end
