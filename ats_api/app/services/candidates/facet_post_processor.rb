# frozen_string_literal: true

module Candidates
  # Post-processes Searchkick aggregations for Candidate (e.g. favorite_user_ids → is_favorited).
  # Shared by AggregatorsController and CandidatesController#search_hints.
  class FacetPostProcessor
    def self.call(aggs, current_user)
      return aggs unless aggs.is_a?(Hash)
      return aggs if aggs["favorite_user_ids"].blank?

      aggs = aggs.dup
      aggs["is_favorited"] = calculate_favorite_aggregator(aggs["favorite_user_ids"], current_user)
      aggs.delete("favorite_user_ids")
      aggs
    end

    def self.calculate_favorite_aggregator(favorite_agg, current_user)
      return {} unless favorite_agg.is_a?(Hash)
      return {} unless favorite_agg["buckets"].is_a?(Array)

      buckets = favorite_agg["buckets"]
      user_bucket = buckets.find { |bucket| bucket["key"] == current_user.id }
      favorited_count = user_bucket ? user_bucket["doc_count"] : 0

      {
        "doc_count" => favorite_agg["doc_count"],
        "doc_count_error_upper_bound" => 0,
        "sum_other_doc_count" => 0,
        "buckets" => [
          { "key" => "Favoritado", "doc_count" => favorited_count }
        ]
      }
    end
    private_class_method :calculate_favorite_aggregator
  end
end
