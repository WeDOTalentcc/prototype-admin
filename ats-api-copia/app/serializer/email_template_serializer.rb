# frozen_string_literal: true

class EmailTemplateSerializer
  include JSONAPI::Serializer

  attributes(
    :id,
    :company_id,
    :name,
    :subject,
    :body_html,
    :body_text,
    :category,
    :channel,
    :situation,
    :trigger_type,
    :used_in,
    :priority,
    :variables,
    :is_active,
    :is_system_template,
    :visibility,
    :origin_template_id,
    :version,
    :created_by,
    :created_at,
    :updated_at
  )
end
