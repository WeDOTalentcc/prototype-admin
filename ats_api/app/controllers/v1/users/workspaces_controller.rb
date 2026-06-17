# frozen_string_literal: true

module V1
  module Users
    class WorkspacesController < ApplicationController
      include SearchParams

      before_action :authorize_request
      before_action :set_workspace, only: [ :show, :update, :destroy ]

      def index
        parsed_where = parse_json_param(params[:where], {})
        parsed_where[:user_id] = @current_user.id if @current_user
        parsed_where[:is_deleted] = false unless parsed_where.key?(:is_deleted) || parsed_where.key?("is_deleted")
        params[:where] = parsed_where
        perform_search(
          model: Workspace,
          serializer: WorkspaceSerializer
        )
      end

      def show
        render_success(@workspace, serializer: WorkspaceSerializer)
      end

      def create
        @workspace = Workspace.new(workspace_params)
        @workspace.user = @current_user
        @workspace.account = @current_user.account

        if @workspace.save
          return render_success(@workspace, serializer: WorkspaceSerializer, status: :created)
        end
        render_error(@workspace, status: :unprocessable_entity)
      end

      def update
        @workspace.update(workspace_params) ? render_success(@workspace, serializer: WorkspaceSerializer) : render_error(@workspace)
      end

      def destroy
        @workspace.update(is_deleted: true)
        render_success(@workspace, serializer: WorkspaceSerializer)
      end

      private

      def set_workspace
        @workspace = Workspace.find_by(uid: params[:id])
      end

      def workspace_params
        params.require(:workspace).permit(:name)
      end
    end
  end
end
