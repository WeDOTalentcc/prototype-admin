# frozen_string_literal: true

class TalentPoolCandidateSerializer
  include JSONAPI::Serializer

  attributes(
    :id,
    :stage,
    :origin,
    :fit_score,
    :notes,
    :moved_to_job_id,
    :moved_at,
    :moved_to_stage,
    :created_at,
    :updated_at
  )

  attribute :candidate do |tpc|
    c = tpc.candidate
    {
      id: c.id,
      name: [c.name, c.surname].compact.join(" "),
      email: c.email,
      current_company: c.current_company,
      role_name: c.role_name,
      seniority_level: c.seniority_level,
      city: c.city,
      state: c.state,
      avatar_url: c.avatar_url,
      technical_skills: c.technical_skills,
      years_of_experience: c.years_of_experience
    }
  end

  attribute :screening_data do |tpc|
    tpc.screening_data || {}
  end

  attribute :match_criteria do |tpc|
    tpc.match_criteria || {}
  end
end
