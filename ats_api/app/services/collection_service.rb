class CollectionService
  FILTER_FIELD_MAPPING = {
    "avatar_url" => "name",
    "picture_url" => "name"
  }.freeze

  def self.call(params, page = 1, light: false)
    params_search = {}
    current_model = ""
    term = params[:search] || "*"

    current_model = params[:reference_type]&.titleize.gsub(" ", "")&.singularize&.constantize

    if params[:reference_ids]
      params_search = { where: { id: params[:reference_ids] } }
    end

    if !params[:reference_ids]
      params_search[:where] ||= {}
      params_search[:where].merge!(params[:where]) if params[:where]
      if params[:filter]
        if params[:filter].is_a?(String)
          params_search[:filter] = JSON.parse(params[:filter])
        elsif params[:filter].is_a?(ActionController::Parameters)
          params_search[:filter] = params[:filter].to_unsafe_h
        else
          params_search[:filter] = params[:filter]
        end
      end
      if params[:order]
        if params[:order].is_a?(ActionController::Parameters)
          params_search[:order] = params[:order].to_unsafe_h
        else
          params_search[:order] = params[:order]
        end
      end
      params_search[:search] = term if term.present?

      params_search[:filter]&.to_a&.each do |field|
        field_name = FILTER_FIELD_MAPPING[field[0].to_s] || field[0].to_s

        if field[1].is_a?(Array) || field[1].is_a?(Integer) || field[1].is_a?(Hash)
          params_search[:where][field_name] = field[1]
          next
        end
        params_search[:where][field_name] = { like: "%#{field[1]&.downcase}%" } if field[1].present?
      end

      if params[:except_ids].present?
        params_search[:where][:id] = { not: params[:except_ids] }
      end
    end

    return { records: [], total_count: 0 } unless current_model

    results = current_model.search_default(
      term,
      params_search.deep_symbolize_keys!,
      page,
      false,
      nil,
      false
    )

    results
  end
end
