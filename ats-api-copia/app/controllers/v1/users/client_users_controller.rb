# frozen_string_literal: true

module V1
  module Users
    class ClientUsersController < ApplicationController
      before_action :authorize_request
      before_action :require_admin!, only: %i[create destroy]
      before_action :require_manager!, only: %i[update]
      before_action :set_client_user, only: %i[show update destroy]

      def index
        perform_search(
          model: ClientUser,
          serializer: ClientUserSerializer
        )
      end

      def show
        render_success(@client_user, serializer: ClientUserSerializer)
      end

      def create
        @client_user = ClientUser.new(client_user_params.merge(account_id: @current_user.account_id))

        if @client_user.save
          return render_success(@client_user, serializer: ClientUserSerializer, status: :created)
        end
        render_error(@client_user, status: :unprocessable_entity)
      end

      def update
        @client_user.update(client_user_params) ? render_success(@client_user, serializer: ClientUserSerializer) : render_error(@client_user)
      end

      def destroy
        @client_user.destroy
        render_no_content
      end

      private

      def set_client_user
        @client_user = ClientUser.find_by(id: params[:id])
        render_not_found("ClientUser") unless @client_user
      end

      def client_user_params
        params.require(:client_user).permit(
          :company_id, :email, :name, :role, :permissions, :status, :avatar_url
        )
      end
    end
  end
end
