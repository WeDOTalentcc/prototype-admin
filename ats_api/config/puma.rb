# config/puma.rb

# Especifica o número de threads que o Puma pode usar.
max_threads_count = ENV.fetch("RAILS_MAX_THREADS", 5)
min_threads_count = ENV.fetch("RAILS_MIN_THREADS", max_threads_count)
threads min_threads_count, max_threads_count

# Porta/Bind: Cloud Run expõe PORT. Faça bind explícito em 0.0.0.0 para o startup probe TCP.
selected_port = ENV.fetch("PORT", 8080)
STDOUT.sync = true
puts "[Puma] Iniciando em PORT=#{selected_port} (bind tcp://0.0.0.0:#{selected_port})"
bind "tcp://0.0.0.0:#{selected_port}"

# Especifica o ambiente (production no Cloud Run).
environment ENV.fetch("RAILS_ENV", "development")

# Permite que o Puma seja encerrado com Ctrl-C.
plugin :tmp_restart
