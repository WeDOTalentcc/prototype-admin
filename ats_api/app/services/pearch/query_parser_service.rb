# frozen_string_literal: true

module Pearch
  class QueryParserService
    def initialize; end

    def self.call(text, **opts)
      new(**opts).call(text)
    end

    def call(text)
      return fallback_response(text) if Rails.env.test? || text.blank?

      Rails.logger.info "🔍 [Pearch::QueryParser] Parsing query: '#{text}'"

      begin
        Rails.logger.info "📤 [Pearch::QueryParser] Sending request to LLM..."

        response = Llm::Gateway.chat(
          messages: [
            { role: "system", content: system_prompt },
            { role: "user", content: user_prompt(text) }
          ],
          temperature: 0.1,
          max_tokens: 2048,
          response_format: { type: "json_object" },
          tracking: { operation: "pearch.query_parsing" }
        )

        content = response.dig("choices", 0, "message", "content")

        if content.nil?
          Rails.logger.error "❌ [Pearch::QueryParser] LLM returned nil content"
          return fallback_response(text)
        end

        Rails.logger.info "📥 [Pearch::QueryParser] Raw LLM response:"
        Rails.logger.info "=" * 80
        Rails.logger.info content
        Rails.logger.info "=" * 80

        parsed = parse_response(content)
        Rails.logger.info "✅ [Pearch::QueryParser] Successfully parsed result: #{parsed.inspect}"
        parsed
      rescue JSON::ParserError => e
        Rails.logger.error "❌ [Pearch::QueryParser] JSON Parse Error: #{e.message}"
        Rails.logger.error "📄 [Pearch::QueryParser] Failed content:"
        Rails.logger.error "=" * 80
        Rails.logger.error content
        Rails.logger.error "=" * 80
        Rails.logger.warn "🔄 [Pearch::QueryParser] Using fallback with original text"
        fallback_response(text)
      rescue => e
        Rails.logger.error "❌ [Pearch::QueryParser] Unexpected error: #{e.class} - #{e.message}"
        Rails.logger.error e.backtrace.first(5).join("\n")
        fallback_response(text)
      end
    end

    private

    def fallback_response(text)
      {
        query: text,
        custom_filters: {},
        metadata: {
          original_query: text,
          parsed: false,
          reason: "LLM parsing skipped or failed"
        }
      }
    end

    def system_prompt
      <<~PROMPT
        You are a query translator for recruitment API. Convert Portuguese queries to English.

        CRITICAL: Return ONLY valid, COMPLETE JSON. Never truncate or break in the middle!

        FORBIDDEN:
        - Markdown (```json)
        - Comments
        - Incomplete/truncated JSON
        - Stopping mid-object

        ALWAYS close all brackets and braces properly!

        Minimum format if no filters:
        {"query": "text in english", "custom_filters": {}}

        Keep it SIMPLE and SHORT - focus on the query translation only.
      PROMPT
    end

    def user_prompt(text)
      <<~PROMPT
        Translate to English: "#{text}"

        Return ONLY this JSON (complete, no truncation):

        {"query": "english translation here", "custom_filters": {}}

        Simple translation rules:
        - "desenvolvedor" → "developer"
        - "sênior/pleno/júnior" → "senior/mid-level/junior"
        - Brazilian cities: add ", Brazil"
        - Keep technical skills in original English
        - ALWAYS close JSON with }}

        Example: "dev python sênior em SP"
        Output: {"query": "Senior Python developer from São Paulo, Brazil", "custom_filters": {}}

        Keep it SIMPLE. Just translate the query to English. No complex filters unless explicitly mentioned.
      PROMPT
    end

    def parse_response(content)
      Rails.logger.info "🔧 [Pearch::QueryParser] Starting JSON extraction..."
      Rails.logger.info "📏 [Pearch::QueryParser] Raw content length: #{content.length} chars"

      # Limpar o conteúdo
      json_content = content.strip
                            .gsub(/^```json\s*/, "")
                            .gsub(/^```\s*/, "")
                            .gsub(/```\s*$/, "")
                            .strip

      Rails.logger.info "🔧 [Pearch::QueryParser] After markdown removal (#{json_content.length} chars)"
      Rails.logger.info "📄 First 300 chars: #{json_content[0..299]}"

      # Extrair apenas o JSON
      json_match = json_content.match(/\{[\s\S]*\}/m)
      if json_match
        json_content = json_match[0]
        Rails.logger.info "✅ [Pearch::QueryParser] JSON pattern found (#{json_content.length} chars)"
      else
        Rails.logger.error "❌ [Pearch::QueryParser] No JSON pattern found!"
        raise JSON::ParserError, "No JSON object found in response"
      end

      # Validar se JSON está completo
      if incomplete_json?(json_content)
        Rails.logger.warn "⚠️  [Pearch::QueryParser] Detected incomplete JSON, attempting recovery..."
        json_content = complete_incomplete_json(json_content)
        Rails.logger.info "🔧 [Pearch::QueryParser] After recovery: #{json_content}"
      end

      # Validar JSON básico antes de parsear
      validate_json_structure(json_content)

      Rails.logger.info "🔧 [Pearch::QueryParser] Attempting to parse JSON..."
      parsed = JSON.parse(json_content, symbolize_names: true)
      Rails.logger.info "✅ [Pearch::QueryParser] JSON parsed successfully!"

      result = {
        query: parsed[:query] || parsed["query"],
        custom_filters: parsed[:custom_filters] || parsed["custom_filters"] || {},
        metadata: parsed[:metadata] || parsed["metadata"] || {}
      }

      Rails.logger.info "🎉 [Pearch::QueryParser] Final result: query=#{result[:query][0..50]}..."
      result
    rescue JSON::ParserError => e
      Rails.logger.error "❌ [Pearch::QueryParser] JSON::ParserError!"
      Rails.logger.error "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.error "Error: #{e.message}"
      Rails.logger.error "Content length: #{content.length} chars"
      Rails.logger.error "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.error "FULL RAW CONTENT:"
      Rails.logger.error content
      Rails.logger.error "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.error "AFTER CLEANING:"
      Rails.logger.error json_content
      Rails.logger.error "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.warn "🔄 [Pearch::QueryParser] Attempting to extract query from incomplete JSON..."

      extracted_query = extract_query_from_incomplete_json(content)
      if extracted_query
        Rails.logger.info "✅ [Pearch::QueryParser] Extracted query: #{extracted_query}"
        return {
          query: extracted_query,
          custom_filters: {},
          metadata: {
            original_query: extracted_query,
            parsed: false,
            reason: "Incomplete JSON, extracted query only"
          }
        }
      end

      raise
    end

    def extract_query_from_incomplete_json(content)
      match = content.match(/"query"\s*:\s*"([^"]*)"/)
      return match[1] if match

      match = content.match(/'query'\s*:\s*'([^']*)'/)
      return match[1] if match

      nil
    end

    def incomplete_json?(json_str)
      return true if json_str.length < 50
      return true unless json_str.end_with?("}")

      open_braces = json_str.count("{")
      close_braces = json_str.count("}")
      return true if open_braces != close_braces

      open_brackets = json_str.count("[")
      close_brackets = json_str.count("]")
      return true if open_brackets != close_brackets

      quote_count = json_str.count('"')
      return true if quote_count.odd?

      false
    end

    def complete_incomplete_json(json_str)
      result = json_str.dup

      open_braces = result.count("{")
      close_braces = result.count("}")
      missing_braces = open_braces - close_braces

      open_brackets = result.count("[")
      close_brackets = result.count("]")
      missing_brackets = open_brackets - close_brackets

      quote_count = result.count('"')
      if quote_count.odd?
        result += '"'
      end

      result += "]" * missing_brackets if missing_brackets > 0
      result += "}" * missing_braces if missing_braces > 0

      result
    end

    def validate_json_structure(json_str)
      # Validações básicas
      errors = []

      errors << "Missing opening brace" unless json_str.start_with?("{")
      errors << "Missing closing brace" unless json_str.end_with?("}")

      # Contar chaves
      open_braces = json_str.count("{")
      close_braces = json_str.count("}")
      errors << "Unmatched braces (open: #{open_braces}, close: #{close_braces})" if open_braces != close_braces

      # Contar colchetes
      open_brackets = json_str.count("[")
      close_brackets = json_str.count("]")
      errors << "Unmatched brackets (open: #{open_brackets}, close: #{close_brackets})" if open_brackets != close_brackets

      # Aspas
      quote_count = json_str.count('"')
      errors << "Odd number of quotes (#{quote_count})" if quote_count.odd?

      if errors.any?
        Rails.logger.error "⚠️  [Pearch::QueryParser] JSON structure issues:"
        errors.each { |err| Rails.logger.error "   - #{err}" }
      else
        Rails.logger.info "✅ [Pearch::QueryParser] JSON structure looks valid"
      end
    end
  end
end
