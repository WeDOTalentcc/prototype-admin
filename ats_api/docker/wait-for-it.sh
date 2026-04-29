#!/usr/bin/env bash
# wait-for-it.sh

host_port="$1"
shift
cmd="$@"

host="${host_port%%:*}"
port="${host_port##*:}"

echo "➡️ Aguardando $host:$port ficar disponível (timeout: 40s)..."

# Tempo máximo em segundos
MAX_WAIT=40
count=0

while ! nc -z -w 1 "$host" "$port" </dev/null >/dev/null 2>&1; do
  echo "⏳ Ainda esperando $host:$port..."
  sleep 1
  count=$((count + 1))
  if [ $count -ge $MAX_WAIT ]; then
    echo "⚠️ Timeout após ${MAX_WAIT}s. Executando comando mesmo assim..."
    break
  fi
done

echo "✅ Executando comando: $cmd"
exec $cmd
