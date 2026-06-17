# frozen_string_literal: true

module Candidates
  module SimilarCandidates
    class EmbeddingRefinementService
      ALPHA = 0.3
      BETA = 0.2

      def initialize(original_centroid:)
        @original = original_centroid
        @dims = original_centroid.size
      end

      def refine(liked_ids:, disliked_ids: [])
        refined = @original.dup

        refined = apply_liked_adjustment(refined, liked_ids) if liked_ids.any?
        refined = apply_disliked_adjustment(refined, disliked_ids) if disliked_ids.any?

        normalize(refined)
      end

      private

      def apply_liked_adjustment(vector, liked_ids)
        centroid = compute_centroid(liked_ids)
        return vector unless centroid

        apply_vector_adjustment(vector, centroid, ALPHA)
      end

      def apply_disliked_adjustment(vector, disliked_ids)
        centroid = compute_centroid(disliked_ids)
        return vector unless centroid

        apply_vector_adjustment(vector, centroid, -BETA)
      end

      def apply_vector_adjustment(vector, target_centroid, weight)
        adjusted = vector.dup
        @dims.times { |i| adjusted[i] += weight * (target_centroid[i] - @original[i]) }
        adjusted
      end

      def compute_centroid(candidate_ids)
        vectors = fetch_vectors(candidate_ids)
        return nil if vectors.empty?

        average_vectors(vectors)
      end

      def fetch_vectors(candidate_ids)
        Embedding
          .where(reference_type: "Candidate", reference_id: candidate_ids)
          .pluck(:embedding)
      end

      def average_vectors(vectors)
        return vectors.first if vectors.one?

        centroid = Array.new(@dims, 0.0)
        vectors.each { |vec| vec.each_with_index { |v, i| centroid[i] += v } }
        centroid.map { |v| v / vectors.size }
      end

      def normalize(vector)
        magnitude = compute_magnitude(vector)
        return vector if magnitude.zero?

        vector.map { |v| v / magnitude }
      end

      def compute_magnitude(vector)
        Math.sqrt(vector.sum { |v| v**2 })
      end
    end
  end
end
