# frozen_string_literal: true

module Security
  class PromptInjectionGuard
    MAX_LENGTH = 4000

    INJECTION_RESPONSE = "Desculpe, não consigo processar essa solicitação. Por favor, reformule sua resposta."

    INJECTION_PATTERNS = [
      # English patterns
      { name: "ignore_instructions_en", regex: /ignore\s+(previous\s+|all\s+|above\s+)*instructions?/i },
      { name: "disregard_en", regex: /disregard\s+(previous|all|above)/i },
      { name: "forget_en", regex: /forget\s+(everything|all|previous)/i },
      { name: "role_override_en", regex: /you\s+are\s+now\s+a/i },
      { name: "act_as_en", regex: /act\s+as\s+(a|an)/i },
      { name: "pretend_en", regex: /pretend\s+(to\s+be|you\s+are)/i },
      { name: "system_colon", regex: /system\s*:\s*/i },
      { name: "system_tag", regex: /<\s*system\s*>/i },
      { name: "system_bracket", regex: /\[\s*system\s*\]/i },
      { name: "override_en", regex: /override\s+(your|the)\s+(instructions?|rules?|guidelines?)/i },
      { name: "new_instructions_en", regex: /new\s+instructions?\s*:/i },
      { name: "jailbreak", regex: /jailbreak/i },
      { name: "dan_mode", regex: /dan\s*mode/i },
      { name: "developer_mode_en", regex: /developer\s*mode/i },
      { name: "bypass_en", regex: /bypass\s+(safety|filter|restriction)/i },
      { name: "reveal_en", regex: /reveal\s+(your|the)\s+(prompt|instructions?|system)/i },
      { name: "what_instructions_en", regex: /what\s+(is|are)\s+your\s+(instructions?|rules?|prompt)/i },
      { name: "output_prompt_en", regex: /output\s+your\s+(system|initial)\s+prompt/i },

      # Portuguese patterns
      { name: "ignore_instructions_pt", regex: /ignore\s+as\s+instru[çc][õo]es/i },
      { name: "forget_pt", regex: /esque[çc]a\s+tudo/i },
      { name: "role_override_pt", regex: /agora\s+voc[êe]\s+[ée]/i },
      { name: "disregard_pt", regex: /desconsidere\s+(tudo|as\s+regras|as\s+instru)/i },
      { name: "new_instructions_pt", regex: /novas?\s+instru[çc][õo]es?\s*:/i },
      { name: "pretend_pt", regex: /finja\s+(ser|que\s+[ée])/i },
      { name: "developer_mode_pt", regex: /modo\s+desenvolvedor/i }
    ].freeze

    MALICIOUS_CHAR_PATTERNS = [
      /[\x00-\x08\x0b\x0c\x0e-\x1f]/,
      /\u200b|\u200c|\u200d|\ufeff/
    ].freeze

    class << self
      def sanitize(text)
        return "" if text.blank?

        sanitized = text.to_s.strip
        MALICIOUS_CHAR_PATTERNS.each { |p| sanitized = sanitized.gsub(p, "") }
        sanitized = sanitized.gsub(/\s+/, " ")
        sanitized.truncate(MAX_LENGTH, omission: "")
      end

      def detect_injection(text)
        return [ false, nil ] if text.blank?

        INJECTION_PATTERNS.each do |entry|
          if entry[:regex].match?(text)
            Rails.logger.warn "[PromptInjectionGuard] Injection detected: #{entry[:name]}"
            return [ true, entry[:name] ]
          end
        end

        [ false, nil ]
      end

      def safe_process(text)
        sanitized = sanitize(text)
        detected, pattern = detect_injection(sanitized)

        if detected
          Rails.logger.warn "[PromptInjectionGuard] Input blocked: pattern=#{pattern}"
          return { safe: false, sanitized: "", detected_pattern: pattern }
        end

        { safe: true, sanitized: sanitized, detected_pattern: nil }
      end

      def escape_for_prompt(text)
        return "" if text.blank?

        text.to_s.gsub("{", "{{").gsub("}", "}}").gsub("```", "'''")
      end
    end
  end
end
