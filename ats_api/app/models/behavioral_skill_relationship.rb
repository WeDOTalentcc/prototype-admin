# frozen_string_literal: true

class BehavioralSkillRelationship < ApplicationRecord
  include Searchable

  belongs_to :behavioral_skill
  belongs_to :reference, polymorphic: true
  belongs_to :account
  belongs_to :user, optional: true

  validates :reference_type, :reference_id, presence: true
  validates :behavioral_skill_id, uniqueness: {
    scope: [ :reference_type, :reference_id ],
    conditions: -> { where(is_deleted: false) },
    message: "Behavioral skill já existe para esta referência"
  }

  EXPERIENCE_TIMES = SkillRelationship::EXPERIENCE_TIMES
  SKILL_LEVELS = SkillRelationship::SKILL_LEVELS

  def search_data
    {
      id: id,
      behavioral_skill_id: behavioral_skill_id,
      behavioral_skill_name: behavioral_skill&.name,
      reference_type: reference_type,
      reference_id: reference_id,
      priority: priority,
      min_value: min_value,
      max_value: max_value,
      description: description,
      main: main,
      experience_time: experience_time,
      level_skill: level_skill,
      is_deleted: is_deleted,
      account_id: account_id,
      created_at: created_at,
      updated_at: updated_at
    }
  end
end
