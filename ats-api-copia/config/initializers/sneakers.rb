require 'sneakers'

if defined?(Sneakers)
  Sneakers.configure(
    amqp: ENV.fetch('RABBITMQ_URL') { 'amqp://guest:guest@localhost:5672' },
    vhost: '/',
    exchange: '',
    exchange_type: :direct,
    durable: true,
    ack: true,
    heartbeat: 30,
    workers: 2,
    prefetch: 10,
    threads: 4,
    timeout_job_after: 60,
    retry_max_times: 5,
    retry_timeout: 5000,
    log: STDOUT
  )

  Sneakers.logger.level = Logger::INFO
end


Sneakers.logger.level = Logger::INFO
