class Matching::CandidatesForSourcedProfileSourcing
  DEFAULT_TOP_K = 500
  MIN_TOP_K = 100
  MAX_TOP_K = 2000
  DEFAULT_MIN_SCORE = 0.0
  FALLBACK_MIN_SCORE = 0.0

  def initialize(sourced_profile_sourcing_id, top_k: DEFAULT_TOP_K, account_id: nil, filters: {}, page: 1, per_page: 30, min_score: DEFAULT_MIN_SCORE, max_score: 1.0)
    @sourced_profile_sourcing = SourcedProfileSourcing.find(sourced_profile_sourcing_id)
    @sourced_profile = @sourced_profile_sourcing.sourced_profile
    @top_k = normalize_top_k(top_k)
    @account_id = account_id || @sourced_profile_sourcing.account_id
    @filters = filters || {}
    @page = normalize_page(page)
    @per_page = normalize_per_page(per_page)
    @min_score = normalize_min_score(min_score)
    @max_score = normalize_max_score(max_score)
  end

  def call
    Apartment::Tenant.switch!(@sourced_profile_sourcing.account.tenant) if @sourced_profile_sourcing.account.tenant.present?

    embedding = generate_profile_embedding
    return empty_result("embedding inválido") if embedding.blank?

    vector_matches = find_vector_matches(embedding)
    return empty_result("nenhum candidato encontrado") if vector_matches.empty?

    candidates_with_scores = calculate_scores(vector_matches)
    return empty_result("nenhum candidato com score suficiente") if candidates_with_scores.empty?

    paginated_candidates = paginate_candidates(candidates_with_scores)
    return empty_result("página vazia") if paginated_candidates.empty?

    build_result(paginated_candidates, candidates_with_scores.size)
  rescue ActiveRecord::RecordNotFound => e
    { records: [], meta: { total: 0, error: "SourcedProfileSourcing não encontrado" } }
  rescue => e
    Rails.logger.error("[Matching::CandidatesForSourcedProfileSourcing] Error: #{e.message}")
    Rails.logger.error(e.backtrace.first(5).join("\n"))
    { records: [], meta: { total: 0, error: e.message } }
  end

  private

  attr_reader :sourced_profile_sourcing, :sourced_profile, :top_k, :account_id, :filters, :page, :per_page, :min_score, :max_score

  def generate_profile_embedding
    text = SourcedProfiles::TextBuilder.call(sourced_profile)
    return nil if text.blank?

    Embeddings::Encoder.new.call(text)
  rescue => e
    Rails.logger.error("[Matching::CandidatesForSourcedProfileSourcing] Embedding generation failed: #{e.message}")
    nil
  end

  def find_vector_matches(embedding)
    embedding_results = Embedding
      .for_candidates
      .nearest_neighbors(:embedding, embedding, distance: "cosine")
      .limit(top_k * 2)

    candidate_ids = embedding_results.map(&:reference_id).uniq
    return [] if candidate_ids.empty?

    scope = Candidate.where(account_id: account_id, is_deleted: false).where(id: candidate_ids)
    scope = apply_filters(scope)
    allowed_ids = scope.pluck(:id).to_set

    ordered_ids = embedding_results
      .map(&:reference_id)
      .uniq
      .select { |id| allowed_ids.include?(id) }
      .first(top_k)

    return [] if ordered_ids.empty?

    distance_by_id = embedding_results.each_with_object({}) do |e, h|
      h[e.reference_id] = e.neighbor_distance unless h.key?(e.reference_id)
    end

    candidates = Candidate.where(id: ordered_ids).index_by(&:id)
    ordered_ids.filter_map do |id|
      c = candidates[id]
      next unless c

      c.define_singleton_method(:neighbor_distance) { distance_by_id[id] }
      c
    end
  end

  def apply_filters(scope)
    return scope if filters.empty?

    filter_handlers = build_filter_handlers
    filters.each do |field, value|
      handler = filter_handlers[field.to_sym]
      scope = handler ? handler.call(scope, value) : scope
    end

    scope
  end

  def build_filter_handlers
    {
      city: ->(s, v) { s.where(city: normalize_location_value(v)) },
      state: ->(s, v) { s.where(state: normalize_location_value(v)) },
      country: ->(s, v) { s.where(country: normalize_location_value(v)) },
      remote_work: ->(s, v) { s.where(remote_work: v) },
      position_level: ->(s, v) { s.where(position_level: v) },
      years_of_experience_min: ->(s, v) { s.where("years_of_experience >= ?", v.to_f) },
      years_of_experience_max: ->(s, v) { s.where("years_of_experience <= ?", v.to_f) }
    }
  end

  def normalize_location_value(value)
    return value if value.is_a?(Array)
    value.to_s.downcase.strip
  end

  def calculate_scores(vector_matches)
    candidates_with_scores = vector_matches.map do |match|
      score = 1 - match.neighbor_distance
      { candidate: match, score: score }
    end

    filtered = candidates_with_scores.select do |item|
      item[:score] >= min_score && item[:score] <= max_score
    end

    return filtered if filtered.any?

    candidates_with_scores.sort_by { |item| -item[:score] }.first(per_page)
  end

  def paginate_candidates(candidates_with_scores)
    filtered_ids = candidates_with_scores.map { |item| item[:candidate].id }
    total_filtered = filtered_ids.size
    offset = (page - 1) * per_page
    paginated_ids = filtered_ids[offset, per_page] || []

    return [] if paginated_ids.empty?

    load_candidates_with_scores(paginated_ids, candidates_with_scores)
  end

  def load_candidates_with_scores(paginated_ids, candidates_with_scores)
    scores_hash = candidates_with_scores.each_with_object({}) do |item, h|
      h[item[:candidate].id] = item[:score]
    end

    search_params = build_search_params(paginated_ids)
    search_results = Candidate.search_default("*", search_params, 1, false, nil, false)

    search_results[:records].map do |candidate|
      candidate.score = scores_hash[candidate.id] || 0.0
      candidate
    end
  end

  def build_search_params(paginated_ids)
    {
      where: filters.deep_symbolize_keys.merge(id: paginated_ids),
      order: nil,
      page: 1,
      per_page: per_page,
      body_options: {
        sort: [
          {
            _script: {
              type: "number",
              order: "asc",
              script: {
                lang: "painless",
                source: build_script_source,
                params: { ids: paginated_ids.map(&:to_s) }
              }
            }
          }
        ]
      }
    }
  end

  def build_script_source
    <<~PAINLESS.strip
      int i = params.ids.indexOf(doc['id'].value.toString());
      return i == -1 ? params.ids.size() + 1 : i;
    PAINLESS
  end

  def build_result(paginated_candidates, total_filtered)
    {
      records: paginated_candidates,
      meta: {
        total: total_filtered,
        page: page,
        per_page: per_page,
        total_pages: (total_filtered.to_f / per_page).ceil,
        min_score: min_score,
        max_score: max_score,
        aggregators: {}
      }
    }
  end

  def empty_result(reason = nil)
    {
      records: [],
      meta: {
        total: 0,
        page: page,
        per_page: per_page,
        total_pages: 0,
        min_score: min_score,
        max_score: max_score,
        aggregators: {},
        reason: reason
      }
    }
  end

  def normalize_top_k(value)
    value = value.to_i
    return DEFAULT_TOP_K if value <= 0
    [ [ value, MIN_TOP_K ].max, MAX_TOP_K ].min
  end

  def normalize_page(value)
    [ value.to_i, 1 ].max
  end

  def normalize_per_page(value)
    value = value.to_i
    return 30 if value <= 0
    [ value, 100 ].min
  end

  def normalize_min_score(value)
    value = value.to_f
    return DEFAULT_MIN_SCORE if value < 0
    [ value, 1.0 ].min
  end

  def normalize_max_score(value)
    value = value.to_f
    return 1.0 if value <= 0 || value > 1.0
    value
  end
end
