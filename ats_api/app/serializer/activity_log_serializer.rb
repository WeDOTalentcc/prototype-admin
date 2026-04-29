class ActivityLogSerializer
  include JSONAPI::Serializer
  attributes(
    :id,
    :action,
    :user_id,
    :account_id,
    :created_at,
    :updated_at,
    :reference_type,
    :reference_id,
    :ip_address,
    :rolled_back_from_id,
    :changeset,
    :category
  )

  attribute :user_name do |object|
    if object.respond_to?(:user_name)
      object.user_name
    else
      object.user&.name
    end
  end

  attribute :account_name do |object|
    if object.respond_to?(:account_name)
      object.account_name
    else
      object.account&.name
    end
  end

  attribute :changeset_summary do |object|
    next "" if object.changeset.blank?

    object.changeset.map do |field, changes|
      field_name = field.humanize
      if changes.is_a?(Hash) && changes.key?("from") && changes.key?("to")
        "#{field_name}: #{changes['from']} → #{changes['to']}"
      elsif changes.is_a?(Array)
        "#{field_name}: #{changes[0]} → #{changes[1]}"
      else
        "#{field_name}: #{changes}"
      end
    end.join("; ")
  end
end
