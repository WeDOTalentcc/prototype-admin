module V1
  module Setups
    class ApplicationController < ActionController::API
      include RenderDefault
      before_action :find_account_by_valid_token

      def find_account_by_valid_token
        @account = Account.find_by(setup_token: params[:setup_token])
        Apartment::Tenant.switch!(@account.tenant)
        @business = Business.find_by(account_id: @account.id) if @account
        if @account.nil?
          return render_not_found("Convite de configuração inválido ou já utilizado.")
        end

        if @account.setup_token_expires_at < Time.current
          render json: { error: "Este convite de configuração expirou." }, status: :gone
        end
      end
    end
  end
end
