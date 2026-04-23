# frozen_string_literal: true

class PublicApplySerializer
  include JSONAPI::Serializer

  attributes :id, :candidate_id, :job_id, :source, :created_at

  attribute :message do |_object|
    "Application submitted successfully"
  end
end
