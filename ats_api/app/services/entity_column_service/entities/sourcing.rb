# frozen_string_literal: true

module EntityColumnService
  module Entities
    class Sourcing < Base
      def self.structure
        [
          {
            value: "action",
            text: "",
            sortable: false,
            type: "actions",
            width: "auto",
            avoid_list: true,
            min_width: "auto",
            default_values: [ {
              name: "show"
            }, {
              name: "destroy"
            } ]
          },
          {
            value: "query",
            text: "Query",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "provider",
            text: "Provider",
            sortable: true,
            type: "text",
            filter: "agg",
            width: "auto"
          },
          {
            value: "status",
            text: "Status",
            sortable: true,
            type: "text",
            filter: "agg",
            width: "auto"
          },
          {
            value: "results_count",
            text: "Results",
            sortable: true,
            type: "number",
            filter: "number",
            width: "auto"
          },
          {
            value: "credits_used",
            text: "Credits Used",
            sortable: true,
            type: "number",
            filter: "number",
            width: "auto"
          },
          {
            value: "duration",
            text: "Duration (s)",
            sortable: true,
            type: "number",
            filter: "number",
            width: "auto"
          },
          {
            value: "searched_at",
            text: "Searched At",
            sortable: true,
            type: "date",
            filter: "date",
            width: "auto"
          },
          {
            value: "created_at",
            text: "Created At",
            sortable: true,
            type: "date",
            filter: "date",
            width: "auto"
          }
        ]
      end

      def self.default
        structure.select do |column|
          %w[action query provider status results_count credits_used searched_at].include?(column[:value])
        end
      end
    end
  end
end
