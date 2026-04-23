# frozen_string_literal: true

module V1
  module Users
    module Jobs
      class PipelineHealthController < ApplicationController
        def index
          job_ids = params[:job_ids]&.split(",")&.map(&:to_i)
          include_inactive = ActiveModel::Type::Boolean.new.cast(params[:include_inactive])
          aging_threshold_days = params[:aging_threshold_days]
          limit = params[:limit]

          result = ::Jobs::PipelineHealthService.new(
            job_ids: job_ids,
            include_inactive: include_inactive,
            aging_threshold_days: aging_threshold_days,
            limit: limit
          ).call

          status = result[:success] ? :ok : :unprocessable_entity
          render json: result, status: status
        end
      end
    end
  end
end
