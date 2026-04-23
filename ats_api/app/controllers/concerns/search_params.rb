# app/controllers/concerns/search_params.rb
module SearchParams
  extend ActiveSupport::Concern

  DEFAULT_LIMIT = 30
  DEFAULT_ORDER = { created_at: "desc" }.freeze
  WILDCARD_SEARCH = "*"
  BOOLEAN_TRUE_VALUES = [ "true", true ].freeze
  BOOLEAN_FALSE_VALUES = [ "false", false ].freeze
  ID_FIELDS = %w[id external_id].freeze

  def parse_json_param(param_value, default = {})
    return default if param_value.blank?
    return param_value.to_unsafe_h if param_value.is_a?(ActionController::Parameters)
    return param_value unless param_value.is_a?(String)

    JSON.parse(param_value)
  rescue JSON::ParserError
    default
  end

  def search_with_pin
    build_search_params_with_pin
  end

  def search_with_pin_and_confidential
    build_search_params_with_pin.tap do |params_new|
      user_or_filters = params_new[:where].delete(:_or) || []
      confidential_condition = { _or: confidential_or_conditions }
      if user_or_filters.any?
        params_new[:where][:_and] = [
          confidential_condition,
          { _or: user_or_filters }
        ]
      else
        params_new[:where][:_or] = confidential_or_conditions
      end
    end
  end

  def search_params
    params[:search] = WILDCARD_SEARCH unless params[:search]
    params[:search].downcase
  end

  def custom_params
    {
      where: where_params,
      order: order_params,
      extra_params: params[:extra_params],
      entity_column_id: params[:entity_column_id],
      limit: limit_params
    }
  end

  def model_class_from_string(model_name)
    class_name = model_name.singularize.camelize
    klass = class_name.safe_constantize

    return klass if klass && klass < ActiveRecord::Base
    nil
  end

  def global_search_params
    {
      where: where_params,
      order: order_params,
      page: params[:page] || 1,
      limit: limit_params
    }
  end

  def where_params(base = {})
    where = base.dup || {}

    process_where_param(where) if params[:where].present?
    process_filter_param(where) if params[:filter].present?

    normalize_like_filters(where.deep_symbolize_keys)
  end

  def order_params
    return DEFAULT_ORDER.dup if wildcard_search_without_order?

    order = parse_json_param(params[:order])
    return order unless order.is_a?(Hash)

    normalize_order_keys(order)
  end

  def limit_params
    value = (params[:per_page] || params[:limit]).to_i
    return DEFAULT_LIMIT if value <= 0 || value > DEFAULT_LIMIT
    value
  end

  private

  def build_search_params_with_pin
    params_new = custom_params
    params_new[:order] = { _score: "desc" }.merge(order_params)
    params_new[:boost_where] = { "pin_user_ids" => @current_user.id }

    merge_boost_where(params_new) if params[:boost_where].present?

    params_new
  end

  def merge_boost_where(params_new)
    boost = params[:boost_where]
    return if boost.is_a?(String) && boost.bytesize > 4.kilobytes

    boost = JSON.parse(boost) if boost.is_a?(String)
    params_new[:boost_where].merge!(boost) if boost.is_a?(Hash)
  rescue JSON::ParserError
    nil
  end

  def confidential_or_conditions
    [
      { confidential_user_ids: @current_user.id },
      { confidential_user_ids: [ nil ] },
      { confidential_user_ids: nil }
    ]
  end

  def process_where_param(where)
    parsed_where = parse_json_param(params[:where])
    normalized_where = normalize_hash_values(parsed_where)
    where.merge!(normalized_where)
  end

  def process_filter_param(where)
    filter = parse_json_param(params[:filter])
    return unless filter

    normalized_filter = normalize_hash_values(filter)
    apply_filters(where, normalized_filter)
  end

  def normalize_hash_values(hash)
    hash.transform_values do |value|
      normalize_value(value)
    end
  end

  def normalize_value(value)
    return convert_numeric_hash_to_array(value) if numeric_hash_keys?(value)
    return true if BOOLEAN_TRUE_VALUES.include?(value)
    return false if BOOLEAN_FALSE_VALUES.include?(value)

    value
  end

  def numeric_hash_keys?(value)
    value.is_a?(Hash) && value.keys.all? { |k| k.to_s.match?(/^\d+$/) }
  end

  def convert_numeric_hash_to_array(hash)
    hash.sort_by { |k, _| k.to_i }.map { |_, v| v }
  end

  def apply_filters(where, filter)
    filter.each do |field, value|
      next if handle_favorited_filter(where, field, value)
      next if handle_hidden_filter(where, field, value)

      process_filter_value(where, field, value)
    end
  end

  def handle_favorited_filter(where, field, value)
    return false unless field.to_s == "is_favorited"
    return false unless value.is_a?(Array) && value.include?("Favoritado")

    where[:favorite_user_ids] = @current_user.id
    true
  end

  def handle_hidden_filter(where, field, value)
    return false unless field.to_s == "is_hidden"
    return false unless value.is_a?(Array) && value.include?("Hidden")

    where[:hide_user_ids] = @current_user.id
    true
  end

  def process_filter_value(where, field, value)
    return process_array_filter(where, field, value) if value.is_a?(Array)
    return where[field.to_s] = value if value.is_a?(Integer) || value.is_a?(Hash)
    return unless value.present?

    process_string_or_numeric_filter(where, field, value)
  end

  def process_array_filter(where, field, values)
    return where[field.to_s] = values unless all_strings_or_numerics?(values)

    where[:_or] ||= []
    values.each do |val|
      condition = build_filter_condition(field, val)
      where[:_or] << (id_field?(field) ? condition : { field.to_s => condition })
    end
  end

  def all_strings_or_numerics?(array)
    array.all? { |v| v.is_a?(String) || v.is_a?(Numeric) }
  end

  def process_string_or_numeric_filter(where, field, value)
    condition = build_filter_condition(field, value)
    where[field.to_s] = id_field?(field) ? condition[field.to_s] : condition
  end

  def build_filter_condition(field, value)
    return { field.to_s => convert_id_value(value) } if id_field?(field)

    { like: "%#{value.to_s.downcase}%" }
  end

  def id_field?(field)
    ID_FIELDS.include?(field.to_s)
  end

  def convert_id_value(value)
    value.to_s.match?(/^\d+$/) ? value.to_i : value
  end

  def wildcard_search_without_order?
    params[:search] == WILDCARD_SEARCH && params[:order].blank?
  end

  def normalize_order_keys(order)
    order.transform_keys { |key| key.to_s == "score" ? :_score : key }
  end

  def normalize_like_filters(value)
    return normalize_like_hash(value) if value.is_a?(Hash)
    return value.map { |item| normalize_like_filters(item) } if value.is_a?(Array)

    value
  end

  def normalize_like_hash(hash)
    hash.each_with_object({}) do |(key, val), normalized|
      normalized_value = normalize_like_filters(val)
      normalized_value = normalized_value.downcase if %i[like ilike].include?(key.to_sym) && normalized_value.is_a?(String)
      normalized[key] = normalized_value
    end
  end
end
