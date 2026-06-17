# frozen_string_literal: true

module V1
  class NotificationsController < ApplicationController
    include RenderDefault

    before_action :authorize_request
    before_action :set_target_user
    before_action :set_notification, only: %i[show read dismiss]

    def index
      scope = @target_user.agent_notifications.recent_first
      scope = scope.by_category(params[:category]) if params[:category].present?
      scope = scope.by_type(params[:notification_type]) if params[:notification_type].present?
      scope = scope.unread if ActiveModel::Type::Boolean.new.cast(params[:unread_only])
      scope = scope.since(Time.zone.parse(params[:since])) if params[:since].present?

      total = scope.count
      limit = (params[:limit] || params[:per_page] || 20).to_i.clamp(1, 100)
      page  = (params[:page] || 1).to_i
      records = scope.offset((page - 1) * limit).limit(limit)

      payload = NotificationSerializer.new(records).serializable_hash
      notifications = payload[:data].map { |d| d[:attributes].merge(id: d[:id]) }

      render json: {
        success: true,
        data: {
          notifications: notifications,
          total: total,
          page: page,
          limit: limit,
          unread_count: @target_user.agent_notifications.unread.count
        }
      }, status: :ok
    end

    def show
      render_success(@notification, serializer: NotificationSerializer)
    end

    def read
      @notification.mark_as_read!
      render json: { success: true, data: NotificationSerializer.new(@notification).serializable_hash }, status: :ok
    end

    def dismiss
      @notification.destroy
      render json: { success: true }, status: :ok
    end

    def read_all
      @target_user.agent_notifications.unread.update_all(read_at: Time.current, status: "read")
      render json: { success: true }, status: :ok
    end

    def unread_count
      count = Rails.cache.fetch("notifications:unread:#{@target_user.id}", expires_in: 10.seconds) do
        @target_user.agent_notifications.unread.count
      end
      render json: { success: true, unread_count: count, data: { unread_count: count } }, status: :ok
    end

    private

    def set_target_user
      @target_user = if service_token? && params[:user_id].present?
                       resolve_user_param(params[:user_id])
                     else
                       @current_user
                     end

      render_unauthorized("Usuário não resolvido") unless @target_user
    end

    def resolve_user_param(value)
      return User.find_by(id: value) if value.to_s.match?(/\A\d+\z/)

      User.find_by(email: value)
    end

    def set_notification
      @notification = @target_user.agent_notifications.find_by(id: params[:id])
      render_not_found("Notification") unless @notification
    end

    def service_token?
      @jwt_payload&.dig(:role).to_s == "service"
    end
  end
end
