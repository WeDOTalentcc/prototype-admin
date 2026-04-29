module V1
  module Users
    module SourcedProfiles
      class AnalysisController < ApplicationController
        before_action :set_sourced_profile

        def create
          analysis = SourcedProfileAnalysisService.new(
            sourced_profile: @sourced_profile,
            force_refresh: ActiveModel::Type::Boolean.new.cast(params[:refresh]),
            account: @current_user.account
          ).call

          render json: SourcedProfileAnalysisSerializer.new(
            sourced_profile: @sourced_profile,
            analysis: analysis
          ).as_json, status: :ok
        end

        private

        def set_sourced_profile
          @sourced_profile = @current_user.account.sourced_profiles.active.find(params[:id])
        rescue ActiveRecord::RecordNotFound
          render json: { error: "Sourced profile not found" }, status: :not_found
        end
      end
    end
  end
end
