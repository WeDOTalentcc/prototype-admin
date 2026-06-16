# frozen_string_literal: true

class LlmUsage < ApplicationRecord
  belongs_to :user
  belongs_to :account

  validates :model, presence: true
  validates :operation, presence: true
  validates :cost_usd, numericality: { greater_than_or_equal_to: 0 }
  validates :latency_ms, numericality: { greater_than_or_equal_to: 0 }

  scope :successful, -> { where(success: true) }
  scope :failed, -> { where(success: false) }
  scope :by_model, ->(model_name) { where(model: model_name) }
  scope :by_operation, ->(operation) { where(operation: operation) }
  scope :by_account, ->(account_id) { where(account_id: account_id) }
  scope :by_user, ->(user_id) { where(user_id: user_id) }
  scope :recent, -> { order(created_at: :desc) }
  scope :today, -> { where("created_at >= ?", Time.zone.today) }
  scope :this_month, -> { where("created_at >= ?", Time.zone.now.beginning_of_month) }

  def self.total_cost_by_account(account_id, start_date: nil, end_date: nil)
    query = by_account(account_id).successful
    query = query.where("created_at >= ?", start_date) if start_date
    query = query.where("created_at <= ?", end_date) if end_date
    query.sum(:cost_usd)
  end

  def self.usage_stats_by_model(account_id, start_date: nil, end_date: nil)
    query = by_account(account_id).successful
    query = query.where("created_at >= ?", start_date) if start_date
    query = query.where("created_at <= ?", end_date) if end_date

    query
      .group(:model)
      .select(
        "model",
        "COUNT(*) as request_count",
        "SUM(input_tokens) as total_input_tokens",
        "SUM(output_tokens) as total_output_tokens",
        "SUM(total_tokens) as total_tokens",
        "SUM(cost_usd) as total_cost",
        "AVG(latency_ms) as avg_latency_ms"
      )
  end

  def self.daily_costs(account_id, days: 30)
    by_account(account_id)
      .successful
      .where("created_at >= ?", days.days.ago)
      .group("DATE(created_at)")
      .select("DATE(created_at) as date, SUM(cost_usd) as total_cost")
      .order("date DESC")
  end
end
