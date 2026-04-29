require "sneakers"

if defined?(Sneakers)
  Sneakers.configure(
    amqp: ENV.fetch("RABBITMQ_URL", "amqp://guest:guest@localhost:5672"),
    vhost: ENV["RABBITMQ_VHOST"] || "/",
    exchange: "",
    exchange_type: :direct,
    durable: true,
    ack: true,
    heartbeat: 30,
    daemonize: false,
    workers: 2,
    threads: 4,
    prefetch: 2,                # Para evitar lotar memória
    timeout_job_after: 300,     # Até 5 min por job
    retry_max_times: 5,
    retry_timeout: 5000,
    verify_peer: false,
    # handler: Sneakers::Handlers::Maxretry,   # Habilita retry automáticos
    log: STDOUT
  )

  Sneakers.logger.level = Logger::INFO
end
