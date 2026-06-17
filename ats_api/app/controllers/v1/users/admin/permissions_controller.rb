# frozen_string_literal: true

module V1
  module Users
    module Admin
      class PermissionsController < ApplicationController
        skip_before_action :load_resource
        skip_before_action :authorize_resource!
        skip_before_action :authorize_resource_class!

        def index
          authorize Permission
          policy_scope(Permission)

          perform_search(
            model: Permission,
            serializer: PermissionSerializer
          )
        end

        def show
          @permission = Permission.find_by(id: params[:id])
          render_not_found("Permission") unless @permission
          authorize @permission
          render_success(@permission, serializer: PermissionSerializer)
        end
      end
    end
  end
end
