# frozen_string_literal: true

module V1
  module Users
    class EvaluationsBulkStatsController < ApplicationController
      def index
        evaluation_ids = params[:evaluation_ids]&.split(",")&.map(&:to_i)
        min_response_rate = params[:min_response_rate]&.to_f

        result = ::Evaluations::BulkDashboardStatsService.new(
          evaluation_ids: evaluation_ids,
          min_response_rate: min_response_rate
        ).call

        if result[:success]
          render json: result, status: :ok
        else
          render json: result, status: :unprocessable_entity
        end
      end
    end
  end
end
