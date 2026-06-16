# frozen_string_literal: true

module Wsi
  class PiiMasker
    CPF_PATTERN = /\b\d{3}[.\-]?\d{3}[.\-]?\d{3}[.\/-]?\d{2}\b/
    EMAIL_PATTERN = /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/
    PHONE_BR_PATTERN = %r{(?:\+55\s?)?(?:\(?\d{2}\)?\s?)?(?:9\s?)?\d{4}[-\s]?\d{4}\b}
    RG_PATTERN = /\b\d{1,2}[.\-]?\d{3}[.\-]?\d{3}[\-]?[0-9Xx]\b/
    CNPJ_PATTERN = %r{\b\d{2}[.\-]?\d{3}[.\-]?\d{3}[/\\]?\d{4}[\-]?\d{2}\b}
    PORTUGUESE_SURNAME_PATTERN = /
      \b[A-ZÁÉÍÓÚÃÕÇ][a-záéíóúãõç]+\s+(?:da|de|do|das|dos)\s+[A-ZÁÉÍÓÚÃÕÇ][a-záéíóúãõç]+\b
    /x
    NAME_IN_LOG_PATTERN = /(?:name|nome|candidato|recruiter|user)\s*[=:]\s*["'][^"']+["']/i
    GRADUATION_YEAR_PATTERN = /
      \b(?:formad[oa]|graduad[oa]|formatura|conclu[ií][u]|bacharelad[oa]|pós[-\s]graduad[oa])
      (?:\s+em)?\s+(?:em\s+)?\d{4}\b
    /ix
    AGE_EXPLICIT_PATTERN = /\b\d{2}\s*anos?\b/i
    ADDRESS_BAIRRO_PATTERN = /
      \b(?:moro|resido|residente|moradora?|endere[çc]o|bairro|cep|rua|avenida|av\.|r\.)\b[^.]{0,60}
    /ix

    LLM_PROMPT_PATTERNS = [
      [ CPF_PATTERN, "[CPF REMOVIDO]" ],
      [ EMAIL_PATTERN, "[EMAIL REMOVIDO]" ],
      [ PHONE_BR_PATTERN, "[TELEFONE REMOVIDO]" ],
      [ RG_PATTERN, "[RG REMOVIDO]" ],
      [ CNPJ_PATTERN, "[CNPJ REMOVIDO]" ],
      [ PORTUGUESE_SURNAME_PATTERN, "[NOME REMOVIDO]" ],
      [ NAME_IN_LOG_PATTERN, "[NOME REMOVIDO]" ],
      [ GRADUATION_YEAR_PATTERN, "[ANO_FORMATURA REMOVIDO]" ],
      [ AGE_EXPLICIT_PATTERN, "[IDADE REMOVIDA]" ],
      [ ADDRESS_BAIRRO_PATTERN, "[ENDEREÇO REMOVIDO]" ]
    ].freeze

    def self.call(text:)
      new(text: text).call
    end

    def initialize(text:)
      @text = text
    end

    def call
      raw = @text.to_s
      return "" if raw.blank?

      result = raw.dup
      LLM_PROMPT_PATTERNS.each { |pattern, replacement| result.gsub!(pattern, replacement) }
      result
    end
  end
end
