module V1
  module Users
    class PositionAssignmentsController < ApplicationController
      before_action :set_assignment, only: %i[show update destroy]

      def index
        enforce_limit!
        params[:where] ||= {}
        params[:where][:account_id] = @current_user.account_id
        if params[:position_id].present?
          params[:where][:organizational_position_id] = params[:position_id].to_i
        end

        perform_search(
          model: PositionAssignment,
          serializer: PositionAssignmentSerializer,
          include_aggregators: true
        )
      end

      def show
        render_success(@assignment, serializer: PositionAssignmentSerializer)
      end

      def create
        assignment = PositionAssignment.new(assignment_params)
        assignment.account_id = @current_user.account_id

        if assignment.save
          render_success(assignment, serializer: PositionAssignmentSerializer, status: :created)
        else
          render_error(assignment)
        end
      end

      def update
        if @assignment.update(assignment_params)
          render_success(@assignment, serializer: PositionAssignmentSerializer)
        else
          render_error(@assignment)
        end
      end

      def destroy
        @assignment.destroy
        render_no_content
      end

      private

      def assignment_params
        params.require(:position_assignment).permit(
          :user_id,
          :organizational_position_id,
          :start_date,
          :end_date,
          :is_current,
          :employment_type
        )
      end

      def set_assignment
        @assignment = PositionAssignment.where(account_id: @current_user.account_id).find(params[:id])
      rescue ActiveRecord::RecordNotFound
        render_not_found("Atribuição")
      end

      def enforce_limit!(max = 100)
        limit_value = params[:limit].presence || params[:per_page].presence
        limit_value = limit_value.to_i if limit_value
        limit_value = max if limit_value.blank? || limit_value <= 0 || limit_value > max
        params[:limit] = limit_value
      end
    end
  end
end
