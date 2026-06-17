module V1
  module Users
    class DepartmentRelationshipsController < ApplicationController
      before_action :set_department_relationship, only: %i[show update destroy]

      def index
        enforce_limit!
        params[:where] ||= {}
        params[:where][:account_id] = @current_user.account_id
        params[:where][:is_deleted] = false unless params[:where].key?(:is_deleted)

        perform_search(
          model: DepartmentRelationship,
          serializer: DepartmentRelationshipSerializer,
          include_aggregators: true
        )
      end

      def show
        render_success(@department_relationship, serializer: DepartmentRelationshipSerializer)
      end

      def create
        @department_relationship = DepartmentRelationship.new(department_relationship_params)
        @department_relationship.account_id = @current_user.account_id
        set_user_from_reference

        if @department_relationship.save
          update_department_manager if @department_relationship.role == "manager"
          render_success(@department_relationship, serializer: DepartmentRelationshipSerializer, status: :created)
          return
        end

        render_error(@department_relationship)
      end

      def update
        @department_relationship.assign_attributes(department_relationship_params)
        set_user_from_reference

        if @department_relationship.save
          update_department_manager if @department_relationship.role == "manager"
          render_success(@department_relationship, serializer: DepartmentRelationshipSerializer)
        else
          render_error(@department_relationship)
        end
      end

      def destroy
        @department_relationship.update(is_deleted: true)
        clear_department_manager if @department_relationship.role == "manager"
        render_success(@department_relationship, serializer: DepartmentRelationshipSerializer)
      end

      private

      def department_relationship_params
        params.require(:department_relationship).permit(
          :department_id, :user_id, :reference_type, :reference_id,
          :role, :title, :is_primary
        )
      end

      def set_department_relationship
        @department_relationship = DepartmentRelationship.where(account_id: @current_user.account_id).find(params[:id])
      rescue ActiveRecord::RecordNotFound
        render_not_found("Vínculo de departamento")
      end

      def set_user_from_reference
        return unless @department_relationship.reference_type == "User" && @department_relationship.user_id.nil?

        @department_relationship.user_id = @department_relationship.reference_id
      end

      def update_department_manager
        return unless @department_relationship.is_primary

        department = @department_relationship.department
        return unless department

        department.update(manager_id: @department_relationship.user_id)
      end

      def clear_department_manager
        department = @department_relationship.department
        return unless department
        return unless department.manager_id == @department_relationship.user_id

        new_manager = department.department_relationships.managers.where(is_primary: true).where.not(id: @department_relationship.id).first
        department.update(manager_id: new_manager&.user_id)
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
