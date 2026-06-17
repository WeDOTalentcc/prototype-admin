# frozen_string_literal: true

module V1
  module Users
    class ActivityLogsController < ApplicationController
      before_action :set_activity_log, only: %i[show update destroy rollback]
      before_action :ensure_owner, only: %i[update destroy rollback]

      def index
        perform_search(
          model: ActivityLog,
          serializer: ActivityLogSerializer
        )
      end

      def show
        render_success(@activity_log, serializer: ActivityLogSerializer)
      end

      def create
        @activity_log = ActivityLog.new(activity_log_params)
        @activity_log.user = @current_user
        @activity_log.account = @current_user&.account
        @activity_log.ip_address = Current.ip

        if @activity_log.save
          return render_success(@activity_log, serializer: ActivityLogSerializer, status: :created)
        end
        render_error(@activity_log, status: :unprocessable_entity)
      end

      def update
        @activity_log.update(activity_log_params) ? render_success(@activity_log, serializer: ActivityLogSerializer) : render_error(@activity_log)
      end

      def destroy
        @activity_log.destroy
        render_success(@activity_log, serializer: ActivityLogSerializer)
      end

      def rollback
        begin
          @activity_log.rollback!(current_user: @current_user)
          render_success(@activity_log, serializer: ActivityLogSerializer)
        rescue => e
          render_simple_error(e.message, status: :unprocessable_entity)
        end
      end

      private

      def set_activity_log
        @activity_log = ActivityLog.find_by(id: params[:id])
        render_not_found("ActivityLog") unless @activity_log
      end

      def ensure_owner
        return if @activity_log.user_id == @current_user.id
        render_simple_error("Não autorizado a realizar esta ação neste activity log", status: :forbidden)
      end

      def activity_log_params
        params.require(:activity_log).permit(
          :action, :reference_type, :reference_id, changeset: {}
        )
      end
    end
  end
end
