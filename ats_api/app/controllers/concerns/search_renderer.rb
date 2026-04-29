module SearchRenderer
  extend ActiveSupport::Concern

  def perform_search(
    model:,
    serializer:,
    term: params[:term],
    search_params: params[:search],
    page: params[:page],
    pinned_first: term.blank?,
    current_user_id: @current_user&.id || nil,
    search_with_pin: nil,
    return_results: false,
    include_aggregators: false,
    compact: [],
    serializer_params: {}
  )
    return perform_autocomplete(model) if params[:autocomplete].present?

    search_params_to_use = search_with_pin || global_search_params

    unless include_aggregators
      search_params_to_use = search_params_to_use.dup
      search_params_to_use[:aggs] = {}
    end

    results = model.search_default(
      term || search_params,
      search_params_to_use,
      page,
      pinned_first,
      false,
      include_aggregators
    )

    return results if return_results

    meta = { total: results[:total_count] }
    meta[:aggregators] = results[:aggs] if include_aggregators
    meta[:where] = search_params_to_use[:where] if search_params_to_use[:where].present?
    meta[:search] = params[:search] if params[:search].present?

    if compact.any?
      records = results[:records]
      compact_fields = compact.map(&:strip).map(&:to_s)
      include_skills = compact_fields.include?("skills") && records.first&.respond_to?(:skills)

      ActiveRecord::Associations::Preloader.new(records: records, associations: :skills).call if include_skills

      render json: {
        data: records.map { |record|
          attrs = record.attributes.slice(*compact_fields)
          attrs["skills"] = record.skills.map(&:name) if include_skills
          attrs
        },
        meta: meta
      }
    else
      render json: serializer.new(
        results[:records],
        meta: meta,
        params: {
          includes: params[:includes] || nil,
          extra_params: params[:extra_params] || nil,
          current_user: @current_user
        }.merge(serializer_params)
      ).serializable_hash
    end
  end

  private

  def perform_autocomplete(model)
    label = model._autocomplete_label
    term_value = params[:term].to_s.strip

    where = {}
    where[:is_deleted] = [ false, nil ] if model.column_names.include?("is_deleted")

    search_fields = term_value.match?(/\A\d+/) ? [ label, :id ] : [ label ]

    results = model.search(
      term_value.presence || "*",
      fields: search_fields,
      match: :word_start,
      where: where,
      limit: 10,
      load: false,
      misspellings: { below: 5 }
    )

    render json: results.map { |r| { id: r.id.to_i, name: r.try(label) } }
  end
end
