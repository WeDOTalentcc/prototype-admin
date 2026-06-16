# frozen_string_literal: true

module V1
  module Users
    class InterviewsController < ApplicationController
      before_action :authorize_request
      before_action :set_interview, only: %i[show update destroy]

      def index
        perform_search(
          model: Interview,
          serializer: InterviewSerializer
        )
      end

      def show
        render_success(@interview, serializer: InterviewSerializer)
      end

      def create
        @interview = Interview.new(interview_params.merge(account_id: @current_user.account_id))

        if @interview.save
          return render_success(@interview, serializer: InterviewSerializer, status: :created)
        end
        render_error(@interview, status: :unprocessable_entity)
      end

      def update
        @interview.update(interview_params) ? render_success(@interview, serializer: InterviewSerializer) : render_error(@interview)
      end

      def destroy
        @interview.destroy
        render_no_content
      end

      private

      def set_interview
        @interview = Interview.find_by(id: params[:id])
        render_not_found("Interview") unless @interview
      end

      def interview_params
        params.require(:interview).permit(
          :company_id, :title, :description, :interview_type, :interview_mode,
          :candidate_id, :candidate_name, :candidate_email,
          :interviewer_name, :interviewer_email, :start_time, :end_time,
          :timezone, :duration_minutes, :location, :meeting_url, :meeting_platform,
          :meeting_id, :graph_event_id, :graph_calendar_id, :graph_organizer_email,
          :is_synced_to_calendar, :calendar_sync_error, :last_synced_at,
          :google_event_id, :google_meet_link, :status, :confirmation_status,
          :reminder_sent, :reminder_sent_at, :confirmation_request_sent,
          :confirmation_request_sent_at, :job_vacancy_id, :job_title,
          :application_stage, :interviewer_notes, :recording_url,
          :created_by, :cancelled_at, :cancellation_reason,
          additional_interviewers: [], feedback: {}, lia_preparation_notes: {},
          lia_suggested_questions: []
        )
      end
    end
  end
end
