# frozen_string_literal: true

module V1
  module Users
    class UsersController < ApplicationController
      before_action :authorize_request
      before_action :require_admin!, only: %i[create destroy]
      before_action :require_manager!, only: %i[update]
      before_action :set_user, only: %i[show update destroy]

      def index
        perform_search(
          model: User,
          serializer: UserSerializer
        )
      end

      def show
        render json: @user, status: :ok
      end

      def create
        @user = User.create(user_params)
        @user.account_id = @current_user.account_id
        if @user.save
          render json: @user, status: :created
        else
          render json: { errors: @user.errors.full_messages }, status: :unprocessable_entity
        end
      end

      def update
        if @user.update(user_params)
          render json: @user, status: :ok
        else
          render json: { errors: @user.errors.full_messages }, status: :unprocessable_entity
        end
      end

      def destroy
        @user.destroy
        head :no_content
      end

      private

      def set_user
        @user = User.find_by(id: params[:id])
        render json: { error: 'User not found!' }, status: :not_found unless @user
      end

      def user_params
        params.require(:user).permit(:email, :password)
      end
    end
  end
end
