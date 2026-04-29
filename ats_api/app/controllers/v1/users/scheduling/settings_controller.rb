# frozen_string_literal: true

module V1
  module Users
    module Scheduling
      class SettingsController < ApplicationController
        before_action :set_settings, only: %i[show update]

        def show
          render_success(@settings)
        end

        def update
          return render_simple_error("Invalid parameters", status: :unprocessable_entity) unless @settings.update(settings_params)

          render_success(@settings)
        end

        private

        def set_settings
          @settings = SchedulingSetting.find_or_create_by(user: @current_user) do |s|
            s.account = @current_user.account
          end
        end

        def settings_params
          params.permit(
            :timezone,
            :work_hours_start,
            :work_hours_end,
            :default_duration_minutes,
            :buffer_minutes,
            :lookahead_days
          )
        end
      end
    end
  end
end
