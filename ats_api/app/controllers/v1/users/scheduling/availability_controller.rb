# frozen_string_literal: true

module V1
  module Users
    module Scheduling
      class AvailabilityController < ApplicationController
        include MicrosoftLinked

        def index
          service = ::Scheduling::AvailabilityService.new(user: @current_user)

          if params[:start_date].present? && params[:end_date].present?
            result = service.available_slots_for_range(
              start_date: params[:start_date],
              end_date: params[:end_date],
              duration_minutes: params[:duration_minutes]&.to_i
            )
          elsif params[:date].present?
            result = service.available_slots(
              date: params[:date],
              duration_minutes: params[:duration_minutes]&.to_i
            )
          else
            return render_simple_error("date or start_date/end_date required", status: :bad_request)
          end

          render json: result, status: :ok
        end
      end
    end
  end
end
