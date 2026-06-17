# frozen_string_literal: true

module V1
  module Users
    class ApplyStatusesController < ApplicationController
      include ResourceLoader

      def index
        params[:where] ||= {}
        params[:where][:is_deleted] = false unless params[:where].key?(:is_deleted)
        perform_search(
          model: ApplyStatus,
          serializer: ApplyStatusSerializer,
        )
      end

      def show
        render_success(@apply_status, serializer: ApplyStatusSerializer)
      end

      def create
        @apply_status = ApplyStatus.new(apply_status_params)

        if @apply_status.save
          return render_success(@apply_status, serializer: ApplyStatusSerializer, status: :created)
        end
        render_error(@apply_status, status: :unprocessable_entity)
      end

      def update
        @apply_status.update(apply_status_params) ? render_success(@apply_status, serializer: ApplyStatusSerializer) : render_error(@apply_status)
      end

      def destroy
        @apply_status.update(is_deleted: true)
        render_success(@apply_status, serializer: ApplyStatusSerializer)
      end

      private

      def apply_status_params
        params.require(:apply_status).permit(
          :apply_id, :selective_process_id, :is_deleted, :account_id, :user_id, :status_name
        )
      end
    end
  end
end
