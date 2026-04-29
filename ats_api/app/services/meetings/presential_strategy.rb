# frozen_string_literal: true

module Meetings
  module PresentialStrategy
    class << self
      def create(user:, subject:, start_time:, end_time:, location: nil, sub_status: nil, job_id: nil, apply_id: nil, settings: {})
        Meeting.create!(
          account_id: user.account_id,
          organizer_id: user.id,
          provider: Meeting::PROVIDERS[:presential],
          subject: subject,
          start_time: start_time,
          end_time: end_time,
          location: location,
          sub_status: sub_status || Meeting::SUB_STATUSES[:invite_sent],
          job_id: job_id,
          apply_id: apply_id,
          settings: settings
        )
      end

      def update(meeting:, user:, **params)
        meeting.update!(params.slice(:subject, :start_time, :end_time, :location, :settings))
        meeting
      end

      def delete(meeting:, user:)
        meeting.update!(is_deleted: true)
      end

      def get_details(meeting:, user:)
        meeting
      end
    end
  end
end
