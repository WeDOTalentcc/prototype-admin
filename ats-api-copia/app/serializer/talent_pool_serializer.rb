# frozen_string_literal: true

class TalentPoolSerializer
  include JSONAPI::Serializer

  attributes(
    :id,
    :name,
    :description,
    :status,
    :agent_sourcing_enabled,
    :screening_approved,
    :candidates_count,
    :screened_count,
    :ready_count,
    :created_at,
    :updated_at
  )

  attribute :ideal_profile_id do |pool|
    pool.ideal_profile_id
  end

  attribute :ideal_profile_name do |pool|
    pool.ideal_profile&.name
  end

  attribute :created_by do |pool|
    pool.created_by_user&.name
  end

  attribute :screening_questions do |pool|
    pool.screening_questions || []
  end

  attribute :agent_config do |pool|
    pool.agent_config || {}
  end
end
