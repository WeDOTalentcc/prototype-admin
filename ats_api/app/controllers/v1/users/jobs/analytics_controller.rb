# frozen_string_literal: true

module V1
  module Users
    module Jobs
      class AnalyticsController < ApplicationController
        before_action :set_job

        def show
          force = ActiveModel::Type::Boolean.new.cast(params[:force_refresh])
          data = fetch_analytics(force)

          render json: { success: true, data: data }, status: :ok
        end

        private

        def set_job
          @job = Job.find_by(id: params[:id])
          return render_not_found("Job") unless @job
          render_simple_error("Not authorized", status: :forbidden) unless authorized?
        end

        def authorized?
          @job.account_id == @current_user.account_id
        end

        def fetch_analytics(force_refresh)
          ::Jobs::AnalyticsService.new(job: @job, force_refresh: force_refresh).call
        end
      end
    end
  end
end
