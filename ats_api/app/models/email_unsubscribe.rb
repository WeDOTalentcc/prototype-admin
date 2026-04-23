class EmailUnsubscribe < ApplicationRecord
  belongs_to :account
  belongs_to :candidate

  validates :email, presence: true, uniqueness: { scope: :account_id }
  validates :token, presence: true, uniqueness: true

  before_validation :generate_token, on: :create

  scope :active, -> { where.not(unsubscribed_at: nil) }

  def self.unsubscribed?(account_id, email)
    where(account_id: account_id, email: email).where.not(unsubscribed_at: nil).exists?
  end

  private

  def generate_token
    self.token = SecureRandom.urlsafe_base64(48) while token.blank? || EmailUnsubscribe.where(token: token).exists?
  end
end
