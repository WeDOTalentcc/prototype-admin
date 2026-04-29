# frozen_string_literal: true

module Matching
  class CandidateForText
    DEFAULT_TOP_K = 500
    MAX_TOP_K = 2000
    DEFAULT_PER_PAGE = 20
    MAX_PER_PAGE = 100
    MIN_TEXT_LENGTH = 10

    def initialize(text:, account_id:, top_k: DEFAULT_TOP_K, filters: {}, page: 1, per_page: DEFAULT_PER_PAGE, min_score: 0.0, max_score: 1.0)
      @text       = text.to_s.strip
      @account_id = account_id
      @top_k      = [[top_k.to_i, 1].max, MAX_TOP_K].min
      @filters    = filters || {}
      @page       = [page.to_i, 1].max
      @per_page   = [[per_page.to_i, 1].max, MAX_PER_PAGE].min
      @min_score  = [min_score.to_f, 0.0].max
      @max_score  = [max_score.to_f, 1.0].min
    end

    def call
      return error("Text is required") if @text.blank?
      return error("Text too short (minimum #{MIN_TEXT_LENGTH} characters)") if @text.length < MIN_TEXT_LENGTH

      vec = generate_embedding
      return error("Failed to generate embedding") if vec.blank?

      candidates_with_scores = find_matching_candidates(vec)
      return empty_result if candidates_with_scores.empty?

      build_paginated_result(candidates_with_scores)
    end

    private

    def generate_embedding
      Embeddings::Encoder.new.call(@text)
    rescue StandardError => e
      Rails.logger.error "[Matching::CandidateForText] Embedding generation failed: #{e.message}"
      nil
    end

    def find_matching_candidates(vec)
      embedding_results = Embedding
        .for_candidates
        .nearest_neighbors(:embedding, vec, distance: "cosine")
        .limit(@top_k * 2)

      candidate_ids = embedding_results.map(&:reference_id).uniq
      valid_ids = Candidate
        .where(id: candidate_ids, account_id: @account_id, is_deleted: false)
        .pluck(:id)
        .to_set

      distance_by_id = embedding_results.each_with_object({}) do |e, h|
        h[e.reference_id] = e.neighbor_distance unless h.key?(e.reference_id)
      end

      ordered_ids = embedding_results
        .map(&:reference_id)
        .uniq
        .select { |id| valid_ids.include?(id) }
        .first(@top_k)

      candidates_by_id = Candidate.where(id: ordered_ids, account_id: @account_id).index_by(&:id)

      ordered_ids.filter_map do |id|
        candidate = candidates_by_id[id]
        next unless candidate

        score = 1 - distance_by_id[id].to_f
        next unless score >= @min_score && score <= @max_score

        { candidate: candidate, score: score }
      end
    end

    def build_paginated_result(candidates_with_scores)
      total = candidates_with_scores.size
      offset = (@page - 1) * @per_page
      paginated = candidates_with_scores[offset, @per_page] || []

      return empty_result if paginated.empty?

      paginated_ids = paginated.map { |item| item[:candidate].id }
      scores_hash = paginated.each_with_object({}) { |item, h| h[item[:candidate].id] = item[:score] }

      search_params = {
        where: (@filters.deep_symbolize_keys).merge(id: paginated_ids),
        order: nil,
        page: 1,
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

      formatted_records = search_results[:records].map do |candidate|
        candidate.score = scores_hash[candidate.id] || 0.0
        candidate
      end

      {
        success: true,
        records: formatted_records,
        meta: {
          total: total,
          page: @page,
          per_page: @per_page,
          total_pages: (total.to_f / @per_page).ceil,
          min_score: @min_score,
          max_score: @max_score,
          aggregators: search_results[:aggs] || {}
        }
      }
    end

    def empty_result
      { success: true, records: [], meta: { total: 0, page: @page, per_page: @per_page, total_pages: 0, aggregators: {} } }
    end

    def error(message)
      { success: false, error: message, records: [], meta: { total: 0 } }
    end
  end
end
