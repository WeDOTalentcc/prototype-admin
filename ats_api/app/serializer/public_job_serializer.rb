# frozen_string_literal: true

class PublicJobSerializer
  include JSONAPI::Serializer

  attributes(
    :title,
    :description,
    :city,
    :country,
    :confidential_company_name,
    :disabilities,
    :responsibilities,
    :sector,
    :state,
  )
  attribute :department_name do |object|
    object.respond_to?(:department_name) ? object[:department_name] : object.department&.name
  end

  attribute :employment_type_text do |object|
    idx = object.employment_type
    idx.nil? ? "Não informado" : (Job::EMPLOYMENT_TYPES[idx] || "Não informado")
  end

  attribute :seniority_text do |object|
    idx = object.seniority
    idx.nil? ? "Não informado" : (Job::SENIORITY[idx] || "Não informado")
  end

  attribute :workplace_type_text do |object|
    Job::WORKPLACE_TYPES.find { |w| w["id"].to_s == object.workplace_type.to_s || w["name"] == object.workplace_type }&.dig("name") || "Não informado"
  end

  attribute :skills do |object|
    object.skill_relationships_data[:skills]
  end

  attribute :languages_data do |object|
    object.language_relationships_data[:languages_with_level]
  end

  attribute :behavioral_skills do |object|
    object.behavioral_skills_data[:behavioral_skills]
  end

  attribute :benefits do |object|
    object.benefit_relationships_data[:benefits_with_values]
  end
end
