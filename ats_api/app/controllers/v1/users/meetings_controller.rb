# frozen_string_literal: true

module V1
  module Users
    class MeetingsController < ApplicationController
      before_action :set_meeting, only: %i[show update destroy]

      def index
        params[:where] = parse_json_param(params[:where]) || {}
        params[:where]["is_deleted"] = false if params[:where]["is_deleted"].nil?

        perform_search(
          model: Meeting,
          serializer: MeetingSerializer
        )
      end

      def stats
        start_date = params[:start_date]&.to_date || 30.days.ago.to_date
        end_date = params[:end_date]&.to_date || Date.current

        cache_key = "meetings_stats:#{@current_user.account_id}:#{params[:job_id]}:#{params[:organizer_id]}:#{start_date}:#{end_date}"
        data = Rails.cache.fetch(cache_key, expires_in: 15.minutes) do
          Meetings::StatsService.new(
            start_date: start_date,
            end_date: end_date,
            job_id: params[:job_id],
            organizer_id: params[:organizer_id]
          ).call
        end

        render json: data, status: :ok
      end

      def show
        render_success(@meeting, serializer: MeetingSerializer)
      end

      def create
        meeting = MeetingService.create(
          user: @current_user,
          subject: meeting_params[:subject],
          start_time: parse_datetime(meeting_params[:start_time]),
          end_time: parse_datetime(meeting_params[:end_time]),
          provider: meeting_params[:provider],
          location: meeting_params[:location],
          sub_status: meeting_params[:sub_status],
          job_id: meeting_params[:job_id],
          apply_id: meeting_params[:apply_id],
          settings: meeting_params[:settings] || {}
        )

        create_meeting_relationship(meeting_id: meeting.id)

        render_success(meeting, serializer: MeetingSerializer, status: :created)
      rescue MeetingService::ProviderNotAvailable => e
        render json: {
          success: false,
          error: { code: "PROVIDER_NOT_AVAILABLE", message: e.message }
        }, status: :unprocessable_entity
      rescue MeetingService::MeetingCreationFailed => e
        render json: {
          success: false,
          error: { code: "MEETING_CREATION_FAILED", message: e.message }
        }, status: :unprocessable_entity
      end

      def update
        MeetingService.update(
          meeting: @meeting,
          user: @current_user,
          **update_params
        )

        render_success(@meeting.reload, serializer: MeetingSerializer)
      rescue => e
        render json: {
          success: false,
          error: { code: "UPDATE_FAILED", message: e.message }
        }, status: :unprocessable_entity
      end

      def destroy
        MeetingService.delete(meeting: @meeting, user: @current_user)
        render_success(@meeting, serializer: MeetingSerializer)
      rescue => e
        render json: {
          success: false,
          error: { code: "DELETE_FAILED", message: e.message }
        }, status: :unprocessable_entity
      end

      private

      def set_meeting
        @meeting = Meeting.find_by!(id: params[:id], account_id: @current_user.account_id, is_deleted: false)
      rescue ActiveRecord::RecordNotFound
        render json: {
          success: false,
          error: { code: "MEETING_NOT_FOUND", message: "Meeting not found" }
        }, status: :not_found
      end

      def meeting_params
        params.require(:meeting).permit(
          :subject, :start_time, :end_time, :provider, :location, :sub_status, :job_id,
          :reference_type, :reference_id, :apply_id, :role,
          settings: %i[
            lobby_bypass_scope dial_in_bypass allow_chat allow_reactions
            allowed_presenters record_automatically allow_attendee_mic allow_attendee_camera
          ]
        )
      end

      def update_params
        params.require(:meeting).permit(:subject, :start_time, :end_time, :location, :sub_status, :job_id, :apply_id, :settings).to_h.symbolize_keys
      end

      def create_meeting_relationship(meeting_id:, calendar_event_id: nil)
        return unless meeting_params[:reference_type].present? && meeting_params[:reference_id].present?

        MeetingRelationship.create!(
          account_id: @current_user.account_id,
          reference_type: meeting_params[:reference_type],
          reference_id: meeting_params[:reference_id],
          apply_id: meeting_params[:apply_id],
          role: meeting_params[:role],
          meeting_id: meeting_id,
          calendar_event_id: calendar_event_id
        )
      end

      def parse_datetime(value)
        return value if value.is_a?(Time) || value.is_a?(DateTime)
        Time.zone.parse(value.to_s)
      end
    end
  end
end
