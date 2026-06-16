# frozen_string_literal: true

class NotificationPreference < ApplicationRecord
  VALID_CHANNELS = %w[web whatsapp teams].freeze
  VALID_BRIEFING_CHANNELS = %w[web whatsapp teams].freeze
  BRIEFING_TIME_FORMAT = /\A([01]\d|2[0-3]):[0-5]\d\z/

  belongs_to :user

  validates :user_id, uniqueness: true
  validates :briefing_time, format: { with: BRIEFING_TIME_FORMAT }
  validates :briefing_channel, inclusion: { in: VALID_BRIEFING_CHANNELS }
  validates :aging_threshold_days, numericality: { greater_than: 0, less_than_or_equal_to: 30 }
  validate :valid_alert_channels

  def alert_settings
    {
      aging: { enabled: alert_aging_enabled, threshold_days: aging_threshold_days },
      deadline: { enabled: alert_deadline_enabled },
      no_show: { enabled: alert_no_show_enabled },
      evaluation_completed: { enabled: alert_evaluation_enabled },
      strong_fit: { enabled: alert_strong_fit_enabled },
      stale_job: { enabled: alert_stale_job_enabled }
    }
  end

  def alert_enabled?(type)
    public_send(:"alert_#{type}_enabled")
  rescue NoMethodError
    false
  end

  private

  def valid_alert_channels
    return if alert_channels.blank?

    invalid = alert_channels - VALID_CHANNELS
    return if invalid.empty?

    errors.add(:alert_channels, "contains invalid channels: #{invalid.join(', ')}")
  end
end
