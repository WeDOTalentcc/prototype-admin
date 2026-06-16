# frozen_string_literal: true

module V1
  module Users
    module Jobs
      class BulkAnalyticsController < ApplicationController
        def create
          job_ids = params[:job_ids]
          where_filters = parse_json_param(params[:where]) || {}
          force = ActiveModel::Type::Boolean.new.cast(params[:force_refresh])
          limit = params[:limit]

          result = ::Jobs::BulkAnalyticsService.new(
            job_ids: job_ids.presence,
            where: where_filters.symbolize_keys,
            force_refresh: force,
            limit: limit
          ).call

          status = result[:success] ? :ok : :unprocessable_entity
          render json: result, status: status
        end

        private

        def parse_json_param(value)
          return value if value.is_a?(Hash)
          return nil if value.blank?

          JSON.parse(value)
        rescue JSON::ParserError
          nil
        end
      end
    end
  end
end
