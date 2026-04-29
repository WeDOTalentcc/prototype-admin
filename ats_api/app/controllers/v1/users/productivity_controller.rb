# frozen_string_literal: true

module V1
  module Users
    class ProductivityController < ApplicationController
      def show
        start_date = params[:start_date]&.to_date || 30.days.ago.to_date
        end_date = params[:end_date]&.to_date || Date.current

        cache_key = "productivity:#{@current_user.id}:#{start_date}:#{end_date}"
        data = Rails.cache.fetch(cache_key, expires_in: 10.minutes) do
          Productivity::ShowService.new(
            user: @current_user,
            start_date: start_date,
            end_date: end_date
          ).call
        end

        render json: data, status: :ok
      end
    end
  end
end
