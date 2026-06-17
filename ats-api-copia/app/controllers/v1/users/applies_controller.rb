# frozen_string_literal: true

module V1
  module Users
    class AppliesController < ApplicationController
      include ResourceLoader

      def index
        perform_search(
          model: Apply,
          serializer: ApplySerializer,
          search_with_pin: { where: { is_deleted: false } },
        )
      end

      def show
        render_success(@apply, serializer: ApplySerializer)
      end

      def create
        @apply = Apply.new(apply_params)

        if @apply.save
          return render_success(@apply, serializer: ApplySerializer, status: :created)
        end
        render_error(@apply, status: :unprocessable_entity)
      end

      def update
        @apply.update(apply_params) ? render_success(@apply, serializer: ApplySerializer) : render_error(@apply)
      end

      def destroy
        @apply.update(is_deleted: true)
        render_no_content
      end

      private

      def apply_params
        params.require(:apply).permit(
          :candidate_id, :job_id, :selective_process_id, :is_deleted, :account_id
        )
      end
    end
  end
end
