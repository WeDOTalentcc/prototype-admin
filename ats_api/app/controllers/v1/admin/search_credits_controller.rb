module V1
  module Admin
    class SearchCreditsController < ApplicationController
      before_action :set_account, only: [ :add, :remove, :show, :transactions ]
      before_action :authorize_super_admin

      def add
        amount = params[:amount].to_i
        reason = params[:reason] || "Manual credit addition"
        transaction_type = params[:transaction_type] || "purchase"

        if amount <= 0
          return render json: { error: "Amount must be positive" }, status: :bad_request
        end

        credits_service = ::Pearch::CreditsService.new(@account)
        previous_balance = credits_service.current_balance

        credits_service.add_credits!(
          amount,
          reason: reason,
          transaction_type: transaction_type,
          metadata: {
            added_by_user_id: @current_user.id,
            added_by_user_name: @current_user.name
          }
        )

        render json: {
          success: true,
          message: "#{amount} credits added successfully",
          account: {
            id: @account.id,
            name: @account.name,
            previous_balance: previous_balance,
            current_balance: credits_service.current_balance,
            total_consumed: credits_service.total_consumed
          }
        }, status: :ok
      rescue => e
          Rails.logger.error("[Admin::SearchCreditsController] Add credits failed: #{e.message}")
        render json: { error: e.message }, status: :unprocessable_entity
      end

      def remove
        amount = params[:amount].to_i
        reason = params[:reason] || "Manual credit removal"

        if amount <= 0
          return render json: { error: "Amount must be positive" }, status: :bad_request
        end

        credits_service = ::Pearch::CreditsService.new(@account)
        previous_balance = credits_service.current_balance

        if previous_balance < amount
          return render json: {
            error: "Insufficient credits",
            current_balance: previous_balance,
            requested_amount: amount
          }, status: :unprocessable_entity
        end

        credits_service.consume_credits!(
          amount,
          reason: reason,
          metadata: {
            removed_by_user_id: @current_user.id,
            removed_by_user_name: @current_user.name
          }
        )

        render json: {
          success: true,
          message: "#{amount} credits removed successfully",
          account: {
            id: @account.id,
            name: @account.name,
            previous_balance: previous_balance,
            current_balance: credits_service.current_balance,
            total_consumed: credits_service.total_consumed
          }
        }, status: :ok
      rescue => e
          Rails.logger.error("[Admin::SearchCreditsController] Remove credits failed: #{e.message}")
        render json: { error: e.message }, status: :unprocessable_entity
      end

      def show
        credits_service = ::Pearch::CreditsService.new(@account)
        start_date = params[:start_date] ? Date.parse(params[:start_date]) : nil
        end_date = params[:end_date] ? Date.parse(params[:end_date]) : nil

        render json: {
          account: {
            id: @account.id,
            name: @account.name
          },
          statistics: credits_service.statistics(
            start_date: start_date,
            end_date: end_date
          )
        }, status: :ok
      rescue ArgumentError => e
        render json: { error: "Invalid date format: #{e.message}" }, status: :bad_request
      end

      def transactions
        limit = [ params[:limit]&.to_i || 50, 100 ].min
        start_date = params[:start_date] ? Date.parse(params[:start_date]) : nil
        end_date = params[:end_date] ? Date.parse(params[:end_date]) : nil

        credits_service = ::Pearch::CreditsService.new(@account)
        transactions = credits_service.transaction_history(
          limit: limit,
          start_date: start_date,
          end_date: end_date
        )

        render json: {
          account: {
            id: @account.id,
            name: @account.name,
            current_balance: credits_service.current_balance,
            total_consumed: credits_service.total_consumed
          },
          transactions: transactions.as_json(only: [
            :id, :transaction_type, :amount, :balance_before, :balance_after,
            :reason, :reference_id, :reference_type, :metadata, :created_at
          ])
        }, status: :ok
      rescue ArgumentError => e
        render json: { error: "Invalid date format: #{e.message}" }, status: :bad_request
      end

      def list_accounts
        accounts = Account.select(:id, :name, :pearch_credits, :pearch_total_consumed)
                         .order(pearch_credits: :desc)

        render json: {
          accounts: accounts.map { |acc|
            {
              id: acc.id,
              name: acc.name,
              current_balance: acc.pearch_credits,
              total_consumed: acc.pearch_total_consumed
            }
          }
        }, status: :ok
      end

      private

      def set_account
        @account = Account.find_by(id: params[:account_id])

        unless @account
          render json: { error: "Account not found" }, status: :not_found
        end
      end

      def authorize_super_admin
        authorize :search_credit, :add_credits?
      rescue Pundit::NotAuthorizedError
        render json: { error: "Unauthorized. Super admin access required." }, status: :forbidden
      end
    end
  end
end
