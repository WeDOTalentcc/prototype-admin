# frozen_string_literal: true

module V1
  module Users
    class SelectiveProcessesController < ApplicationController
      include ResourceLoader
      before_action :authorize_request

      def index
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
        @selective_process.update(selective_process_params) ? render_success(@selective_process, serializer: SelectiveProcessSerializer) : render_error(@selective_process)
      end

      def destroy
        @selective_process.destroy
        render_no_content
      end

      private

      def selective_process_params
        params.require(:selective_process).permit(:name, :position, :status, :job_id, :uid, :account_id, sub_status: [])
      end
    end
  end
end
