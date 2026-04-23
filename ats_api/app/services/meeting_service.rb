# frozen_string_literal: true

module MeetingService
  class ProviderNotAvailable < StandardError; end
  class MeetingCreationFailed < StandardError; end

  class << self
    def create(user:, subject:, start_time:, end_time:, provider: nil, location: nil, sub_status: nil, job_id: nil, apply_id: nil, settings: {})
      provider_name = determine_provider(user, provider)
      strategy = strategy_for(provider_name)

      strategy.create(
        user: user,
        subject: subject,
        start_time: start_time,
        end_time: end_time,
        location: location,
        sub_status: sub_status,
        job_id: job_id,
        apply_id: apply_id,
        settings: settings
      )
    end

    def update(meeting:, user:, **params)
      strategy = strategy_for(meeting.provider)
      strategy.update(meeting: meeting, user: user, **params)
    end

    def delete(meeting:, user:)
      strategy = strategy_for(meeting.provider)
      strategy.delete(meeting: meeting, user: user)
    end

    def get_details(meeting:, user:)
      strategy = strategy_for(meeting.provider)
      strategy.get_details(meeting: meeting, user: user)
    end

    private

    def determine_provider(user, explicit_provider = nil)
      return explicit_provider if explicit_provider == Meeting::PROVIDERS[:presential]
      return explicit_provider if explicit_provider

      account = user.account

      if account.microsoft_sso_enabled? && user.microsoft_connected?
        return Meeting::PROVIDERS[:microsoft_teams]
      end

      if account.google_sso_enabled? && user.google_connected?
        return Meeting::PROVIDERS[:google_meet]
      end

      raise ProviderNotAvailable, "No online meeting provider available for user #{user.id}. " \
        "Account providers: microsoft=#{account.microsoft_sso_enabled?}, google=#{account.google_sso_enabled?}"
    end

    def strategy_for(provider)
      case provider
      when Meeting::PROVIDERS[:microsoft_teams]
        Meetings::MicrosoftTeamsStrategy
      when Meeting::PROVIDERS[:google_meet]
        Meetings::GoogleMeetStrategy
      when Meeting::PROVIDERS[:presential]
        Meetings::PresentialStrategy
      when Meeting::PROVIDERS[:zoom]
        Meetings::ZoomStrategy
      else
        raise ProviderNotAvailable, "Unknown provider: #{provider}"
      end
    end
  end
end
