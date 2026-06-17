module Candidates
  module Search
    class EmbeddingCache
      CACHE_PREFIX = "search_emb".freeze

      def initialize(embedding_service: EmbeddingService.new)
        @embedding_service = embedding_service
      end

      def fetch(query_text, account_id:)
        key = build_key(query_text, account_id)
        model_version = Configuration.embedding_model_version

        cached = ::EmbeddingCache.find_by(key: key)

        if cached
          cached.touch_access
          return cached.embedding
        end

        embedding = @embedding_service.generate(query_text)

        ::EmbeddingCache.create!(
          key: key,
          model_version: model_version,
          query_text: normalize(query_text),
          embedding: embedding,
          account_id: account_id,
          last_accessed_at: Time.current
        )

        embedding
      rescue ActiveRecord::RecordNotUnique
        ::EmbeddingCache.find_by!(key: key).tap(&:touch_access).embedding
      end

      def invalidate(query_text, account_id:)
        key = build_key(query_text, account_id)
        ::EmbeddingCache.find_by(key: key)&.destroy
      end

      def self.invalidate_all!
        ::EmbeddingCache.delete_all
        Rails.logger.info("[EmbeddingCache] All cache entries deleted")
      end

      private

      def build_key(query_text, account_id)
        normalized = normalize(query_text)
        hash = Digest::SHA256.hexdigest(normalized)[0..15]
        model_version = Configuration.embedding_model_version

        "#{CACHE_PREFIX}:#{model_version}:#{account_id}:#{hash}"
      end

      def normalize(text)
        text.to_s.downcase.strip.gsub(/\s+/, " ")
      end

      def ttl
        Configuration.embedding_cache_ttl
      end
    end
  end
end
