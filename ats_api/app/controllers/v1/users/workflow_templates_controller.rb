module V1
  module Users
    class WorkflowTemplatesController < ApplicationController
      include ResourceLoader

      def index
        params[:where] ||= {}
        params[:where][:is_deleted] = false unless params[:where].key?(:is_deleted)
        perform_search(
          model: WorkflowTemplate,
          serializer: WorkflowTemplateSerializer
        )
      end

      def show
        render_success(@workflow_template, serializer: WorkflowTemplateSerializer)
      end

      def create
        @workflow_template = WorkflowTemplate.new(workflow_template_params)

        if @workflow_template.save
          return render_success(@workflow_template, serializer: WorkflowTemplateSerializer, status: :created)
        end
        render_error(@workflow_template, status: :unprocessable_entity)
      end

      def update
        if @workflow_template.update(workflow_template_params)
          return render_success(@workflow_template, serializer: WorkflowTemplateSerializer)
        end
        render_error(@workflow_template)
      end

      def destroy
        @workflow_template.update(is_deleted: true)
        render_success(@workflow_template, serializer: WorkflowTemplateSerializer)
      end

      private

      def workflow_template_params
        params.require(:workflow_template).permit(
          :name, :user_id, :is_deleted, :account_id
        )
      end
    end
  end
end
