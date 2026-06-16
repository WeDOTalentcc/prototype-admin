class ListRelationshipSerializer
  include JSONAPI::Serializer

  attributes(
    :id,
    :list_id,
    :reference_type,
    :reference_id,
    :position,
    :general_comments,
    :score,
    :account_id,
    :created_at,
    :updated_at
  )

  attribute :list_name do |relationship|
    relationship.list&.name
  end

  def serializable_hash
    hash = super

    relationships_map = if @resource.is_a?(Array)
      @resource.index_by { |r| r.id.to_s }
    else
      { @resource.id.to_s => @resource }
    end

    params_to_use = @params || {}

    if hash[:data].is_a?(Array)
      hash[:data] = hash[:data].map do |item|
        relationship = relationships_map[item[:id].to_s]
        merge_reference_attributes(item, relationship, params_to_use)
      end
    elsif hash[:data] && hash[:data][:attributes]
      relationship = relationships_map[hash[:data][:id].to_s]
      hash[:data] = merge_reference_attributes(hash[:data], relationship, params_to_use)
    end

    hash
  end

  private

  def merge_reference_attributes(item, relationship, params = {})
    return item unless item[:attributes] && relationship && relationship.reference

    serializer_class = self.class.serializer_for_reference_type(relationship.reference_type)
    return item unless serializer_class

    serializer_instance = serializer_class.new(
      relationship.reference,
      params: params
    )

    reference_serialized = serializer_instance.serializable_hash

    reference_attributes = if reference_serialized[:data] && reference_serialized[:data][:attributes]
      reference_serialized[:data][:attributes].deep_symbolize_keys
    elsif reference_serialized[:data] && reference_serialized[:data].is_a?(Array)
      {}
    else
      {}
    end

    item[:attributes] = item[:attributes].merge(reference_attributes)

    item
  end

  def self.serializer_for_reference_type(reference_type)
    return nil unless reference_type.present?

    serializer_name = "#{reference_type}Serializer"
    serializer_name.constantize
  rescue NameError
    Rails.logger.warn("Serializer not found for reference_type: #{reference_type}")
    nil
  end
end
