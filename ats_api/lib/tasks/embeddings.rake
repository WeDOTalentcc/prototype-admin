namespace :embeddings do
  # Escopo de contas para as tasks. Use ENV para filtrar:
  #   ACCOUNT_ID=1              → só a conta com id 1
  #   TENANT=wedotalent         → só a conta com tenant "wedotalent"
  #   (nenhum)                  → todas as contas
  def embeddings_account_scope
    scope = Account.all
    scope = scope.where(id: ENV["ACCOUNT_ID"]) if ENV["ACCOUNT_ID"].present?
    scope = scope.where(tenant: ENV["TENANT"]) if ENV["TENANT"].present?
    scope
  end

  # Formata segundos em "Xs", "Xm Ys" ou "Xh Ym"
  def format_duration(sec)
    return "0s" if sec.nil? || sec < 0
    return "#{sec.round(0)}s" if sec < 60
    m = (sec / 60).floor
    s = (sec % 60).round(0)
    return "#{m}m #{s}s" if m < 60
    h = (m / 60).floor
    m = m % 60
    "#{h}h #{m}m"
  end

  # Estimativa de custo (alinhada a scripts/embedding_cost_calculator.rb)
  PRICE_PER_MILLION_TOKENS = 0.15  # USD (Gemini)
  BRL_RATE = 6.0

  def avg_tokens_per_candidate
    (ENV["AVG_TOKENS"] || 1500).to_i
  end

  def estimated_rate_per_sec
    (ENV["EST_RATE"] || 3).to_f
  end

  def estimated_cost_brl(candidate_count)
    tokens = candidate_count * avg_tokens_per_candidate
    usd = (tokens / 1_000_000.0) * PRICE_PER_MILLION_TOKENS
    (usd * BRL_RATE).round(2)
  end

  # Workers limitado ao pool do DB para evitar "all pooled connections were in use"
  def safe_workers(requested = nil)
    pool_size = ActiveRecord::Base.connection_pool.size
    max_safe = [ pool_size - 1, 1 ].max
    requested = (requested || ENV["WORKERS"]).to_i
    requested = max_safe if requested <= 0
    [ requested, max_safe ].min
  end

  desc "Migrate embeddings from candidates/jobs columns to embeddings table (com progresso, % e ETA)"
  task migrate_with_progress: :environment do
    load Rails.root.join("scripts/embedding_migrate.rb")
  end

  desc "Migrate embeddings from candidates/jobs columns to embeddings table (silencioso)"
  task migrate: :environment do
    migrate_candidates
    migrate_jobs
  end

  desc "Validate migration - compare counts old vs embeddings table (ou só embeddings se coluna removida). ENV: ACCOUNT_ID, TENANT"
  task validate: :environment do
    puts "Tenants: #{ENV['ACCOUNT_ID'].present? ? "ACCOUNT_ID=#{ENV['ACCOUNT_ID']}" : ENV['TENANT'].present? ? "TENANT=#{ENV['TENANT']}" : 'todos'}"
    embeddings_account_scope.find_each do |account|
      Apartment::Tenant.switch!(account.tenant)

      new_c = Embedding.for_candidates.count
      if Candidate.column_names.include?("embedding")
        old_c = Candidate.unscope(:select).where.not(embedding: nil).count
        status_c = old_c == new_c ? "✅" : "❌"
        puts "[#{account.tenant}] Candidates: #{status_c} old=#{old_c} embeddings=#{new_c}"
      else
        puts "[#{account.tenant}] Candidates: embeddings=#{new_c}"
      end

      new_j = Embedding.for_jobs.count
      if Job.column_names.include?("embedding")
        old_j = Job.unscope(:select).where.not(embedding: nil).count
        status_j = old_j == new_j ? "✅" : "❌"
        puts "[#{account.tenant}] Jobs: #{status_j} old=#{old_j} embeddings=#{new_j}"
      else
        puts "[#{account.tenant}] Jobs: embeddings=#{new_j}"
      end
    end
  end

  def migrate_candidates
    embeddings_account_scope.find_each do |account|
      Apartment::Tenant.switch!(account.tenant)
      next unless Candidate.column_names.include?("embedding")

      total = Candidate.unscope(:select).where.not(embedding: nil).count
      next if total.zero?

      migrated = 0
      errors = 0
      puts "\n[#{account.tenant}] Migrando #{total} candidates..."

      Candidate.unscope(:select)
        .where.not(embedding: nil)
        .select(:id, :embedding, :updated_at)
        .find_in_batches(batch_size: 500) do |batch|
          records = batch.map do |c|
            {
              reference_type: "Candidate",
              reference_id: c.id,
              embedding: c.embedding,
              model_version: "gemini-embedding-001",
              dimensions: 768,
              created_at: c.updated_at,
              updated_at: c.updated_at
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
            puts "  Erro no batch: #{e.message}"
          end
          print "\r  Progresso: #{migrated}/#{total} (#{errors} erros)"
        end

      puts "\n  ✅ Concluído: #{migrated} migrados, #{errors} erros"
    end
  end

  def migrate_jobs
    embeddings_account_scope.find_each do |account|
      Apartment::Tenant.switch!(account.tenant)
      next unless Job.column_names.include?("embedding")

      total = Job.unscope(:select).where.not(embedding: nil).count
      next if total.zero?

      migrated = 0
      puts "\n[#{account.tenant}] Migrando #{total} jobs..."

      Job.unscope(:select)
        .where.not(embedding: nil)
        .select(:id, :embedding, :updated_at)
        .find_in_batches(batch_size: 500) do |batch|
          records = batch.map do |j|
            {
              reference_type: "Job",
              reference_id: j.id,
              embedding: j.embedding,
              model_version: "gemini-embedding-001",
              dimensions: 768,
              created_at: j.updated_at,
              updated_at: j.updated_at
            }
          end

          Embedding.upsert_all(
            records,
            unique_by: %i[reference_type reference_id],
            update_only: [ :embedding ]
          )
          migrated += batch.size
          print "\r  Progresso: #{migrated}/#{total}"
        end

      puts "\n  ✅ Concluído"
    end
  end

  desc "Re-embed all candidates with Gemini 768 dims (PARALLEL - FAST). ENV: ACCOUNT_ID, TENANT, WORKERS, AVG_TOKENS, EST_RATE"
  task sync_all_candidates_parallel: :environment do
    require "parallel"

    pool_size = ActiveRecord::Base.connection_pool.size
    workers = safe_workers(ENV["WORKERS"])
    scope = embeddings_account_scope

    puts "Workers: #{workers} (pool DB: #{pool_size}; use WORKERS=N e DB_POOL/RAILS_MAX_THREADS maior para mais paralelo)"
    puts ""

    # Prévia: total de candidatos e estimativas
    global_total = 0
    scope.find_each do |account|
      Apartment::Tenant.switch(account.tenant) do
        global_total += Candidate.where(is_deleted: false).count
      end
    end

    puts "Tenants: #{ENV['ACCOUNT_ID'].present? ? "ACCOUNT_ID=#{ENV['ACCOUNT_ID']}" : ENV['TENANT'].present? ? "TENANT=#{ENV['TENANT']}" : 'todos'}"
    puts "Total de candidatos: #{global_total}"
    if global_total.positive?
      eta_sec = global_total / estimated_rate_per_sec
      puts "Tempo estimado (inicial): ~#{format_duration(eta_sec)} (#{estimated_rate_per_sec} c/s)"
      puts "Custo estimado (aprox.): ~R$ #{estimated_cost_brl(global_total)} (#{avg_tokens_per_candidate} tokens/candidato, $#{PRICE_PER_MILLION_TOKENS}/M)"
    end
    puts "429 (rate limit Gemini): retentado automaticamente com backoff (até 5x). Se persistir, reduza WORKERS."
    puts ""

    global_start_time = Time.now
    global_processed = 0
    global_errors = 0

    scope.find_each do |account|
      puts "\n🚀 Account #{account.id} (#{account.name}) — tenant: #{account.tenant}"
      Apartment::Tenant.switch(account.tenant) do
        ids = Candidate.where(is_deleted: false).pluck(:id)
        next if ids.empty?

        total = ids.size
        processed = Concurrent::AtomicFixnum.new(0)
        errors = Concurrent::AtomicFixnum.new(0)
        account_start_time = Time.now
        last_update = Time.now

        mutex = Mutex.new

        Parallel.each(ids, in_threads: workers) do |candidate_id|
          begin
            Candidates::EmbeddingSyncJob.perform_now(candidate_id, nil, account.id)
            current = processed.increment

            mutex.synchronize do
              if Time.now - last_update > 2 || current == total
                elapsed = Time.now - account_start_time
                rate = elapsed > 0 ? current / elapsed : 0
                remaining = total - current
                eta_sec = rate > 0 ? remaining / rate : 0
                pct = (current.to_f / total * 100).round(1)

                print "\r  📊 #{current}/#{total} (#{pct}%) | #{rate.round(2)} c/s | ETA: #{format_duration(eta_sec)} | Erros: #{errors.value}      "
                last_update = Time.now
              end
            end
          rescue => e
            errors.increment
            puts "\n⚠️  ERROR candidate #{candidate_id}: #{e.message}"
          end
        end

        account_time = (Time.now - account_start_time).round(1)
        puts "\n✅ Account #{account.id}: #{processed.value}/#{total} processados (#{errors.value} erros) em #{format_duration(account_time)}"
        global_processed += processed.value
        global_errors += errors.value
      end
    end

    total_time = (Time.now - global_start_time).round(1)
    rate_final = total_time.positive? ? (global_processed.to_f / total_time).round(2) : 0
    puts "\n" + "="*70
    puts "✓ CONCLUÍDO!"
    puts "Total: #{global_processed}/#{global_total} candidatos processados"
    puts "Erros: #{global_errors}"
    puts "Tempo total: #{format_duration(total_time)} (#{rate_final} c/s)"
    if global_processed.positive?
      puts "Custo estimado (aprox.): ~R$ #{estimated_cost_brl(global_processed)} (#{avg_tokens_per_candidate} tokens/candidato)"
    end
    puts "="*70
  end

  desc "Re-embed all candidates with Gemini 768 dims (SEQUENTIAL - SAFE). ENV: ACCOUNT_ID, TENANT"
  task sync_all_candidates: :environment do
    puts "Tenants: #{ENV['ACCOUNT_ID'].present? ? "ACCOUNT_ID=#{ENV['ACCOUNT_ID']}" : ENV['TENANT'].present? ? "TENANT=#{ENV['TENANT']}" : 'todos'}"
    embeddings_account_scope.find_each do |account|
      puts "\nAccount #{account.id} (#{account.name}) — tenant: #{account.tenant}"
      Apartment::Tenant.switch(account.tenant) do
        total = Candidate.where(is_deleted: false).count
        processed = 0
        errors = 0

        Candidate.where(is_deleted: false).find_in_batches(batch_size: 100) do |batch|
          batch.each do |candidate|
            begin
              Candidates::EmbeddingSyncJob.perform_now(candidate.id, nil, account.id)
              processed += 1
              print "\rProgress: #{processed}/#{total} (#{(processed.to_f / total * 100).round(1)}%)"
            rescue => e
              errors += 1
              puts "\nERROR candidate #{candidate.id}: #{e.message}"
            end
            sleep 1
          end
        end

        puts "\nAccount #{account.id} done: #{processed}/#{total} (#{errors} errors)"
      end
    end

    puts "\n✓ Done (sequential candidates)"
  end

  desc "Re-embed all jobs with Gemini 768 dims (PARALLEL - FAST). ENV: ACCOUNT_ID, TENANT, WORKERS"
  task sync_all_jobs_parallel: :environment do
    require "parallel"

    pool_size = ActiveRecord::Base.connection_pool.size
    workers = safe_workers(ENV["WORKERS"])
    puts "Workers: #{workers} (pool DB: #{pool_size})"
    puts ""

    global_start_time = Time.now
    global_processed = 0
    global_errors = 0
    global_total = 0

    puts "Tenants: #{ENV['ACCOUNT_ID'].present? ? "ACCOUNT_ID=#{ENV['ACCOUNT_ID']}" : ENV['TENANT'].present? ? "TENANT=#{ENV['TENANT']}" : 'todos'}"
    embeddings_account_scope.find_each do |account|
      puts "\n🚀 Account #{account.id} (#{account.name}) — tenant: #{account.tenant}"
      Apartment::Tenant.switch(account.tenant) do
        ids = Job.where(is_deleted: false).pluck(:id)
        next if ids.empty?

        total = ids.size
        global_total += total
        processed = Concurrent::AtomicFixnum.new(0)
        errors = Concurrent::AtomicFixnum.new(0)
        account_start_time = Time.now
        last_update = Time.now

        mutex = Mutex.new

        Parallel.each(ids, in_threads: workers) do |job_id|
          begin
            Jobs::EmbeddingSyncJob.perform_now(job_id, nil, account.id)
            current = processed.increment

            mutex.synchronize do
              if Time.now - last_update > 2 || current == total
                elapsed = Time.now - account_start_time
                rate = elapsed > 0 ? current / elapsed : 0
                remaining = total - current
                eta = rate > 0 ? remaining / rate : 0
                pct = (current.to_f / total * 100).round(1)

                print "\r  📊 Progresso: #{current}/#{total} (#{pct}%) | #{rate.round(2)} j/s | ETA: #{eta.round(0)}s | Erros: #{errors.value}      "
                last_update = Time.now
              end
            end
          rescue => e
            errors.increment
            puts "\n⚠️  ERROR job #{job_id}: #{e.message}"
          end
        end

        account_time = (Time.now - account_start_time).round(1)
        puts "\n✅ Account #{account.id}: #{processed.value}/#{total} processados (#{errors.value} erros) em #{account_time}s"
        global_processed += processed.value
        global_errors += errors.value
      end
    end

    total_time = (Time.now - global_start_time).round(1)
    puts "\n" + "="*70
    puts "✓ CONCLUÍDO!"
    puts "Total: #{global_processed}/#{global_total} jobs processados"
    puts "Erros: #{global_errors}"
    puts "Tempo total: #{total_time}s (#{(global_processed.to_f / total_time).round(2)} j/s)"
    puts "="*70
  end

  desc "Re-embed all jobs with Gemini 768 dims (SEQUENTIAL - SAFE). ENV: ACCOUNT_ID, TENANT"
  task sync_all_jobs: :environment do
    puts "Tenants: #{ENV['ACCOUNT_ID'].present? ? "ACCOUNT_ID=#{ENV['ACCOUNT_ID']}" : ENV['TENANT'].present? ? "TENANT=#{ENV['TENANT']}" : 'todos'}"
    embeddings_account_scope.find_each do |account|
      puts "\nAccount #{account.id} (#{account.name}) — tenant: #{account.tenant}"
      Apartment::Tenant.switch(account.tenant) do
        total = Job.where(is_deleted: false).count
        processed = 0
        errors = 0

        Job.where(is_deleted: false).find_in_batches(batch_size: 100) do |batch|
          batch.each do |job|
            begin
              Jobs::EmbeddingSyncJob.perform_now(job.id, nil, account.id)
              processed += 1
              print "\rProgress: #{processed}/#{total} (#{(processed.to_f / total * 100).round(1)}%)"
            rescue => e
              errors += 1
              puts "\nERROR job #{job.id}: #{e.message}"
            end
            sleep 1
          end
        end

        puts "\nAccount #{account.id} done: #{processed}/#{total} (#{errors} errors)"
      end
    end

    puts "\n✓ Done (sequential jobs)"
  end

  desc "Estimativa de custo de re-embedding (amostra por tenant). ENV: ACCOUNT_ID, TENANT"
  task estimate_cost: :environment do
    ENV["FROM_RAKE"] = "1"
    load Rails.root.join("scripts/embedding_cost_calculator.rb")
    puts "Tenants: #{ENV['ACCOUNT_ID'].present? ? "ACCOUNT_ID=#{ENV['ACCOUNT_ID']}" : ENV['TENANT'].present? ? "TENANT=#{ENV['TENANT']}" : 'todos'}"
    embeddings_account_scope.find_each do |account|
      Apartment::Tenant.switch(account.tenant) do
        puts "\n>>> Account #{account.id} (#{account.name}) — tenant: #{account.tenant}"
        EmbeddingCostCalculator.run
      end
    end
  end

  desc "Check embedding dimensions (usa tabela embeddings). ENV: ACCOUNT_ID, TENANT"
  task check_dimensions: :environment do
    puts "Tenants: #{ENV['ACCOUNT_ID'].present? ? "ACCOUNT_ID=#{ENV['ACCOUNT_ID']}" : ENV['TENANT'].present? ? "TENANT=#{ENV['TENANT']}" : 'todos'}"
    embeddings_account_scope.find_each do |account|
      Apartment::Tenant.switch(account.tenant) do
        c_with_emb = Embedding.for_candidates.count
        c_total = Candidate.where(is_deleted: false).count
        c_sample = Embedding.for_candidates.first
        c_dim = c_sample&.embedding&.length || 0

        j_with_emb = Embedding.for_jobs.count
        j_total = Job.where(is_deleted: false).count
        j_sample = Embedding.for_jobs.first
        j_dim = j_sample&.embedding&.length || 0

        puts "Account #{account.id} (#{account.name}):"
        puts "  Candidates: #{c_with_emb}/#{c_total} embedded (dim: #{c_dim})"
        puts "  Jobs: #{j_with_emb}/#{j_total} embedded (dim: #{j_dim})"
      end
    end
  end

  desc "Re-embed single candidate"
  task :sync_candidate, %i[candidate_id account_id] => :environment do |_t, args|
    account = Account.find(args[:account_id])

    Apartment::Tenant.switch(account.tenant) do
      candidate = Candidate.find(args[:candidate_id])
      puts "Re-embedding candidate #{candidate.id} (#{candidate.name})..."

      Candidates::EmbeddingSyncJob.perform_now(candidate.id, nil, account.id)

      candidate.reload
      dim = candidate.embedding_record&.embedding&.length || candidate.vector_embedding&.length
      puts "✓ Done! Embedding dimension: #{dim || 'nil'}"
    end
  end

  desc "Re-embed single job"
  task :sync_job, %i[job_id account_id] => :environment do |_t, args|
    account = Account.find(args[:account_id])

    Apartment::Tenant.switch(account.tenant) do
      job = Job.find(args[:job_id])
      puts "Re-embedding job #{job.id} (#{job.title})..."

      Jobs::EmbeddingSyncJob.perform_now(job.id, nil, account.id)

      job.reload
      dim = job.embedding_record&.embedding&.length || job.vector_embedding&.length
      puts "✓ Done! Embedding dimension: #{dim || 'nil'}"
    end
  end

  desc "Re-embed candidates with curriculum_text. ENV: ACCOUNT_ID, TENANT"
  task sync_candidates_with_curriculum_text: :environment do
    started_at = Time.now
    total_processed = 0
    total_errors = 0

    puts "Tenants: #{ENV['ACCOUNT_ID'].present? ? "ACCOUNT_ID=#{ENV['ACCOUNT_ID']}" : ENV['TENANT'].present? ? "TENANT=#{ENV['TENANT']}" : 'todos'}"
    embeddings_account_scope.find_each do |account|
      puts "Processing account: #{account.id} (#{account.name}) — tenant: #{account.tenant}"

      Apartment::Tenant.switch(account.tenant) do
        ids = Candidate.where(is_deleted: false)
                       .where.not(curriculum_text: [ nil, "" ])
                       .pluck(:id)
        next if ids.empty?

        total = ids.size
        processed = 0
        errors = 0
        account_started_at = Time.now

        ids.each do |candidate_id|
          begin
            Candidates::EmbeddingSyncJob.perform_now(candidate_id, nil, account.id)
            processed += 1
            if processed == total || (processed % 10).zero?
              elapsed = Time.now - account_started_at
              rate = processed.positive? && elapsed.positive? ? processed / elapsed : 0.0
              remaining = total - processed
              eta = rate.positive? ? remaining / rate : nil
              pct = ((processed.to_f / total) * 100).round(1)

              puts "  Progress: #{processed}/#{total} (#{pct}%) | rate: #{rate.round(2)} c/s | eta: #{eta ? eta.round(1) : 'n/a'}s"
            end
          rescue => e
            errors += 1
            puts "\nERROR candidate #{candidate_id}: #{e.message}"
          end
        end

        puts "Account #{account.id} done: #{processed}/#{total} candidates (#{errors} errors)"
        total_processed += processed
        total_errors += errors
      end
    end

    total_time = (Time.now - started_at).round(1)
    puts "\n✓ Candidates with curriculum_text re-embedded!"
    puts "Total processed: #{total_processed} (#{total_errors} errors)"
    puts "Total time: #{total_time}s"
  end
end
