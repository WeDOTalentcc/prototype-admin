module Candidates
  module Search
    class QueryRewriter
      def initialize; end

      def rewrite(original_query, context: {})
        response = Llm::Gateway.chat(
          messages: [
            { role: "system", content: system_prompt },
            { role: "user", content: build_prompt(original_query, context) }
          ],
          temperature: 0.2,
          response_format: { type: "json_object" },
          tracking: { operation: "search.query_rewriting" }
        )

        parsed = parse_response(response)

        {
          original: original_query,
          rewritten: parsed[:query],
          reasoning: parsed[:reasoning],
          confidence: parsed[:confidence],
          applied: parsed[:confidence].to_f > 0.7,
          timestamp: Time.current
        }
      rescue => e
        Rails.logger.error("[QueryRewriter] Failed: #{e.message}")
        { original: original_query, rewritten: original_query, applied: false, error: e.message }
      end

      private

      def system_prompt
        <<~PROMPT
          Você é um especialista em otimização de buscas de candidatos.
          Sua tarefa é sugerir uma query alternativa APENAS se a original tiver problemas claros.

          NÃO invente informações que não estão na query original.
          NÃO adicione filtros de senioridade/localização/salário sem evidência clara.

          Retorne JSON: { "query": "...", "reasoning": "...", "confidence": 0.0-1.0 }
        PROMPT
      end

      def build_prompt(query, context)
        "Query original: #{query}\nContexto: #{context.to_json}"
      end

      def parse_response(response)
        content = response.dig("choices", 0, "message", "content")
        JSON.parse(content, symbolize_names: true)
      end
    end
  end
end
