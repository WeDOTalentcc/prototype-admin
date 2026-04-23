module Candidates
  module Search
    class SearchExplainer
      attr_reader :request_id

      def initialize(request_id: SecureRandom.uuid)
        @request_id = request_id
        @steps = []
        @timings = {}
        @start_time = Time.current
      end

      def log_step(name, data = {})
        @steps << {
          step: name,
          timestamp: Time.current,
          elapsed_ms: ((Time.current - @start_time) * 1000).round(2),
          data: data
        }
      end

      def time(name)
        start = Time.current
        result = yield
        @timings[name] = ((Time.current - start) * 1000).round(2)
        result
      end

      def build_explanation(results, query:, filters:, es_results:, emb_results:, pool_info:)
        {
          request_id: @request_id,
          query: query,
          filters: filters.except(:account_id),

          sources: {
            elasticsearch: {
              count: es_results.size,
              top_3: es_results.first(3).map { |r| { id: r[:id], rank: r[:rank] } }
            },
            embedding: {
              count: emb_results.size,
              top_3: emb_results.first(3).map { |r| { id: r[:id], rank: r[:rank] } }
            }
          },

          fusion: {
            overlap: pool_info[:overlap],
            pool_size: pool_info[:new_pool],
            pool_adjusted: pool_info[:previous_pool] != pool_info[:new_pool]
          },

          results: {
            count: results.size,
            top_5_explained: results.first(5).map do |r|
              {
                id: r[:id],
                final_score: r[:final_score]&.round(4),
                rrf_score: r[:score]&.round(4),
                boost: r[:boost]&.round(4),
                contributions: r[:contributions],
                boost_reasons: r[:boost_reasons]
              }
            end
          },

          performance: {
            total_ms: ((Time.current - @start_time) * 1000).round(2),
            breakdown: @timings
          },

          steps: @steps
        }
      end
    end
  end
end
