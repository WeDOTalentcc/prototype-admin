# frozen_string_literal: true

# Close the shared Bunny connection pool on app shutdown.
at_exit do
  MessageService::ConnectionPool.shutdown
rescue StandardError
  nil
end
