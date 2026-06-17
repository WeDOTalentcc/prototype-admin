# frozen_string_literal: true

module Wsi
  class QuestionValidator
    Result = Struct.new(:valid, :error, keyword_init: true)

    HYPOTHETICAL_PATTERN = /imagine\s+que|como\s+você\s+faria\s+se/i.freeze
    RUBRIC_LEAK_PATTERN = /com\s+trade[-\s]?offs?|com\s+critérios|resultados\s+mensuráveis/i.freeze
    EMBEDDED_CHOICE_PATTERN = /\b[ABCD]\)\s|\bopção\s+[ABCD]\b|\s[ABCD]\.\s/mi.freeze

    PAST_VERB_PATTERN = /
      \b(foi|esteve|fez|teve|disse|decidiu|trabalhou|liderou|organizou|desenvolveu|resolveu|
      enfrentou|apresentou|criou|implementou|geriu|conduziu|estruturou|mediou|alinhou)\b
    /ix.freeze

    SITUATION_CUE_PATTERN = /situação|momento|vez|projeto|entrega|ocasião|contexto|caso/i.freeze

    IMPERATIVE_SITUATIONAL = /\A\s*(Descreva|Conte|Explique|Relate)\b/i.freeze

    def self.call(text:)
      new(text: text).call
    end

    def initialize(text:)
      @text = text.to_s.strip
    end

    def call
      return Result.new(valid: false, error: :blank) if @text.blank?

      words = @text.split(/\s+/)
      word_count = words.size
      return Result.new(valid: false, error: :too_short) if word_count < 15
      return Result.new(valid: false, error: :too_long) if word_count > 80

      return Result.new(valid: false, error: :hypothetical_format) if @text.match?(HYPOTHETICAL_PATTERN)
      return Result.new(valid: false, error: :rubric_leak) if @text.match?(RUBRIC_LEAK_PATTERN)
      return Result.new(valid: false, error: :embedded_choices) if @text.match?(EMBEDDED_CHOICE_PATTERN)

      return Result.new(valid: false, error: :situational_past) unless situational_past_ok?

      Result.new(valid: true, error: nil)
    end

    private

    def situational_past_ok?
      return true if @text.match?(PAST_VERB_PATTERN)
      return true if @text.match?(IMPERATIVE_SITUATIONAL) && @text.match?(SITUATION_CUE_PATTERN)

      false
    end
  end
end
