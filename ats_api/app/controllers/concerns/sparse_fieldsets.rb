module SparseFieldsets
  extend ActiveSupport::Concern

  AI_PRESETS = {
    candidate: {
      list: [ :id, :name, :email, :mobile_phone, :role_name, :city, :state, :current_company ],
      minimal: [ :id, :name, :role_name, :curriculum_text ],
      contact: [ :id, :name, :email, :mobile_phone, :secondary_phone, :linkedin ]
    },
    sourced_profile: {
      list: [ :id, :name, :email, :phone, :title, :city, :state, :current_company ],
      minimal: [ :id, :name, :curriculum_text ]
    },
    job: {
      list: [ :id, :title, :location, :contract_type, :status, :created_at ],
      minimal: [ :id, :title, :description ]
    }
  }.freeze

  private

  def sparse_fields_for(serializer_class)
    resource_type = extract_resource_type(serializer_class)

    if params[:preset].present?
      return resolve_preset(resource_type, params[:preset])
    end

    return nil unless params[:fields].present?

    fields_param = params[:fields]

    if fields_param.is_a?(String)
      parse_fields_string(fields_param)
    elsif fields_param.is_a?(Hash) && fields_param[resource_type].present?
      parse_fields_string(fields_param[resource_type])
    end
  end

  def resolve_preset(resource_type, preset_name)
    AI_PRESETS.dig(resource_type, preset_name.to_sym)
  end

  def extract_resource_type(serializer_class)
    serializer_class.name.demodulize.underscore.gsub("_serializer", "").to_sym
  end

  def parse_fields_string(fields_string)
    fields_string.split(",").map(&:strip).map(&:to_sym)
  end
end
