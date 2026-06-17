# frozen_string_literal: true

module V1
  module Users
    class CalendarEventsController < ApplicationController
      before_action :set_event, only: %i[show update destroy sync]

      def index
        params[:where] = parse_json_param(params[:where]) || {}
        params[:where]["is_deleted"] = false if params[:where]["is_deleted"].nil?
        params[:where]["account_id"] = @current_user.account_id

        perform_search(
          model: CalendarEvent,
          serializer: CalendarEventSerializer
        )
      end

      def show
        render_success(@event, serializer: CalendarEventSerializer)
      end

      def create
        result = CalendarService.create(
          user: @current_user,
          title: event_params[:title],
          start_time: parse_datetime(event_params[:start_time]),
          end_time: parse_datetime(event_params[:end_time]),
          provider: event_params[:provider],
          description: event_params[:description],
          location: event_params[:location],
          event_type: event_params[:event_type],
          importance: event_params[:importance],
          timezone: event_params[:timezone],
          is_all_day: event_params[:is_all_day],
          meeting_id: event_params[:meeting_id],
          job_id: event_params[:job_id],
          apply_id: event_params[:apply_id],
          sub_status: event_params[:sub_status],
          settings: event_params[:settings] || {},
          attendees: parsed_attendees
        )

        create_meeting_relationship(calendar_event_id: result.id)

        render_success(result, serializer: CalendarEventSerializer, status: :created)
      rescue CalendarService::ProviderNotAvailable => e
        render json: {
          success: false,
          error: { code: "PROVIDER_NOT_AVAILABLE", message: e.message }
        }, status: :unprocessable_entity
      rescue CalendarService::EventCreationFailed => e
        render json: {
          success: false,
          error: { code: "EVENT_CREATION_FAILED", message: e.message }
        }, status: :unprocessable_entity
      end

      def update
        update_attrs = {
          title: event_params[:title],
          description: event_params[:description],
          location: event_params[:location],
          sub_status: event_params[:sub_status],
          start_time: event_params[:start_time] ? parse_datetime(event_params[:start_time]) : nil,
          end_time: event_params[:end_time] ? parse_datetime(event_params[:end_time]) : nil,
          importance: event_params[:importance],
          timezone: event_params[:timezone],
          event_type: event_params[:event_type],
          settings: event_params[:settings],
          job_id: event_params[:job_id],
          apply_id: event_params[:apply_id],
          attendees: parsed_attendees
        }.compact

        result = CalendarService.update(event: @event, user: @current_user, **update_attrs)

        render_success(result, serializer: CalendarEventSerializer)
      rescue CalendarService::EventCreationFailed => e
        render json: {
          success: false,
          error: { code: "UPDATE_FAILED", message: e.message }
        }, status: :unprocessable_entity
      end

      def destroy
        @event.cancel!
        render_success(@event.reload, serializer: CalendarEventSerializer)
      rescue => e
        render json: {
          success: false,
          error: { code: "CANCEL_FAILED", message: e.message }
        }, status: :unprocessable_entity
      end

      def daily_agenda
        result = CalendarEvents::DailyAgendaService.new(
          account_id: @current_user.account_id,
          params: agenda_params
        ).call

        render json: {
          success: true,
          data: result.days,
          meta: result.meta
        }
      end

      def missing_feedback
        result = CalendarEvents::MissingFeedbackService.new(
          account_id: @current_user.account_id,
          user_id: @current_user.id,
          params: missing_feedback_params
        ).call

        render json: {
          success: true,
          data: result.events,
          meta: result.meta
        }
      end

      def suggest_schedule
        text = params.require(:text)
        timezone = params.fetch(:timezone, "America/Sao_Paulo")

        result = CalendarEvents::ScheduleSuggestionService.call(text: text, timezone: timezone)

        render json: { success: true, data: result }
      rescue ActionController::ParameterMissing => e
        render json: {
          success: false,
          error: { code: "MISSING_PARAM", message: e.message }
        }, status: :bad_request
      end

      def sync
        CalendarService.get_details(event: @event, user: @current_user)
        render_success(@event.reload, serializer: CalendarEventSerializer)
      rescue => e
        render json: {
          success: false,
          error: { code: "SYNC_FAILED", message: e.message }
        }, status: :unprocessable_entity
      end

      private

      def set_event
        @event = CalendarEvent.find_by!(
          id: params[:id],
          account_id: @current_user.account_id,
          is_deleted: false
        )
      rescue ActiveRecord::RecordNotFound
        render json: {
          success: false,
          error: { code: "CALENDAR_EVENT_NOT_FOUND", message: "Calendar event not found" }
        }, status: :not_found
      end

      def event_params
        params.require(:calendar_event).permit(
          :title, :description, :location, :provider, :interview_type, :sub_status, :job_id,
          :start_time, :end_time, :timezone,
          :event_type, :importance,
          :is_all_day, :meeting_id,
          :reference_type, :reference_id, :apply_id, :role,
          settings: {},
          attendees: %i[email name required]
        )
      end

      def agenda_params
        params.permit(
          :kind, :search, :from, :to, :timezone,
          :event_type, :provider, :is_cancelled, :organizer_id,
          :page, :per_page
        )
      end

      def missing_feedback_params
        params.permit(:from, :to, :organizer_id, :job_id, :page, :per_page)
      end

      def parsed_attendees
        return nil unless params.dig(:calendar_event, :attendees)

        (event_params[:attendees] || []).map(&:to_h).map(&:symbolize_keys)
      end

      def parse_datetime(value)
        return value if value.is_a?(Time) || value.is_a?(DateTime)

        Time.zone.parse(value.to_s)
      end

      def create_meeting_relationship(meeting_id: nil, calendar_event_id: nil)
        return unless event_params[:reference_type].present? && event_params[:reference_id].present?

        MeetingRelationship.create!(
          account_id: @current_user.account_id,
          reference_type: event_params[:reference_type],
          reference_id: event_params[:reference_id],
          apply_id: event_params[:apply_id],
          role: event_params[:role],
          meeting_id: meeting_id,
          calendar_event_id: calendar_event_id
        )
      end
    end
  end
end
