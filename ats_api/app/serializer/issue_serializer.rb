# frozen_string_literal: true

class IssueSerializer
  include JSONAPI::Serializer

  attributes(
    :id,
    :text,
    :reference_type,
    :reference_id,
    :account_id,
    :candidate_id,
    :evaluation_id,
    :evaluation_candidate_id,
    :question_id,
    :job_id,
    :created_at,
    :updated_at
  )

  attribute :type do |object|
    raw = object.read_attribute(:type)
    { id: raw, value: Issue::ISSUE_TYPE_LABELS[object.type&.to_sym] || "Não informado" }
  end

  attribute :status do |object|
    raw = object.read_attribute(:status)
    { id: raw, value: Issue::STATUS_LABELS[object.status&.to_sym] || "Pendente" }
  end
end
