module Candidates
  module Search
     class HydeQueryExpander
      CACHE_PREFIX = "hyde_query"
      CACHE_TTL = 1.hour

      PROMPT_TEMPLATE = <<~PROMPT
        Busca do recrutador: "%{query}"

        Gere um MINI CURRÍCULO (texto curto) de um candidato ideal para essa vaga.
        O texto será usado para buscar candidatos reais com perfil similar.
        Use o MESMO estilo de um currículo: cargo, nível, tecnologias, experiência resumida, competências.

        REGRAS:
        1. Use APENAS tecnologias e requisitos mencionados na busca + relacionadas diretas (ex: React → JavaScript, TypeScript).
        2. NÃO adicione AWS, Docker, Kubernetes, cloud, agile, etc. a menos que estejam na busca.
        3. NÃO invente anos de experiência, empresas ou formação.
        4. Seja conciso: 3 a 6 linhas em prosa ou tópicos.
        5. Idioma: português do Brasil.

        FORMATO (respeite essa estrutura para alinhar com nossos currículos):
        [Nome fictício ou "Candidato ideal"] | [Cargo] [nível] | [tecnologias principais]
        Resume: [1-2 frases sobre experiência relevante para a vaga]
        Skills: [lista das tecnologias/ferramentas da busca e diretas]
        Competências: [lista curta, 3-5 itens]

        Retorne SOMENTE o mini currículo, sem título nem explicação.
      PROMPT

      def initialize; end

      # Retorna o texto do "mini currículo ideal" para a query (cacheado por query).
      def expand(query_text)
        return "" if query_text.blank?

        cached = Rails.cache.read(cache_key(query_text))
        return cached if cached.present?

        text = generate(query_text)
        Rails.cache.write(cache_key(query_text), text, expires_in: CACHE_TTL) if text.present?
        text.to_s.strip
      rescue => e
        Rails.logger.warn("[HydeQueryExpander] Failed: #{e.message}")
        ""
      end

      private

      def generate(query_text)
        prompt = format(PROMPT_TEMPLATE, query: query_text.strip)

        response = Llm::Gateway.fast_chat(
          messages: [ { role: "user", content: prompt } ],
          temperature: 0.1,
          max_tokens: 400,
          tracking: { operation: "search.hyde_query_expansion" }
        )

        content = response.dig("choices", 0, "message", "content").to_s.strip
        content.presence || ""
      end

      def cache_key(query_text)
        normalized = query_text.to_s.downcase.strip.gsub(/\s+/, " ")
        hash = Digest::SHA256.hexdigest(normalized)[0..15]
        "#{CACHE_PREFIX}:#{hash}"
      end
     end
  end
end
