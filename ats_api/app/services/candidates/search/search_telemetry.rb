module Candidates
  module Search
    class SearchTelemetry
      attr_reader :request_id

      def initialize
        @request_id = SecureRandom.uuid
        @start_time = Process.clock_gettime(Process::CLOCK_MONOTONIC)
        @timings = {}
        @events = []
      end

      def time(name)
        start = Process.clock_gettime(Process::CLOCK_MONOTONIC)
        result = yield
        @timings[name] = ((Process.clock_gettime(Process::CLOCK_MONOTONIC) - start) * 1000).round(2)
        result
      end

      def event(name, data = {})
        @events << {
          name: name,
          elapsed_ms: elapsed_ms,
          data: sanitize_data(data)
        }
      end

      def elapsed_ms
        ((Process.clock_gettime(Process::CLOCK_MONOTONIC) - @start_time) * 1000).round(2)
      end

      def log_summary(result_count:, account_id: nil, search_type: nil)
        payload = {
          event: "hybrid_search_completed",
          request_id: @request_id,
          result_count: result_count,
          total_ms: elapsed_ms,
          timings: @timings
        }
        payload[:search_type] = search_type if search_type.present?
        payload[:account_id] = account_id if account_id.present?
        Rails.logger.info(payload.to_json)
      end

      def build_simple_explanation(es_count:, emb_count:, fusion_weights: nil)
        return nil unless Configuration.debug_enabled?

        {
          request_id: @request_id,
          search_path: "simple",
          sources: { elasticsearch: { count: es_count }, embedding: { count: emb_count } },
          fusion_weights: fusion_weights,
          performance: { total_ms: elapsed_ms, breakdown: @timings },
          events: @events
        }
      end

      def build_explanation(results:, query_analysis:, pool_adjustment:, es_count:, emb_count:, force: false, es_query_used: nil, fusion_weights: nil, es_first_ordering: false, embedding_query_used: nil, hyde_used: false)
        return nil unless Configuration.debug_enabled? || force

        explanation = {
          request_id: @request_id,

          query: {
            original: query_analysis.original_query,
            elasticsearch_query: es_query_used || query_analysis.original_query,
            embedding_query: embedding_query_used.presence || query_analysis.embedding_query,
            expanded_terms: query_analysis.expanded_terms,
            confidence: query_analysis.confidence
          },

          sources: {
            elasticsearch: { count: es_count },
            embedding: { count: emb_count }
          },

          pool: pool_adjustment.to_h,

          results: {
            count: results.size,
            top_5: results.first(5).map(&:to_h)
          },

          performance: {
            total_ms: elapsed_ms,
            breakdown: @timings
          },

          events: @events
        }
        explanation[:fusion_weights] = fusion_weights if fusion_weights.present?
        explanation[:es_first_ordering] = es_first_ordering if es_first_ordering
        explanation[:hyde_used] = hyde_used if hyde_used
        explanation
      end

      private

      def sanitize_data(data)
        data.except(:account_id, :email, :cpf, :phone)
      end
    end
  end
end
