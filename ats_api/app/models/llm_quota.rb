# frozen_string_literal: true

class LlmQuota < ApplicationRecord
  belongs_to :account

  validates :plan, presence: true, inclusion: { in: %w[starter pro enterprise custom] }
  validates :monthly_cost_limit_usd, presence: true, numericality: { greater_than_or_equal_to: 0 }
  validates :burst_rpm, presence: true, numericality: { greater_than: 0 }
  validates :extra_budget_usd, numericality: { greater_than_or_equal_to: 0 }
  validates :notify_at_percentage, numericality: { in: 1..100 }
  validates :account_id, uniqueness: true

  scope :active, -> { where(enabled: true) }
  scope :by_plan, ->(plan) { where(plan: plan) }

  def effective_monthly_limit
    monthly_cost_limit_usd + active_extra_budget
  end

  def active_extra_budget
    return 0.0 if extra_budget_usd.zero?
    return 0.0 if extra_budget_expires_at.present? && extra_budget_expires_at < Time.current

    extra_budget_usd
  end

  def extra_budget_expired?
    extra_budget_expires_at.present? && extra_budget_expires_at < Time.current
  end

  def current_usage
    LlmQuotaUsage.current_for(account_id)
  end

  def usage_percentage
    usage = current_usage
    return 0.0 if effective_monthly_limit.zero?

    ((usage.total_cost_usd / effective_monthly_limit) * 100).round(2)
  end

  def cost_remaining
    [ effective_monthly_limit - current_usage.total_cost_usd, 0 ].max
  end

  def requests_remaining
    return nil unless monthly_request_limit

    [ monthly_request_limit - current_usage.total_requests, 0 ].max
  end

  def apply_plan!(plan_name)
    defaults = Llm::QuotaPlan.defaults_for(plan_name)
    update!(
      plan: plan_name,
      monthly_cost_limit_usd: defaults[:monthly_cost_limit_usd],
      monthly_request_limit: defaults[:monthly_request_limit],
      burst_rpm: defaults[:burst_rpm]
    )
  end

  def grant_extra_budget!(amount:, expires_at: nil, reason: nil)
    current_metadata = metadata.is_a?(Hash) ? metadata : {}
    update!(
      extra_budget_usd: extra_budget_usd + amount,
      extra_budget_expires_at: expires_at,
      metadata: current_metadata.merge(
        "last_extra_granted_at" => Time.current.iso8601,
        "last_extra_amount" => amount.to_f,
        "last_extra_reason" => reason
      )
    )
  end

  private

  def current_period
    Date.current.strftime("%Y-%m")
  end
end
