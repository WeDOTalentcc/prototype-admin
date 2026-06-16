# frozen_string_literal: true

module V1
  module Users
    class ClientAccountsController < ApplicationController
      before_action :authorize_request
      before_action :require_admin!
      before_action :set_client_account, only: %i[show update destroy]

      def index
        perform_search(
          model: ClientAccount,
          serializer: ClientAccountSerializer
        )
      end

      def show
        render_success(@client_account, serializer: ClientAccountSerializer)
      end

      def create
        @client_account = ClientAccount.new(client_account_params.merge(account_id: @current_user.account_id))

        if @client_account.save
          return render_success(@client_account, serializer: ClientAccountSerializer, status: :created)
        end
        render_error(@client_account, status: :unprocessable_entity)
      end

      def update
        @client_account.update(client_account_params) ? render_success(@client_account, serializer: ClientAccountSerializer) : render_error(@client_account)
      end

      def destroy
        @client_account.destroy
        render_no_content
      end

      private

      def set_client_account
        @client_account = ClientAccount.find_by(id: params[:id])
        render_not_found("ClientAccount") unless @client_account
      end

      def client_account_params
        params.require(:client_account).permit(
          :name, :cnpj, :trade_name, :industry, :sector, :size, :employee_count,
          :website, :phone, :email, :address_street, :address_number, :address_complement,
          :address_district, :address_city, :address_state, :address_zip, :address_country,
          :plan_id, :status, :user_limit, :job_limit, :ai_credits_monthly, :features_enabled
        )
      end
    end
  end
end
