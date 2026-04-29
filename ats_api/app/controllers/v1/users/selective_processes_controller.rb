# frozen_string_literal: true

module V1
  module Users
    class SelectiveProcessesController < ApplicationController
      include ResourceLoader
      before_action :authorize_request

      def index
        params[:where] = parse_json_param(params[:where])
        params[:where] ||= {}
        params[:where][:job_id] = params[:where][:job_id] == "null" ? nil : params[:where][:job_id]
        perform_search(
          model: SelectiveProcess,
          serializer: SelectiveProcessSerializer
        )
      end

      def show
        render_success(@selective_process, serializer: SelectiveProcessSerializer)
      end

      def create
        @selective_process = SelectiveProcess.new(selective_process_params)

        if @selective_process.save
          return render_success(@selective_process, serializer: SelectiveProcessSerializer, status: :created)
        end
        render_error(@selective_process, status: :unprocessable_entity)
      end

      def update
        result = @selective_process.update(selective_process_params)
        @selective_process.reload
        result ? render_success(@selective_process, serializer: SelectiveProcessSerializer) : render_error(@selective_process)
      end

      def order_position
        params[:selective_processes].each_with_index do |selective_process, index|
          process = SelectiveProcess.find(selective_process[:id])
          process.update(position: selective_process[:position])
        end
      end

      def destroy
        @selective_process.update(is_deleted: true)
        render_success(@selective_process, serializer: SelectiveProcessSerializer, status: :ok)
      end

      private

      def selective_process_params
        params.require(:selective_process).permit(
                                                  :name, :position, :user_id, :status, :job_id, :uid, :account_id, :duration,
                                                  :workflow_template_id, :position_x, :position_y, :external_id, :color, :is_deleted,
                                                  :approved_process_id, :rejected_process_id, sub_status: [], childrens: []
                                                 )
      end
    end
  end
end
