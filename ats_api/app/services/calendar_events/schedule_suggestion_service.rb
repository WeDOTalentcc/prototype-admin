# frozen_string_literal: true

module CalendarEvents
  class ScheduleSuggestionService
    DEFAULT_DURATION_MINUTES = 60
    CACHE_TTL = 24.hours

    def initialize(text:, timezone: "America/Sao_Paulo")
      @text = text
      @timezone = timezone
    end

    def self.call(text:, timezone: "America/Sao_Paulo")
      new(text: text, timezone: timezone).call
    end

    def call
      Rails.logger.info "🗓️ [ScheduleSuggestion] Parsing: '#{@text}'"

      cached = Rails.cache.read(cache_key)
      if cached
        Rails.logger.info "⚡ [ScheduleSuggestion] Cache hit"
        return cached
      end

      raw = Timeout.timeout(5.0) do
        Llm::Gateway.fast_chat(
          messages: [
            { role: "system", content: system_prompt },
            { role: "user", content: @text }
          ],
          temperature: 0.1,
          max_tokens: 512,
          tracking: { operation: "calendar.schedule_suggestion" }
        )
      end

      content = raw.dig("choices", 0, "message", "content").to_s.strip
      json_str = extract_json(content)
      result = JSON.parse(json_str)

      response = build_response(result)
      Rails.cache.write(cache_key, response, expires_in: CACHE_TTL)
      response
    rescue Timeout::Error
      Rails.logger.warn "[ScheduleSuggestion] LLM timeout"
      { error: "timeout", suggestions: [] }
    rescue JSON::ParserError => e
      Rails.logger.error "[ScheduleSuggestion] JSON parse error: #{e.message}"
      Rails.logger.error "[ScheduleSuggestion] Raw content: #{content.to_s.first(500)}"
      { error: "parse_error", suggestions: [] }
    end

    private

    def extract_json(content)
      return content if content.start_with?("{")

      if (match = content.match(/```(?:json)?\s*(\{.+\})\s*```/m))
        return match[1]
      end

      if (match = content.match(/(\{.+\})/m))
        return match[1]
      end

      content
    end

    def build_response(result)
      now_in_tz = Time.current.in_time_zone(@timezone)

      suggestions = Array(result["suggestions"]).map do |s|
        start_dt = parse_datetime_str(s["start_time"])
        end_dt   = parse_datetime_str(s["end_time"])

        next nil unless start_dt && end_dt

        {
          is_primary:       s["is_primary"] == true,
          label:            s["label"],
          day_of_week:      start_dt.strftime("%A"),
          day_of_week_pt:   weekday_pt(start_dt.wday),
          date:             start_dt.strftime("%Y-%m-%d"),
          start_time:       start_dt.iso8601,
          end_time:         end_dt.iso8601,
          duration_minutes: ((end_dt - start_dt) / 60).round,
          human_readable:   s["human_readable"]
        }
      end.compact

      { suggestions: suggestions }
    end

    def parse_datetime_str(str)
      return nil if str.blank?
      ActiveSupport::TimeZone[@timezone].parse(str)
    rescue ArgumentError
      nil
    end

    def weekday_pt(wday)
      %w[Domingo Segunda-feira Terça-feira Quarta-feira Quinta-feira Sexta-feira Sábado][wday]
    end

    def cache_key
      date_context = Time.current.in_time_zone(@timezone).strftime("%Y-%m-%d")
      digest = Digest::SHA256.hexdigest("#{@text.downcase.strip}|#{@timezone}|#{date_context}")
      "schedule_suggestion:#{digest}"
    end

    def system_prompt
      now = Time.current.in_time_zone(@timezone)
      <<~PROMPT
        You are a scheduling assistant. The current date and time is #{now.strftime("%Y-%m-%d %H:%M")} (#{@timezone}).

        The user will write a natural language instruction in Portuguese or English about when they want to schedule a meeting/interview.

        Your job is to parse the instruction and return a JSON object with up to 2 suggestions (the most probable interpretation first).

        Rules:
        - If "terça" or "tuesday" is mentioned without a specific date, use the NEXT occurrence of that weekday from today (not today if today is that weekday, unless "hoje" or "today" is explicit).
        - If no duration is mentioned, default to #{DEFAULT_DURATION_MINUTES} minutes.
        - If no time of day is mentioned, default to 09:00.
        - All datetimes must be in ISO8601 format with timezone offset (e.g. "2026-02-24T09:00:00-03:00").
        - Always return valid JSON only — no markdown, no explanation outside the JSON.
        - The "label" field should be a short human label in Portuguese (e.g. "Terça-feira, 24 de fev às 9h").
        - The "human_readable" field should be a friendly sentence in Portuguese explaining the suggestion.
        - Set "is_primary": true on the most probable suggestion and false on any alternative.

        Response format (strict JSON):
        {
          "suggestions": [
            {
              "is_primary": true,
              "label": "Terça-feira, 24 de fev às 9h",
              "start_time": "2026-02-24T09:00:00-03:00",
              "end_time": "2026-02-24T10:00:00-03:00",
              "human_readable": "Próxima terça-feira, 24 de fevereiro às 9h (1 hora de duração)"
            }
          ]
        }
      PROMPT
    end
  end
end
