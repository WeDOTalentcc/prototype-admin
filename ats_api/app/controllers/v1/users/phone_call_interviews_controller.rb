# frozen_string_literal: true

module V1
  module Users
    class PhoneCallInterviewsController < ApplicationController
      def create
        result = PhoneCallInterviews::CreateService.new(
          user: @current_user,
          params: phone_call_params
        ).call

        if result.success?
          render_success(result.data, serializer: EvaluationCandidateSerializer, status: :created)
        else
          render json: { errors: result.errors }, status: :unprocessable_entity
        end
      end

      private

      def phone_call_params
        params.permit(
          :evaluation_id, :candidate_id, :job_id, :apply_id,
          :custom_invite_message, :date_expiration, :duration_minutes,
          channels: [],
          slots: [ :start_time, :end_time ]
        )
      end
    end
  end
end
