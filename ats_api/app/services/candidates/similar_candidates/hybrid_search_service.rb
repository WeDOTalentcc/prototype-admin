# frozen_string_literal: true

module Candidates
  module SimilarCandidates
    class HybridSearchService
      POOL_MULTIPLIER = 3
      EXTENDED_POOL_MULTIPLIER = 6
      MIN_POOL_SIZE = 60

      def initialize(account_id:)
        @account_id = account_id
      end

      def search(embedding:, intent_result:, exclude_ids:, limit:, threshold:)
        vector_pool = [ limit * POOL_MULTIPLIER, MIN_POOL_SIZE ].max
        vector_results = search_vectors(
          embedding: embedding,
          exclude_ids: exclude_ids,
          limit: vector_pool,
          threshold: threshold
        )

        return vector_results.first(limit) unless text_search_applicable?(intent_result)

        text_results = search_text(
          intent_result: intent_result,
          exclude_ids: exclude_ids,
          limit: limit
        )

        return vector_results.first(limit) if text_results.empty?

        log_fusion(vector_results.size, text_results.size)

        fuse_results(vector_results: vector_results, text_results: text_results, limit: limit)
      end

      private

      def search_vectors(embedding:, exclude_ids:, limit:, threshold:)
        pool_size = [ limit * POOL_MULTIPLIER, MIN_POOL_SIZE ].max
        filtered = fetch_and_filter(embedding: embedding, exclude_ids: exclude_ids, pool_size: pool_size, threshold: threshold)

        if filtered.size < limit && pool_size < limit * EXTENDED_POOL_MULTIPLIER
          extended_pool = limit * EXTENDED_POOL_MULTIPLIER
          filtered = fetch_and_filter(embedding: embedding, exclude_ids: exclude_ids, pool_size: extended_pool, threshold: threshold)
        end

        filtered.first(limit)
      end

      def fetch_and_filter(embedding:, exclude_ids:, pool_size:, threshold:)
        results = Embedding
          .where(reference_type: "Candidate")
          .where.not(reference_id: exclude_ids)
          .nearest_neighbors(:embedding, embedding, distance: "cosine")
          .limit(pool_size)

        tenant_ids = Candidate
          .where(account_id: @account_id, is_deleted: false)
          .where(id: results.map(&:reference_id))
          .pluck(:id)
          .to_set

        results
          .select { |emb| tenant_ids.include?(emb.reference_id) }
          .map { |emb|
            {
              candidate_id: emb.reference_id,
              similarity: (1.0 - emb.neighbor_distance).clamp(0.0, 1.0)
            }
          }
          .select { |r| r[:similarity] >= threshold }
      end

      def text_search_applicable?(intent_result)
        return false unless intent_result
        return false if intent_result.skipped

        intent_result.elasticsearch_query.present?
      end

      def search_text(intent_result:, exclude_ids:, limit:)
        TextSearchService.new(account_id: @account_id).search(
          query: intent_result.elasticsearch_query,
          exclude_ids: exclude_ids,
          must_have_skills: intent_result.must_have_skills || [],
          limit: limit
        )
      end

      def fuse_results(vector_results:, text_results:, limit:)
        fused = RankFusionService.new.fuse(
          vector_results: vector_results,
          text_results: text_results,
          limit: limit
        )

        fused.map do |result|
          {
            candidate_id: result[:candidate_id],
            similarity: result[:similarity],
            source: result[:source],
            rrf_score: result[:rrf_score]
          }
        end
      end

      def log_fusion(vector_count, text_count)
        Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        Rails.logger.info "🔗 [HybridSearch] RECIPROCAL RANK FUSION"
        Rails.logger.info "   Vector results: #{vector_count}"
        Rails.logger.info "   Text results: #{text_count}"
        Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      end
    end
  end
end
