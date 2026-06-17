# frozen_string_literal: true

class NotificationPreferenceSerializer
  include JSONAPI::Serializer

  attributes :briefing_enabled, :briefing_time, :briefing_channel,
             :aging_threshold_days, :alert_channels, :timezone

  attribute :alerts do |pref|
    pref.alert_settings
  end
end
