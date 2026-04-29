# frozen_string_literal: true

module SourcedProfileSourcings
  class SearchService
    def self.call(query:, account_id:, where: {}, limit: 10)
      new(query: query, account_id: account_id, where: where, limit: limit).call
    end

    def initialize(query:, account_id:, where: {}, limit:)
      @query = query
      @account_id = account_id
      @where = where || {}
      @limit = limit
    end

    def call
      results = perform_search
      results
    rescue => e
      raise
    end

    private

    def perform_search
      SourcedProfileSourcing.search(
        @query,
        fields: search_fields,
        where: build_where_clause,
        order: { _score: :desc },
        limit: @limit,
        load: false
      )
    end

    def search_fields
      [
        "curriculum_text^5",
        "role_name^3",
        "name^2",
        "summary^2",
        "current_company^2",
        "skills",
        "behavioral_skills",
        "expertise",
        "recent_roles",
        "education_institutions",
        "study_areas"
      ]
    end

    def build_where_clause
      base_filters = {
        account_id: @account_id,
        is_deleted: false
      }

      merged_filters = base_filters.merge(@where)
      merged_filters
    end
  end
end
