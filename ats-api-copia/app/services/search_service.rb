# frozen_string_literal: true

# service for search
class SearchService
  def self.exist_search?(class_current)
    return false unless class_current.respond_to?(:search_default)

    return false if class_current.first.nil?

    true
  end

  def self.default_response
    {
      total_count: 0,
      records: [],
      aggs: []
    }
  end

  def self.simple_search(class_current, text_search, where = {}, order = {})
    order[:created_at] = "desc" if order == {}
    ids = class_current.search(text_search, where:, match: :word_start, order:,
                                            body_options: { track_total_hits: true })
                       .hits.map do |id|
      id["_id"].to_i
    end

    SearchService.order_ids(class_current, ids)
  end

  def self.build(class_current, text_search, params, comparison_term = false)
    return SearchService.default_response unless SearchService.exist_search?(class_current)

    boolean_search = false
    current_params = params
    text_search ||= "*"
    text_search = "*" if text_search == "" || text_search.nil?
    boolean_fields = [ " or ", " and " ]
    boolean_fields.each do |boolean_field|
      boolean_search = true if text_search.include?(boolean_field)
    end

    if comparison_term
      (text_search, custom_search) = SearchService.build_text_search(text_search, params,
                                                                     comparison_term)
    end
    return SearchService.build_boolean_search(class_current, text_search, params, comparison_term) if boolean_search

    params = SearchService.build_agg(params, text_search)

    records = class_current.search(text_search,
                                   where: params[:where],
                                   limit: params[:limit],
                                   order: params[:order],
                                   operator: params[:operator] || "and",
                                   page: params[:page] || 1,
                                   smart_aggs: true,
                                   per_page: params[:per_page] || 30,
                                   body_options: params[:body_options] || nil,
                                   boost_where: params[:boost_where] || nil,
                                   aggs: params[:aggs] || [],
                                   match: params[:match] || nil)
    #  exclude: custom_search&.dig(:not) || ''
    {
      total_count: records&.total_count,
      records: SearchService.order_ids(class_current, records.hits.map { |id| id["_id"].to_i }, current_params),
      aggs: records.aggs
    }
  end

  def self.build_light(class_current, text_search, params)
    return SearchService.default_response unless SearchService.exist_search?(class_current)

    text_search ||= "*"
    text_search = "*" if text_search == "" || text_search.nil?

    records = class_current.search(
      text_search,
      where: params[:where],
      order: params[:order],
      operator: params[:operator] || "and",
      page: params[:page] || 1,
      per_page: params[:per_page] || 30,
      fields: [ :id ] # Apenas IDs
    )

    {
      total_count: records&.total_count,
      records: records.hits.map { |hit| hit["_id"].to_i }
    }
  end
  # require 'pry' # must install the gem... but you ALWAYS want pry installed anyways

  def self.build_boolean_search(class_current, text_search, params, _comparison_term)
    filter = {
      bool: {
        must: {
          query_string: {
            query: CustomSearchkick::Where.convert_to_query_string(text_search),
            fields: params[:fields] || [ "*.analyzed" ],
            boost: 10,
            type: "best_fields",
            # max_expansions: 3,
            fuzzy_transpositions: true
          }
        },
        filter: CustomSearchkick::Where.call(params[:where] || {})
      }
    }

    aggs = params[:aggs] || []
    if aggs.class != Hash
      aggs = aggs.map do |agg|
        new_agg = {}
        new_agg[agg&.to_sym] = { terms: { size: 100, field: agg } }
      end
    end

    if aggs.instance_of?(Hash)
      new_aggs = {}
      aggs&.keys&.each do |agg|
        new_aggs[agg] = {
          aggs: {},
          filter:
        }
        new_aggs[agg][:aggs][agg] = {
          terms: {
            field: agg,
            size: 100
          }
        }
      end
      aggs = new_aggs
    end

    query_string = {
      _source: false,
      from: (params[:page].to_i - 1) * (params[:per_page] || 30),
      size: params[:per_page].to_i || 30,
      track_scores: true,
      track_total_hits: true,
      query: filter
    }

    query_string[:aggs] = aggs if aggs.count > 0

    records = class_current.search(body: query_string)
    {
      total_count: records.total_count,
      records: SearchService.order_ids(class_current, records.hits.map { |id| id["_id"].to_i }, params),
      aggs: records.aggs
    }
    # rescue StandardError => e
    #   {
    #     total_count: 0,
    #     records: [],
    #     aggs: []
    #   }
  end

  def self.build_agg(params, text_search)
    return params unless params[:aggs]

    new_params = params
    params[:aggs] = SearchService.normalize_aggs(params, text_search) if params[:aggs].instance_of?(Array)

    if params[:entity_column_id]
      entity_columns = EntityColumn.find(params[:entity_column_id]).columns_view
      columns_in_use = entity_columns.map { |column| column["value"] }
      new_aggs = {}
      params[:aggs]&.keys&.each do |agg|
        new_aggs[agg.to_sym] = params[:aggs][agg] if columns_in_use.include?(agg.to_s)
      end

      entity_columns.each do |column|
        new_aggs[column["text"].downcase.gsub(" ", "_").to_sym] = { limit: 50 } if column["value"] == "answers_cache"
      end

      params[:aggs] = new_aggs
    end

    params[:aggs]&.each_key do |agg|
      new_params[:aggs][agg] = params[:aggs][agg]
      new_params[:aggs][agg] = new_params[:aggs][agg].merge({ where: params[:where] })
    end

    new_params
  end

  def self.normalize_aggs(params, text_search)
    params[:order] = { created_at: "desc" } unless params[:order] || text_search != "*"
    return nil if params[:aggs] && params[:aggs].empty?

    new_aggs = {}
    params[:aggs].each do |agg|
      new_aggs[agg.to_sym] = {}
    end
    new_aggs
  end

  def self.word_start(class_current, text_search, params)
    class_current.search(text_search, params.merge(match: :word_start, limit: 5))
  end

  def self.build_text_search(text_search, params, comparison_term)
    (custom_search, params) = SearchService.build_where(text_search, params, comparison_term)
    text_search = custom_search[:required] unless custom_search[:required].length.zero?
    text_search = text_search.join(" ") if custom_search[:required] != "*" && custom_search[:required].length.positive?
    text_search = "*" if text_search == ""
    [ text_search, custom_search ]
  end

  def self.build_where(text_search, params, comparison_term)
    terms = { required: "*", and: [], not: [] }
    return [ terms, params ] if text_search == "*"

    terms_new = SearchService.build_terms(text_search)
    return [ SearchService.build_terms(text_search), params ] unless comparison_term

    params = SearchService.comparison_term_or(params, terms_new[:or], comparison_term)
    # params = SearchService.comparison_term_not(params, terms_new[:not], comparison_term)
    [ SearchService.build_terms(text_search), params ]
  end

  def self.comparison_term_or(params, term_or, comparison_term)
    return params unless term_or.length.positive?

    term_or.each do |term|
      params[:where][:_or] = [] unless params[:where][:_or]
      comparison_term.each do |comparison|
        params[:where][:_or] << { comparison.to_sym => { like: "%#{term}%" } }
      end
    end
    params
  end

  def self.comparison_term_not(params, term_not, comparison_term)
    return params unless term_not.length.positive?

    comparison_term.each do |comparison|
      params[:where][comparison.to_sym ] = { _not: term_not }
    end
  end

  def self.build_terms(text_search)
    terms = { required: [], or: [], not: [] }
    operator = { '+': :required, '-': :not, '!': :or }

    text_search.split(",").each do |query|
      if query[0] == "+" || query[0] == "-" || query[0] == "!"
        terms[operator[query[0].to_sym]] << query[1..-1]
        next
      end
    end
    terms
  end

  def self.check_term(query, operator)
    return query if query[0] == operator

    nil
  end

  def self.find_with(class_current, id)
    class_current.where(id:).or(class_current.where(uid: id)).first
  end

  def self.order_ids(class_current, ids, params = false)
    return [] if ids.blank?

    indexed_banks = class_current
    indexed_banks = class_current.include_base if class_current.respond_to?(:include_base)
    indexed_banks = class_current.include_base if class_current.method_defined?(:include_base)

    if params && params[:extra_params]
      methods = params[:extra_params].split(";")
      methods.each do |method|
        method_customs = method.split("(")
        current_method = method_customs[0]
        current_params = method_customs[1].split(")")[0]
        next unless class_current.respond_to? current_method.to_sym

        indexed_banks = if current_params.present?
                          indexed_banks.send(current_method, current_params)
        else
                          indexed_banks.send(current_method)
        end
      end
    end

    indexed_banks
      .where(id: ids)
      .order(Arel.sql("array_position(ARRAY[#{ids.join(',')}]::bigint[], id)"))
      .to_a
  end

  def self.generate_search_query(params, _search_text = "*")
    query_body = {
      track_total_hits: params.dig(:body_options, :track_total_hits) || false,
      timeout: "10s",
      sort: generate_order(params),
      _source: false,
      size: params[:per_page] || 30,
      from: calculate_from(params),
      query: {
        bool: {
          must: [
            {
              match_all: {}
            }
          ],
          filter: generate_filter(params[:where])
        }
      },
      aggs: generate_aggs(params[:aggs])
    }

    if params[:aggs]
      query_body[:aggs][:filtered_aggregations] = {
        filter: {
          bool: {
            must: generate_filter(params[:where])
          }
        },
        aggs: generate_aggs(params[:aggs])
      }
    end

    query_body
  end

  def self.calculate_from(params)
    page = params[:page].to_i
    per_page = params[:per_page].to_i
    page > 0 ? (page - 1) * per_page : 0
  end

  def self.generate_filter(where)
    return [] unless where

    operator_mapping = {
      gt: ->(field, value) { { range: { field => { gt: value } } } },
      gte: ->(field, value) { { range: { field => { gte: value } } } },
      lt: ->(field, value) { { range: { field => { lt: value } } } },
      lte: ->(field, value) { { range: { field => { lte: value } } } },
      not: ->(field, value) { { bool: { must_not: { term: { field => value } } } } },
      exists: ->(field, _) { { exists: { field: } } },
      prefix: ->(field, value) { { prefix: { field => value } } },
      like: ->(field, value) { { wildcard: { field => value.gsub("%", "*") } } },
      ilike: ->(field, value) { { wildcard: { field => value.gsub("%", "*") } } },
      all: ->(field, value) { { bool: { must: value.map { |v| { term: { field => v } } } } } },
      regexp: ->(field, value) { { regexp: { field => value.source } } },
      _not: ->(_, value) { { bool: { must_not: generate_filter(value) } } },
      _or: ->(_, value) { { bool: { should: value.map { |v| generate_filter(v) } } } },
      _and: ->(_, value) { { bool: { must: value.map { |v| generate_filter(v) } } } }
    }

    filters = where.flat_map do |field, condition|
      case condition
      when Array
        if condition.include?(nil)
          { bool: { should: [ { bool: { must_not: { exists: { field: } } } },
                             { terms: { field => condition.compact } } ] } }
        else
          { terms: { field => condition } }
        end
      when Hash
        condition.map do |operator, value|
          if operator_mapping.key?(operator)
            operator_mapping[operator].call(field, value)
          else
            { term: { field => value } }
          end
        end
      else
        { term: { field => condition } }
      end
    end

    filters.flatten
  end

  def self.generate_aggs(aggs)
    return {} unless aggs.is_a?(Hash)

    aggs.transform_values do |agg|
      { terms: { field: agg[:field], size: agg[:limit] || 10 } } if agg[:field]
    end.compact
  end

  def self.generate_order(params)
    if params[:order]
      return params[:order]["created_at"] == "desc" ? { created_at: { order: "desc" } } : { created_at: { order: "asc" } }
    end

    { created_at: { order: "desc" } }
  end

  def self.search_v2(current_class, text_search, params)
    query = generate_search_query(params, text_search)
    current_class.search("*", body: query)
  end
end
