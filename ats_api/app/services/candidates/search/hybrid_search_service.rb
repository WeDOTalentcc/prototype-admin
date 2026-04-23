module Candidates
  module Search
    class HybridSearchService
      Result = Struct.new(:candidates, :metadata, :explanation, :search_meta_by_id, keyword_init: true)

      def initialize(account_id:, tenant:, sourcing_id: nil, user_id: nil)
        @account_id = account_id
        @tenant = tenant
        @sourcing_id = sourcing_id
        @user_id = user_id

        @es_strategy = ElasticsearchStrategy.new(account_id: account_id)
        @emb_strategy = EmbeddingStrategy.new(account_id: account_id)
        @embedding_cache = EmbeddingCache.new
        @query_analyzer = QueryAnalyzer.new
        @hyde_expander = HydeQueryExpander.new

        @profile_extractor = ProfileExtractor.new
        @multi_query_generator = MultiQueryGenerator.new
        @hyde_generator = HydeDocumentGenerator.new
        @jd_processor = JobDescriptionProcessor.new
      end

      def search(query_text, user_filters: {}, limit: Configuration.final_limit, debug: false)
        telemetry = SearchTelemetry.new

        with_tenant do
          execute_search(query_text, user_filters, limit, telemetry, debug)
        end
      end

      private

      def execute_search(query_text, user_filters, limit, telemetry, debug)
        query_type = SimpleQueryDetector.detect(query_text)
        telemetry.event(:query_type_detected, type: query_type, length: query_text.to_s.length)
        Rails.logger.info("[HybridSearch] Query type: #{query_type}, Length: #{query_text.to_s.length}")

        return execute_simple_search(query_text, user_filters, limit, telemetry, debug) if query_type == :simple
        return execute_resume_search(query_text, user_filters, limit, telemetry) if query_type == :resume
        return execute_jd_search(query_text, user_filters, limit, telemetry) if query_type == :job_description

        execute_complex_search(query_text, user_filters, limit, telemetry, debug)
      end

      # ROTA RÁPIDA: Query simples — pula QueryAnalyzer (~1.3s a menos)
      def execute_simple_search(query_text, user_filters, limit, telemetry, debug)
        pool_size = effective_pool_size(limit)

        broadcast_search_step(:elasticsearch_running, pool_size: pool_size * 2)

        es_results = telemetry.time(:elasticsearch) do
          @es_strategy.search(
            query_text,
            user_filters: user_filters,
            pool_size: pool_size * 2
          )
        end

        broadcast_search_step(:embedding_running, pool_size: pool_size)

        embedding = telemetry.time(:embedding_fetch) do
          @embedding_cache.fetch(query_text, account_id: @account_id)
        end

        emb_results = telemetry.time(:embedding_search) do
          @emb_strategy.search(
            embedding,
            user_filters: user_filters,
            pool_size: pool_size
          )
        end

        emb_results = apply_embedding_relevance_filter(emb_results, telemetry, min_keep: limit)
        telemetry.event(:simple_search_results, es: es_results.size, emb: emb_results.size)

        broadcast_search_step(:fusion_running, es_count: es_results.size, emb_count: emb_results.size)

        fusion_weights = { elasticsearch: 0.70, embedding: 0.30 }
        fused = telemetry.time(:rank_fusion) do
          WeightedRankFusion.combine(
            { elasticsearch: es_results, embedding: emb_results },
            weights: fusion_weights
          )
        end

        if fused.size < limit && pool_size < Configuration.max_pool_size
          larger_pool = [ pool_size * 2, Configuration.max_pool_size ].min
          telemetry.event(:simple_search_low_results_retry, fused: fused.size, limit: limit, new_pool: larger_pool)
          Rails.logger.warn("[HybridSearch] Simple: fused=#{fused.size} < limit=#{limit}, retrying with pool=#{larger_pool}")

          es_results = @es_strategy.search(query_text, user_filters: user_filters, pool_size: larger_pool * 2)
          emb_results = @emb_strategy.search(embedding, user_filters: user_filters, pool_size: larger_pool)
          emb_results = apply_embedding_relevance_filter(emb_results, telemetry, min_keep: limit)
          fused = WeightedRankFusion.combine(
            { elasticsearch: es_results, embedding: emb_results },
            weights: fusion_weights
          )
          telemetry.event(:simple_search_after_retry, es: es_results.size, emb: emb_results.size, fused: fused.size)
        end

        if fused.size < limit
          Rails.logger.warn("[HybridSearch] Requested limit=#{limit}, returning #{fused.size} (es=#{es_results.size}, emb=#{emb_results.size}) - limited by matching candidates")
        end

        reranked = Reranker.apply(fused, limit: limit)
        candidates = load_in_order(reranked.first(limit).map(&:id))
        search_meta_by_id = build_search_meta_by_id(reranked.first(limit), candidates.map(&:id))
        candidates.first(5).each_with_index do |candidate, i|
          search_data = candidate.search_data rescue {}
          prev_exp = search_data[:previous_experiences] || []

          meta = search_meta_by_id[candidate.id] || {}
          source = meta[:source] || "unknown"
          score = meta[:score] || 0
        end

        telemetry.log_summary(result_count: candidates.size, account_id: @account_id, search_type: :simple)

        Result.new(
          candidates: candidates,
          metadata: {
            request_id: telemetry.request_id,
            count: candidates.size,
            search_type: :simple,
            query_analyzer_skipped: true
          },
          search_meta_by_id: search_meta_by_id,
          explanation: debug ? telemetry.build_simple_explanation(
            es_count: es_results.size,
            emb_count: emb_results.size,
            fusion_weights: fusion_weights
          ) : nil
        )
      end

      # ROTA CURRÍCULO: extração de perfil + multi-query para similaridade
      def execute_resume_search(resume_text, user_filters, limit, telemetry)
        Rails.logger.info("[HybridSearch] Using RESUME search path")

        broadcast_search_step(:query_analyzing, query_length: resume_text.length)

        extraction = telemetry.time(:profile_extraction) do
          @profile_extractor.extract(resume_text, source_type: :resume)
        end

        telemetry.event(:profile_extracted,
          confidence: extraction.confidence,
          method: extraction.extraction_method,
          missing: extraction.missing_fields
        )

        search_strategy = determine_search_strategy(extraction)

        multi_query_result = @multi_query_generator.generate(extraction.profile, context: :resume)
        telemetry.event(:multi_query_generated, count: multi_query_result.queries.size)

        pool_size = effective_pool_size(limit)

        broadcast_search_step(:elasticsearch_running, pool_size: pool_size)

        keywords = build_keywords_from_profile(extraction.profile)
        es_results = telemetry.time(:elasticsearch) do
          @es_strategy.search(keywords, user_filters: user_filters, pool_size: pool_size)
        end

        broadcast_search_step(:embedding_running, pool_size: pool_size)

        emb_results = telemetry.time(:multi_embedding_search) do
          execute_multi_query_embedding_search(
            multi_query_result,
            user_filters: user_filters,
            pool_size: pool_size
          )
        end

        emb_results = apply_embedding_relevance_filter(emb_results, telemetry, min_keep: limit)
        telemetry.event(:resume_search_results, es: es_results.size, emb: emb_results.size)

        broadcast_search_step(:fusion_running, es_count: es_results.size, emb_count: emb_results.size)

        fusion_weights = calculate_confidence_adjusted_weights(extraction.confidence, search_strategy)
        fused = telemetry.time(:rank_fusion) do
          WeightedRankFusion.combine(
            { elasticsearch: es_results, embedding: emb_results },
            weights: fusion_weights
          )
        end

        if fused.size < limit && pool_size < Configuration.max_pool_size
          larger_pool = [ pool_size * 2, Configuration.max_pool_size ].min
          telemetry.event(:resume_search_low_results_retry, fused: fused.size, limit: limit, new_pool: larger_pool)
          Rails.logger.warn("[HybridSearch] Resume: fused=#{fused.size} < limit=#{limit}, retrying with pool=#{larger_pool}")

          es_results = @es_strategy.search(keywords, user_filters: user_filters, pool_size: larger_pool)
          emb_results = execute_multi_query_embedding_search(
            multi_query_result,
            user_filters: user_filters,
            pool_size: larger_pool
          )
          emb_results = apply_embedding_relevance_filter(emb_results, telemetry, min_keep: limit)
          fused = WeightedRankFusion.combine(
            { elasticsearch: es_results, embedding: emb_results },
            weights: fusion_weights
          )
          telemetry.event(:resume_search_after_retry, es: es_results.size, emb: emb_results.size, fused: fused.size)
        end

        if fused.size < limit
          Rails.logger.warn("[HybridSearch] Requested limit=#{limit}, returning #{fused.size} (es=#{es_results.size}, emb=#{emb_results.size}) - limited by matching candidates")
        end

        reranked = Reranker.apply(fused, limit: limit)
        candidates = load_in_order(reranked.first(limit).map(&:id))
        search_meta_by_id = build_search_meta_by_id(reranked.first(limit), candidates.map(&:id))

        telemetry.log_summary(result_count: candidates.size, account_id: @account_id, search_type: :resume)

        Result.new(
          candidates: candidates,
          metadata: {
            request_id: telemetry.request_id,
            count: candidates.size,
            search_type: :resume,
            extraction_confidence: extraction.confidence,
            extraction_method: extraction.extraction_method,
            missing_fields: extraction.missing_fields,
            queries_generated: multi_query_result.queries.size,
            fusion_weights: fusion_weights,
            strategy_used: multi_query_result.strategy_used
          },
          search_meta_by_id: search_meta_by_id,
          explanation: nil
        )
      end

      def execute_jd_search(jd_text, user_filters, limit, telemetry)
        Rails.logger.info("[HybridSearch] Using JOB DESCRIPTION search path")

        broadcast_search_step(:query_analyzing, query_length: jd_text.length)

        processed_jd = telemetry.time(:jd_processing) do
          @jd_processor.process(jd_text)
        end

        telemetry.event(:jd_processed,
          required_count: processed_jd.required_skills.size,
          nice_to_have_count: processed_jd.nice_to_have_skills.size
        )

        pool_size = effective_pool_size(limit)

        broadcast_search_step(:elasticsearch_running, pool_size: pool_size * 2)

        es_query = build_jd_elasticsearch_query(processed_jd)
        es_results = telemetry.time(:elasticsearch) do
          @es_strategy.search(es_query, user_filters: user_filters, pool_size: pool_size * 2)
        end

        broadcast_search_step(:embedding_running, pool_size: pool_size)

        emb_results = telemetry.time(:jd_embedding_search) do
          execute_jd_embedding_search(processed_jd, user_filters: user_filters, pool_size: pool_size)
        end

        emb_results = apply_embedding_relevance_filter(emb_results, telemetry, min_keep: limit)

        broadcast_search_step(:fusion_running, es_count: es_results.size, emb_count: emb_results.size)

        fusion_weights = { elasticsearch: 0.60, embedding: 0.40 }
        fused = WeightedRankFusion.combine(
          { elasticsearch: es_results, embedding: emb_results },
          weights: fusion_weights
        )

        reranked = Reranker.apply(
          fused,
          limit: limit,
          custom_boost_config: processed_jd.boost_config
        )

        candidates = load_in_order(reranked.first(limit).map(&:id))
        search_meta_by_id = build_search_meta_by_id(reranked.first(limit), candidates.map(&:id))

        telemetry.log_summary(result_count: candidates.size, account_id: @account_id, search_type: :job_description)

        Result.new(
          candidates: candidates,
          metadata: {
            request_id: telemetry.request_id,
            count: candidates.size,
            search_type: :job_description,
            required_skills: processed_jd.required_skills,
            nice_to_have_skills: processed_jd.nice_to_have_skills,
            fusion_weights: fusion_weights
          },
          search_meta_by_id: search_meta_by_id,
          explanation: nil
        )
      end

      # ROTA COMPLEXA: QueryAnalyzer + HyDE (fluxo original)
      def execute_complex_search(query_text, user_filters, limit, telemetry, debug)
        Rails.logger.info("[HybridSearch] Using COMPLEX search path (with QueryAnalyzer)")

        broadcast_search_step(:query_analyzing, query_length: query_text.length)

        analysis = telemetry.time(:query_analysis) { @query_analyzer.analyze(query_text) }
        telemetry.event(:query_analyzed, confidence: analysis.confidence)

        hyde_text = @hyde_expander.expand(query_text)
        text_for_embedding = hyde_text.presence || analysis.embedding_query
        telemetry.event(:hyde_used, { length: hyde_text.length }) if hyde_text.present?

        embedding = telemetry.time(:embedding_fetch) do
          @embedding_cache.fetch(text_for_embedding, account_id: @account_id)
        end

        pool_size = Configuration.initial_pool_size
        es_pool = [ (pool_size * Configuration.es_pool_multiplier).to_i, Configuration.max_pool_size ].min
        emb_pool = [ (pool_size * Configuration.emb_pool_multiplier).to_i, Configuration.max_pool_size ].min
        max_retries = Configuration.max_pool_retries
        retry_count = 0

        broadcast_search_step(:elasticsearch_running, pool_size: es_pool)

        es_results = telemetry.time(:elasticsearch) do
          @es_strategy.search(
            analysis.elasticsearch_query,
            user_filters: user_filters,
            pool_size: es_pool
          )
        end

        broadcast_search_step(:embedding_running, pool_size: emb_pool)

        emb_results = telemetry.time(:embedding_search) do
          @emb_strategy.search(
            embedding,
            user_filters: user_filters,
            pool_size: emb_pool
          )
        end

        emb_results = apply_embedding_keyword_gate(emb_results, analysis, telemetry)
        telemetry.event(:initial_search, es: es_results.size, emb: emb_results.size)

        pool_adjustment = AdaptivePool.adjust(es_results, emb_results, current_pool: pool_size)

        while pool_adjustment.should_retry && retry_count < max_retries
          retry_count += 1
          new_pool = pool_adjustment.new_pool
          es_retry_pool = [ (new_pool * Configuration.es_pool_multiplier).to_i, Configuration.max_pool_size ].min
          emb_retry_pool = [ (new_pool * Configuration.emb_pool_multiplier).to_i, Configuration.max_pool_size ].min
          telemetry.event(:pool_retry, pool_adjustment.to_h.merge(retry: retry_count))

          es_results = @es_strategy.search(
            analysis.elasticsearch_query,
            user_filters: user_filters,
            pool_size: es_retry_pool
          )

          emb_results = @emb_strategy.search(
            embedding,
            user_filters: user_filters,
            pool_size: emb_retry_pool
          )
          emb_results = apply_embedding_keyword_gate(emb_results, analysis, telemetry)

          pool_adjustment = AdaptivePool.adjust(es_results, emb_results, current_pool: pool_adjustment.new_pool)
        end

        if retry_count >= max_retries && pool_adjustment.should_retry
          telemetry.event(:pool_retry_limit_reached, final_overlap: pool_adjustment.overlap)
        end

        if es_results.empty? && emb_results.empty?
          telemetry.event(:fallback_triggered)
          return handle_fallback(query_text, user_filters, limit, telemetry, analysis)
        end

        broadcast_search_step(:fusion_running, es_count: es_results.size, emb_count: emb_results.size)

        fusion_weights = fusion_weights_for(es_results.size, emb_results.size, pool_adjustment.overlap)
        fused = telemetry.time(:rank_fusion) do
          WeightedRankFusion.combine(
            { elasticsearch: es_results, embedding: emb_results },
            weights: fusion_weights
          )
        end

        if fused.size < limit
          Rails.logger.warn("[HybridSearch] Complex: requested limit=#{limit}, fused=#{fused.size} (es=#{es_results.size}, emb=#{emb_results.size}) - limited by matching candidates")
        end

        reranked = telemetry.time(:reranking) { Reranker.apply(fused, limit: limit) }
        use_es_first = pool_adjustment.overlap < Configuration.low_overlap_threshold && es_results.any?
        ordered_ids = nil
        final_reranked = nil

        if use_es_first
          ordered_ids = es_first_ordered_ids(es_results, emb_results, limit)
          reranked_by_id = reranked.each_with_object({}) { |c, h| h[c.id] = c }
          final_reranked = ordered_ids.map { |id| reranked_by_id[id] }.compact
          es_ids_set = es_results.map { |r| r[:id] }.uniq.to_set
          emb_only_used = ordered_ids.count { |id| !es_ids_set.include?(id) }
          telemetry.event(:es_first_ordering, es_count: es_results.size, emb_only_used: emb_only_used)
        end

        candidates = telemetry.time(:load_candidates) do
          if use_es_first && ordered_ids
            load_in_order(ordered_ids)
          else
            load_in_order(reranked.first(limit).map(&:id))
          end
        end

        final_reranked ||= reranked.first(limit)
        search_meta_by_id = build_search_meta_by_id(final_reranked, candidates.map(&:id))

        telemetry.log_summary(result_count: candidates.size, account_id: @account_id, search_type: :complex)

        Result.new(
          candidates: candidates,
          metadata: { request_id: telemetry.request_id, count: candidates.size, search_type: :complex },
          search_meta_by_id: search_meta_by_id,
          explanation: telemetry.build_explanation(
            results: final_reranked,
            query_analysis: analysis,
            pool_adjustment: pool_adjustment,
            es_count: es_results.size,
            emb_count: emb_results.size,
            es_query_used: analysis.elasticsearch_query,
            fusion_weights: fusion_weights,
            es_first_ordering: use_es_first,
            embedding_query_used: text_for_embedding,
            hyde_used: hyde_text.present?,
            force: debug
          )
        )
      end

      # Garante pool grande o suficiente para preencher o limit (ex.: limit=10 → pedir pelo menos 40)
      def effective_pool_size(limit)
        min_pool = (limit * 4).clamp(Configuration.min_pool_size, Configuration.max_pool_size)
        [ Configuration.initial_pool_size, min_pool ].max
      end

      def execute_multi_query_embedding_search(multi_query_result, user_filters:, pool_size:)
        all_results = []

        multi_query_result.queries.each_with_index do |query, idx|
          weight = multi_query_result.weights[idx]

          hyde_doc = @hyde_generator.generate(
            extract_profile_from_query(query),
            context: :resume,
            verbosity: :concise
          )

          embedding = @embedding_cache.fetch(hyde_doc, account_id: @account_id)

          results = @emb_strategy.search(
            embedding,
            user_filters: user_filters,
            pool_size: (pool_size * weight * 2).to_i.clamp(20, pool_size)
          )

          results.each { |r| r[:query_index] = idx }
          all_results.concat(results)
        end

        deduplicate_and_boost(all_results)
      end

      def extract_profile_from_query(query)
        words = query.split
        {
          "primary_role" => words.select { |w| w.match?(/\w{4,}/) }.first(2).join(" "),
          "core_technologies" => words.select { |w| w.match?(/^[A-Z]/) },
          "seniority" => words.find { |w| w.downcase.match?(/junior|pleno|senior/) } || "pleno"
        }
      end

      def deduplicate_and_boost(results)
        by_id = {}

        results.each do |result|
          id = result[:id]

          if by_id[id]
            by_id[id][:multi_query_boost] = (by_id[id][:multi_query_boost] || 1.0) + 0.15
            by_id[id][:query_hits] = (by_id[id][:query_hits] || 1) + 1
            by_id[id][:distance] = [ by_id[id][:distance], result[:distance] ].min
          else
            by_id[id] = result.merge(multi_query_boost: 1.0, query_hits: 1)
          end
        end

        by_id.values
          .sort_by { |r| r[:distance].to_f / r[:multi_query_boost] }
          .each_with_index
          .map { |r, idx| r.merge(rank: idx + 1) }
      end

      def determine_search_strategy(extraction)
        return :high_confidence if extraction.confidence >= 0.75
        return :medium_confidence if extraction.confidence >= 0.50

        :low_confidence
      end

      def calculate_confidence_adjusted_weights(confidence, strategy)
        base_weights = {
          high_confidence: { elasticsearch: 0.35, embedding: 0.65 },
          medium_confidence: { elasticsearch: 0.50, embedding: 0.50 },
          low_confidence: { elasticsearch: 0.70, embedding: 0.30 }
        }

        base_weights.fetch(strategy, base_weights[:medium_confidence])
      end

      def build_jd_elasticsearch_query(processed_jd)
        parts = []

        parts << processed_jd.required_skills.join(" ") if processed_jd.required_skills.any?
        parts << processed_jd.role_titles.first if processed_jd.role_titles.any?
        parts << processed_jd.nice_to_have_skills.first(3).join(" ") if processed_jd.nice_to_have_skills.any?

        parts.compact.join(" ")
      end

      def execute_jd_embedding_search(processed_jd, user_filters:, pool_size:)
        hyde_doc = @hyde_generator.generate(
          {
            "primary_role" => processed_jd.role_titles.first,
            "core_technologies" => processed_jd.required_skills,
            "transferable_skills" => processed_jd.nice_to_have_skills,
            "seniority" => processed_jd.seniority_range[:min],
            "industry" => processed_jd.industry_keywords.first
          },
          context: :job_description,
          verbosity: :standard
        )

        embedding = @embedding_cache.fetch(hyde_doc, account_id: @account_id)

        @emb_strategy.search(
          embedding,
          user_filters: user_filters,
          pool_size: pool_size
        )
      end

      # Filtra por relevância mínima; se min_keep presente, mantém pelo menos min_keep resultados
      # (para não devolver menos candidatos que o solicitado quando o usuário pede N)
      def apply_embedding_relevance_filter(emb_results, telemetry, min_keep: nil)
        return emb_results unless Configuration.embedding_keyword_gate?
        return emb_results if emb_results.empty?

        threshold = Configuration.embedding_relevance_threshold
        threshold_percent = threshold * 100.0

        filtered = emb_results.select do |result|
          distance = result[:distance].to_f
          relevance = (1.0 - distance) * 100.0
          relevance >= threshold_percent
        end

        # Garantir pelo menos min_keep resultados quando solicitado (ex.: limit=10)
        if min_keep.present? && filtered.size < min_keep && emb_results.size >= min_keep
          sorted = emb_results.sort_by { |r| r[:distance].to_f }
          filtered = sorted.first(min_keep)
          telemetry.event(
            :embedding_relevance_filter,
            before: emb_results.size,
            after: filtered.size,
            threshold: threshold_percent.round(1),
            min_keep_used: true
          )
        elsif filtered.size < emb_results.size
          avg = emb_results.sum { |r| (1.0 - r[:distance].to_f) * 100.0 } / emb_results.size.to_f
          telemetry.event(
            :embedding_relevance_filter,
            before: emb_results.size,
            after: filtered.size,
            threshold: threshold_percent.round(1),
            avg_relevance: avg.round(1)
          )
        end
        filtered
      end

      # Retorna [profile_hash, :extraction | :keyword_fallback] para o metadata (vagas variadas).
      def extract_key_profile_with_source(resume_text)
        text = resume_text.to_s[0, 5000]
        prompt = <<~PROMPT
          Analise este currículo e extraia características-chave para buscar candidatos SIMILARES.
          Currículo (truncado):
          #{text}
          Retorne APENAS um objeto JSON válido, sem markdown e sem texto antes/depois. Exemplo:
          {"seniority":"senior","years_experience":10,"primary_role":"CTO engenheiro de software","core_technologies":["Ruby on Rails","PHP","Laravel","Elasticsearch"],"transferable_skills":["liderança técnica","SaaS"],"industry":"tecnologia"}
          Campos obrigatórios: seniority, primary_role, core_technologies (array), transferable_skills (array). Use termos genéricos.
        PROMPT

        response = Llm::Gateway.chat(
          messages: [ { role: "user", content: prompt } ],
          temperature: 0.2,
          max_tokens: 500,
          tracking: { operation: "search.resume_profile_extraction" }
        )

        content = response.dig("choices", 0, "message", "content").to_s
        parsed = parse_profile_json(content)
        return [ parsed, :extraction ] if parsed.present?

        # Fallback: extrair keywords do currículo (variado por texto, não chumbado)
        Rails.logger.warn("[HybridSearch] Profile extraction failed or empty; using keyword fallback from resume text")
        [ build_profile_from_resume_keywords(resume_text), :keyword_fallback ]
      rescue => e
        Rails.logger.error("[HybridSearch] Profile extraction failed: #{e.message}")
        [ build_profile_from_resume_keywords(resume_text), :keyword_fallback ]
      end

      # Tenta extrair e parsear JSON da resposta do LLM (pode vir com markdown ou truncado)
      def parse_profile_json(content)
        return nil if content.blank?

        raw = content.gsub(/\A\s*```(?:json)?\s*/i, "").gsub(/\s*```\s*\z/, "").strip
        # Extrai o primeiro objeto JSON (do primeiro { até o último } balanceado)
        start_idx = raw.index("{")
        return nil unless start_idx

        depth = 0
        end_idx = nil
        raw[start_idx..].each_char.with_index do |c, i|
          depth += 1 if c == "{"
          depth -= 1 if c == "}"
          if depth == 0
            end_idx = start_idx + i
            break
          end
        end
        json_str = end_idx ? raw[start_idx..end_idx] : raw[start_idx..]
        # Tenta fechar colchetes/chaves se truncado
        json_str += "]" while json_str.count("[") > json_str.count("]")
        json_str += "}" while json_str.count("{") > json_str.count("}")

        data = JSON.parse(json_str)
        return nil unless data.is_a?(Hash)

        {
          "seniority" => data["seniority"].to_s.presence,
          "years_experience" => data["years_experience"].is_a?(Numeric) ? data["years_experience"] : nil,
          "primary_role" => data["primary_role"].to_s.presence,
          "core_technologies" => Array(data["core_technologies"]).map(&:to_s).reject(&:blank?).first(5),
          "transferable_skills" => Array(data["transferable_skills"]).map(&:to_s).reject(&:blank?).first(4),
          "industry" => data["industry"].to_s.presence
        }.compact
      rescue JSON::ParserError
        nil
      end

      # Fallback quando o LLM falha: extrai termos do currículo para montar perfil (variado por vaga, não chumbado).
      def build_profile_from_resume_keywords(resume_text)
        raw = resume_text.to_s[0, 6000]
        text = raw.downcase
        # Senioridade
        seniority = if text.match?(/\b(cto|ceo|tech\s*lead|gerente|diretor)\b/i) then "senior"
        elsif text.match?(/\bsenior\b/i) then "senior"
        elsif text.match?(/\bpleno\b/i) then "pleno"
        elsif text.match?(/\bjunior\b/i) then "junior"
        else "pleno"
        end
        # Cargo genérico
        primary_role = if text.match?(/\bcto\b|chief\s*technology/i) then "CTO engenheiro de software"
        elsif text.match?(/\bceo\b|chief\s*executive/i) then "CEO engenheiro de software"
        elsif text.match?(/\b(engenheiro|engineer)\s+(de\s+)?software/i) then "engenheiro de software"
        elsif text.match?(/\bdesenvolvedor|developer\b/i) then "desenvolvedor"
        else "desenvolvedor"
        end
        # Tecnologias: lista conhecida + termos significativos extraídos do texto (variado por currículo)
        tech_terms = %w[
          ruby rails php laravel javascript node react vue python java elasticsearch
          postgres mysql redis sidekiq docker aws saas nginx heroku unicorn
          typescript kotlin swift go golang scala c# dotnet angular next
        ]
        found_tech = tech_terms.select { |t| text.include?(t) }.first(5).map(&:titleize)
        # Termos do próprio texto (palavras 3+ chars que parecem tech/cargo, para variar por vaga)
        extracted = extract_significant_terms_from_text(raw)
        core_tech = (found_tech + extracted).uniq.first(5)
        # Skills transferíveis
        transferable = []
        transferable << "liderança técnica" if text.match?(/\b(cto|tech\s*lead|equipe|times)\b/i)
        transferable << "SaaS" if text.include?("saas")
        transferable << "desenvolvimento web" if text.match?(/\b(web|backend|frontend)\b/i)
        transferable = transferable.presence || [ "desenvolvimento de software" ]

        {
          "seniority" => seniority,
          "years_experience" => 5,
          "primary_role" => primary_role,
          "core_technologies" => core_tech,
          "transferable_skills" => transferable,
          "industry" => "tecnologia"
        }
      end

      # Extrai termos que parecem tecnologias/cargos do texto (primeiras linhas, palavras 3+ chars).
      # Evita fallback sempre "pleno desenvolvedor desenvolvimento de software" — varia por vaga.
      def extract_significant_terms_from_text(raw_text)
        return [] if raw_text.blank?

        # Palavras que costumam ser tech/ferramentas (preservar capitalização do texto)
        known_caps = %w[Ruby Rails PHP Laravel JavaScript Node React Vue Python Java TypeScript
                       Kotlin Swift Go Scala Angular Next.js AWS Docker Kubernetes]
        found = known_caps.select { |w| raw_text.include?(w) }
        return found.first(5) if found.any?

        # Fallback: palavras 4+ chars nas primeiras 1500 chars (evita ruído)
        words = raw_text[0, 1500].scan(/\b[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9.]{3,}\b/)
        freq = words.each_with_object(Hash.new(0)) { |w, h| h[w] += 1 }
        freq.sort_by { |_, c| -c }.map(&:first).reject { |w| w.length > 25 }.first(5)
      end

      def build_keywords_from_profile(profile)
        parts = []
        parts << profile["seniority"] if profile["seniority"].present?
        parts << profile["primary_role"] if profile["primary_role"].present?
        parts += Array(profile["core_technologies"]).first(3)
        parts += Array(profile["transferable_skills"]).first(2)
        parts.compact.reject(&:blank?).join(" ")
      end

      def generate_hyde_cv(profile)
        <<~CV.strip
          Profissional #{profile['seniority'] || 'pleno'} com #{profile['years_experience'] || 5} anos de experiência.
          Atuação como #{profile['primary_role'] || 'desenvolvedor'}.
          Tecnologias: #{Array(profile['core_technologies']).join(', ')}.
          Competências: #{Array(profile['transferable_skills']).join(', ')}.
          Setor: #{profile['industry'] || 'tecnologia'}.
        CV
      end

      def handle_fallback(query_text, user_filters, limit, telemetry, analysis)
        original_filter_keys = user_filters.keys

        embedding = @embedding_cache.fetch(analysis.embedding_query, account_id: @account_id)
        emb_only = @emb_strategy.search(embedding, user_filters: {}, pool_size: Configuration.max_pool_size)
        emb_only = apply_embedding_keyword_gate(emb_only, analysis, telemetry)

        if emb_only.any?
          telemetry.event(:fallback_embedding_only, count: emb_only.size)
          ids = emb_only.first(limit).map { |r| r[:id] }
          candidates = load_in_order(ids)
          search_meta_by_id = ids.to_h do |id|
            r = emb_only.find { |x| x[:id] == id }
            score = r && r[:distance] ? (1.0 - r[:distance].to_f).round(6) : nil
            [ id, { source: "embedding", score: score } ]
          end
          return Result.new(
            candidates: candidates,
            metadata: {
              request_id: telemetry.request_id,
              fallback: :embedding_only,
              filters_removed: original_filter_keys,
              message: "Não encontramos resultados com os filtros. Mostrando candidatos similares."
            },
            search_meta_by_id: search_meta_by_id,
            explanation: nil
          )
        end

        es_only = @es_strategy.search(query_text, user_filters: {}, pool_size: Configuration.max_pool_size)

        if es_only.any?
          telemetry.event(:fallback_es_only, count: es_only.size)
          ids = es_only.first(limit).map { |r| r[:id] }
          candidates = load_in_order(ids)
          search_meta_by_id = ids.to_h do |id|
            r = es_only.find { |x| x[:id] == id }
            score = r && r[:score] ? r[:score].to_f.round(6) : nil
            [ id, { source: "elasticsearch", score: score } ]
          end
          return Result.new(
            candidates: candidates,
            metadata: {
              request_id: telemetry.request_id,
              fallback: :es_only,
              filters_removed: original_filter_keys,
              message: "Não encontramos resultados com os filtros. Mostrando candidatos por palavra-chave."
            },
            search_meta_by_id: search_meta_by_id,
            explanation: nil
          )
        end

        telemetry.event(:no_results)
        telemetry.log_summary(result_count: 0, account_id: @account_id)

        Result.new(
          candidates: [],
          metadata: {
            request_id: telemetry.request_id,
            fallback: :none,
            filters_applied: original_filter_keys,
            message: "Nenhum candidato encontrado."
          },
          search_meta_by_id: {},
          explanation: nil
        )
      end

      def load_in_order(ids)
        return [] if ids.empty?

        candidates_by_id = Candidate.where(id: ids).index_by(&:id)
        ids.filter_map { |id| candidates_by_id[id] }
      end

      # Quando overlap é 0 e ES trouxe poucos resultados, aumenta peso do ES para não deixar embedding dominar
      # Mantém só candidatos do embedding que tenham pelo menos 1 termo da busca no currículo ou cargo (evita perfis irrelevantes).
      def apply_embedding_keyword_gate(emb_results, analysis, telemetry)
        return emb_results unless Configuration.embedding_keyword_gate?
        return emb_results if emb_results.empty?

        terms = extract_search_terms(analysis)
        return emb_results if terms.empty?

        ids = emb_results.map { |r| r[:id] }.uniq
        allowed_ids = candidate_ids_with_any_keyword(ids, terms)
        filtered = emb_results.select { |r| allowed_ids.include?(r[:id]) }

        if filtered.size < emb_results.size
          telemetry.event(:embedding_keyword_gate, before: emb_results.size, after: filtered.size, terms_count: terms.size)
        end
        filtered
      end

      def extract_search_terms(analysis)
        query = analysis.elasticsearch_query.presence || analysis.original_query.to_s
        query.to_s.split(/\s+/).map(&:strip).reject { |w| w.size < 2 }.uniq
      end

      def candidate_ids_with_any_keyword(candidate_ids, terms)
        return candidate_ids.to_set if terms.empty?

        conn = Candidate.connection
        conditions = terms.map do |t|
          pattern = "%#{ActiveRecord::Base.sanitize_sql_like(t)}%"
          "(curriculum_text ILIKE #{conn.quote(pattern)} OR role_name ILIKE #{conn.quote(pattern)})"
        end.join(" OR ")

        Candidate.where(id: candidate_ids).where(conditions).pluck(:id).to_set
      end

      # Por candidato: origem da busca (elasticsearch, embedding, both) e score para estatísticas
      def build_search_meta_by_id(final_reranked, candidate_ids)
        by_id = final_reranked.each_with_object({}) { |c, h| h[c.id] = c }
        candidate_ids.to_h do |id|
          r = by_id[id]
          if r
            source = search_source_from_contributions(r.contributions)
            [ id, { source: source, score: r.final_score&.round(6) } ]
          else
            [ id, { source: nil, score: nil } ]
          end
        end
      end

      def search_source_from_contributions(contributions)
        keys = contributions.is_a?(Hash) ? contributions.keys.map(&:to_sym) : []
        return "both" if keys.include?(:elasticsearch) && keys.include?(:embedding)
        return "elasticsearch" if keys.include?(:elasticsearch)
        return "embedding" if keys.include?(:embedding)
        nil
      end

      # Ordem: primeiro todos os IDs do ES (na ordem do ES), depois IDs só do embedding (na ordem do embedding), até limit
      def es_first_ordered_ids(es_results, emb_results, limit)
        es_ids = es_results.map { |r| r[:id] }.uniq
        emb_ids = emb_results.map { |r| r[:id] }.uniq
        emb_only = emb_ids - es_ids
        (es_ids + emb_only).first(limit)
      end

      def fusion_weights_for(es_count, emb_count, overlap)
        default = Configuration.default_weights
        return default if overlap > 0
        return default if es_count >= 5
        # ES trouxe muito pouco e embedding trouxe vários → prioriza ES (evita "Solutions Architects" irrelevantes)
        if es_count <= 2 && emb_count >= 5
          return { elasticsearch: 0.80, embedding: 0.20 }
        end
        if es_count <= 5 && emb_count >= 10
          return { elasticsearch: 0.70, embedding: 0.30 }
        end
        default
      end

      def with_tenant(&block)
        Apartment::Tenant.switch(@tenant, &block)
      end

      def broadcast_search_step(step, **metadata)
        return unless @sourcing_id && @user_id

        event_messages = {
          query_analyzing: "Analisando consulta...",
          elasticsearch_running: "Buscando candidatos no banco de dados...",
          embedding_running: "Processamento semântico em andamento...",
          fusion_running: "Combinando e classificando resultados..."
        }

        SourcingChannel.broadcast_to(
          "#{@user_id}_sourcing_#{@sourcing_id}",
          {
            type: "search_#{step}",
            sourcing_id: @sourcing_id,
            search_type: "local",
            timestamp: Time.current.iso8601,
            message: event_messages[step]
          }.merge(metadata)
        )
      rescue => e
        Rails.logger.error("[HybridSearch] Failed to broadcast #{step}: #{e.message}")
      end
    end
  end
end
