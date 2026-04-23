# frozen_string_literal: true

# Carga de embeddings: candidates/jobs -> tabela embeddings
# Uso: rails runner scripts/embedding_migrate.rb
# ENV:
#   BATCH_SIZE=2000 (default; use 3000-5000 para mais velocidade)
#   ACCOUNT_ID=1   (opcional: só esse tenant)
#   TENANT=public  (opcional: só esse tenant)

BATCH_SIZE = ENV.fetch("BATCH_SIZE", 2000).to_i.clamp(100, 10_000)

def format_duration(sec)
  return "0s" if sec.nil? || sec < 0
  return "#{sec.round(0)}s" if sec < 60
  m = (sec / 60).floor
  s = (sec % 60).round(0)
  return "#{m}m #{s}s" if m < 60
  h = (m / 60).floor
  m = m % 60
  "#{h}h #{m}m #{s}s"
end

def run_migrate_entity(tenant, reference_type, total, batch_size)
  return 0 if total.zero?

  model = reference_type == "Candidate" ? Candidate : Job
  return 0 unless model.column_names.include?("embedding")

  start_time = Time.current
  migrated = 0
  errors = 0

  scope = model.unscope(:select).where.not(embedding: nil).select(:id, :embedding, :updated_at)

  scope.find_in_batches(batch_size: batch_size) do |batch|
    batch_start = Time.current
    records = batch.map do |row|
      {
        reference_type: reference_type,
        reference_id: row.id,
        embedding: row.embedding,
        model_version: "gemini-embedding-001",
        dimensions: 768,
        created_at: row.updated_at,
        updated_at: row.updated_at
      }
    end

    begin
      Embedding.upsert_all(
        records,
        unique_by: %i[reference_type reference_id],
        update_only: [ :embedding ]
      )
      migrated += batch.size
    rescue => e
      errors += batch.size
      Rails.logger.error "[embedding_migrate] #{tenant} #{reference_type} batch: #{e.message}"
    end

    elapsed = Time.current - start_time
    rate = elapsed.positive? ? migrated / elapsed : 0
    remaining = total - migrated
    eta_sec = rate.positive? ? remaining / rate : nil
    pct = total.positive? ? (migrated.to_f / total * 100) : 100

    print "\r  #{reference_type}: #{pct.round(2)}% (#{migrated}/#{total}) | #{rate.round(0)}/s | ETA #{format_duration(eta_sec)} | #{errors} erros    "
  end

  elapsed = Time.current - start_time
  rate = elapsed.positive? ? migrated / elapsed : 0
  puts "\n  ✅ #{migrated} em #{format_duration(elapsed)} (#{rate.round(1)}/s)"
  migrated
end

puts "=== Carga embeddings → tabela embeddings ==="
puts "BATCH_SIZE=#{BATCH_SIZE}"
puts ""

global_start = Time.current
total_candidates = 0
total_jobs = 0
tenants_done = 0

accounts = Account.all
accounts = accounts.where(id: ENV["ACCOUNT_ID"]) if ENV["ACCOUNT_ID"].present?
accounts = accounts.where(tenant: ENV["TENANT"]) if ENV["TENANT"].present?

accounts.find_each do |account|
  Apartment::Tenant.switch!(account.tenant)

  count_c = Candidate.column_names.include?("embedding") ? Candidate.unscope(:select).where.not(embedding: nil).count : 0
  count_j = Job.column_names.include?("embedding") ? Job.unscope(:select).where.not(embedding: nil).count : 0
  next if count_c.zero? && count_j.zero?

  tenants_done += 1
  puts "\n[#{account.tenant}] (#{account.name}) — candidates: #{count_c}, jobs: #{count_j}"

  total_candidates += run_migrate_entity(account.tenant, "Candidate", count_c, BATCH_SIZE)
  total_jobs += run_migrate_entity(account.tenant, "Job", count_j, BATCH_SIZE)
end

global_elapsed = Time.current - global_start
total_rows = total_candidates + total_jobs
global_rate = global_elapsed.positive? ? total_rows / global_elapsed : 0

puts ""
puts "=== Resumo ==="
puts "Tenants: #{tenants_done}"
puts "Candidates: #{total_candidates}"
puts "Jobs: #{total_jobs}"
puts "Total: #{total_rows} em #{format_duration(global_elapsed)} (#{global_rate.round(1)}/s)"
puts "✅ Fim"
