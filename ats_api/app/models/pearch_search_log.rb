class PearchSearchLog < ApplicationRecord
  belongs_to :account
  belongs_to :user

  validates :query, presence: true
  validates :credits_used, presence: true, numericality: { greater_than_or_equal_to: 0 }
  validates :credits_remaining_after, presence: true, numericality: { greater_than_or_equal_to: 0 }

  scope :successful, -> { where(status: "Done") }
  scope :failed, -> { where.not(status: "Done") }
  scope :recent, -> { order(created_at: :desc) }
  scope :for_account, ->(account_id) { where(account_id: account_id) }
  scope :for_user, ->(user_id) { where(user_id: user_id) }
  scope :by_date_range, ->(start_date, end_date) { where(created_at: start_date..end_date) }

  def self.total_credits_consumed(account_id: nil, start_date: nil, end_date: nil)
    scope = all
    scope = scope.for_account(account_id) if account_id
    scope = scope.by_date_range(start_date, end_date) if start_date && end_date
    scope.sum(:credits_used)
  end

  def self.search_statistics(account_id: nil, start_date: nil, end_date: nil)
    scope = all
    scope = scope.for_account(account_id) if account_id
    scope = scope.by_date_range(start_date, end_date) if start_date && end_date

    {
      total_searches: scope.count,
      successful_searches: scope.successful.count,
      failed_searches: scope.failed.count,
      total_credits_used: scope.sum(:credits_used),
      total_results_returned: scope.sum(:results_count),
      average_duration: scope.average(:duration_seconds)&.round(2)
    }
  end
end
