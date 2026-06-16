# frozen_string_literal: true

module V1
  module Users
    class LinkedinImportsController < ApplicationController
      before_action :set_job
      before_action :set_selective_process

      def create
        urls = linkedin_import_params[:linkedin_urls]
        return render_simple_error("linkedin_urls is required", status: :bad_request) if urls.blank?

        Candidates::LinkedinBatchImportJob.perform_async(
          @current_user.account_id,
          @job.id,
          @selective_process.id,
          urls,
          @current_user.id
        )

        render_success({
          status: "processing",
          message: "#{urls.size} LinkedIn profiles are being imported in background",
          job_id: @job.id,
          selective_process_id: @selective_process.id,
          total_urls: urls.size
        }, status: :accepted)
      end

      private

      def set_job
        @job = Job.find_by(id: linkedin_import_params[:job_id], is_deleted: false)
        render_not_found("Job") unless @job
      end

      def set_selective_process
        return unless @job

        sp_id = linkedin_import_params[:selective_process_id]
        @selective_process = @job.selective_processes.find_by(id: sp_id)
        render_not_found("SelectiveProcess") unless @selective_process
      end

      def linkedin_import_params
        params.require(:linkedin_import).permit(:job_id, :selective_process_id, linkedin_urls: [])
      end
    end
  end
end
