require_relative "boot"

require "rails"
# Pick the frameworks you want:
require "active_model/railtie"
require "active_job/railtie"
require "active_record/railtie"
require "active_storage/engine"
require "action_controller/railtie"
require "action_mailer/railtie"
require "action_mailbox/engine"
require "action_text/engine"
require "action_view/railtie"
require "action_cable/engine"
require "apartment"

# require "rails/test_unit/railtie"

# Require the gems listed in Gemfile, including any gems
# you've limited to :test, :development, or :production.
Bundler.require(*Rails.groups)

module AtsApi
  class Application < Rails::Application
    config.api_only = false
    # Initialize configuration defaults for originally generated Rails version.
    config.load_defaults 7.1

    # Please, add to the `ignore` list any other `lib` subdirectories that do
    # not contain `.rb` files, or that should not be reloaded or eager loaded.
    # Common ones are `templates`, `generators`, or `middleware`, for example.
    # config.middleware.delete Apartment::Elevators::Generic
    config.autoload_lib(ignore: %w[assets tasks ])
    # Rails 7.1+ fix: use paths.add instead of << to avoid FrozenError
    config.paths.add "app/lib", eager_load: true
    config.paths.add "app/services", eager_load: true

    # Ignore linkedin_search subdirectory as it uses manual require_relative
    Rails.autoloaders.main.ignore(Rails.root.join("app/services/apify/linkedin_search"))

    # Configuration for the application, engines, and railties goes here.
    #
    # These settings can be overridden in specific environments using the files
    # in config/environments, which are processed later.
    #
    # config.time_zone = "Central Time (US & Canada)"
    # config.eager_load_paths << Rails.root.join("extras")

    # Don't generate system test files.
    config.generators.system_tests = nil
    config.middleware.use ActionDispatch::Cookies
    config.middleware.use ActionDispatch::Session::CookieStore
    config.active_job.queue_adapter = :sidekiq
  end
end
