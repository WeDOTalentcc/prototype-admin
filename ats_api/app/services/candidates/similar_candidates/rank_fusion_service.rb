# frozen_string_literal: true

module Candidates
  module SimilarCandidates
    class RankFusionService
      DEFAULT_K = 60
      DEFAULT_VECTOR_WEIGHT = 0.6
      DEFAULT_TEXT_WEIGHT = 0.4
      MIN_TEXT_RATIO = 0.3

      def initialize(k: DEFAULT_K, vector_weight: DEFAULT_VECTOR_WEIGHT, text_weight: DEFAULT_TEXT_WEIGHT)
        @k = k
        @vector_weight = vector_weight
        @text_weight = text_weight
      end

      def fuse(vector_results:, text_results:, limit:)
        return vector_results if text_results.empty?
        return text_results if vector_results.empty?

        scored = compute_rrf_scores(vector_results, text_results)
        interleave(scored, limit)
      end

      private

      def compute_rrf_scores(vector_results, text_results)
        vector_rankings = build_rankings(vector_results)
        text_rankings = build_rankings(text_results)
        all_candidate_ids = (vector_rankings.keys + text_rankings.keys).uniq

        all_candidate_ids.map do |cid|
          vector_rank = vector_rankings[cid]
          text_rank = text_rankings[cid]

          rrf_score = 0.0
          rrf_score += @vector_weight * (1.0 / (@k + vector_rank)) if vector_rank
          rrf_score += @text_weight * (1.0 / (@k + text_rank)) if text_rank

          {
            candidate_id: cid,
            rrf_score: rrf_score,
            similarity: find_similarity(cid, vector_results, text_results),
            source: determine_source(vector_rank, text_rank)
          }
        end
      end

      def interleave(scored, limit)
        both, rest = scored.partition { |r| r[:source] == :both }
        text_only = rest.select { |r| r[:source] == :text }.sort_by { |r| -r[:rrf_score] }
        vector_only = rest.select { |r| r[:source] == :vector }.sort_by { |r| -r[:rrf_score] }

        both_sorted = both.sort_by { |r| -r[:rrf_score] }
        return (both_sorted + vector_only + text_only).first(limit) if text_only.empty?

        remaining = limit - both_sorted.size
        return both_sorted.first(limit) if remaining <= 0

        min_text = (remaining * MIN_TEXT_RATIO).ceil
        text_slots = [ min_text, text_only.size ].min
        vector_slots = remaining - text_slots

        both_sorted
          .concat(vector_only.first(vector_slots))
          .concat(text_only.first(text_slots))
          .first(limit)
      end

      def build_rankings(results)
        results.each_with_index.each_with_object({}) do |(result, index), rankings|
          rankings[result[:candidate_id]] = index + 1
        end
      end

      def determine_source(vector_rank, text_rank)
        return :both if vector_rank && text_rank
        return :vector if vector_rank

        :text
      end

      def find_similarity(candidate_id, vector_results, text_results)
        vec = vector_results.find { |r| r[:candidate_id] == candidate_id }
        return vec[:similarity] if vec

        txt = text_results.find { |r| r[:candidate_id] == candidate_id }
        txt&.dig(:similarity) || 0.0
      end
    end
  end
end
