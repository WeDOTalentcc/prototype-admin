module Candidates
  module Search
    class WeightedRankFusion
      K = Configuration.rrf_k_constant

      class << self
        def combine(result_sets, weights: nil)
          weights ||= Configuration.default_weights

          scores = Hash.new { |h, k| h[k] = RankedCandidate.new(k) }

          result_sets.each do |source, results|
            weight = weights[source.to_sym] || 0.5

            results.each do |result|
              candidate = scores[result[:id]]
              candidate.add_contribution(
                source: source,
                rank: result[:rank],
                weight: weight,
                k: K,
                raw_score: result[:score] || result[:distance]
              )
            end
          end

          scores.values.sort_by { |c| -c.final_score }
        end
      end
    end

    class RankedCandidate
      attr_reader :id, :contributions

      def initialize(id)
        @id = id
        @contributions = {}
        @score = 0.0
      end

      def add_contribution(source:, rank:, weight:, k:, raw_score: nil)
        rrf_score = 1.0 / (k + rank)
        weighted_score = weight * rrf_score

        @contributions[source] = {
          rank: rank,
          rrf_score: rrf_score.round(6),
          weighted_score: weighted_score.round(6),
          raw_score: raw_score
        }

        @score += weighted_score
      end

      def final_score
        @score
      end

      def appeared_in_both?
        contributions.size > 1
      end

      def sources
        contributions.keys
      end

      def to_h
        {
          id: id,
          score: final_score.round(6),
          contributions: contributions,
          sources: sources,
          in_both: appeared_in_both?
        }
      end
    end
  end
end
