# frozen_string_literal: true

module EntityColumnService
  module Entities
    class SkillRelationship < Base
      def self.structure
        [
          {
            value: "name",
            text: "Skill",
            sortable: true,
            type: "text",
            filter: "agg",
            width: "auto"
          },
          {
            value: "description",
            text: "Description",
            sortable: true,
            type: "dynamicText",
            filter: "text",
            width: "auto",
            update_url: "/users/skill_relationships/",
            update_entity: "skill_relationship",
            update_field: "id",
            object_key: "description"
          },
          {
            value: "min_value",
            text: "Min Value",
            sortable: true,
            type: "dynamicText",
            filter: "number",
            width: "auto",
            update_url: "/users/skill_relationships/",
            update_entity: "skill_relationship",
            update_field: "id",
            object_key: "min_value"
          },
          {
            value: "max_value",
            text: "Max Value",
            sortable: true,
            type: "dynamicText",
            filter: "number",
            width: "auto",
            update_url: "/users/skill_relationships/",
            update_entity: "skill_relationship",
            update_field: "id",
            object_key: "max_value"
          },
          {
            value: "main",
            text: "Principal",
            sortable: true,
            type: "dynamicSwitch",
            filter: "boolean",
            width: "auto",
            update_url: "/users/skill_relationships/",
            update_entity: "skill_relationship",
            update_field: "id",
            object_key: "main"
          },
          {
            value: "experience_time",
            text: "Tempo de Experiência",
            sortable: true,
            type: "dynamicSelect",
            filter: "agg",
            default_values: ::SkillRelationship::EXPERIENCE_TIMES,
            width: "auto",
            update_url: "/users/skill_relationships/",
            update_entity: "skill_relationship",
            update_field: "id",
            object_key: "experience_time"
          },
          {
            value: "level_skill",
            text: "Nível da Habilidade",
            sortable: true,
            type: "dynamicSelect",
            filter: "agg",
            default_values: ::SkillRelationship::SKILL_LEVELS,
            width: "auto",
            update_url: "/users/skill_relationships/",
            update_entity: "skill_relationship",
            update_field: "id",
            object_key: "level_skill"
          },
          {
            value: "created_at",
            text: "Date Created",
            sortable: true,
            type: "date",
            filter: "date",
            width: "auto"
          }
        ]
      end
    end
  end
end
