# frozen_string_literal: true

module Candidates
  module SimilarCandidates
    class FeedbackAnalyzerService
      MIN_DISLIKES_FOR_ANALYSIS = 2
      TIMEOUT = 3.0

      def initialize; end

      def analyze(base_candidates:, liked_candidates:, dislike_feedbacks:)
        return nil if dislike_feedbacks.size < MIN_DISLIKES_FOR_ANALYSIS

        prompt = build_prompt(base_candidates, liked_candidates, dislike_feedbacks)
        response = call_llm_with_timeout(prompt)

        return nil unless response

        parse_response(response)
      rescue StandardError => e
        Rails.logger.warn "[#{self.class.name}] LLM analysis failed: #{e.message}"
        nil
      end

      private

      def build_prompt(base, liked, dislikes)
        <<~PROMPT
          You are a recruitment assistant. Analyze the recruiter's feedback to understand what type of candidate they are looking for.

          ## BASE candidates (original reference):
          #{base.map { |c| "- #{c.name}: #{c.role_name} @ #{c.current_company}" }.join("\n")}

          ## LIKED candidates (approved by recruiter):
          #{liked.map { |c| "- #{c.name}: #{c.role_name} @ #{c.current_company}" }.join("\n")}

          ## DISLIKED candidates with reason:
          #{dislikes.map { |d| "- #{d[:candidate]&.name}: #{d[:candidate]&.role_name} @ #{d[:candidate]&.current_company}\n  Reason: #{d[:reason]}" }.join("\n")}

          Return ONLY valid JSON (no markdown, no backticks):
          {
            "desired_profile": "description in 1-2 sentences of inferred ideal profile",
            "rejection_patterns": ["pattern 1", "pattern 2"],
            "positive_patterns": ["what the likes have in common"],
            "explanation": "why the recruiter made these choices"
          }
        PROMPT
      end

      def call_llm_with_timeout(prompt)
        Timeout.timeout(TIMEOUT) do
          Llm::Gateway.chat(
            messages: [
              { role: "system", content: "You are a recruitment analytics assistant. Always respond with valid JSON." },
              { role: "user", content: prompt }
            ],
            temperature: 0.1,
            max_tokens: 500,
            tracking: { operation: "similar_candidates.feedback_analysis" }
          )
        end
      rescue Timeout::Error
        Rails.logger.warn "[#{self.class.name}] LLM timeout (#{TIMEOUT}s), using fallback"
        nil
      end

      def parse_response(response)
        text = response&.dig("choices", 0, "message", "content")
        return nil unless text

        json = JSON.parse(text.gsub(/```json\n?|\n?```/, "").strip)

        {
          desired_profile: json["desired_profile"],
          rejection_patterns: json["rejection_patterns"] || [],
          positive_patterns: json["positive_patterns"] || [],
          explanation: json["explanation"]
        }
      rescue JSON::ParserError => e
        Rails.logger.warn "[#{self.class.name}] JSON parse failed: #{e.message}"
        nil
      end
    end
  end
end
