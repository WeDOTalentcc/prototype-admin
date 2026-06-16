# frozen_string_literal: true

module V1
  module Users
    class NotificationsController < ApplicationController
      before_action :authorize_request
      before_action :set_notification, only: %i[show update destroy]

      def index
        perform_search(
          model: Notification,
          serializer: NotificationSerializer
        )
      end

      def show
        render_success(@notification, serializer: NotificationSerializer)
      end

      def create
        @notification = Notification.new(notification_params.merge(account_id: @current_user.account_id))

        if @notification.save
          return render_success(@notification, serializer: NotificationSerializer, status: :created)
        end
        render_error(@notification, status: :unprocessable_entity)
      end

      def update
        @notification.update(notification_params) ? render_success(@notification, serializer: NotificationSerializer) : render_error(@notification)
      end

      def destroy
        @notification.destroy
        render_no_content
      end

      private

      def set_notification
        @notification = Notification.find_by(id: params[:id])
        render_not_found("Notification") unless @notification
      end

      def notification_params
        params.require(:notification).permit(
          :user_id, :company_id, :notification_type, :title, :message,
          :status, :priority, :action_url, :read_at, :dismissed_at,
          metadata: {}
        )
      end
    end
  end
end
