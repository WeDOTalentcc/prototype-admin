# frozen_string_literal: true

class TeamsChatSubscription < ApplicationRecord
  belongs_to :lia_user, class_name: "User"
  belongs_to :recruiter_user, class_name: "User"
  belongs_to :account

  validates :chat_id, presence: true, uniqueness: true
  validates :tenant, presence: true
  validates :subscription_id, uniqueness: true, allow_nil: true
  validates :status, inclusion: { in: %w[active expired failed] }

  scope :active, -> { where(status: "active") }
  scope :failed, -> { where(status: "failed") }
  scope :expiring_soon, -> { active.where("subscription_expires_at < ?", 20.minutes.from_now) }
  scope :expired, -> { where("subscription_expires_at < ?", Time.current) }
  scope :for_recruiter, ->(user_id) { where(recruiter_user_id: user_id) }

  def subscription_active?
    status == "active" && subscription_id.present? && subscription_expires_at&.future?
  end

  def mark_expired!
    update!(status: "expired")
  end
end
