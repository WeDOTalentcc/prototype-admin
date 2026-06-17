# frozen_string_literal: true

class EntityPageSerializer
  include JSONAPI::Serializer

  attributes(
    :entity,
    :type_view,
    :label,
    :icon,
    :link,
    :pages,
    :link,
    :custom_entity,
    :job_id,
    :created_at,
    :updated_at
  )
end
