module V1
  module Setups
    module WorkflowTemplates
      class SelectiveProcessesController < ApplicationController
        before_action :set_main_workflow_template
        before_action :set_selective_process, only: [ :show, :update, :destroy ]

        def index
          @selective_processes = @workflow_template.selective_processes.order(:position)
          render_success(@selective_processes, serializer: SelectiveProcessSerializer)
        end

        def show
          render_success(@selective_process, serializer: SelectiveProcessSerializer)
        end

        def create
          @selective_process = @workflow_template.selective_processes.new(selective_process_params)
          @selective_process.account = @account

          if @selective_process.save
            return render_success(@selective_process, serializer: SelectiveProcessSerializer, status: :created)
          end

          render_error(@selective_process, status: :unprocessable_entity)
        end

        def update
          if @selective_process.update(selective_process_params)
            return render_success(@selective_process, serializer: SelectiveProcessSerializer)
          end
          render_error(@selective_process)
        end

        def destroy
          @selective_process.destroy
          render_no_content
        end

        private

        def set_main_workflow_template
          @workflow_template = WorkflowTemplate.find_by(account_id: @account.id, is_main: true)
          render_not_found("Workflow Template Principal") unless @workflow_template
        end

        def set_selective_process
          @selective_process = @workflow_template.selective_processes.find_by(id: params[:id])
          render_not_found("Etapa do Processo") unless @selective_process
        end

        def selective_process_params
          params.require(:selective_process).permit(:name, :position, :status, :account_id)
        end
      end
    end
  end
end
