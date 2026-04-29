module V1
  module Setups
    class AccountsController < ApplicationController
      def show
        render_success(@account, serializer: AccountSerializer)
      end

      def update
        if @account.update(account_params)
          return render_success(@account, serializer: AccountSerializer)
        end
        render_error(@account, status: :unprocessable_entity)
      end

      def account_params
        params.require(:account).permit(
          :name,
        )
      end
    end
  end
end
