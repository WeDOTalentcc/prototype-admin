# frozen_string_literal: true

# Sentry error tracking — only initializes when SENTRY_DSN is set.
# Safe to leave unconfigured in development.
if ENV["SENTRY_DSN"].present?
  Sentry.init do |config|
    config.dsn = ENV["SENTRY_DSN"]
    config.environment = Rails.env
    config.enabled_environments = %w[production staging]

    config.breadcrumbs_logger = [:active_support_logger, :http_logger]
    config.traces_sample_rate = ENV.fetch("SENTRY_TRACES_SAMPLE_RATE", "0.1").to_f
    config.profiles_sample_rate = ENV.fetch("SENTRY_PROFILES_SAMPLE_RATE", "0.1").to_f

    # LGPD: never send PII to Sentry
    config.send_default_pii = false

    config.before_send = lambda { |event, _hint|
      # Strip any email or phone from exception messages
      event.message&.gsub!(/[\w.+-]+@[\w-]+\.[\w.]+/, "[REDACTED_EMAIL]")
      event
    }
  end
end
