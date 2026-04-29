# Script para calcular custo de re-embedding de candidatos
# Execute no rails console: load 'scripts/embedding_cost_calculator.rb'

module EmbeddingCostCalculator
  PRICE_PER_MILLION_TOKENS = 0.15 # USD
  AVG_CHARS_PER_TOKEN = 4
  MAX_CHARS = 8000
  BRL_RATE = 6.0
  SAMPLE_SIZE = 100 # Amostra para estimar

  def self.run
    tenant = Apartment::Tenant.current rescue "public"

    puts "\n" + "="*60
    puts "📊 ESTIMATIVA DE CUSTO - RE-EMBEDDING"
    puts "="*60
    puts "🏢 Tenant: #{tenant}"
    puts "="*60

    # Usar SQL direto para contagem rápida
    total = Candidate.count
    with_count = Candidate.where.not(curriculum_text: [ nil, "" ]).count
    without_count = total - with_count

    puts "\n📈 CANDIDATOS:"
    puts "   Total: #{total}"
    puts "   ✅ Com curriculum: #{with_count}"
    puts "   ❌ Sem curriculum: #{without_count}"

    return if with_count == 0

    # Amostrar apenas SAMPLE_SIZE candidatos para estimar
    puts "\n🔍 Amostrando #{SAMPLE_SIZE} candidatos..."

    sample = Candidate.where.not(curriculum_text: [ nil, "" ])
                      .order("RANDOM()")
                      .limit(SAMPLE_SIZE)
                      .includes(:skills, :experiences, :educations, :language_relationships)

    char_counts = sample.map do |c|
      text = CandidateService::TextBuilder.call(c) rescue ""
      [ text.to_s.length, MAX_CHARS ].min
    end

    avg_chars = char_counts.sum.to_f / char_counts.size
    avg_tokens = avg_chars / AVG_CHARS_PER_TOKEN

    puts "\n📏 ANÁLISE (amostra de #{char_counts.size}):"
    puts "   Média: #{avg_chars.round(0)} chars → #{avg_tokens.round(0)} tokens"
    puts "   Mín: #{char_counts.min} | Máx: #{char_counts.max}"

    # Extrapolar para total
    total_tokens = with_count * avg_tokens
    cost_usd = (total_tokens / 1_000_000.0) * PRICE_PER_MILLION_TOKENS
    cost_brl = cost_usd * BRL_RATE

    puts "\n" + "="*60
    puts "💰 CUSTO ESTIMADO:"
    puts "="*60
    puts "   Candidatos a embedar: #{with_count}"
    puts "   Tokens estimados: #{(total_tokens / 1000.0).round(1)}K"
    puts "   💵 $#{cost_usd.round(2)} USD = R$ #{cost_brl.round(2)}"
    puts "="*60

    { tenant: tenant, candidates: with_count, cost_brl: cost_brl.round(2) }
  end
end

# Executa ao rodar com rails runner; quando carregado pelo rake (ENV FROM_RAKE=1) não roda (rake chama .run por tenant)
EmbeddingCostCalculator.run unless ENV["FROM_RAKE"] == "1"
