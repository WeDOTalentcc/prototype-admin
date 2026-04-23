class SharedSearch < ApplicationRecord
  include UidGeneratable

  belongs_to :user
  belongs_to :account

  validates :title, presence: true
  validates :token, presence: true, uniqueness: true

  before_validation :ensure_token, on: :create

  scope :active, -> { where(is_deleted: false) }
  scope :not_expired, -> { where("expires_at IS NULL OR expires_at > ?", Time.current) }

  def expired?
    expires_at.present? && expires_at <= Time.current
  end

  def add_emails(emails)
    normalized = Array(emails).compact.map(&:to_s).map(&:downcase).uniq
    update(shared_with_emails: (shared_with_emails + normalized).uniq)
  end

  private

  def ensure_token
    self.token ||= SecureRandom.urlsafe_base64(24)
  end
end
