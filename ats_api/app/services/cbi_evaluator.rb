# frozen_string_literal: true

class CbiEvaluator
  STAR_WEIGHTS = { situation: 0.20, task: 0.20, action: 0.40, result: 0.20 }.freeze

  INJECTION_PATTERNS = [
    /ignore\s+(suas\s+)?instru[cç][oõ]es/i,
    /esque[cç]a\s+o\s+sistema/i,
    /voc[eê]\s+agora\s+[eé]/i,
    /novo\s+sistema\s+prompt/i,
    /\boverride\b/i,
    /\bjailbreak\b/i,
    /\bDAN\b/,
    /\[INST\]/i,
    /<\s*system\s*>/i
  ].freeze

  FIRST_PERSON_PATTERN = /\b(eu|mim|meu|minha|meus|minhas)\b/i
  FIRST_PERSON_VERB_PATTERN = /\b(fiz|fui|implementei|criei|conduzi|desenvolvi|liderei|propus|automatizei|estabeleci|defini|organizei|gerenciei|coordenei|analisei)\b/i

  QUANTIFIED_PATTERN = /\b\d+([.,]\d+)?\s*%|\b(reduziu|aumentou|economizou|melhorou)\s+(em\s+)?\d/i

  EPISODE_SPLIT_PATTERN = /\b(uma\s+vez|outra\s+vez|em\s+outro|segundo\s+projeto|primeiro\s+caso|depois\s+disso)\b/i

  def self.extract_star(response_text)
    new(response_text: response_text).call[:star]
  end

  def initialize(response_text:, question_text: nil, expected_language: :pt)
    @response_text = response_text.to_s
    @question_text = question_text.to_s
    @expected_language = expected_language
  end

  def call
    star = detect_star_components
    star_score = weighted_star_score(star)
    wc = word_count
    penalties_and_bonuses = build_structural_adjustments(star, wc)

    {
      star: star,
      star_score: star_score.round(4),
      completeness_score: (star_score * 5.0).round(2),
      evidences: star.select { |_, v| v }.keys,
      word_count: wc,
      injection_detected: injection_detected?,
      wrong_language_detected: wrong_language_detected?,
      paraphrase_similarity: paraphrase_ratio,
      **penalties_and_bonuses
    }
  end

  private

  def detect_star_components
    t = @response_text
    {
      situation: component_situation?(t),
      task: component_task?(t),
      action: component_action?(t),
      result: component_result?(t)
    }
  end

  def component_situation?(t)
    t.match?(/situa[cç][aã]o|contexto|cen[aá]rio|quando|empresa|projeto|time|equipe|ambiente|no\s+projeto/i)
  end

  def component_task?(t)
    t.match?(/tarefa|objetivo|meta|respons[aá]vel|precisava|deveria|desafio|precisei|tinha\s+que/i)
  end

  def component_action?(t)
    t.match?(/a[cç][aã]o|implementei|executei|fiz\s+com\s+que|conduzi|desenvolvi|criei|automatizei/i) ||
      (t.match?(FIRST_PERSON_PATTERN) && t.match?(/implement|execut|desenvolv|cri|automatiz|defin/i))
  end

  def component_result?(t)
    t.match?(/resultado|impacto|reduz|aument|economia|ganho|melhoria|em\s+\d+|%\s|métrica/i) ||
      t.match?(/\d+\s*%/)
  end

  def weighted_star_score(star)
    STAR_WEIGHTS.sum { |key, weight| (star[key] ? 1.0 : 0.0) * weight }
  end

  def word_count
    @response_text.scan(/[a-zA-ZÀ-ÿ0-9]+/).size
  end

  def injection_detected?
    INJECTION_PATTERNS.any? { |pattern| @response_text.match?(pattern) }
  end

  def wrong_language_detected?
    return false if @response_text.length < 40

    tl = @response_text.downcase
    en = %w[the and with that this from have you were was are].sum { |w| tl.scan(/\b#{Regexp.escape(w)}\b/).size }
    pt = %w[que não foi para com uma pelo pela mais como].sum { |w| tl.scan(/\b#{Regexp.escape(w)}\b/).size }
    en >= 4 && pt <= 3
  end

  def paraphrase_ratio
    return 0.0 if @question_text.blank?

    qw = tokenize(@question_text)
    aw = tokenize(@response_text)
    return 0.0 if aw.empty?

    stop = %w[de da do das dos em um uma uns umas o a os as por com para que no na nos nas]
    qw = qw - stop
    aw = aw - stop
    overlap = (aw & qw).size
    overlap.to_f / aw.size
  end

  def tokenize(text)
    text.downcase.scan(/[a-záàãâéêíóôõúç]+/)
  end

  def has_first_person_verb?
    @response_text.match?(FIRST_PERSON_PATTERN) || @response_text.match?(FIRST_PERSON_VERB_PATTERN)
  end

  def quantified_metric?
    @response_text.match?(QUANTIFIED_PATTERN)
  end

  def long_response?(wc)
    wc > 150 && !repetitive_response?
  end

  def repetitive_response?
    words = tokenize(@response_text)
    return false if words.size < 20

    words.tally.values.max.to_f / words.size > 0.35
  end

  def multi_episode?
    @response_text.scan(EPISODE_SPLIT_PATTERN).size >= 1 ||
      @response_text.split(/\n+/).count { |p| p.strip.length > 40 } >= 2
  end

  def build_structural_adjustments(star, wc)
    {
      star_penalty_words: penalty_words(wc),
      star_penalty_no_first_person: penalty_no_first_person,
      star_penalty_missing_result: penalty_missing_result(star),
      star_penalty_paraphrase: penalty_paraphrase,
      star_penalty_wrong_language: penalty_wrong_language,
      star_penalty_injection: 0.0,
      star_bonus_quantified: quantified_metric? ? 0.5 : 0.0,
      star_bonus_long_response: long_response?(wc) ? 0.3 : 0.0,
      star_bonus_multi_episode: multi_episode? ? 0.3 : 0.0
    }
  end

  def penalty_words(wc)
    return -2.5 if wc < 30
    return -1.0 if wc <= 50

    0.0
  end

  def penalty_no_first_person
    has_first_person_verb? ? 0.0 : -1.5
  end

  def penalty_missing_result(star)
    star[:result] ? 0.0 : -0.8
  end

  def penalty_paraphrase
    paraphrase_ratio > 0.6 ? -2.0 : 0.0
  end

  def penalty_wrong_language
    wrong_language_detected? ? -1.0 : 0.0
  end
end
