# frozen_string_literal: true

module CalendarService
  class ProviderNotAvailable < StandardError; end
  class EventCreationFailed < StandardError; end
  class EventNotFound < StandardError; end

  class << self
    def create(user:, title:, start_time:, end_time:, **params)
      strategy = detect_strategy(user, params[:provider])
      strategy.create(
        user: user,
        title: title,
        start_time: start_time,
        end_time: end_time,
        **params
      )
    end

    def update(event:, user:, **params)
      strategy = strategy_for(event.provider)
      strategy.update(event: event, user: user, **params)
    end

    def delete(event:, user:)
      strategy = strategy_for(event.provider)
      strategy.delete(event: event, user: user)
    end

    def get_details(event:, user:)
      strategy = strategy_for(event.provider)
      strategy.get_details(event: event, user: user)
    end

    def get_free_busy(user:, start_time:, end_time:, duration_minutes: 60)
      strategy = detect_strategy(user)
      strategy.get_free_busy(user: user, start_time: start_time, end_time: end_time, duration_minutes: duration_minutes)
    end

    def sync_events(user:, start_time:, end_time:)
      strategy = detect_strategy(user)
      strategy.sync_events(user: user, start_time: start_time, end_time: end_time)
    end

    private

    def detect_strategy(user, explicit_provider = nil)
      return strategy_for(explicit_provider) if explicit_provider

      account = user.account

      if account.microsoft_sso_enabled? && user.microsoft_connected?
        return Calendars::MicrosoftCalendarStrategy
      end

      if account.google_sso_enabled? && user.google_connected?
        return Calendars::GoogleCalendarStrategy
      end

      raise ProviderNotAvailable, "No calendar provider connected for user #{user.id}. " \
        "Account providers: microsoft=#{account.microsoft_sso_enabled?}, google=#{account.google_sso_enabled?}"
    end

    def strategy_for(provider)
      case provider.to_s
      when CalendarEvent::PROVIDERS[:microsoft]
        Calendars::MicrosoftCalendarStrategy
      when CalendarEvent::PROVIDERS[:google]
        Calendars::GoogleCalendarStrategy
      else
        raise ProviderNotAvailable, "Unknown calendar provider: #{provider}"
      end
    end
  end
end
