# frozen_string_literal: true

module Meetings
  class GoogleMeetStrategy
    class << self
      def create(user:, subject:, start_time:, end_time:, location: nil, sub_status: nil, job_id: nil, apply_id: nil, settings: {})
        raise NotImplementedError, "Google Meet integration coming soon"
      end

      def update(meeting:, user:, **params)
        raise NotImplementedError, "Google Meet integration coming soon"
      end

      def delete(meeting:, user:)
        raise NotImplementedError, "Google Meet integration coming soon"
      end

      def get_details(meeting:, user:)
        raise NotImplementedError, "Google Meet integration coming soon"
      end
    end
  end
end
