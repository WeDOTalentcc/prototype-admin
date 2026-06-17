# frozen_string_literal: true

# Script para recalcular estatísticas agregadas de sourcings existentes
#
# USO:
#   rails runner scripts/recalculate_sourcing_stats.rb
#
# OU no Rails Console:
#   load 'scripts/recalculate_sourcing_stats.rb'
#

module SourcingStatsRecalculator
  extend self

  def recalculate_all
    puts "🔄 Iniciando recálculo de estatísticas de sourcings..."
    puts "=" * 80

    sourcings = Sourcing.where(status: "done", is_deleted: false)
    total = sourcings.count

    puts "📊 Total de sourcings para recalcular: #{total}"
    puts "=" * 80
    puts ""

    return puts "✅ Nenhum sourcing para recalcular." if total.zero?

    success_count = 0
    error_count = 0
    skipped_count = 0

    sourcings.find_each.with_index do |sourcing, index|
      begin
        progress = ((index + 1).to_f / total * 100).round(1)
        print "\r[#{progress}%] Processando sourcing ##{sourcing.id} (#{sourcing.query})..."

        # Verificar se tem profiles
        profiles_count = sourcing.sourced_profile_sourcings.where(is_deleted: false).count

        if profiles_count.zero?
          skipped_count += 1
          next
        end

        # Calcular e salvar stats
        sourcing.refresh_aggregated_stats!
        success_count += 1

      rescue => e
        error_count += 1
        puts "\n❌ Erro ao processar sourcing ##{sourcing.id}: #{e.message}"
        Rails.logger.error "[SourcingStatsRecalculator] Error on sourcing ##{sourcing.id}: #{e.message}"
        Rails.logger.error e.backtrace.join("\n")
      end
    end

    puts "\n"
    puts "=" * 80
    puts "✅ Recálculo concluído!"
    puts "   Total processado: #{total}"
    puts "   ✅ Sucesso: #{success_count}"
    puts "   ⏭️  Pulados (sem profiles): #{skipped_count}"
    puts "   ❌ Erros: #{error_count}"
    puts "=" * 80
  end

  def recalculate_by_id(sourcing_id)
    sourcing = Sourcing.find(sourcing_id)

    unless sourcing.status == "done"
      return puts "⚠️  Sourcing ##{sourcing_id} não está concluído (status: #{sourcing.status})"
    end

    profiles_count = sourcing.sourced_profile_sourcings.where(is_deleted: false).count

    if profiles_count.zero?
      return puts "⚠️  Sourcing ##{sourcing_id} não possui profiles"
    end

    puts "🔄 Recalculando stats para sourcing ##{sourcing_id}..."
    stats = sourcing.refresh_aggregated_stats!
    puts "✅ Stats recalculadas com sucesso!"
    puts ""
    puts "📊 Resumo das estatísticas:"
    puts "   Total de candidatos: #{stats.dig(:counts, :total)}"
    puts "   Score médio: #{stats.dig(:score_stats, :average)}"
    puts "   Experiência média: #{stats.dig(:experience_stats, :average)} anos"
    puts "   Skills únicas: #{stats.dig(:skills_distribution, :unique_count)}"
    puts ""
  rescue ActiveRecord::RecordNotFound
    puts "❌ Sourcing ##{sourcing_id} não encontrado"
  rescue => e
    puts "❌ Erro ao recalcular stats: #{e.message}"
    Rails.logger.error "[SourcingStatsRecalculator] Error: #{e.message}"
    Rails.logger.error e.backtrace.join("\n")
  end

  def recalculate_recent(days: 7)
    puts "🔄 Recalculando stats dos últimos #{days} dias..."
    puts "=" * 80

    sourcings = Sourcing.where(status: "done", is_deleted: false)
                       .where("created_at >= ?", days.days.ago)

    total = sourcings.count
    puts "📊 Total encontrado: #{total}"
    puts ""

    return puts "✅ Nenhum sourcing para recalcular." if total.zero?

    success_count = 0
    error_count = 0
    skipped_count = 0

    sourcings.find_each.with_index do |sourcing, index|
      begin
        progress = ((index + 1).to_f / total * 100).round(1)
        print "\r[#{progress}%] Processando sourcing ##{sourcing.id}..."

        profiles_count = sourcing.sourced_profile_sourcings.where(is_deleted: false).count

        if profiles_count.zero?
          skipped_count += 1
          next
        end

        sourcing.refresh_aggregated_stats!
        success_count += 1

      rescue => e
        error_count += 1
        puts "\n❌ Erro ao processar sourcing ##{sourcing.id}: #{e.message}"
      end
    end

    puts "\n"
    puts "=" * 80
    puts "✅ Recálculo concluído!"
    puts "   ✅ Sucesso: #{success_count}"
    puts "   ⏭️  Pulados: #{skipped_count}"
    puts "   ❌ Erros: #{error_count}"
    puts "=" * 80
  end

  def enqueue_all_async
    puts "🔄 Enfileirando recálculo assíncrono de todos os sourcings..."
    puts "=" * 80

    sourcings = Sourcing.where(status: "done", is_deleted: false)
    total = sourcings.count

    puts "📊 Total de sourcings para enfileirar: #{total}"
    puts ""

    return puts "✅ Nenhum sourcing para enfileirar." if total.zero?

    enqueued = 0

    sourcings.find_each do |sourcing|
      profiles_count = sourcing.sourced_profile_sourcings.where(is_deleted: false).count
      next if profiles_count.zero?

      sourcing.enqueue_stats_calculation
      enqueued += 1
      print "\r✅ Enfileirados: #{enqueued}/#{total}"
    end

    puts "\n"
    puts "=" * 80
    puts "✅ Jobs enfileirados com sucesso!"
    puts "   Total: #{enqueued}"
    puts "   Verifique o Sidekiq para acompanhar o processamento."
    puts "=" * 80
  end

  def show_stats_summary(sourcing_id)
    sourcing = Sourcing.find(sourcing_id)
    stats = sourcing.aggregated_stats

    if stats.blank?
      return puts "⚠️  Sourcing ##{sourcing_id} não possui estatísticas calculadas"
    end

    puts "📊 Estatísticas do Sourcing ##{sourcing_id}: #{sourcing.query}"
    puts "=" * 80
    puts ""

    puts "📈 CONTAGENS:"
    puts "   Total de candidatos: #{stats.dig('counts', 'total')}"
    puts "   Com score: #{stats.dig('counts', 'with_score')}"
    puts "   Do LinkedIn: #{stats.dig('counts', 'from_linkedin')}"
    puts "   Do Local: #{stats.dig('counts', 'from_local')}"
    puts ""

    puts "🎯 SCORES:"
    puts "   Média: #{stats.dig('score_stats', 'average')}"
    puts "   Mediana: #{stats.dig('score_stats', 'median')}"
    puts "   Mín/Máx: #{stats.dig('score_stats', 'min')} / #{stats.dig('score_stats', 'max')}"
    puts "   Acima de 70: #{stats.dig('score_stats', 'above_70')}"
    puts "   Acima de 80: #{stats.dig('score_stats', 'above_80')}"
    puts ""

    puts "💼 EXPERIÊNCIA:"
    puts "   Média: #{stats.dig('experience_stats', 'average')} anos"
    puts "   Junior: #{stats.dig('experience_stats', 'distribution', 'junior')}"
    puts "   Pleno: #{stats.dig('experience_stats', 'distribution', 'pleno')}"
    puts "   Senior: #{stats.dig('experience_stats', 'distribution', 'senior')}"
    puts "   Specialist: #{stats.dig('experience_stats', 'distribution', 'specialist')}"
    puts ""

    puts "🔧 TOP 5 SKILLS:"
    top_skills = stats.dig('skills_distribution', 'top_skills') || {}
    top_skills.first(5).each_with_index do |(skill, count), index|
      puts "   #{index + 1}. #{skill.capitalize}: #{count}"
    end
    puts ""

    puts "📍 TOP 5 CIDADES:"
    top_cities = stats.dig('location_distribution', 'by_city') || {}
    top_cities.first(5).each_with_index do |(city, count), index|
      puts "   #{index + 1}. #{city.capitalize}: #{count}"
    end
    puts ""

    puts "💰 SALÁRIO CLT:"
    puts "   Média: R$ #{stats.dig('salary_stats', 'clt', 'average')}"
    puts "   Mediana: R$ #{stats.dig('salary_stats', 'clt', 'median')}"
    puts ""

    puts "🏠 TRABALHO REMOTO:"
    puts "   Aceita remoto: #{stats.dig('remote_work_stats', 'accepts_remote')}"
    puts "   Prefere presencial: #{stats.dig('remote_work_stats', 'prefers_onsite')}"
    puts "   Aceita híbrido: #{stats.dig('remote_work_stats', 'remote_with_mobility')}"
    puts ""

    puts "📞 CONTATO:"
    puts "   Com email: #{stats.dig('contact_stats', 'with_email')}"
    puts "   Com telefone: #{stats.dig('contact_stats', 'with_phone')}"
    puts "   Contactáveis: #{stats.dig('contact_stats', 'contactable')}"
    puts ""

    puts "=" * 80

  rescue ActiveRecord::RecordNotFound
    puts "❌ Sourcing ##{sourcing_id} não encontrado"
  rescue => e
    puts "❌ Erro ao exibir stats: #{e.message}"
  end
end

# Se executado diretamente via rails runner
if __FILE__ == $0 || defined?(Rails::Console)
  puts ""
  puts "🔧 SOURCING STATS RECALCULATOR"
  puts "=" * 80
  puts ""
  puts "Comandos disponíveis:"
  puts ""
  puts "  # Recalcular TODOS os sourcings (síncrono, pode demorar)"
  puts "  SourcingStatsRecalculator.recalculate_all"
  puts ""
  puts "  # Recalcular sourcings dos últimos 7 dias"
  puts "  SourcingStatsRecalculator.recalculate_recent(days: 7)"
  puts ""
  puts "  # Recalcular um sourcing específico"
  puts "  SourcingStatsRecalculator.recalculate_by_id(211)"
  puts ""
  puts "  # Enfileirar recálculo assíncrono (recomendado para muitos sourcings)"
  puts "  SourcingStatsRecalculator.enqueue_all_async"
  puts ""
  puts "  # Ver resumo das estatísticas de um sourcing"
  puts "  SourcingStatsRecalculator.show_stats_summary(211)"
  puts ""
  puts "=" * 80
  puts ""

  # Se recebeu argumento na linha de comando
  if ARGV.any?
    command = ARGV[0]

    case command
    when "all"
      SourcingStatsRecalculator.recalculate_all
    when "recent"
      days = ARGV[1]&.to_i || 7
      SourcingStatsRecalculator.recalculate_recent(days: days)
    when "async"
      SourcingStatsRecalculator.enqueue_all_async
    when "show"
      sourcing_id = ARGV[1]&.to_i
      if sourcing_id
        SourcingStatsRecalculator.show_stats_summary(sourcing_id)
      else
        puts "❌ Erro: Informe o ID do sourcing"
        puts "   Exemplo: rails runner scripts/recalculate_sourcing_stats.rb show 211"
      end
    when "id"
      sourcing_id = ARGV[1]&.to_i
      if sourcing_id
        SourcingStatsRecalculator.recalculate_by_id(sourcing_id)
      else
        puts "❌ Erro: Informe o ID do sourcing"
        puts "   Exemplo: rails runner scripts/recalculate_sourcing_stats.rb id 211"
      end
    else
      puts "❌ Comando inválido: #{command}"
      puts ""
      puts "Comandos disponíveis:"
      puts "  all     - Recalcula todos os sourcings"
      puts "  recent  - Recalcula sourcings recentes (ex: recent 7)"
      puts "  async   - Enfileira recálculo assíncrono"
      puts "  id      - Recalcula sourcing específico (ex: id 211)"
      puts "  show    - Mostra estatísticas (ex: show 211)"
    end
  end
end
