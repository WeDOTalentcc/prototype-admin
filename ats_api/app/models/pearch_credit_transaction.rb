class PearchCreditTransaction < ApplicationRecord
  belongs_to :account

  TRANSACTION_TYPES = {
    purchase: "purchase",           # Manual credit purchase
    refund: "refund",              # Credit refund
    bonus: "bonus",                # Promotional bonus
    adjustment: "adjustment",       # Manual adjustment
    consumption: "consumption"      # Automatic consumption from search
  }.freeze

  enum transaction_type: TRANSACTION_TYPES

  validates :amount, presence: true, numericality: { other_than: 0 }
  validates :transaction_type, presence: true, inclusion: { in: TRANSACTION_TYPES.keys.map(&:to_s) }
  validates :balance_after, presence: true, numericality: { greater_than_or_equal_to: 0 }

  scope :credits_added, -> { where("amount > 0") }
  scope :credits_consumed, -> { where("amount < 0") }
  scope :recent, -> { order(created_at: :desc) }
  scope :for_account, ->(account_id) { where(account_id: account_id) }
  scope :by_type, ->(type) { where(transaction_type: type) }
  scope :by_date_range, ->(start_date, end_date) { where(created_at: start_date..end_date) }

  def self.total_added(account_id: nil, start_date: nil, end_date: nil)
    scope = credits_added
    scope = scope.for_account(account_id) if account_id
    scope = scope.by_date_range(start_date, end_date) if start_date && end_date
    scope.sum(:amount)
  end

  def self.total_consumed(account_id: nil, start_date: nil, end_date: nil)
    scope = credits_consumed
    scope = scope.for_account(account_id) if account_id
    scope = scope.by_date_range(start_date, end_date) if start_date && end_date
    scope.sum(:amount).abs
  end
end
