# frozen_string_literal: true

module V1
  module Users
    class NotificationsController < ApplicationController
      before_action :set_notification, only: %i[show read]

      def index
        scope = @current_user.agent_notifications.recent_first
        scope = scope.by_type(params[:notification_type]) if params[:notification_type].present?
        scope = scope.by_status(params[:status]) if params[:status].present?
        scope = scope.since(Time.zone.parse(params[:since])) if params[:since].present?

        page = (params[:page] || 1).to_i
        per_page = [ (params[:per_page] || 20).to_i, 30 ].min
        total = scope.count

        records = scope.offset((page - 1) * per_page).limit(per_page)

        render json: AgentNotificationSerializer.new(
          records,
          meta: {
            total: total,
            page: page,
            per_page: per_page,
            unread_count: @current_user.agent_notifications.unread.count
          }
        ).serializable_hash, status: :ok
      end

      def show
        render_success(@notification, serializer: AgentNotificationSerializer)
      end

      def read
        @notification.mark_as_read!
        render_success(@notification, serializer: AgentNotificationSerializer)
      end

      def mark_all_read
        @current_user.agent_notifications.unread.update_all(read_at: Time.current, status: "read")
        render json: { success: true }, status: :ok
      end

      def unread_count
        count = @current_user.agent_notifications.unread.count
        render json: { unread_count: count }, status: :ok
      end

      def send_push
        return render_forbidden("Service token required") unless service_token?

        user = User.find_by(id: params[:user_id], account_id: Current.account.id)
        return render_not_found("User") unless user

        reference = resolve_reference

        result = Notifications::SendPushService.new(
          user: user,
          notification_type: params[:notification_type],
          content: params[:content],
          channel: params[:channel] || "web",
          reference: reference,
          alert_key: params[:alert_key],
          metadata: params[:metadata]&.to_unsafe_h || {}
        ).call

        if result[:success]
          render json: result, status: :created
        else
          render json: result, status: :unprocessable_entity
        end
      end

      private

      def set_notification
        @notification = @current_user.agent_notifications.find_by(id: params[:id])
        render_not_found("Notification") unless @notification
      end

      def service_token?
        @jwt_payload&.dig(:role).to_s == "service"
      end

      def resolve_reference
        return unless params[:reference_type].present? && params[:reference_id].present?

        params[:reference_type].constantize.find_by(id: params[:reference_id])
      rescue NameError
        nil
      end
    end
  end
end
