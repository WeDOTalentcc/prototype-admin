
module V1
  module Setups
    class SetupsController < ApplicationController
      before_action :find_account_by_valid_token

      def find_account_by_valid_token
        @account = Account.find_by(setup_token: params[:setup_token])

        if @account.nil?
          return render_not_found("Convite de configuração inválido ou já utilizado.")
        end

        if @account.setup_token_expires_at < Time.current
          render_error(@account, status: :gone)
        end
      end

      def show
        @user = User.find_by(account_id: @account.id)
        if @user.nil?
          render_success({ message: "Valid Setup" }, status: :ok)
        else
          render_success(@user, serializer: UserSerializer, status: :ok)
        end
      end

      def create_user
        result = nil

        @account.with_lock do
          if User.exists?(account_id: @account.id)
            result = :conflict
            next
          end

          @user = User.new(user_params)
          @user.account = @account

          if @user.save
            @account.update_columns(setup_token_expires_at: Time.current)
            result = :created
          else
            result = :invalid
          end
        end

        case result
        when :conflict
          render json: { error: "Convite de configuração já utilizado." }, status: :conflict
        when :created
          token = JsonWebToken.encode(user_id: @user.id)
          render json: {
            data: UserSerializer.new(@user).serializable_hash[:data],
            token: token
          }, status: :created
        when :invalid
          render_error(@user, status: :unprocessable_entity)
        end
      end

      def complete
        @account.update(setup_token_expires_at: Time.now)
        render_success(@account, serializer: AccountSerializer, status: :ok)
      end

      private

      def user_params
        params.require(:user).permit(
          :email, :password, :name
        )
      end
    end
  end
end
