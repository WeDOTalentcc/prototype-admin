class SelectiveProcessSerializer
  include JSONAPI::Serializer

  attributes(
    :id,
    :name,
    :position,
    :job_id,
    :uid,
    :sub_status,
    :display_name,
    :description,
    :color,
    :icon,
    :stage_type,
    :is_initial,
    :is_final,
    :is_rejection,
    :is_hired,
    :auto_advance_rules,
    :sla_hours,
    :is_active,
    :is_system,
    :stage_category,
    :action_behavior,
    :default_channel,
    :stage_metadata,
    :created_by,
    :company_id,
    :created_at,
    :updated_at
  )

  attribute :status_code do |object|
    object[:status]
  end

  attribute :status do |object|
    object.status
  end

  attribute :status_label do |object|
    I18n.t(
      "models.selective_process.statuses.#{object.status}",
      default: object.status.humanize
    )
  end
end
