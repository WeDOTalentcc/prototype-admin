# frozen_string_literal: true

module Meetings
  class MicrosoftTeamsStrategy
    GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0"

    class << self
      def create(user:, subject:, start_time:, end_time:, location: nil, sub_status: nil, job_id: nil, apply_id: nil, settings: {})
        Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        Rails.logger.info "🎥 [MicrosoftTeamsStrategy] Creating Teams meeting"
        Rails.logger.info "   User: #{user.id} | Subject: #{subject}"
        Rails.logger.info "   Start: #{start_time} | End: #{end_time}"
        Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

        meeting_params = build_meeting_params(subject, start_time, end_time, settings)

        response = MicrosoftService::Api.post(
          "/me/onlineMeetings",
          user,
          body: meeting_params,
          headers: { "Content-Type" => "application/json" }
        )

        meeting = create_meeting_record(
          user: user,
          response: response,
          subject: subject,
          start_time: start_time,
          end_time: end_time,
          sub_status: sub_status,
          job_id: job_id,
          apply_id: apply_id,
          settings: settings
        )

        Rails.logger.info "✅ [MicrosoftTeamsStrategy] Meeting created successfully"
        Rails.logger.info "   ID: #{meeting.id} | Join URL: #{meeting.join_url[0..50]}..."

        meeting
      rescue => e
        Rails.logger.error "❌ [MicrosoftTeamsStrategy] Failed to create meeting: #{e.message}"
        Rails.logger.error e.backtrace.first(5).join("\n")
        raise MeetingService::MeetingCreationFailed, "Failed to create Teams meeting: #{e.message}"
      end

      def update(meeting:, user:, **params)
        Rails.logger.info "🔄 [MicrosoftTeamsStrategy] Updating Teams meeting #{meeting.external_id}"

        update_params = {}
        update_params[:subject] = params[:subject] if params[:subject]
        update_params[:startDateTime] = params[:start_time].iso8601 if params[:start_time]
        update_params[:endDateTime] = params[:end_time].iso8601 if params[:end_time]

        if update_params.any?
          MicrosoftService::Api.patch(
            "/me/onlineMeetings/#{meeting.external_id}",
            user,
            body: update_params,
            headers: { "Content-Type" => "application/json" }
          )
        end

        meeting.update!(params.slice(:subject, :start_time, :end_time, :settings))
        meeting.reload

        Rails.logger.info "✅ [MicrosoftTeamsStrategy] Meeting updated successfully"
        meeting
      rescue => e
        Rails.logger.error "❌ [MicrosoftTeamsStrategy] Failed to update meeting: #{e.message}"
        raise MeetingService::MeetingCreationFailed, "Failed to update Teams meeting: #{e.message}"
      end

      def delete(meeting:, user:)
        Rails.logger.info "🗑️ [MicrosoftTeamsStrategy] Deleting Teams meeting #{meeting.external_id}"

        MicrosoftService::Api.delete(
          "/me/onlineMeetings/#{meeting.external_id}",
          user
        )

        meeting.soft_delete!

        Rails.logger.info "✅ [MicrosoftTeamsStrategy] Meeting deleted successfully"
        meeting
      rescue => e
        Rails.logger.error "❌ [MicrosoftTeamsStrategy] Failed to delete meeting: #{e.message}"
        meeting.soft_delete!
        meeting
      end

      def get_details(meeting:, user:)
        Rails.logger.info "🔍 [MicrosoftTeamsStrategy] Getting Teams meeting details #{meeting.external_id}"

        response = MicrosoftService::Api.get(
          "/me/onlineMeetings/#{meeting.external_id}",
          user
        )

        meeting.update(metadata: response)
        meeting
      rescue => e
        Rails.logger.error "❌ [MicrosoftTeamsStrategy] Failed to get meeting details: #{e.message}"
        meeting
      end

      private

      def build_meeting_params(subject, start_time, end_time, settings)
        {
          subject: subject,
          startDateTime: start_time.utc.iso8601,
          endDateTime: end_time.utc.iso8601,
          lobbyBypassSettings: {
            scope: settings[:lobby_bypass_scope] || "organization",
            isDialInBypassEnabled: settings[:dial_in_bypass] || false
          },
          allowMeetingChat: settings[:allow_chat] || "enabled",
          allowTeamworkReactions: settings[:allow_reactions] || true,
          allowedPresenters: settings[:allowed_presenters] || "everyone",
          recordAutomatically: settings[:record_automatically] || false,
          allowAttendeeToEnableMic: settings[:allow_attendee_mic] || true,
          allowAttendeeToEnableCamera: settings[:allow_attendee_camera] || true
        }
      end

      def create_meeting_record(user:, response:, subject:, start_time:, end_time:, sub_status: nil, job_id: nil, apply_id: nil, settings:)
        Meeting.create!(
          account_id: user.account_id,
          organizer_id: user.id,
          provider: Meeting::PROVIDERS[:microsoft_teams],
          external_id: response["id"],
          join_url: response["joinUrl"] || response["joinWebUrl"],
          subject: subject,
          start_time: start_time,
          end_time: end_time,
          sub_status: sub_status || Meeting::SUB_STATUSES[:invite_sent],
          job_id: job_id,
          apply_id: apply_id,
          settings: settings,
          metadata: response
        )
      end
    end
  end
end
