# frozen_string_literal: true

# Shared Redis connection for application-wide use (JWT blacklist, caching, etc.)
# Sidekiq has its own pool configured in config/initializers/sidekiq.rb.

REDIS = Redis.new(url: ENV.fetch("REDIS_URL", "redis://localhost:6379/0"))
