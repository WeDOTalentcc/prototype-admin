# frozen_string_literal: true

module V1
  module Users
    class SourcingsBulkStatsController < ApplicationController
      def create
        sourcing_ids = params[:sourcing_ids] || []

        result = ::Sourcings::BulkStatsService.new(sourcing_ids: sourcing_ids).call

        if result[:success]
          render json: result, status: :ok
        else
          render json: result, status: :unprocessable_entity
        end
      end
    end
  end
end
