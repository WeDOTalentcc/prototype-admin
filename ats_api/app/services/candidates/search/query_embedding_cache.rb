module Candidates
  module Search
    class QueryEmbeddingCache
      CACHE_PREFIX = "search_embedding".freeze

      def initialize(embedding_service: EmbeddingService.new)
        @embedding_service = embedding_service
      end

      def fetch(query_text, tenant:)
        normalized = normalize_query(query_text)
        cache_key = build_key(normalized, tenant)

        cached = Rails.cache.read(cache_key)
        return cached if cached

        embedding = @embedding_service.generate(query_text)
        Rails.cache.write(cache_key, embedding, expires_in: ttl) if embedding

        embedding
      end

      def invalidate(query_text, tenant:)
        normalized = normalize_query(query_text)
        Rails.cache.delete(build_key(normalized, tenant))
      end

      private

      def normalize_query(text)
        text.to_s.downcase.strip.gsub(/\s+/, " ")
      end

      def build_key(normalized_query, tenant)
        hash = Digest::SHA256.hexdigest(normalized_query)[0..15]
        "#{CACHE_PREFIX}:#{tenant}:#{hash}"
      end

      def ttl
        Configuration.embedding_cache_ttl
      end
    end
  end
end
