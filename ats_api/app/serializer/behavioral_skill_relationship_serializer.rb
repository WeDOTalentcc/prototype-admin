# frozen_string_literal: true

class BehavioralSkillRelationshipSerializer
  include JSONAPI::Serializer

  attributes(
    :id,
    :behavioral_skill_id,
    :account_id,
    :reference_type,
    :reference_id,
    :is_deleted,
    :priority,
    :min_value,
    :max_value,
    :description,
    :main,
    :experience_time,
    :level_skill,
    :created_at,
    :updated_at
  )

  attribute :behavioral_skill_name do |obj|
    obj.behavioral_skill&.name
  end

  attribute :experience_time_name do |obj|
    exp = BehavioralSkillRelationship::EXPERIENCE_TIMES.find { |e| e[:id] == obj.experience_time }
    exp ? exp[:name] : nil
  end

  attribute :level_skill_name do |obj|
    level = BehavioralSkillRelationship::SKILL_LEVELS.find { |s| s[:id] == obj.level_skill }
    level ? level[:name] : nil
  end
end
