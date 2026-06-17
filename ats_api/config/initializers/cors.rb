Rails.application.config.middleware.insert_before 0, Rack::Cors do
  allow do
    origins "https://app.wedotalent.cc",
            "https://interview.wedotalent.cc",
            "https://wedotalent.cc",
            "http://localhost:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001"
    resource "*",
      headers: :any,
      methods: %i[get post put patch delete options head],
      credentials: true
  end
end
