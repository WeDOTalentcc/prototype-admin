class Matching::CandidateForJob
  def initialize(job_id, top_k: 500, account_id: nil, filters: {}, page: 1, per_page: 30, min_score: 0.0, max_score: 1.0)
    @job        = Job.find(job_id)
    @top_k      = top_k
    @account_id = account_id || @job.account_id
    @filters    = filters || {}
    @page       = (page.to_i <= 0 ? 1 : page.to_i)
    @per_page   = [ per_page.to_i, 100 ].min.positive? ? [ per_page.to_i, 100 ].min : 30
    @min_score  = [ min_score.to_f, 0.0 ].max
    @max_score  = [ max_score.to_f, 1.0 ].min
  end

  def call
    Apartment::Tenant.switch!(@job.account.tenant) if @job.account.tenant.present?

    vec = generate_job_vector
    raise "vetor da vaga inválido" if vec.blank?


    embedding_results = Embedding
      .for_candidates
      .nearest_neighbors(:embedding, vec, distance: "cosine")
      .limit(@top_k * 2)

    candidate_ids = embedding_results.map(&:reference_id).uniq
    candidates_in_account = Candidate
      .where(id: candidate_ids, account_id: @account_id, is_deleted: false)
      .pluck(:id)
      .to_set

    ordered_ids = embedding_results
      .map(&:reference_id)
      .uniq
      .select { |id| candidates_in_account.include?(id) }
      .first(@top_k)

    distance_by_id = embedding_results.each_with_object({}) do |e, h|
      h[e.reference_id] = e.neighbor_distance unless h.key?(e.reference_id)
    end

    candidates_by_id = Candidate.where(id: ordered_ids, account_id: @account_id).index_by(&:id)
    vector_matches = ordered_ids.filter_map do |id|
      c = candidates_by_id[id]
      next unless c

      c.define_singleton_method(:neighbor_distance) { distance_by_id[id] }
      c
    end

    return { records: [], meta: { total: 0, aggregators: {} } } if vector_matches.empty?

    candidates_with_scores = vector_matches.map do |match|
      score = 1 - match.neighbor_distance
      { candidate: match, score: score }
    end.select do |item|
      item[:score] >= @min_score && item[:score] <= @max_score
    end

    return { records: [], meta: { total: 0, aggregators: {} } } if candidates_with_scores.empty?

    filtered_ids = candidates_with_scores.map { |item| item[:candidate].id }
    total_filtered = filtered_ids.size
    offset = (@page - 1) * @per_page
    paginated_ids = filtered_ids[offset, @per_page] || []

    return { records: [], meta: { total: total_filtered, aggregators: {} } } if paginated_ids.empty?

    search_params = {
      where: (@filters.deep_symbolize_keys).merge(id: paginated_ids),
      order: nil,
      page: 1, # Sempre página 1 pois já aplicamos paginação nos IDs
      per_page: @per_page,
      body_options: {
        sort: [
          {
            _script: {
              type: "number",
              order: "asc",
              script: {
                lang: "painless",
                source: <<~PAINLESS.strip,
                  int i = params.ids.indexOf(doc['id'].value.toString());
                  return i == -1 ? params.ids.size() + 1 : i;
                PAINLESS
                params: { ids: paginated_ids.map(&:to_s) }
              }
            }
          }
        ]
      }
    }

    search_results = Candidate.search_default("*", search_params, 1, false, nil, false)

    scores_hash = candidates_with_scores.each_with_object({}) do |item, h|
      h[item[:candidate].id] = item[:score]
    end

    formatted_records = search_results[:records].map do |candidate|
      candidate.score = scores_hash[candidate.id] || 0.0
      candidate
    end

    {
      records: formatted_records,
      meta: {
        total: total_filtered,
        page: @page,
        per_page: @per_page,
        total_pages: (total_filtered.to_f / @per_page).ceil,
        min_score: @min_score,
        max_score: @max_score,
        aggregators: search_results[:aggs] || {}
      }
    }
  end

  private

  def generate_job_vector
    text = [
      @job.title,
      @job.description,
      [ @job.city, @job.state, @job.country ].compact.join(", "),
      @job.workplace_type
    ].compact.join("\n\n").strip
    raise "texto da vaga vazio" if text.blank?
    Embeddings::Encoder.new.call(text)
  end
end
