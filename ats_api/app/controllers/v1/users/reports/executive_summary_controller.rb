# frozen_string_literal: true

module V1
  module Users
    module Reports
      class ExecutiveSummaryController < ApplicationController
        def create
          result = ::Reports::ExecutiveSummaryService.new(
            user: @current_user,
            period: params[:period],
            compare_previous: ActiveModel::Type::Boolean.new.cast(params[:compare_previous])
          ).call

          status = result[:success] ? :ok : :unprocessable_entity
          render json: result, status: status
        end
      end
    end
  end
end
