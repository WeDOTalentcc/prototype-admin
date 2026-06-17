# frozen_string_literal: true

module Calendars
  class MicrosoftCalendarStrategy
    class << self
      def create(user:, title:, start_time:, end_time:, **params)
        Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        Rails.logger.info "📅 [MicrosoftCalendarStrategy] Creating calendar event"
        Rails.logger.info "   User: #{user.id} | Title: #{title}"
        Rails.logger.info "   Start: #{start_time} | End: #{end_time}"
        Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

        graph_body = build_event_params(title, start_time, end_time, params)
        response = MicrosoftService::Api.post(
          "/me/events",
          user,
          body: graph_body,
          headers: { "Content-Type" => "application/json" }
        )

        event = create_event_record(user: user, response: response, title: title,
                                    start_time: start_time, end_time: end_time, params: params)
        sync_attendees(event, params[:attendees] || [], response)

        Rails.logger.info "✅ [MicrosoftCalendarStrategy] Event created | ID: #{event.id} | External: #{event.external_id}"
        event
      rescue => e
        Rails.logger.error "❌ [MicrosoftCalendarStrategy] Failed to create event: #{e.message}"
        Rails.logger.error e.backtrace.first(5).join("\n")
        raise CalendarService::EventCreationFailed, "Failed to create calendar event: #{e.message}"
      end

      def update(event:, user:, **params)
        Rails.logger.info "🔄 [MicrosoftCalendarStrategy] Updating calendar event #{event.external_id}"

        graph_body = build_update_params(params)

        if graph_body.any? && event.external_id.present?
          MicrosoftService::Api.patch(
            "/me/events/#{event.external_id}",
            user,
            body: graph_body,
            headers: { "Content-Type" => "application/json" }
          )
        end

        event.update!(build_local_update_params(params))
        sync_attendees(event, params[:attendees], nil) if params.key?(:attendees)
        event.reload

        Rails.logger.info "✅ [MicrosoftCalendarStrategy] Event updated"
        event
      rescue => e
        Rails.logger.error "❌ [MicrosoftCalendarStrategy] Failed to update event: #{e.message}"
        Rails.logger.error e.backtrace.first(5).join("\n")
        raise CalendarService::EventCreationFailed, "Failed to update calendar event: #{e.message}"
      end

      def delete(event:, user:)
        Rails.logger.info "🗑️  [MicrosoftCalendarStrategy] Deleting calendar event #{event.external_id}"

        if event.external_id.present?
          MicrosoftService::Api.delete("/me/events/#{event.external_id}", user)
        end

        event.soft_delete!
        Rails.logger.info "✅ [MicrosoftCalendarStrategy] Event deleted"
        event
      rescue => e
        Rails.logger.error "❌ [MicrosoftCalendarStrategy] Failed to delete event: #{e.message}"
        event.soft_delete!
        event
      end

      def get_details(event:, user:)
        Rails.logger.info "🔍 [MicrosoftCalendarStrategy] Fetching event details #{event.external_id}"
        return event unless event.external_id.present?

        response = MicrosoftService::Api.get(
          "/me/events/#{event.external_id}?$select=#{CalendarEvent.graph_fields}",
          user
        )

        event.update!(
          metadata: response,
          is_cancelled: response["isCancelled"] || false,
          title: response["subject"] || event.title
        )

        event
      rescue => e
        Rails.logger.error "❌ [MicrosoftCalendarStrategy] Failed to get details: #{e.message}"
        event
      end

      def sync_events(user:, start_time:, end_time:)
        Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        Rails.logger.info "🔄 [MicrosoftCalendarStrategy] Syncing events for user #{user.id}"

        filter = "start/dateTime ge '#{start_time.utc.iso8601}' and end/dateTime le '#{end_time.utc.iso8601}'"
        url = "/me/events?$select=#{CalendarEvent.graph_fields}&$filter=#{CGI.escape(filter)}&$top=100"
        response = MicrosoftService::Api.get(url, user)

        events = (response["value"] || []).map { |graph_event| upsert_from_graph(user, graph_event) }
        Rails.logger.info "✅ [MicrosoftCalendarStrategy] Synced #{events.compact.count} events"
        events.compact
      rescue => e
        Rails.logger.error "❌ [MicrosoftCalendarStrategy] Sync failed: #{e.message}"
        []
      end

      def get_free_busy(user:, start_time:, end_time:, duration_minutes: 60)
        url = "/me/calendarView?startDateTime=#{start_time.utc.iso8601}&endDateTime=#{end_time.utc.iso8601}&$select=subject,start,end,showAs"
        response = MicrosoftService::Api.get(url, user)
        response["value"] || []
      rescue => e
        Rails.logger.error "❌ [MicrosoftCalendarStrategy] Free/busy failed: #{e.message}"
        []
      end

      private

      def build_event_params(title, start_time, end_time, params)
        body = {
          subject: title,
          start: { dateTime: start_time.utc.iso8601, timeZone: "UTC" },
          end: { dateTime: end_time.utc.iso8601, timeZone: "UTC" },
          isAllDay: params[:is_all_day] || false,
          importance: params[:importance] || "normal",
          isOnlineMeeting: params.dig(:settings, :online_meeting) || false,
          attendees: build_graph_attendees(params[:attendees] || [])
        }

        body[:body] = { contentType: "html", content: params[:description] } if params[:description].present?
        body[:location] = { displayName: params[:location] } if params[:location].present?
        body
      end

      def build_update_params(params)
        body = {}
        body[:subject] = params[:title] if params[:title]
        body[:start] = { dateTime: params[:start_time].utc.iso8601, timeZone: "UTC" } if params[:start_time]
        body[:end] = { dateTime: params[:end_time].utc.iso8601, timeZone: "UTC" } if params[:end_time]
        body[:body] = { contentType: "html", content: params[:description] } if params[:description]
        body[:location] = { displayName: params[:location] } if params[:location]
        body[:importance] = params[:importance] if params[:importance]
        body[:attendees] = build_graph_attendees(params[:attendees]) if params[:attendees]
        body
      end

      def build_local_update_params(params)
        local = {}
        local[:title] = params[:title] if params[:title]
        local[:description] = params[:description] if params[:description]
        local[:location] = params[:location] if params[:location]
        local[:start_time] = params[:start_time] if params[:start_time]
        local[:end_time] = params[:end_time] if params[:end_time]
        local[:importance] = params[:importance] if params[:importance]
        local[:timezone] = params[:timezone] if params[:timezone]
        local[:event_type] = params[:event_type] if params[:event_type]
        local[:settings] = params[:settings] if params[:settings]
        local[:sub_status] = params[:sub_status] if params[:sub_status]
        local[:job_id] = params[:job_id] if params.key?(:job_id)
        local[:apply_id] = params[:apply_id] if params.key?(:apply_id)
        local
      end

      def build_graph_attendees(attendees)
        return [] unless attendees.present?

        attendees.map do |a|
          {
            emailAddress: { address: a[:email], name: a[:name] || a[:email] },
            type: a[:required] == false ? "optional" : "required"
          }
        end
      end

      def create_event_record(user:, response:, title:, start_time:, end_time:, params:)
        CalendarEvent.create!(
          account_id: user.account_id,
          organizer_id: user.id,
          provider: CalendarEvent::PROVIDERS[:microsoft],
          external_id: response["id"],
          external_uid: response["iCalUId"],
          title: title,
          description: params[:description],
          location: params[:location],
          event_type: params[:event_type] || CalendarEvent::EVENT_TYPES[:generic],
          importance: params[:importance] || "normal",
          start_time: start_time,
          end_time: end_time,
          timezone: params[:timezone] || "America/Sao_Paulo",
          is_all_day: params[:is_all_day] || false,
          meeting_id: params[:meeting_id],
          job_id: params[:job_id],
          apply_id: params[:apply_id],
          sub_status: params[:sub_status] || CalendarEvent::SUB_STATUSES[:invite_sent],
          settings: params[:settings] || {},
          metadata: response
        )
      end

      def sync_attendees(event, attendees_params, graph_response)
        return if attendees_params.nil?

        event.attendees.destroy_all

        attendee_list = Array(attendees_params)
          .map { |a| { email: a[:email], name: a[:name], is_organizer: false,
                       response_status: CalendarEventAttendee::RESPONSE_STATUSES[:not_responded] } }
          .uniq { |a| a[:email]&.downcase }

        if graph_response
          (graph_response["attendees"] || []).each do |ga|
            email = ga.dig("emailAddress", "address")
            local = attendee_list.find { |a| a[:email]&.downcase == email&.downcase }
            next unless local

            local[:response_status] = CalendarEventAttendee::MICROSOFT_RESPONSE_MAP[
              ga.dig("status", "response")
            ] || CalendarEventAttendee::RESPONSE_STATUSES[:not_responded]
          end
        end

        attendee_list.each { |attrs| event.attendees.create!(attrs) }
      end

      def upsert_from_graph(user, graph_event)
        event = CalendarEvent.find_or_initialize_by(
          external_id: graph_event["id"],
          account_id: user.account_id
        )

        event.assign_attributes(
          organizer_id: user.id,
          provider: CalendarEvent::PROVIDERS[:microsoft],
          external_uid: graph_event["iCalUId"],
          title: graph_event["subject"] || "(No title)",
          description: graph_event.dig("body", "content"),
          start_time: Time.zone.parse(graph_event.dig("start", "dateTime")),
          end_time: Time.zone.parse(graph_event.dig("end", "dateTime")),
          timezone: graph_event.dig("start", "timeZone") || "UTC",
          importance: graph_event["importance"] || "normal",
          is_all_day: graph_event["isAllDay"] || false,
          is_cancelled: graph_event["isCancelled"] || false,
          metadata: graph_event
        )

        event.save!
        event
      rescue => e
        Rails.logger.error "❌ [MicrosoftCalendarStrategy] Failed to upsert event #{graph_event['id']}: #{e.message}"
        nil
      end
    end
  end
end
