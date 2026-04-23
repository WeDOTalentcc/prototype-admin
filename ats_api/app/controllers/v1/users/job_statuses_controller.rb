# frozen_string_literal: true

module V1
  module Users
    class JobStatusesController < ApplicationController
      include ResourceLoader
      include AuthorizableResource

      def index
        authorize JobStatus
        perform_search(
          model: JobStatus,
          serializer: JobStatusSerializer
        )
      end

      def show
        render_success(@job_status, serializer: JobStatusSerializer)
      end

      def create
        @job_status = JobStatus.new(job_status_params)
        @job_status.save ? render_success(@job_status, serializer: JobStatusSerializer, status: :created) : render_error(@job_status)
      end

      def update
        @job_status.update(job_status_params) ? render_success(@job_status, serializer: JobStatusSerializer) : render_error(@job_status)
      end

      def destroy
        @job_status.destroy
        render_success(@job_status, serializer: JobStatusSerializer)
      end

      private

      def job_status_params
        params.require(:job_status).permit(:name, :color)
      end
    end
  end
end
