# frozen_string_literal: true

class SourcingSerializer
  include JSONAPI::Serializer

  attributes :uid, :provider, :external_id, :thread_id, :query, :status,
             :duration, :total_estimate, :total_estimate_is_lower_bound,
             :results_count, :credits_used, :searched_at, :notes,
             :local_results_count, :global_results_count, :processed_count,
             :saved, :cost_per_profile, :created_at, :updated_at, :aggregated_stats

  attribute :parameters do |sourcing|
    sourcing.parameters
  end

  attribute :stats do |sourcing|
    sourcing.stats
  end

  attribute :file_urls do |sourcing|
    if sourcing.files.attached?
      prefix = ENV.fetch("API_URL", "http://localhost:8080")
      sourcing.files.map do |file|
        prefix + Rails.application.routes.url_helpers.rails_blob_url(file, only_path: true)
      end
    else
      []
    end
  end

  belongs_to :user
  belongs_to :account
end
