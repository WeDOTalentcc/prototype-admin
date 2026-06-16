# Load the Rails application.
require_relative "application"

# Initialize the Rails application.
Rails.application.initialize!

# Em development usamos Mailpit (configurado em config/environments/development.rb).
# Em outros ambientes, usamos Mailgun.
unless Rails.env.development?
  ActionMailer::Base.smtp_settings = {
    user_name: ENV["MAILGUN_EMAIL"],
    password: ENV["MAILGUN_PASS"],
    domain: ENV.fetch("MAILGUN_DOMAIN", "mg.wedotalent.cc"),
    address: ENV["MAILGUN_HOST"],
    port: ENV["MAILGUN_PORT"],
    authentication: :plain,
    enable_starttls_auto: true
  }
end

if Rails.env == "development"
  AtsApi::Application.default_url_options.merge!(
    host: "localhost:8080",
    protocol: "http"
  )
else
  AtsApi::Application.default_url_options.merge!(
    host: "app.wedotalent.cc",
    protocol: "https"
  )
end
