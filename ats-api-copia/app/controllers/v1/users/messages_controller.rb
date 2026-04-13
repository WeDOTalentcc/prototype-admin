# frozen_string_literal: true

module V1
  module Users
    class MessagesController < ApplicationController
      before_action :authorize_request
      before_action :set_message, only: %i[show update destroy]
      before_action :ensure_owner, only: %i[update destroy]

      def index
        @messages = Message.search_default(
          params[:term] || search_params,
          global_search_params,
          params[:page],
          params[:term] ? false : true,
          @current_user.id
        )

        render json: {
          messages: @messages[:records],
          total_messages: @messages[:total_count],
          total: @messages[:total_count],
          aggregators: @messages[:aggs]
        }, status: :ok
      end

      def show
        render json: @message, status: :ok
      end

      def create
        @message = Message.create(set_message_params)
        @message.account_id = @current_user.account_id
        if @message.save
          MessageJob.perform_later(@message, @current_user)
          render json: @message, status: :created
        else
          render json: { errors: @message.errors.full_messages }, status: :unprocessable_entity
        end
      end

      def update
        if @message.update(set_message_params)
          render json: @message, status: :ok
        else
          render json: { errors: @message.errors.full_messages }, status: :unprocessable_entity
        end
      end

      def destroy
        @message.destroy
        head :no_content
      end

      private

      def set_message
        @message = Message.find_by(id: params[:id])
        render json: { error: 'Message not found' }, status: :not_found unless @message
      end

      def ensure_owner
        unless @message.reference_id == @current_user.id && @message.reference_type == 'User'
          render json: { error: 'Not authorized' }, status: :forbidden
        end
      end

      def set_message_params
        current_message_params = message_params
        current_message_params[:reference_type] = 'User'
        current_message_params[:reference_id] = @current_user.id
        current_message_params
      end

      def message_params
        params.require(:message).permit(:content, :type, :is_deleted, :status, :parent_message_id, :reference_type, :reference_id, :entity)
      end
    end
  end
end
