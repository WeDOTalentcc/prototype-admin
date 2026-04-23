module Candidates
  module Search
    class Configuration
      class << self
        def initial_pool_size = 100
        def min_pool_size = 50
        def max_pool_size = 300
        def final_limit = 50
        def max_pool_retries = 2

        def rrf_k_constant = 60
        # Por enquanto: mais resultados ES do que embedding (peso maior no ES na fusão RRF)
        def default_weights = { elasticsearch: 0.65, embedding: 0.35 }.freeze
        # Pool: pedir mais do ES e menos do embedding para ter mais ES no resultado final
        def es_pool_multiplier = 1.25
        def emb_pool_multiplier = 0.8

        def min_results_threshold = 5
        def low_overlap_threshold = 0.2
        def high_overlap_threshold = 0.5

        def embedding_cache_ttl = 24.hours
        def query_analysis_cache_ttl = 1.hour
        def query_analyzer_timeout = 0.3
        def embedding_model_version = ENV.fetch("EMBEDDING_MODEL_VERSION", "v1")
        def embedding_model_name = Llm::ClientFactory.embedding_model

        # Require curriculum_text for candidates to appear in search results
        def require_curriculum_text? = ENV.fetch("REQUIRE_CURRICULUM_TEXT", "true") == "true"

        # Máxima distância (cosine) para aceitar resultado do embedding; nil = sem filtro.
        # Menor = mais similar (0 = idêntico). Ex: 0.5 ou 0.6 descarta matches fracos.
        def embedding_max_distance
          val = ENV["EMBEDDING_MAX_DISTANCE"]
          val.present? ? val.to_f : nil
        end

        # Ativar filtro mínimo de relevância dos resultados do embedding.
        def embedding_keyword_gate? = ENV.fetch("EMBEDDING_KEYWORD_GATE", "true") == "true"

        def embedding_relevance_threshold
          ENV.fetch("EMBEDDING_RELEVANCE_THRESHOLD", "0.70").to_f
        end

        def locked_filters = [ :account_id, :is_deleted ].freeze

        def pgvector_allowed_filters
          [
            :city,
            :state,
            :country,
            :remote_work,
            :position_level,
            :years_of_experience_min,
            :years_of_experience_max,
            :current_role_time_min,
            :current_role_time_max,
            :average_time_in_companies_min,
            :average_time_in_companies_max,
            :role_name,
            :experiences_a,
            :previous_experiences,
            :sectors_a
          ].freeze
        end

        def rerank_signals
          {
            profile_completeness: { weight: 0.10, threshold: 0.7 },  # Increased from 5%
            has_contact_info: { weight: 0.05 },                      # Increased from 3%
            has_curriculum: { weight: 0.08 },                        # NEW
            recent_activity: { weight: 0.03, days: 30 },
            has_experience: { weight: 0.04 },                        # Increased from 2%
            has_skills: { weight: 0.03 }                             # Increased from 2%
          }.freeze
        end

        def penalty_signals
          {
            low_completeness: { weight: -0.15, threshold: 0.4 },
            medium_completeness: { weight: -0.08, threshold: 0.6 },
            missing_curriculum: { weight: -0.12 }
          }.freeze
        end

        def completeness_fields
          [
            :name, :email, :phone, :city, :state,
            :role_name, :self_introduction, :current_company
          ].freeze
        end

        def debug_enabled? = ENV.fetch("SEARCH_DEBUG_ENABLED", "false") == "true"
        def log_top_ids_count = 0
        def log_timings? = true
      end
    end
  end
end
