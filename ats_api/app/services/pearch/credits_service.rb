module Pearch
  class CreditsService
    class InsufficientCreditsError < StandardError; end

    def initialize(account)
      @account = account
    end

    def add_credits!(amount, reason:, transaction_type: "purchase", metadata: {})
      raise ArgumentError, "Amount must be positive" unless amount.positive?

      ActiveRecord::Base.transaction do
        balance_before = @account.pearch_credits

        @account.update!(pearch_credits: balance_before + amount)

        transaction = PearchCreditTransaction.create!(
          account: @account,
          transaction_type: transaction_type,
          amount: amount,
          balance_before: balance_before,
          balance_after: @account.pearch_credits,
          reason: reason,
          metadata: metadata
        )

        broadcast_credit_update(
          transaction: transaction,
          change_type: "added",
          amount_changed: amount
        )
      end

      @account.reload
    end

    def consume_credits!(amount, reason:, reference_id: nil, reference_type: nil, metadata: {})
      raise ArgumentError, "Amount must be positive" unless amount.positive?
      raise InsufficientCreditsError, "Insufficient credits. Required: #{amount}, Available: #{@account.pearch_credits}" if @account.pearch_credits < amount

      ActiveRecord::Base.transaction do
        balance_before = @account.pearch_credits

        @account.update!(
          pearch_credits: balance_before - amount,
          pearch_total_consumed: @account.pearch_total_consumed + amount
        )

        transaction = PearchCreditTransaction.create!(
          account: @account,
          transaction_type: "consumption",
          amount: -amount,
          balance_before: balance_before,
          balance_after: @account.pearch_credits,
          reason: reason,
          reference_id: reference_id,
          reference_type: reference_type,
          metadata: metadata
        )

        broadcast_credit_update(
          transaction: transaction,
          change_type: "consumed",
          amount_changed: amount
        )
      end

      @account.reload
    end

    def has_sufficient_credits?(amount)
      @account.pearch_credits >= amount
    end

    def current_balance
      @account.pearch_credits
    end

    def total_consumed
      @account.pearch_total_consumed
    end

    def transaction_history(limit: 50, start_date: nil, end_date: nil)
      scope = @account.pearch_credit_transactions.recent.limit(limit)
      scope = scope.by_date_range(start_date, end_date) if start_date && end_date
      scope
    end

    def statistics(start_date: nil, end_date: nil)
      {
        current_balance: current_balance,
        total_consumed: total_consumed,
        credits_added: PearchCreditTransaction.total_added(
          account_id: @account.id,
          start_date: start_date,
          end_date: end_date
        ),
        credits_consumed: PearchCreditTransaction.total_consumed(
          account_id: @account.id,
          start_date: start_date,
          end_date: end_date
        ),
        search_stats: PearchSearchLog.search_statistics(
          account_id: @account.id,
          start_date: start_date,
          end_date: end_date
        )
      }
    end

    private

    def broadcast_credit_update(transaction:, change_type:, amount_changed:)
      channel_name = "search_credits_account_#{@account.id}"

      payload = {
        type: "credit_update",
        change_type: change_type,
        amount_changed: amount_changed,
        current_balance: @account.pearch_credits,
        total_consumed: @account.pearch_total_consumed,
        transaction: {
          id: transaction.id,
          transaction_type: transaction.transaction_type,
          amount: transaction.amount,
          balance_before: transaction.balance_before,
          balance_after: transaction.balance_after,
          reason: transaction.reason,
          reference_type: transaction.reference_type,
          reference_id: transaction.reference_id,
          created_at: transaction.created_at
        },
        timestamp: Time.current.iso8601
      }

      ActionCable.server.broadcast(channel_name, payload)
    rescue => e
      Rails.logger.error("[Pearch::CreditsService] Failed to broadcast update: #{e.message}")
    end
  end
end
