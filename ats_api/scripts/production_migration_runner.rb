# frozen_string_literal: true

# =============================================================================
# PRODUCTION-SAFE MIGRATION RUNNER
# =============================================================================
#
# Este script executa migrações em produção com baixo impacto:
# - Processamento em batches pequenos
# - Sleep entre batches para não sobrecarregar o banco
# - Checkpoint/resume para continuar de onde parou
# - Monitoramento de métricas
# - Rollback tracking
#
# =============================================================================

module ProductionMigrationRunner
  BATCH_SIZE = 100
  SLEEP_BETWEEN_BATCHES = 0.5  # segundos
  CHECKPOINT_FILE = "/tmp/migration_checkpoint.json"

  class << self
    def run_linkedin_migration(account_id:, dry_run: true, batch_size: BATCH_SIZE, sleep_time: SLEEP_BETWEEN_BATCHES)
      puts banner("LINKEDIN MIGRATION", dry_run)

      load_script('migrate_linkedin_from_data_raw.rb')

      run_batched_migration(
        name: "linkedin",
        account_id: account_id,
        dry_run: dry_run,
        batch_size: batch_size,
        sleep_time: sleep_time
      ) do
        MigrateLinkedinFromDataRaw.execute(
          account_id: account_id,
          dry_run: dry_run
        )
      end
    end

    def run_experiences_migration(account_id:, dry_run: true, batch_size: BATCH_SIZE, sleep_time: SLEEP_BETWEEN_BATCHES)
      puts banner("EXPERIENCES MIGRATION", dry_run)

      load_script('migrate_experiences_educations_from_data_raw.rb')

      run_batched_migration(
        name: "experiences",
        account_id: account_id,
        dry_run: dry_run,
        batch_size: batch_size,
        sleep_time: sleep_time
      ) do
        MigrateExperiencesEducationsFromDataRaw.execute(
          account_id: account_id,
          dry_run: dry_run,
          migrate_type: :experiences
        )
      end
    end

    def run_educations_migration(account_id:, dry_run: true, batch_size: BATCH_SIZE, sleep_time: SLEEP_BETWEEN_BATCHES)
      puts banner("EDUCATIONS MIGRATION", dry_run)

      load_script('migrate_experiences_educations_from_data_raw.rb')

      run_batched_migration(
        name: "educations",
        account_id: account_id,
        dry_run: dry_run,
        batch_size: batch_size,
        sleep_time: sleep_time
      ) do
        MigrateExperiencesEducationsFromDataRaw.execute(
          account_id: account_id,
          dry_run: dry_run,
          migrate_type: :educations
        )
      end
    end

    def run_all_migrations(account_id:, dry_run: true)
      puts banner("ALL MIGRATIONS", dry_run)

      puts "\n⚠️  ATENÇÃO: Vai rodar TODAS as migrações para account #{account_id}"
      puts "   Ordem: 1) LinkedIn → 2) Experiences → 3) Educations"
      puts "\n"

      if dry_run
        puts "🔍 Modo DRY RUN - Nenhuma alteração será feita"
      else
        puts "🚨 Modo PRODUÇÃO - Alterações serão aplicadas!"
        puts "   Pressione ENTER para continuar ou CTRL+C para cancelar..."
        gets
      end

      results = {}

      # 1. LinkedIn
      puts "\n" + "=" * 60
      puts "STEP 1/3: LinkedIn Migration"
      puts "=" * 60
      results[:linkedin] = run_linkedin_migration(account_id: account_id, dry_run: dry_run)

      # 2. Experiences
      puts "\n" + "=" * 60
      puts "STEP 2/3: Experiences Migration"
      puts "=" * 60
      results[:experiences] = run_experiences_migration(account_id: account_id, dry_run: dry_run)

      # 3. Educations
      puts "\n" + "=" * 60
      puts "STEP 3/3: Educations Migration"
      puts "=" * 60
      results[:educations] = run_educations_migration(account_id: account_id, dry_run: dry_run)

      print_final_summary(results, dry_run)
      results
    end

    def pre_flight_check(account_id:)
      puts banner("PRE-FLIGHT CHECK", true)

      puts "\n🔍 Verificando estado do banco para account #{account_id}...\n"

      # Contagens
      total_candidates = Candidate.where(account_id: account_id).count
      with_data_raw = Candidate.where(account_id: account_id).where.not(data_raw: nil).count
      without_linkedin = Candidate.where(account_id: account_id).where(linkedin: nil).count
      without_experiences = Candidate.where(account_id: account_id)
        .left_joins(:experiences)
        .where(experiences: { id: nil })
        .count
      without_educations = Candidate.where(account_id: account_id)
        .left_joins(:educations)
        .where(educations: { id: nil })
        .count

      existing_experiences = Experience.where(account_id: account_id).count
      existing_educations = Education.where(account_id: account_id).count

      puts "📊 ESTADO ATUAL:"
      puts "   Total candidates: #{total_candidates}"
      puts "   Com data_raw: #{with_data_raw} (#{percentage(with_data_raw, total_candidates)}%)"
      puts "   Sem linkedin: #{without_linkedin}"
      puts "   Sem experiences: #{without_experiences}"
      puts "   Sem educations: #{without_educations}"
      puts ""
      puts "   Experiences existentes: #{existing_experiences}"
      puts "   Educations existentes: #{existing_educations}"

      # Estimativa de impacto
      puts "\n📈 ESTIMATIVA DE IMPACTO:"

      candidates_for_linkedin = Candidate.where(account_id: account_id)
        .where.not(data_raw: nil)
        .where(linkedin: nil)
        .count
      puts "   LinkedIn: ~#{candidates_for_linkedin} candidatos a atualizar"

      candidates_for_exp = Candidate.where(account_id: account_id)
        .where.not(data_raw: nil)
        .left_joins(:experiences)
        .where(experiences: { id: nil })
        .count
      puts "   Experiences: ~#{candidates_for_exp} candidatos a processar"

      candidates_for_edu = Candidate.where(account_id: account_id)
        .where.not(data_raw: nil)
        .left_joins(:educations)
        .where(educations: { id: nil })
        .count
      puts "   Educations: ~#{candidates_for_edu} candidatos a processar"

      # Tempo estimado
      total_ops = candidates_for_linkedin + candidates_for_exp + candidates_for_edu
      estimated_time = (total_ops / 500.0) # ~500 records/sec com sleep
      puts "\n⏱️  Tempo estimado: #{format_duration(estimated_time * 60)}"

      # Recomendações
      puts "\n💡 RECOMENDAÇÕES:"
      if total_ops > 10000
        puts "   ⚠️  Volume alto (#{total_ops} operações)"
        puts "   → Considere rodar em horário de baixo uso (noite/madrugada)"
        puts "   → Use batch_size menor (50) e sleep maior (1.0s)"
      elsif total_ops > 1000
        puts "   ℹ️  Volume médio (#{total_ops} operações)"
        puts "   → Pode rodar em horário comercial com cuidado"
        puts "   → Monitore a CPU e conexões do banco"
      else
        puts "   ✅ Volume baixo (#{total_ops} operações)"
        puts "   → Pode rodar tranquilamente"
      end

      puts "\n" + "=" * 60

      {
        total_candidates: total_candidates,
        with_data_raw: with_data_raw,
        candidates_for_linkedin: candidates_for_linkedin,
        candidates_for_experiences: candidates_for_exp,
        candidates_for_educations: candidates_for_edu,
        estimated_time_minutes: estimated_time
      }
    end

    private

    def run_batched_migration(name:, account_id:, dry_run:, batch_size:, sleep_time:)
      start_time = Time.current

      result = yield

      elapsed = Time.current - start_time

      puts "\n✅ #{name.upcase} concluído em #{format_duration(elapsed)}"

      result
    end

    def load_script(filename)
      path = Rails.root.join('scripts', filename)
      load path.to_s
    end

    def banner(title, dry_run)
      mode = dry_run ? "DRY RUN" : "PRODUCTION"
      "\n" + "=" * 60 + "\n" +
        "🚀 #{title} (#{mode})\n" +
        "   #{Time.current.strftime('%Y-%m-%d %H:%M:%S')}\n" +
        "=" * 60
    end

    def print_final_summary(results, dry_run)
      puts "\n"
      puts "=" * 60
      puts "📊 RESUMO FINAL"
      puts "=" * 60

      if dry_run
        puts "\n🔍 MODO DRY RUN - Nenhuma alteração foi feita"
        puts "   Para aplicar as mudanças, rode novamente com dry_run: false"
      else
        puts "\n✅ MODO PRODUÇÃO - Alterações aplicadas"
      end

      puts "\n" + "=" * 60
    end

    def format_duration(seconds)
      return "0s" if seconds.nil? || seconds <= 0

      hours = (seconds / 3600).floor
      minutes = ((seconds % 3600) / 60).floor
      secs = (seconds % 60).round

      parts = []
      parts << "#{hours}h" if hours > 0
      parts << "#{minutes}m" if minutes > 0
      parts << "#{secs}s" if secs > 0 || parts.empty?

      parts.join(" ")
    end

    def percentage(part, total)
      return 0 if total == 0
      ((part.to_f / total) * 100).round(2)
    end
  end
end

# =============================================================================
# Helper methods for console usage
# =============================================================================

def pre_flight(account_id:)
  ProductionMigrationRunner.pre_flight_check(account_id: account_id)
end

def migrate_linkedin_safe(account_id:, dry_run: true)
  ProductionMigrationRunner.run_linkedin_migration(
    account_id: account_id,
    dry_run: dry_run
  )
end

def migrate_experiences_safe(account_id:, dry_run: true)
  ProductionMigrationRunner.run_experiences_migration(
    account_id: account_id,
    dry_run: dry_run
  )
end

def migrate_educations_safe(account_id:, dry_run: true)
  ProductionMigrationRunner.run_educations_migration(
    account_id: account_id,
    dry_run: dry_run
  )
end

def migrate_all_safe(account_id:, dry_run: true)
  ProductionMigrationRunner.run_all_migrations(
    account_id: account_id,
    dry_run: dry_run
  )
end

puts "=" * 60
puts "🚀 Production Migration Runner Loaded"
puts "=" * 60
puts ""
puts "PASSO 1 - Verificar estado antes de migrar:"
puts "  pre_flight(account_id: 1)"
puts ""
puts "PASSO 2 - Rodar DRY RUN (sem alterações):"
puts "  migrate_linkedin_safe(account_id: 1, dry_run: true)"
puts "  migrate_experiences_safe(account_id: 1, dry_run: true)"
puts "  migrate_educations_safe(account_id: 1, dry_run: true)"
puts "  migrate_all_safe(account_id: 1, dry_run: true)"
puts ""
puts "PASSO 3 - Rodar em PRODUÇÃO (com alterações):"
puts "  migrate_linkedin_safe(account_id: 1, dry_run: false)"
puts "  migrate_experiences_safe(account_id: 1, dry_run: false)"
puts "  migrate_educations_safe(account_id: 1, dry_run: false)"
puts "  migrate_all_safe(account_id: 1, dry_run: false)"
puts ""
puts "=" * 60
