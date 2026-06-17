# frozen_string_literal: true

module V1
  module Users
    class DepartmentsController < ApplicationController
      before_action :authorize_request
      before_action :require_manager!, only: %i[create update destroy]
      before_action :set_department, only: %i[show update destroy]

      def index
        perform_search(
          model: Department,
          serializer: DepartmentSerializer
        )
      end

      def show
        render_success(@department, serializer: DepartmentSerializer)
      end

      def create
        @department = Department.new(department_params.merge(account_id: @current_user.account_id))

        if @department.save
          return render_success(@department, serializer: DepartmentSerializer, status: :created)
        end
        render_error(@department, status: :unprocessable_entity)
      end

      def update
        @department.update(department_params) ? render_success(@department, serializer: DepartmentSerializer) : render_error(@department)
      end

      def destroy
        @department.destroy
        render_no_content
      end

      private

      def set_department
        @department = Department.find_by(id: params[:id])
        render_not_found("Department") unless @department
      end

      def department_params
        params.require(:department).permit(
          :company_id, :name, :code, :parent_id, :description, :manager_name,
          :manager_email, :manager_id, :headcount_current, :headcount_target,
          :budget, :cost_center, :is_active
        )
      end
    end
  end
end
