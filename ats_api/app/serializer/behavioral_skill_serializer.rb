# frozen_string_literal: true

class BehavioralSkillSerializer
  include JSONAPI::Serializer

  attributes :id, :name, :is_deleted, :account_id, :skill_category_id, :created_at, :updated_at

  attribute :skill_category_name do |obj|
    obj.skill_category&.name
  end
end
