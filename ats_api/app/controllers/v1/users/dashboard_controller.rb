# frozen_string_literal: true

module V1
  module Users
    class DashboardController < ApplicationController
      def briefing
        since = params[:since].present? ? Time.zone.parse(params[:since]) : 24.hours.ago
        timezone = params[:timezone] || "America/Sao_Paulo"

        cache_key = "dashboard_briefing:#{@current_user.id}:#{since.to_i / 300}"
        data = Rails.cache.fetch(cache_key, expires_in: 5.minutes) do
          Dashboard::BriefingService.new(
            user: @current_user,
            since: since,
            timezone: timezone
          ).call
        end

        render json: data, status: :ok
      end
    end
  end
end
