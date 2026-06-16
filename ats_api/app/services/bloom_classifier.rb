# frozen_string_literal: true

class BloomClassifier
  LEVELS = %w[remember understand apply analyze create].freeze

  KEYWORDS = {
    create: %w[criei criar desenhei projetei inovei estrategia estratég ia arquitetura otimizei],
    analyze: %w[analisei analisar diagnostiquei causa comparando comparei tradeoff avaliar investiguei],
    apply: %w[apliquei implementei configurei executei resolvi entreguei utilizei usei],
    understand: %w[expliquei entendi compreender funciona conceito fundamentos],
    remember: %w[sei conheco lembro teoria definicao]
  }.freeze

  Result = Struct.new(:level, :score, :confidence, :matched_keywords, keyword_init: true)

  def self.classify(response_text)
    new(response_text: response_text).call.level
  end

  def initialize(response_text:)
    @response_text = response_text.to_s.downcase
  end

  def call
    matched = keyword_hits
    level = infer_level(matched)
    Result.new(
      level: level,
      score: LEVELS.index(level).to_i + 1,
      confidence: calculate_confidence(matched, level),
      matched_keywords: matched[level.to_sym] || []
    )
  end

  private

  def keyword_hits
    KEYWORDS.transform_values do |terms|
      terms.select { |term| @response_text.include?(term) }
    end
  end

  def infer_level(matched)
    ordered = %i[create analyze apply understand remember]
    found = ordered.find { |level| matched[level].any? }
    return found.to_s if found

    return "analyze" if @response_text.match?(/\bporque\b|\bimpacto\b|\bresultado\b/)
    return "apply" if @response_text.length > 120

    "remember"
  end

  def calculate_confidence(matched, level)
    hits = (matched[level.to_sym] || []).size
    length_factor = [ @response_text.length / 240.0, 1.0 ].min
    confidence = 0.35 + (hits * 0.15) + (length_factor * 0.25)
    confidence.clamp(0.0, 0.99).round(2)
  end
end
