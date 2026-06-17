# frozen_string_literal: true

module V1
  module Users
    module Admin
      class AccountsController < ApplicationController
        include ResourceLoader

        def index
          authorize Account
          scoped_accounts = policy_scope(Account)
          perform_search(
            model: Account,
            serializer: AccountSerializer
          )
        end

        def show
          render_success(@account, serializer: AccountSerializer)
        end

        def create
          authorize Account
          @account = Account.new(account_params)
          @account.uid = SecureRandom.uuid if @account.uid.blank?

          if @account.save
            return render_success(@account, serializer: AccountSerializer, status: :created)
          end
          render_error(@account, status: :unprocessable_entity)
        end

        def update
          @account.uid = SecureRandom.uuid if @account.uid.blank?
          if @account.update(account_params)
            return render_success(@account, serializer: AccountSerializer)
          end
          render_error(@account)
        end

        def destroy
          @account.destroy
          render_success(@account, serializer: AccountSerializer)
        end

        private

        def account_params
          params.require(:account).permit(
            :name,
            :signup_email,
            :signup_email_content,
            :domain,
            :ats_provider,
            :workos_enabled,
            :workos_organization_id,
            :workos_connection_id,
            :sso_enforced,
            :jit_provisioning_enabled,
            :pearch_credits,
            :web_saturation_amount,
            :sourcing_saturation_amount,
            :saturation_amount_increase,
            :saturation_release_hours,
            sourcing_config: {},
            auth_config: {},
            allowed_domains: [],
            sso_providers: []
          )
        end

        def load_resource
          @account = Account.find(params[:id])
        end
      end
    end
  end
end
