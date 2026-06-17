# frozen_string_literal: true

class LlmQuotaUsage < ApplicationRecord
  belongs_to :account

  validates :period, presence: true, format: { with: /\A\d{4}-\d{2}\z/ }
  validates :total_cost_usd, numericality: { greater_than_or_equal_to: 0 }
  validates :total_requests, numericality: { greater_than_or_equal_to: 0 }
  validates :total_tokens, numericality: { greater_than_or_equal_to: 0 }
  validates :account_id, uniqueness: { scope: :period }

  scope :for_period, ->(period) { where(period: period) }
  scope :current_month, -> { for_period(Date.current.strftime("%Y-%m")) }

  def self.current_for(account_id)
    find_or_create_by!(account_id: account_id, period: Date.current.strftime("%Y-%m")) do |usage|
      usage.total_cost_usd = 0
      usage.total_requests = 0
      usage.total_tokens = 0
      usage.cost_by_model = {}
      usage.cost_by_operation = {}
    end
  end

  def increment_usage!(cost:, tokens:)
    self.class.where(id: id).update_all(
      [
        "total_cost_usd = total_cost_usd + ?, total_requests = total_requests + 1, total_tokens = total_tokens + ?, updated_at = ?",
        cost, tokens, Time.current
      ]
    )
    reload
  end
end
