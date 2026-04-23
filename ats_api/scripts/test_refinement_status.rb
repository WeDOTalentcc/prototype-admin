#!/usr/bin/env ruby
# frozen_string_literal: true

def test_refinement_status
  puts "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  puts "🔍 STATUS DOS TESTES DE REFINAMENTO"
  puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  checks = []

  puts "\n📋 Verificando componentes..."

  print "  [1/6] GeminiClient disponível... "
  begin
    client = GeminiClient.new
    checks << { name: "GeminiClient", status: :ok }
    puts "✅"
  rescue => e
    checks << { name: "GeminiClient", status: :error, message: e.message }
    puts "❌ #{e.message}"
  end

  print "  [2/6] Embeddings::Encoder disponível... "
  begin
    encoder = Embeddings::Encoder.new
    checks << { name: "Encoder", status: :ok }
    puts "✅"
  rescue => e
    checks << { name: "Encoder", status: :error, message: e.message }
    puts "❌ #{e.message}"
  end

  print "  [3/6] IntentBasedRefinementService carregado... "
  begin
    service_class = Candidates::SimilarCandidates::IntentBasedRefinementService
    checks << { name: "IntentService", status: :ok }
    puts "✅"
  rescue => e
    checks << { name: "IntentService", status: :error, message: e.message }
    puts "❌ #{e.message}"
  end

  print "  [4/6] RefinementService carregado... "
  begin
    service_class = Candidates::SimilarCandidates::RefinementService
    checks << { name: "RefinementService", status: :ok }
    puts "✅"
  rescue => e
    checks << { name: "RefinementService", status: :error, message: e.message }
    puts "❌ #{e.message}"
  end

  print "  [5/6] Sourcing com feedbacks existe... "
  begin
    sourcing = Sourcing
      .where(status: "done")
      .where("(parameters->>'search_type') = ?", "similarity")
      .joins(:candidate_feedbacks)
      .where(candidate_feedbacks: { feedback_type: "dislike" })
      .where.not(candidate_feedbacks: { reason: [ nil, "" ] })
      .order(created_at: :desc)
      .first

    if sourcing
      checks << { name: "Sourcing with feedbacks", status: :ok, data: { id: sourcing.id, query: sourcing.query } }
      puts "✅ (Sourcing ##{sourcing.id}: #{sourcing.query.truncate(50)})"
    else
      checks << { name: "Sourcing with feedbacks", status: :warning, message: "No sourcing with dislike feedbacks found" }
      puts "⚠️  No sourcing with feedbacks found - create one to test full flow"
    end
  rescue => e
    checks << { name: "Sourcing with feedbacks", status: :error, message: e.message }
    puts "❌ #{e.message}"
  end

  print "  [6/6] Testando modelo Gemini atual... "
  begin
    model = ENV.fetch('GEMINI_FAST_MODEL', 'gemini-2.5-flash')
    client = GeminiClient.new
    response = client.chat(
      model: model,
      messages: [ { role: "user", content: "Test" } ],
      temperature: 0.1,
      max_tokens: 10
    )
    content = response.dig("choices", 0, "message", "content")
    if content.present?
      checks << { name: "Gemini Model (#{model})", status: :ok }
      puts "✅ (#{model})"
    else
      checks << { name: "Gemini Model (#{model})", status: :error, message: "Empty response" }
      puts "❌ Empty response"
    end
  rescue => e
    checks << { name: "Gemini Model (#{model})", status: :error, message: e.message }
    if e.message.include?("404")
      puts "❌ Model not found (404) - Precisa atualizar GEMINI_FAST_MODEL"
    else
      puts "❌ #{e.message.first(50)}"
    end
  end

  puts "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  puts "📊 RESUMO"
  puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  ok_count = checks.count { |c| c[:status] == :ok }
  warning_count = checks.count { |c| c[:status] == :warning }
  error_count = checks.count { |c| c[:status] == :error }

  puts "\n  ✅ OK:       #{ok_count}/#{checks.size}"
  puts "  ⚠️  Warning:  #{warning_count}/#{checks.size}" if warning_count > 0
  puts "  ❌ Error:    #{error_count}/#{checks.size}" if error_count > 0

  if error_count > 0
    puts "\n❌ PROBLEMAS ENCONTRADOS:"
    checks.select { |c| c[:status] == :error }.each do |check|
      puts "   • #{check[:name]}: #{check[:message]}"
    end

    puts "\n💡 PRÓXIMOS PASSOS:"

    if checks.any? { |c| c[:name].include?("Gemini Model") && c[:status] == :error }
      puts "   1. Verificar modelo Gemini disponível:"
      puts "      make test-models"
      puts ""
      puts "   2. Atualizar variável de ambiente no .env:"
      puts "      GEMINI_FAST_MODEL=gemini-2.5-flash"
      puts ""
      puts "   3. Reiniciar containers:"
      puts "      make restart"
    end
  else
    puts "\n✅ TUDO OK - Sistema pronto para testes!"
    puts ""
    puts "📚 Próximos passos:"
    puts "   • make test-refinement-specs    # Rodar specs RSpec"
    puts "   • make test-intent-quick        # Teste rápido de intent"
    puts "   • make test-intent-full         # Teste completo"
    puts "   • make test-refinement-all      # Suite completa"
  end

  puts "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
end

test_refinement_status
