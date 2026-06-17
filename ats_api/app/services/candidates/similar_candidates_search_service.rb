# frozen_string_literal: true

module Candidates
  class SimilarCandidatesSearchService
    MIN_CANDIDATES = 1
    MAX_CANDIDATES = 10
    DEFAULT_LIMIT = 20
    MAX_LIMIT = 50
    DEFAULT_THRESHOLD = 0.60
    POOL_MULTIPLIER = 3
    MIN_POOL_SIZE = 60
    MAX_SHARED_SIGNALS = 8
    MIN_TOKEN_LENGTH = 3
    CACHE_TTL = 24.hours
    SEARCH_TYPE_SIMILARITY = "similarity"
    PROVIDER_LOCAL = "local"
    PROVIDER_GLOBAL = "global"
    PROVIDER_PEARCH = "pearch"
    PROVIDER_HYBRID = "hybrid"
    STATUS_DONE = "done"
    STATUS_NEW = "new"
    GENDER_MALE = 1
    GENDER_FEMALE = 2
    GENDER_NON_BINARY = 3
    GENDER_UNKNOWN = 0

    STOPWORDS = Set.new(%w[
      que para com por uma como mais sobre entre quando muito desde onde esta
      sao tem sido pode sua seu seus suas anos experiencia profissional
      trabalho empresa area tambem ainda sendo foram fazer pode apos
      das dos nos nas pelo pela pelos pelas esse essa esses essas
      este esta estes estas isso isto aqui ali aquele aquela
      the and for with from that this are was were has have had
      not but also been being will would could should may might
    ]).freeze

    def initialize(account:, user:)
      @account = account
      @user = user
    end

    def call(candidate_ids:, job_id: nil, limit: DEFAULT_LIMIT, threshold: DEFAULT_THRESHOLD,
             exclude_ids: [], sources: [ "local" ], pearch_options: {}, skip_cache: false)
      start_time = Process.clock_gettime(Process::CLOCK_MONOTONIC)

      validate_params!(candidate_ids, limit, threshold, sources)
      base_candidates = load_base_candidates(candidate_ids)

      unless skip_cache
        cached = find_cached_sourcing(candidate_ids, job_id, threshold, sources)
        if cached
          return build_cached_response(cached, base_candidates, start_time)
        end
      end

      local_results = []
      global_data = {}
      warnings = []

      if sources.include?(PROVIDER_LOCAL)
        local_results = search_local(
          base_candidates: base_candidates,
          candidate_ids: candidate_ids,
          job_id: job_id,
          limit: limit,
          threshold: threshold,
          exclude_ids: exclude_ids
        )
      end

      if sources.include?(PROVIDER_GLOBAL)
        global_data = search_global(
          base_candidates: base_candidates,
          pearch_options: pearch_options
        )
        warnings << build_warning_message(global_data) if global_data[:error]
      end

      duration = duration_ms(start_time)
      provider = determine_provider(sources)

      sourcing = create_sourcing(
        candidate_ids: candidate_ids,
        job_id: job_id,
        results_count: local_results.size + (global_data[:results]&.size || 0),
        local_count: local_results.size,
        global_count: global_data[:results]&.size || 0,
        duration: duration,
        provider: provider,
        credits_used: global_data[:credits_used],
        synthesis: global_data[:synthesis]
      )

      enriched_local = process_local_results(local_results, base_candidates, sourcing)
      enriched_global = process_global_results(global_data[:results] || [], sourcing)

      build_response(
        sourcing: sourcing,
        base_candidates: base_candidates,
        local_results: enriched_local,
        global_results: enriched_global,
        candidate_ids: candidate_ids,
        exclude_ids: exclude_ids,
        duration: duration,
        threshold: threshold,
        warnings: warnings
      )
    end

    private

    def find_cached_sourcing(candidate_ids, job_id, threshold, sources)
      sorted_ids = candidate_ids.sort
      provider = determine_provider(sources)

      query = Sourcing
        .where(account_id: @account.id, user_id: @user.id, provider: provider, status: STATUS_DONE)
        .where("(parameters->>'search_type') = ?", SEARCH_TYPE_SIMILARITY)
        .where("(parameters->>'base_candidate_ids') = ?", sorted_ids.to_json)
        .where("(search_metadata->>'threshold') = ?", threshold.to_s)
        .where("searched_at >= ?", CACHE_TTL.ago)

      query = query.where("(parameters->>'job_id') = ?", job_id.to_s) if job_id.present?

      query.order(searched_at: :desc).first
    end

    def build_cached_response(sourcing, base_candidates, start_time)
      local_profiles, global_profiles = partition_cached_profiles(sourcing, base_candidates)

      {
        sourcing_id: sourcing.id,
        sourcing_uid: sourcing.uid,
        mode: sourcing.provider,
        search_type: SEARCH_TYPE_SIMILARITY,
        base_candidates: serialize_base_candidates(base_candidates),
        similar_candidates: { local: local_profiles, global: global_profiles },
        total: local_profiles.size + global_profiles.size,
        local_count: local_profiles.size,
        global_count: global_profiles.size,
        excluded_count: 0,
        from_cache: true,
        cached_at: sourcing.searched_at,
        metadata: build_cached_metadata(sourcing, base_candidates, start_time)
      }
    end

    def partition_cached_profiles(sourcing, base_candidates)
      local_profiles = []
      global_profiles = []

      load_cached_sourced_profiles(sourcing).each do |sps|
        profile = sps.sourced_profile
        next unless profile

        base_result = build_cached_profile_result(profile, sps)

        if local_provider?(profile)
          local_profiles << enrich_local_cached_result(base_result, profile, base_candidates)
        else
          global_profiles << enrich_global_cached_result(base_result, profile, sps)
        end
      end

      [ local_profiles, global_profiles ]
    end

    def load_cached_sourced_profiles(sourcing)
      SourcedProfileSourcing
        .where(sourcing_id: sourcing.id, is_deleted: false)
        .includes(:sourced_profile)
        .order(similarity_score: :desc)
    end

    def build_cached_profile_result(profile, sps)
      {
        candidate_id: profile.candidate_id,
        sourced_profile_id: profile.id,
        name: profile.name,
        role_name: profile.role_name,
        current_company: profile.current_company,
        location: [ profile.city, profile.state ].compact.join(", "),
        similarity_score: sps.similarity_score
      }
    end

    def local_provider?(profile)
      profile.provider == PROVIDER_LOCAL
    end

    def enrich_local_cached_result(result, profile, base_candidates)
      result.merge(
        source: PROVIDER_LOCAL,
        shared_signals: extract_shared_signals_from_text(profile.curriculum_text, base_candidates)
      )
    end

    def enrich_global_cached_result(result, profile, sps)
      result.merge(
        source: PROVIDER_GLOBAL,
        docid: profile.external_id,
        pearch_score: sps.ai_metadata&.dig("pearch_score"),
        expertise: profile.expertise || [],
        insights: sps.ai_metadata&.dig("insights") || {}
      )
    end

    def build_cached_metadata(sourcing, base_candidates, start_time)
      {
        embedding_model: Llm::ClientFactory.embedding_model,
        search_method: base_candidates.size == 1 ? "single" : "centroid",
        base_count: base_candidates.size,
        duration_ms: duration_ms(start_time),
        threshold: sourcing.search_metadata&.dig("threshold"),
        original_duration_ms: sourcing.duration,
        credits_used: sourcing.credits_used
      }.compact
    end

    def extract_shared_signals_from_text(curriculum_text, base_candidates)
      return [] if curriculum_text.blank?

      base_tokens = base_candidates.flat_map { |c| tokenize(c.curriculum_text) }.uniq
      candidate_tokens = tokenize(curriculum_text)
      (base_tokens & candidate_tokens).sort_by { |t| -t.length }.first(MAX_SHARED_SIGNALS)
    end

    def validate_params!(candidate_ids, limit, threshold, sources)
      raise ArgumentError, "candidate_ids must contain #{MIN_CANDIDATES} to #{MAX_CANDIDATES} valid IDs" unless candidate_ids.is_a?(Array) &&
        candidate_ids.size.between?(MIN_CANDIDATES, MAX_CANDIDATES)

      raise ArgumentError, "limit must be between 1 and #{MAX_LIMIT}" unless limit.between?(1, MAX_LIMIT)
      raise ArgumentError, "threshold must be between 0.0 and 1.0" unless threshold.between?(0.0, 1.0)
      raise ArgumentError, "sources must be an array containing 'local' and/or 'global'" unless sources.is_a?(Array) && sources.all? { |s| %w[local global].include?(s) }
      raise ArgumentError, "sources cannot be empty" if sources.empty?
    end

    def load_base_candidates(candidate_ids)
      candidates = Candidate.where(id: candidate_ids, account_id: @account.id, is_deleted: false)
      missing = candidate_ids - candidates.map(&:id)
      raise ActiveRecord::RecordNotFound, "Candidates not found: #{missing.join(', ')}" if missing.any?

      candidates
    end

    def compute_search_embedding(base_candidates)
      embeddings = Embedding
        .where(reference_type: "Candidate", reference_id: base_candidates.map(&:id))
        .pluck(:reference_id, :embedding)

      missing = base_candidates.map(&:id) - embeddings.map(&:first)
      raise ArgumentError, "missing_embeddings:#{missing.join(',')}" if missing.any?

      vectors = embeddings.map(&:last)
      return vectors.first if vectors.size == 1

      dims = vectors.first.size
      centroid = Array.new(dims, 0.0)
      vectors.each { |vec| vec.each_with_index { |val, i| centroid[i] += val } }
      centroid.map { |v| v / vectors.size }
    end

    def build_exclude_ids(candidate_ids, job_id, extra_exclude_ids)
      ids = candidate_ids.dup
      ids += fetch_applied_candidate_ids(job_id) if job_id.present?
      ids += extra_exclude_ids if extra_exclude_ids.present?
      ids.uniq
    end

    def fetch_applied_candidate_ids(job_id)
      Apply.where(job_id: job_id, is_deleted: false).pluck(:candidate_id)
    end

    def determine_provider(sources)
      return PROVIDER_HYBRID if sources.include?(PROVIDER_LOCAL) && sources.include?(PROVIDER_GLOBAL)
      return PROVIDER_PEARCH if sources.include?(PROVIDER_GLOBAL)

      PROVIDER_LOCAL
    end

    def search_local(base_candidates:, candidate_ids:, job_id:, limit:, threshold:, exclude_ids:)
      search_embedding = compute_search_embedding(base_candidates)
      all_exclude_ids = build_exclude_ids(candidate_ids, job_id, exclude_ids)
      search_similar(search_embedding, all_exclude_ids, limit, threshold)
    end

    def search_global(base_candidates:, pearch_options:)
      strategy = SimilarCandidates::GlobalSearchStrategy.new(
        account: @account,
        user: @user
      )

      strategy.search(
        base_candidates: base_candidates,
        exclude_docids: collect_existing_docids,
        pearch_options: pearch_options
      )
    rescue StandardError => e
      Rails.logger.error("[SimilarCandidatesSearch] Global search failed: #{e.message}")
      { results: [], error: "search_failed", error_message: e.message }
    end

    def collect_existing_docids
      SourcedProfile
        .where(account_id: @account.id, provider: "pearch", is_deleted: false)
        .where.not(external_id: nil)
        .pluck(:external_id)
        .compact
        .uniq
    end

    def build_warning_message(global_data)
      case global_data[:error]
      when "insufficient_credits"
        error_parts = global_data[:error_message].to_s.split(":")
        required = error_parts[1]
        available = error_parts[2]
        "Insufficient Pearch credits for global search. Required: #{required}, Available: #{available}"
      else
        "Global search failed: #{global_data[:error_message]}"
      end
    end

    def search_similar(search_embedding, exclude_ids, limit, threshold)
      pool_size = [ limit * POOL_MULTIPLIER, MIN_POOL_SIZE ].max

      results = Embedding
        .where(reference_type: "Candidate")
        .where.not(reference_id: exclude_ids)
        .nearest_neighbors(:embedding, search_embedding, distance: "cosine")
        .limit(pool_size)

      tenant_candidate_ids = Candidate
        .where(account_id: @account.id, is_deleted: false)
        .where(id: results.map(&:reference_id))
        .pluck(:id)
        .to_set

      results
        .select { |emb| tenant_candidate_ids.include?(emb.reference_id) }
        .map { |emb| { candidate_id: emb.reference_id, similarity: (1.0 - emb.neighbor_distance).clamp(0.0, 1.0) } }
        .select { |r| r[:similarity] >= threshold }
        .first(limit)
    end

    def process_local_results(results, base_candidates, sourcing)
      return [] if results.empty?

      candidates = Candidate.where(id: results.map { |r| r[:candidate_id] }).index_by(&:id)

      results.filter_map do |result|
        candidate = candidates[result[:candidate_id]]
        next unless candidate

        profile = create_or_link_sourced_profile(candidate, sourcing, result[:similarity])
        shared = extract_shared_signals(base_candidates, candidate)

        {
          source: "local",
          candidate_id: candidate.id,
          sourced_profile_id: profile.id,
          name: candidate.name,
          role_name: candidate.role_name,
          current_company: candidate.current_company,
          location: [ candidate.city, candidate.state ].compact.join(", "),
          similarity_score: (result[:similarity] * 100).round(1),
          shared_signals: shared
        }
      end
    end

    def process_global_results(results, sourcing)
      return [] if results.blank?

      results.map do |result|
        profile = create_pearch_sourced_profile(result, sourcing)

        {
          source: "global",
          sourced_profile_id: profile.id,
          docid: result[:docid],
          name: result[:name],
          role_name: result[:title],
          current_company: result[:current_company],
          location: result[:location],
          pearch_score: result[:pearch_score],
          expertise: result[:expertise],
          insights: result[:insights]
        }
      end
    end

    def create_pearch_sourced_profile(result, sourcing)
      profile_data = result[:profile_data]
      existing = find_existing_pearch_profile(result[:docid])

      profile = existing || create_new_pearch_profile(result, profile_data, sourcing)
      link_pearch_profile_to_sourcing(profile, sourcing, result)
      profile
    end

    def find_existing_pearch_profile(docid)
      SourcedProfile.find_by(
        account_id: @account.id,
        external_id: docid,
        provider: PROVIDER_PEARCH,
        is_deleted: false
      )
    end

    def create_new_pearch_profile(result, profile_data, sourcing)
      SourcedProfile.create!(
        sourcing: sourcing,
        account_id: @account.id,
        uid: SecureRandom.uuid,
        provider: PROVIDER_PEARCH,
        external_id: result[:docid],
        linkedin_slug: profile_data["linkedin_slug"],
        linkedin_url: build_linkedin_url(profile_data["linkedin_slug"]),
        first_name: profile_data["first_name"],
        last_name: profile_data["last_name"],
        name: result[:name],
        title: profile_data["title"],
        role_name: profile_data["title"],
        summary: profile_data["summary"],
        picture_url: profile_data["picture_url"],
        gender: map_gender(profile_data["gender"]),
        location: profile_data["location"],
        total_experience_years: profile_data["total_experience_years"],
        estimated_age: profile_data["estimated_age"],
        expertise: profile_data["expertise"] || [],
        languages_data: profile_data["languages"] || [],
        skills_data: profile_data["expertise"] || [],
        has_emails: profile_data["has_emails"] || false,
        has_phone_numbers: profile_data["has_phone_numbers"] || false,
        profile_data: profile_data,
        experiences_data: profile_data["experiences"] || [],
        educations_data: profile_data["educations"] || [],
        certifications_data: profile_data["certifications"] || [],
        status: STATUS_NEW
      )
    end

    def build_linkedin_url(slug)
      return nil unless slug.present?

      "https://linkedin.com/in/#{slug}"
    end

    def link_pearch_profile_to_sourcing(profile, sourcing, result)
      SourcedProfileSourcing.find_or_create_by!(
        sourced_profile_id: profile.id,
        sourcing_id: sourcing.id
      ) do |sps|
        sps.account_id = @account.id
        sps.user_id = @user.id
        sps.search_source = "pearch_similarity"
        sps.search_score = result[:pearch_score]&.to_f&./(5.0)
        sps.ai_metadata = build_global_search_metadata(result)
      end
    end

    def map_gender(gender_string)
      return GENDER_MALE if gender_string&.downcase == "male"
      return GENDER_FEMALE if gender_string&.downcase == "female"
      return GENDER_NON_BINARY if gender_string&.downcase == "non-binary"

      GENDER_UNKNOWN
    end

    def create_sourcing(candidate_ids:, job_id:, results_count:, local_count:, global_count:, duration:, provider:, credits_used: nil, synthesis: nil)
      query_text = build_query_text_for_sourcing(candidate_ids)

      Sourcing.create!(
        user_id: @user.id,
        account_id: @account.id,
        uid: SecureRandom.uuid,
        provider: provider,
        query: query_text,
        parameters: build_sourcing_parameters(candidate_ids, job_id, provider),
        status: STATUS_DONE,
        results_count: results_count,
        local_results_count: local_count,
        global_results_count: global_count,
        processed_count: results_count,
        credits_used: credits_used,
        searched_at: Time.current,
        duration: duration,
        search_metadata: build_sourcing_metadata(candidate_ids, provider, synthesis)
      )
    end

    def build_sourcing_parameters(candidate_ids, job_id, provider)
      {
        search_type: SEARCH_TYPE_SIMILARITY,
        base_candidate_ids: candidate_ids,
        job_id: job_id,
        method: candidate_ids.size == 1 ? "single_embedding" : "centroid",
        sources: provider
      }
    end

    def build_sourcing_metadata(candidate_ids, provider, synthesis)
      {
        embedding_model: Llm::ClientFactory.embedding_model,
        search_method: candidate_ids.size == 1 ? "single" : "centroid",
        base_count: candidate_ids.size,
        sources: provider,
        synthesis: synthesis
      }
    end

    def build_query_text_for_sourcing(candidate_ids)
      base_names = Candidate.where(id: candidate_ids).pluck(:name)
      return "Similar to #{base_names.first}" if base_names.size == 1

      "Similar to #{base_names.size} candidates: #{base_names.join(', ').truncate(100)}"
    end

    def create_or_link_sourced_profile(candidate, sourcing, similarity_score)
      existing_profile = SourcedProfile.find_by(
        account_id: @account.id,
        candidate_id: candidate.id,
        is_deleted: false
      )

      profile = existing_profile || build_sourced_profile(candidate, sourcing)
      profile.save! if profile.new_record?
      link_profile_to_sourcing(profile, sourcing, similarity_score)
      profile
    end

    def link_profile_to_sourcing(profile, sourcing, similarity_score)
      SourcedProfileSourcing.find_or_create_by!(
        sourced_profile_id: profile.id,
        sourcing_id: sourcing.id
      ) do |sps|
        sps.account_id = @account.id
        sps.user_id = @user.id
        sps.search_source = SEARCH_TYPE_SIMILARITY
        sps.search_score = similarity_score
        sps.similarity_score = (similarity_score * 100).round(1)
        sps.ai_metadata = build_similarity_metadata(similarity_score)
      end
    end

    def build_similarity_metadata(similarity_score)
      {
        search_type: "similar_candidates",
        similarity_percentage: (similarity_score * 100).round(1)
      }
    end

    def build_global_search_metadata(result)
      {
        search_type: "similar_candidates_global",
        pearch_score: result[:pearch_score],
        insights: result[:insights],
        expertise: result[:expertise]
      }
    end

    def build_sourced_profile(candidate, sourcing)
      profile = SourcedProfile.new(build_sourced_profile_attributes(candidate, sourcing))
      enrich_profile_from_candidate(profile, candidate)
      profile
    end

    def build_sourced_profile_attributes(candidate, sourcing)
      {
        sourcing: sourcing,
        account_id: @account.id,
        candidate: candidate,
        provider: PROVIDER_LOCAL,
        external_id: "similar_#{sourcing.id}_#{candidate.id}",
        status: STATUS_NEW,
        name: candidate.name,
        email: candidate.email,
        phone: candidate.phone || candidate.mobile_phone,
        cpf: candidate.cpf,
        date_birth: candidate.date_birth,
        gender: candidate.gender,
        marital_status: candidate.marital_status,
        role_name: candidate.role_name,
        position_level: candidate.position_level,
        current_company: candidate.current_company,
        city: candidate.city,
        state: candidate.state,
        country: candidate.country,
        linkedin: candidate.linkedin,
        linkedin_slug: candidate.linkedin_slug,
        github: candidate.github,
        portfolio: candidate.portfolio,
        curriculum_text: candidate.curriculum_text,
        self_introduction: candidate.self_introduction,
        clt_expectation: candidate.clt_expectation,
        pj_expectation: candidate.pj_expectation,
        freelance_expectation: candidate.freelance_expectation,
        current_salary: candidate.current_salary,
        desired_salary: candidate.desired_salary,
        remote_work: candidate.remote_work,
        mobility: candidate.mobility,
        secondary_email: candidate.secondary_email,
        mobile_phone: candidate.mobile_phone,
        secondary_phone: candidate.secondary_phone,
        has_emails: candidate.email.present?,
        has_phone_numbers: (candidate.phone || candidate.mobile_phone).present?,
        location: [ candidate.city, candidate.state ].compact.join(", "),
        title: candidate.role_name,
        summary: candidate.self_introduction
      }
    end

    def enrich_profile_from_candidate(profile, candidate)
      SourcedProfiles::CandidateEnrichmentService.call(profile, candidate)
    rescue StandardError => e
      Rails.logger.error("[SimilarCandidatesSearch] CandidateEnrichmentService failed: #{e.message}")
    end

    def extract_shared_signals(base_candidates, similar_candidate)
      base_tokens = base_candidates.flat_map { |c| tokenize(c.curriculum_text) }.uniq
      similar_tokens = tokenize(similar_candidate.curriculum_text)

      (base_tokens & similar_tokens)
        .sort_by { |t| -t.length }
        .first(MAX_SHARED_SIGNALS)
    end

    def tokenize(text)
      return [] if text.blank?

      text.downcase
          .gsub(/[^a-záàâãéèêíïóôõöúçñ0-9\s+#.]/i, " ")
          .split(/\s+/)
          .reject { |t| t.length < MIN_TOKEN_LENGTH || STOPWORDS.include?(t) }
          .uniq
    end

    def duration_ms(start_time)
      ((Process.clock_gettime(Process::CLOCK_MONOTONIC) - start_time) * 1000).round(1)
    end

    def build_empty_response(base_candidates, start_time)
      duration = duration_ms(start_time)
      {
        sourcing_id: nil,
        sourcing_uid: nil,
        mode: "local",
        search_type: "similarity",
        base_candidates: serialize_base_candidates(base_candidates),
        similar_candidates: [],
        total: 0,
        excluded_count: 0,
        metadata: base_metadata(base_candidates, duration)
      }
    end

    def build_response(sourcing:, base_candidates:, local_results:, global_results:, candidate_ids:, exclude_ids:, duration:, threshold:, warnings: [])
      {
        sourcing_id: sourcing.id,
        sourcing_uid: sourcing.uid,
        mode: sourcing.provider,
        search_type: SEARCH_TYPE_SIMILARITY,
        base_candidates: serialize_base_candidates(base_candidates),
        similar_candidates: {
          local: local_results,
          global: global_results
        },
        total: local_results.size + global_results.size,
        local_count: local_results.size,
        global_count: global_results.size,
        excluded_count: exclude_ids.size,
        metadata: base_metadata(base_candidates, duration).merge(
          threshold: threshold,
          credits_used: sourcing.credits_used
        ),
        warnings: warnings.presence
      }.compact
    end

    def serialize_base_candidates(candidates)
      candidates.map do |c|
        {
          id: c.id,
          name: c.name,
          role_name: c.role_name,
          current_company: c.current_company
        }
      end
    end

    def base_metadata(base_candidates, duration)
      {
        embedding_model: Llm::ClientFactory.embedding_model,
        search_method: base_candidates.size == 1 ? "single" : "centroid",
        base_count: base_candidates.size,
        duration_ms: duration
      }
    end
  end
end
