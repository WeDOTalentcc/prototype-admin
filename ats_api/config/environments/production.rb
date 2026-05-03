require "active_support/core_ext/integer/time"

Rails.application.configure do
  config.enable_reloading = false
  config.eager_load = true
  config.consider_all_requests_local = false
  config.action_controller.perform_caching = true

  config.active_storage.service = ENV.fetch("ACTIVE_STORAGE_SERVICE", "local").to_sym

  config.log_level = :info
  config.log_formatter = ::Logger::Formatter.new

  if ENV["RAILS_LOG_TO_STDOUT"].present?
    logger = ActiveSupport::Logger.new($stdout)
    logger.formatter = config.log_formatter
    config.logger = ActiveSupport::TaggedLogging.new(logger)
  end

  config.hosts << "api.wedotalent.cc"
  config.hosts << "app.wedotalent.cc"
  config.hosts << "wedotalent.cc"
  config.hosts << /.*/

  config.action_cable.allowed_request_origins = [
    "https://app.wedotalent.cc", "https://wedotalent.cc", /https?:\/\/.*?\.wedotalent\.cc.*/
  ]

  config.action_cable.url = ENV.fetch("REDIS_URL").gsub(/\/0$/, "/1")
  config.action_cable.disable_request_forgery_protection = true


  config.active_job.queue_adapter = :sidekiq

  config.i18n.fallbacks = true
  config.active_support.report_deprecations = false
  config.active_record.dump_schema_after_migration = false
end
