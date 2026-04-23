module Candidates
  module Search
    class AdaptivePool
      class << self
        def calculate_overlap(ids_a, ids_b)
          return 0.0 if ids_a.empty? || ids_b.empty?

          intersection = (ids_a & ids_b).size
          union = (ids_a | ids_b).size

          intersection.to_f / union
        end

        def adjust(es_results, emb_results, current_pool:)
          es_ids = es_results.map { |r| r[:id] }
          emb_ids = emb_results.map { |r| r[:id] }

          overlap = calculate_overlap(es_ids, emb_ids)

          new_pool = calculate_new_pool(overlap, current_pool)
          should_retry = overlap < Configuration.low_overlap_threshold &&
                         current_pool < Configuration.max_pool_size

          PoolAdjustment.new(
            overlap: overlap,
            previous_pool: current_pool,
            new_pool: new_pool,
            should_retry: should_retry,
            es_count: es_ids.size,
            emb_count: emb_ids.size,
            intersection_count: (es_ids & emb_ids).size
          )
        end

        private

        def calculate_new_pool(overlap, current)
          if overlap < Configuration.low_overlap_threshold
            [ (current * 1.5).to_i, Configuration.max_pool_size ].min
          elsif overlap > Configuration.high_overlap_threshold
            [ (current * 0.8).to_i, Configuration.min_pool_size ].max
          else
            current
          end
        end
      end
    end

    class PoolAdjustment
      attr_reader :overlap, :previous_pool, :new_pool, :should_retry,
                  :es_count, :emb_count, :intersection_count

      def initialize(overlap:, previous_pool:, new_pool:, should_retry:,
                     es_count:, emb_count:, intersection_count:)
        @overlap = overlap
        @previous_pool = previous_pool
        @new_pool = new_pool
        @should_retry = should_retry
        @es_count = es_count
        @emb_count = emb_count
        @intersection_count = intersection_count
      end

      def pool_changed?
        previous_pool != new_pool
      end

      def to_h
        {
          overlap: overlap.round(3),
          previous_pool: previous_pool,
          new_pool: new_pool,
          should_retry: should_retry,
          es_count: es_count,
          emb_count: emb_count,
          intersection_count: intersection_count
        }
      end
    end
  end
end
