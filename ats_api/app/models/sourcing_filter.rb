# frozen_string_literal: true

class SourcingFilter < ApplicationRecord
  belongs_to :account
  belongs_to :user

  validates :uid, presence: true, uniqueness: true
  validates :name, presence: true, uniqueness: { scope: :account_id }

  before_validation :generate_uid, on: :create

  scope :by_account, ->(account_id) { where(account_id: account_id) }
  scope :active, -> { where(is_deleted: false) }
  scope :most_used, -> { order(usage_count: :desc) }
  scope :recently_used, -> { order(last_used_at: :desc) }

  def increment_usage!
    increment!(:usage_count)
    touch(:last_used_at)
  end

  def to_search_params
    {
      query: query,
      **parameters.symbolize_keys
    }
  end

  private

  def generate_uid
    self.uid ||= SecureRandom.uuid
  end
end
