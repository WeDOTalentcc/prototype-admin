class SelectiveProcessSerializer
  include JSONAPI::Serializer

  attributes(
    :id,
    :name,
    :position,
    :job_id,
    :uid,
    :external_id,
    :sub_status,
    :childrens,
    :position_x,
    :position_y,
    :color,
    :created_at,
    :updated_at,
    :external_id,
    :approved_process_id,
    :rejected_process_id,
    :duration
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

  attribute :color_with_fallback do |object|
    object.color_with_fallback
  end

  attribute :action_behavior do |object|
    object.action_behavior
  end

  attribute :sub_status_options do |object|
    object.sub_status_options
  end
end
