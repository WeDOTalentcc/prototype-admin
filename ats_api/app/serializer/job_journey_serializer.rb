class JobJourneySerializer
  include JSONAPI::Serializer

  attributes(
    :id,
    :name,
    :description,
    :position,
    :active,
    :required,
    :account_id,
    :job_id,
    :created_at,
    :updated_at
  )

  belongs_to :account
  belongs_to :job, optional: true
end
