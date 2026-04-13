# app/serializers/apply_serializer.rb
# frozen_string_literal: true

class ApplySerializer
  include JSONAPI::Serializer

  attributes(
    :id,
    :candidate_id,
    :job_id,
    :selective_process_id,
    :is_deleted,
    :source,
    :status,
    :lia_score,
    :match_percentage,
    :current_stage,
    :stage_entered_at,
    :additional_data,
    :fork_uuid,
    :created_at,
    :updated_at
  )
end
