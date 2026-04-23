#!/bin/bash

# Script para reembedar candidatos e jobs de UMA conta específica
# Use este script se quiser testar ou reembedar apenas uma conta

set -e

if [ -z "$1" ]; then
  echo "❌ ERRO: Forneça o account_id"
  echo ""
  echo "Uso: ./reembed_single_account.sh <account_id>"
  echo ""
  echo "Para listar accounts disponíveis:"
  echo "  RAILS_ENV=production bundle exec rails runner 'Account.all.each { |a| puts \"#{a.id}: #{a.name} (#{a.tenant})\" }'"
  echo ""
  exit 1
fi

ACCOUNT_ID=$1

# Verificar se está na VM correta
if [ ! -d "/home/rails/ats_api" ]; then
  echo "❌ ERRO: Este script deve ser executado na VM ats-infra-server"
  exit 1
fi

cd /home/rails/ats_api

echo "=========================================="
echo "🚀 REEMBEDDING ACCOUNT $ACCOUNT_ID"
echo "=========================================="
echo ""

# Verificar se a conta existe
echo "Verificando conta..."
RAILS_ENV=production bundle exec rails runner "
account = Account.find_by(id: $ACCOUNT_ID)
if account.nil?
  puts '❌ ERRO: Conta não encontrada'
  exit 1
end

puts '✓ Conta encontrada:'
puts \"  ID: #{account.id}\"
puts \"  Nome: #{account.name}\"
puts \"  Tenant: #{account.tenant}\"
puts ''

Apartment::Tenant.switch(account.tenant) do
  c_total = Candidate.where(is_deleted: false).count
  j_total = Job.where(is_deleted: false).count
  puts \"  Candidatos: #{c_total}\"
  puts \"  Jobs: #{j_total}\"
end
"

if [ $? -ne 0 ]; then
  exit 1
fi

echo ""
read -p "Continuar com o reembedding? (s/N): " confirm

if [ "$confirm" != "s" ] && [ "$confirm" != "S" ]; then
  echo "Cancelado pelo usuário"
  exit 0
fi

echo ""
echo "🔄 Reembedding candidatos..."
echo ""

RAILS_ENV=production bundle exec rails runner "
require 'parallel'

account = Account.find($ACCOUNT_ID)
puts \"Account: #{account.name}\"

Apartment::Tenant.switch(account.tenant) do
  ids = Candidate.where(is_deleted: false).pluck(:id)
  total = ids.size
  
  puts \"Total de candidatos: #{total}\"
  processed = Concurrent::AtomicFixnum.new(0)
  errors = Concurrent::AtomicFixnum.new(0)
  start_time = Time.now
  
  Parallel.each(ids, in_threads: 20) do |candidate_id|
    begin
      Candidates::EmbeddingSyncJob.perform_now(candidate_id, nil, account.id)
      current = processed.increment
      
      if current % 10 == 0 || current == total
        elapsed = Time.now - start_time
        rate = current / elapsed
        remaining = total - current
        eta = remaining / rate
        pct = (current.to_f / total * 100).round(1)
        
        print \"\rProgresso: #{current}/#{total} (#{pct}%) | #{rate.round(2)} c/s | ETA: #{eta.round(0)}s | Erros: #{errors.value}      \"
      end
    rescue => e
      errors.increment
      puts \"\n⚠️  ERRO candidate #{candidate_id}: #{e.message}\"
    end
  end
  
  puts \"\n✅ Candidatos processados: #{processed.value}/#{total} (#{errors.value} erros)\"
end
"

echo ""
echo "🔄 Reembedding jobs..."
echo ""

RAILS_ENV=production bundle exec rails runner "
require 'parallel'

account = Account.find($ACCOUNT_ID)

Apartment::Tenant.switch(account.tenant) do
  ids = Job.where(is_deleted: false).pluck(:id)
  total = ids.size
  
  puts \"Total de jobs: #{total}\"
  processed = Concurrent::AtomicFixnum.new(0)
  errors = Concurrent::AtomicFixnum.new(0)
  start_time = Time.now
  
  Parallel.each(ids, in_threads: 20) do |job_id|
    begin
      Jobs::EmbeddingSyncJob.perform_now(job_id, nil, account.id)
      current = processed.increment
      
      if current % 10 == 0 || current == total
        elapsed = Time.now - start_time
        rate = current / elapsed
        remaining = total - current
        eta = remaining / rate
        pct = (current.to_f / total * 100).round(1)
        
        print \"\rProgresso: #{current}/#{total} (#{pct}%) | #{rate.round(2)} j/s | ETA: #{eta.round(0)}s | Erros: #{errors.value}      \"
      end
    rescue => e
      errors.increment
      puts \"\n⚠️  ERRO job #{job_id}: #{e.message}\"
    end
  end
  
  puts \"\n✅ Jobs processados: #{processed.value}/#{total} (#{errors.value} erros)\"
end
"

echo ""
echo "=========================================="
echo "✅ REEMBEDDING FINALIZADO!"
echo "=========================================="
