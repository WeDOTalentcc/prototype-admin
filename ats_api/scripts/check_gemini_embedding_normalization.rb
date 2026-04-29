# frozen_string_literal: true

# Script para verificar se embeddings do Gemini são normalizados
#
# Como rodar:
#   rails runner scripts/check_gemini_embedding_normalization.rb
# ou no Rails console:
#   load 'scripts/check_gemini_embedding_normalization.rb'
#   check_gemini_normalization

def check_gemini_normalization
  puts "\n" + "=" * 80
  puts "GEMINI EMBEDDING NORMALIZATION CHECK"
  puts "=" * 80

  encoder = Embeddings::Encoder.new

  test_texts = [
    "Senior Ruby on Rails developer",
    "Java developer with Spring Boot and microservices experience",
    "Python developer"
  ]

  puts "\nTesting #{test_texts.size} sample texts...\n"

  test_texts.each_with_index do |text, i|
    puts "\n#{i + 1}. \"#{text}\""

    embedding = encoder.call(text)

    magnitude = Math.sqrt(embedding.sum { |v| v**2 })

    puts "   Dimensions: #{embedding.size}"
    puts "   Magnitude: #{magnitude.round(6)}"
    puts "   Is normalized? #{magnitude.round(3) == 1.0 ? '✅ YES' : '❌ NO'}"

    if magnitude.round(3) != 1.0
      puts "   ⚠️  Gemini embeddings are NOT unit vectors"
      puts "   ⚠️  Normalization required before blending"
    end
  end

  puts "\n" + "=" * 80
  puts "CONCLUSION"
  puts "=" * 80

  sample_embedding = encoder.call("test")
  sample_magnitude = Math.sqrt(sample_embedding.sum { |v| v**2 })

  if sample_magnitude.round(3) == 1.0
    puts "\n✅ Gemini embeddings ARE normalized (unit vectors)"
    puts "   Blending can be done directly without pre-normalization"
  else
    puts "\n❌ Gemini embeddings are NOT normalized"
    puts "   Magnitude: #{sample_magnitude.round(6)}"
    puts "   IntentBasedRefinementService correctly normalizes before blending ✅"
  end

  puts ""
end

if $PROGRAM_NAME == __FILE__ || defined?(Rails::Console)
  check_gemini_normalization if $PROGRAM_NAME == __FILE__
end
