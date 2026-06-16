# frozen_string_literal: true

module EntityColumnService
  module Entities
    class LanguageRelationship < Base
      def self.structure
        [
          {
            value: "action",
            text: "",
            sortable: false,
            type: "actions",
            width: "auto",
            avoid_list: true,
            default_values: [
              { name: "destroy" }
            ]
          },
          {
            value: "language_name",
            text: "Language",
            sortable: true,
            type: "text",
            filter: "agg",
            width: "auto"
          },
          {
            value: "level",
            text: "Level",
            sortable: true,
            type: "dynamicSelect",
            filter: "agg",
            default_values: ::LanguageRelationship::LEVELS,
            width: "auto",
            update_url: "/users/language_relationships/",
            update_entity: "language_relationship",
            update_field: "id",
            object_key: "level"
          },
          {
            value: "priority",
            text: "Priority",
            sortable: true,
            type: "dynamicText",
            filter: "number",
            width: "auto",
            update_url: "/users/language_relationships/",
            update_entity: "language_relationship",
            update_field: "id",
            object_key: "priority"
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
