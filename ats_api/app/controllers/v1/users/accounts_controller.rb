# frozen_string_literal: true

module V1
  module Users
    class AccountsController < ApplicationController
      def show
        account = @current_user.account

        render json: AccountSerializer.new(account).serializable_hash[:data][:attributes], status: :ok
      end
    end
  end
end
