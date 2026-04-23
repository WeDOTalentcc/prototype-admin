module Candidates
  module Search
    class EmbeddingService
      def generate(text)
        return nil if text.blank?

        response = Llm::Gateway.embed(
          text: text,
          dimensions: 768,
          tracking: { operation: "search.embedding_generation" }
        )

        response.dig("data", 0, "embedding")
      rescue => e
        Rails.logger.error("[EmbeddingService] Gemini failed: #{e.message}")
        nil
      end
    end
  end
end
