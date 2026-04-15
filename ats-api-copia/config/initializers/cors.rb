# CORS configuration — accepts multiple origins via ENV, comma-separated.
# Example: CORS_ALLOWED_ORIGINS=https://app.wedotalent.com,https://staging.wedotalent.com
Rails.application.config.middleware.insert_before 0, Rack::Cors do
  allow do
    origins(*ENV.fetch('CORS_ALLOWED_ORIGINS', 'http://localhost:3000').split(',').map(&:strip))

    resource '*',
      headers: :any,
      methods: %i[get post put patch delete options head],
      credentials: true
  end
end