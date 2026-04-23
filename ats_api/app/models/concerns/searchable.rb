# frozen_string_literal: true

module Searchable
  extend ActiveSupport::Concern

  included do
    @_pending_searchkick_options = { index_name: -> { tenant_index_name } }

    klass = self
    TracePoint.new(:end) do |tp|
      if tp.self == klass
        tp.disable
        klass._finalize_searchkick
      end
    end.enable
  end

  module ClassMethods
    def enable_autocomplete(*fields)
      @_pending_searchkick_options = { word_start: fields + [ :id ], index_name: -> { tenant_index_name } }
      self._autocomplete_label = fields.first
    end

    def _finalize_searchkick
      return unless @_pending_searchkick_options

      searchkick(**@_pending_searchkick_options)
      @_pending_searchkick_options = nil
    end

    def _autocomplete_label
      @_autocomplete_label || :name
    end

    def _autocomplete_label=(field)
      @_autocomplete_label = field
    end

    def tenant_index_name
      tenant = Apartment::Tenant.current
      if Apartment.excluded_models.include?(model_name)
        tenant = "public"
      end
      [ tenant, model_name.plural, Rails.env ].join("_")
    end

    def search_fields
      [ :id ]
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

    def search_default(search_text, params = {}, page = 1, build_where_for_autocomplete = false, current_user_id = nil, include_aggregators = false)
      params ||= {}

      if column_names.include?("is_deleted")
        params[:where] = (params[:where] || {}).merge(is_deleted: [ false, nil ])
      end

      unless params[:order]
        params[:order] = default_search_order
      end

      fields_to_search =
        if build_where_for_autocomplete
          false
        else
          respond_to?(:search_fields) ? search_fields : [ :id ]
        end

      force_aggregators = params.delete(:force_aggregators)
      should_include_aggs = force_aggregators || include_aggregators

      aggs_to_use = if should_include_aggs && respond_to?(:agg_search_array)
                      agg_search_array(params)
      else
                      {}
      end

      comparison_terms = respond_to?(:comparison_search_terms) ? comparison_search_terms : false

      search_options = {
        operator: "and",
        page: page || 1,
        limit: params[:limit] || 30,
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
