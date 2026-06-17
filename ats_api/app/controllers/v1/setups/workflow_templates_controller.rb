module V1
  module Setups
    class WorkflowTemplatesController < ApplicationController
      before_action :set_main_workflow_template

      def show
        render_success(@workflow_template, serializer: WorkflowTemplateSerializer)
      end

      def update
        if @workflow_template.update(workflow_template_params)
          return render_success(@workflow_template, serializer: WorkflowTemplateSerializer)
        end
        render_error(@workflow_template)
      end

      private

      def set_main_workflow_template
        @workflow_template = WorkflowTemplate.find_by(account_id: @account.id, is_main: true)
        render_not_found("Workflow Template Principal") unless @workflow_template
      end

      def workflow_template_params
        params.require(:workflow_template).permit(:name)
      end
    end
  end
end
