class CandidateFeedbackSerializer
  include JSONAPI::Serializer

  CONTEXT_PRIORITY = {
    apply_id: "apply",
    sourced_profile_sourcing_id: "sourced_profile_sourcing",
    sourcing_id: "sourcing",
    candidate_id: "candidate"
  }.freeze

  attributes(
    :id,
    :sourcing_id,
    :apply_id,
    :candidate_id,
    :user_id,
    :account_id,
    :job_id,
    :sourced_profile_sourcing_id,
    :reference_type,
    :reference_id,
    :reason,
    :feedback_type,
    :search_query_snapshot,
    :candidate_score_snapshot,
    :is_deleted,
    :created_at,
    :updated_at
  )

  attribute :is_like do |object|
    object.feedback_type == "like"
  end

  attribute :is_dislike do |object|
    object.feedback_type == "dislike"
  end

  attribute :context do |object|
    CONTEXT_PRIORITY.find { |attr, _| object.public_send(attr).present? }&.last || "unknown"
  end

  attribute :query_summary do |object|
    next nil unless object.search_query_snapshot.present?

    {
      query: object.search_query_snapshot.dig("query"),
      searched_at: object.search_query_snapshot.dig("searched_at")
    }
  end

  attribute :candidate_score do |object|
    next nil unless object.candidate_score_snapshot.present?

    object.candidate_score_snapshot.dig("score")
  end

  belongs_to :sourcing, serializer: SourcingSerializer
  belongs_to :apply, serializer: ApplySerializer
  belongs_to :candidate, serializer: CandidateSerializer
  belongs_to :user, serializer: UserSerializer
  belongs_to :job, serializer: JobSerializer
  belongs_to :sourced_profile_sourcing, serializer: SourcedProfileSourcingSerializer
end
