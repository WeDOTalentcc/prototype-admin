# frozen_string_literal: true

module V1
  module Users
    module Evaluations
      class ResponseRatesController < ApplicationController
        def index
          result = ::Evaluations::ResponseRatesService.new(
            evaluation_ids: parse_ids(params[:evaluation_ids]),
            job_ids: parse_ids(params[:job_ids]),
            min_rate: params[:min_rate],
            max_rate: params[:max_rate],
            include_pending: ActiveModel::Type::Boolean.new.cast(params[:include_pending])
          ).call

          status = result[:success] ? :ok : :unprocessable_entity
          render json: result, status: status
        end

        private

        def parse_ids(raw)
          return nil if raw.blank?

          raw.split(",").map(&:to_i)
        end
      end
    end
  end
end
