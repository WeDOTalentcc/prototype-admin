# frozen_string_literal: true

class BigFiveAnalyzer
  TRAITS = {
    openness: %w[inovei criativo explorar aprendizado aprender experimentar],
    conscientiousness: %w[planejei processo organizado prazo disciplina qualidade],
    extraversion: %w[comuniquei apresentei alinhei negociei facilitei conduzi],
    agreeableness: %w[colaborei ajudei empatia ouvir suporte parceria equipe],
    neuroticism: %w[pressao conflito crise ansiedade estresse urgencia]
  }.freeze

  def self.analyze(response_text)
    new(response_text: response_text).call
  end

  def initialize(response_text:)
    @response_text = response_text.to_s.downcase
  end

  def call
    {
      o: score_trait(:openness),
      c: score_trait(:conscientiousness),
      e: score_trait(:extraversion),
      a: score_trait(:agreeableness),
      n: score_trait(:neuroticism),
      confidence: global_confidence
    }
  end

  private

  def score_trait(trait)
    hits = TRAITS[trait].count { |term| @response_text.include?(term) }
    base = trait == :neuroticism ? 2.8 : 3.0
    adjusted = if trait == :neuroticism
      base + (hits * 0.35)
    else
      base + (hits * 0.3)
    end

    adjusted.clamp(1.0, 5.0).round(2)
  end

  def global_confidence
    density = TRAITS.values.flatten.count { |term| @response_text.include?(term) }
    confidence = 0.4 + (density * 0.05) + [ @response_text.length / 500.0, 0.25 ].min
    confidence.clamp(0.3, 0.95).round(2)
  end
end
