# frozen_string_literal: true

module V1
  module Users
    class NotificationPreferencesController < ApplicationController
      before_action :set_preference

      def show
        render_success(@preference, serializer: NotificationPreferenceSerializer)
      end

      def update
        if @preference.update(preference_params)
          render_success(@preference, serializer: NotificationPreferenceSerializer)
        else
          render_error(@preference)
        end
      end

      private

      def set_preference
        @preference = NotificationPreference.find_or_create_by(user: @current_user)
      end

      def preference_params
        params.permit(
          :briefing_enabled, :briefing_time, :briefing_channel,
          :alert_aging_enabled, :alert_deadline_enabled, :alert_no_show_enabled,
          :alert_evaluation_enabled, :alert_strong_fit_enabled, :alert_stale_job_enabled,
          :aging_threshold_days, :timezone,
          alert_channels: []
        )
      end
    end
  end
end
