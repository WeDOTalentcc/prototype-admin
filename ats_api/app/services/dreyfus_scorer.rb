# frozen_string_literal: true

class DreyfusScorer
  LEVELS = {
    1 => "novice",
    2 => "advanced_beginner",
    3 => "competent",
    4 => "proficient",
    5 => "expert"
  }.freeze

  Result = Struct.new(:level, :score, :confidence, :signals, keyword_init: true)

  def self.evaluate(response_text, rubric = nil)
    new(response_text: response_text, rubric: rubric).call.to_h
  end

  def initialize(response_text:, rubric: nil, self_declaration_score: nil)
    @response_text = response_text.to_s.downcase
    @rubric = rubric
    @self_declaration_score = self_declaration_score
  end

  def call
    inferred = infer_score
    blended = blend_with_self_declaration(inferred)

    Result.new(
      level: LEVELS[blended.round],
      score: blended.round(2),
      confidence: confidence_for(blended),
      signals: extract_signals
    )
  end

  private

  def infer_score
    score = 1.4
    score += 0.8 if @response_text.match?(/\bimplementei\b|\bresolvi\b|\bentreguei\b|\bconfigurei\b/)
    score += 0.8 if @response_text.match?(/\bresultado\b|\bimpacto\b|\bmelhoria\b|\bredu[çc][aã]o\b/)
    score += 0.7 if @response_text.match?(/\bmentorei\b|\bliderei\b|\barquitetura\b|\bestrat[eé]gia\b/)
    score += 0.6 if @response_text.match?(/\baut[ôo]nomo\b|\bsem supervis[aã]o\b|\bproativo\b/)
    score += 0.5 if @response_text.match?(/\d+%|\d+\s*(dias|meses|anos|horas)/)
    score.clamp(1.0, 5.0)
  end

  def blend_with_self_declaration(inferred)
    return inferred unless @self_declaration_score

    ((inferred * 0.7) + (@self_declaration_score.to_f * 0.3)).clamp(1.0, 5.0)
  end

  def confidence_for(score)
    variance = (score - score.round).abs
    base = 0.62 - variance
    base += 0.15 if @response_text.length > 220
    base += 0.1 if @response_text.match?(/\bresultado\b|\bm[ée]trica\b|\bimpacto\b/)
    base.clamp(0.35, 0.95).round(2)
  end

  def extract_signals
    {
      has_ownership: @response_text.match?(/\bimplementei\b|\bliderei\b|\bconduzi\b/),
      has_impact: @response_text.match?(/\bresultado\b|\bimpacto\b|\bm[ée]trica\b|\bredu[çc][aã]o\b/),
      has_autonomy: @response_text.match?(/\baut[ôo]nomo\b|\bdecidi\b|\bproativo\b/),
      mentions_strategy: @response_text.match?(/\bestrat[eé]gia\b|\barquitetura\b/)
    }
  end
end
