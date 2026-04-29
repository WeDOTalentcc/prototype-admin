# Script para reindexar qualquer model no Elasticsearch
# Execute: load 'scripts/elasticsearch_reindex.rb'
#
# Uso:
#   ElasticsearchReindex.run(Candidate)
#   ElasticsearchReindex.run(Job)
#   ElasticsearchReindex.run(Candidate, filters: { is_deleted: false })
#   ElasticsearchReindex.run(Candidate, filters: ->(s) { s.where.not(curriculum_text: nil) })

module ElasticsearchReindex
  BATCH_SIZE = 500

  # Eager loading para evitar N+1 queries
  INCLUDES_MAP = {
    "Candidate" => [
      :skills,
      { skill_relationships: :skill },
      { language_relationships: :language },
      { educations: [ :institution, :study_area ] },
      { experiences: [ :occupation, :company ] }
    ],
    "Job" => [ :company, :job_status, :department ]
  }

  # Colunas grandes para excluir do SELECT inicial
  EXCLUDE_COLUMNS = {
    "Candidate" => [ "embedding" ], # curriculum_text é necessário para search_data
    "Job" => [ "embedding" ]
  }

  def self.run(model_class, filters: nil, batch_size: BATCH_SIZE)
    tenant = Apartment::Tenant.current rescue "public"
    model_name = model_class.name

    puts "\n#{'='*60}"
    puts "🔄 REINDEX ELASTICSEARCH (OTIMIZADO)"
    puts "#{'='*60}"
    puts "📦 Model: #{model_name}"
    puts "🏢 Tenant: #{tenant}"

    # Aplicar filtros primeiro para contagem
    scope = model_class.all

    if filters.is_a?(Proc)
      scope = filters.call(scope)
    elsif filters.is_a?(Hash)
      scope = scope.where(filters)
    end

    # Contagem aproximada (muito mais rápido)
    total = fast_count(model_class, scope)
    puts "📊 Registros: ~#{total}"
    puts "📦 Batch: #{batch_size}"

    # Excluir colunas grandes do SELECT
    exclude_cols = EXCLUDE_COLUMNS[model_name]
    if exclude_cols
      cols = model_class.column_names - exclude_cols
      scope = scope.select(cols.map { |c| "#{model_class.table_name}.#{c}" })
      puts "✅ Excluindo colunas: #{exclude_cols.join(', ')}"
    end

    # Aplicar includes para evitar N+1
    includes_for_model = INCLUDES_MAP[model_name]
    if includes_for_model
      scope = scope.includes(*includes_for_model)
      puts "✅ Eager loading ativado"
    end

    puts "#{'='*60}\n"

    return puts "⚠️  Nenhum registro encontrado!" if total == 0

    # Contadores
    processed = 0
    success = 0
    errors = []
    start_time = Time.now

    # Processar em batches
    scope.find_in_batches(batch_size: batch_size) do |batch|
      begin
        # Reindex batch
        model_class.searchkick_index.import(batch)
        success += batch.size
      rescue => e
        # Se batch falhar, tenta individualmente
        batch.each do |record|
          begin
            record.reindex
            success += 1
          rescue => individual_error
            errors << { id: record.id, error: individual_error.message.truncate(100) }
          end
        end
      end

      processed += batch.size
      print_progress(processed, total, start_time, errors.size)
    end

    # Resultado final
    elapsed = Time.now - start_time
    puts "\n\n#{'='*60}"
    puts "✅ REINDEX CONCLUÍDO - #{model_name}"
    puts "#{'='*60}"
    puts "   Total: #{processed} | Sucesso: #{success} | Erros: #{errors.size}"
    puts "   Tempo: #{format_duration(elapsed)} | Velocidade: #{(processed / elapsed).round}/s"
    puts "#{'='*60}"

    # Mostrar erros se houver
    if errors.any?
      puts "\n⚠️  ERROS (primeiros 10):"
      errors.first(10).each { |e| puts "   ID #{e[:id]}: #{e[:error]}" }
      puts "   ... +#{errors.size - 10} erros" if errors.size > 10
    end

    { model: model_name, success: success, errors: errors.size, duration: elapsed }
  end

  def self.print_progress(current, total, start_time, error_count)
    percent = (current.to_f / total * 100).round(1)
    elapsed = Time.now - start_time
    rate = current.to_f / elapsed
    remaining = rate > 0 ? ((total - current) / rate) : 0

    bar_width = 30
    filled = (percent / 100 * bar_width).round
    bar = "█" * filled + "░" * (bar_width - filled)

    status = "\r[#{bar}] #{percent}% | #{current}/#{total} | "
    status += "⏱️  #{format_duration(remaining)} restante"
    status += " | ❌ #{error_count}" if error_count > 0

    print status
    $stdout.flush
  end

  def self.format_duration(seconds)
    return "0s" if seconds <= 0
    h = (seconds / 3600).to_i
    m = ((seconds % 3600) / 60).to_i
    s = (seconds % 60).to_i
    [ h > 0 && "#{h}h", m > 0 && "#{m}m", "#{s}s" ].compact.join(" ")
  end

  # Contagem rápida usando estatísticas do PostgreSQL
  def self.fast_count(model_class, scope)
    # Se tem filtros, usa COUNT normal (não tem como aproximar)
    if scope.where_clause.any?
      return scope.count
    end

    # Usa estatísticas do pg_class para contagem aproximada
    table_name = model_class.table_name
    result = ActiveRecord::Base.connection.execute(<<~SQL)
      SELECT reltuples::bigint AS count#{' '}
      FROM pg_class#{' '}
      WHERE relname = '#{table_name}'
    SQL

    count = result.first&.dig("count").to_i
    count > 0 ? count : scope.count
  rescue
    scope.count
  end
end

puts "📦 Script carregado com otimizações!"
puts ""
puts "IMPORTANTE: Rode a migration primeiro:"
puts "  docker compose exec web bin/rails db:migrate"
puts ""
puts "Depois:"
puts "  ElasticsearchReindex.run(Candidate)"
puts "  ElasticsearchReindex.run(Job)"
