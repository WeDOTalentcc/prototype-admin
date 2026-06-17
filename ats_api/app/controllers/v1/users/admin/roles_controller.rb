# frozen_string_literal: true

module V1
  module Users
    module Admin
      class RolesController < ApplicationController
        def index
          authorize Role
          scoped_roles = policy_scope(Role)

          perform_search(
            model: Role,
            serializer: RoleSerializer
          )
        end

        def show
          render_success(@role, serializer: RoleSerializer)
        end

        def create
          @role = Role.new(role_params)
          @role.save ? render_success(@role, serializer: RoleSerializer, status: :created) : render_error(@role)
        end

        def update
          @role.update(role_params) ? render_success(@role, serializer: RoleSerializer) : render_error(@role)
        end

        def destroy
          @role.destroy
          render_success(@role, serializer: RoleSerializer)
        end

        private

        def role_params
          params.require(:role).permit(:name, :description)
        end
      end
    end
  end
end
