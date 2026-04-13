# frozen_string_literal: true

module Searchable
  extend ActiveSupport::Concern

  included do
    searchkick index_name: -> { tenant_index_name }
  end

  module ClassMethods
    def tenant_index_name
      [Apartment::Tenant.current, model_name.plural, Rails.env].join('_')
    end

    def search_fields
      [:id]
    end

    def agg_search_array(_params = {})
      {}
    end

    def comparison_search_terms
      []
    end

    def include_base
      self
    end

    def default_search_order
      { created_at: :desc }
    end

    def search_default(search_text, params = {}, page = 1, build_where_for_autocomplete = false, current_user_id = nil)
      params ||= {}

      if column_names.include?('is_deleted')
        params[:where] = (params[:where] || {}).merge(is_deleted: [false, nil])
      end

      fields_to_search =
        if build_where_for_autocomplete
          false
        else
          respond_to?(:search_fields) ? search_fields : [:id]
        end

      aggs_to_use = respond_to?(:agg_search_array) ? agg_search_array(params) : {}

      comparison_terms = respond_to?(:comparison_search_terms) ? comparison_search_terms : false

      search_options = {
        operator: 'and',
        page: page || 1,
        per_page: 30,
        smart_aggs: true,
        body_options: { track_total_hits: true },
        aggs: aggs_to_use,
        fields: fields_to_search,
        current_user_id: current_user_id
      }.merge(params)

      SearchService.build(self, search_text, search_options, comparison_terms)
    end
  end
end
