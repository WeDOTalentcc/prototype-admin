# frozen_string_literal: true

module V1
  module Users
    class InterviewSessionsController < ApplicationController
      before_action :set_interview_session, only: %i[show]

      def index
        sessions = InterviewSession.where(account_id: @current_user.account_id)
          .includes(:candidate, :job, :evaluation)
          .order(created_at: :desc)

        sessions = sessions.where(job_id: params[:job_id]) if params[:job_id]
        sessions = sessions.where(status: params[:status]) if params[:status]
        sessions = sessions.where(candidate_id: params[:candidate_id]) if params[:candidate_id]

        render_success(sessions, serializer: InterviewSessionSerializer)
      end

      def show
        render_success(@interview_session, serializer: InterviewSessionSerializer)
      end

      def create
        service = InterviewSessions::CreateService.new(
          user: @current_user,
          params: session_params
        )
        result = service.call

        if result.success?
          render_success(result.data, serializer: InterviewSessionSerializer, status: :created)
        else
          render json: { errors: result.errors }, status: :unprocessable_entity
        end
      end

      private

      def set_interview_session
        @interview_session = InterviewSession.find_by!(
          id: params[:id],
          account_id: @current_user.account_id
        )
      rescue ActiveRecord::RecordNotFound
        render_not_found("InterviewSession")
      end

      def session_params
        params.permit(
          :evaluation_id, :candidate_id, :job_id, :apply_id,
          :interview_type, :duration_minutes, :language,
          channels: []
        )
      end
    end
  end
end
