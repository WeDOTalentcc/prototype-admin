# frozen_string_literal: true

class OpinionSerializer
  include JSONAPI::Serializer

  attributes(
    :id,
    :uid,
    :candidate_id,
    :job_id,
    :user_id,
    :account_id,
    :content,
    :status,
    :metadata,
    :is_deleted,
    :created_at,
    :updated_at
  )

  attribute :author_name do |object|
    object.user&.name
  end

  attribute :job_title do |object|
    object.job&.title
  end

  belongs_to :user
  belongs_to :candidate
  belongs_to :job, if: proc { |obj| obj.job_id.present? }
end
