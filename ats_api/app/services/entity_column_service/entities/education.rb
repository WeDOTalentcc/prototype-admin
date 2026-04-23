# frozen_string_literal: true

module EntityColumnService
  module Entities
    class Education < Base
      def self.structure
        [
          {
            value: "action",
            text: "",
            sortable: false,
            type: "actions",
            width: "200px",
            avoid_list: true,
            default_values: [
              { name: "destroy" },
              { name: "edit" }
            ]
          },
          {
            value: "institution_name",
            text: "Institution",
            sortable: true,
            type: "text",
            filter: "agg",
            width: "auto"
          },
          {
            value: "study_area_name",
            text: "Study Area",
            sortable: true,
            type: "text",
            filter: "agg",
            width: "auto"
          },
          {
            value: "degree",
            text: "Degree",
            sortable: true,
            type: "text",
            filter: "agg",
            width: "auto"
          },
          {
            value: "start_date",
            text: "Start Date",
            sortable: true,
            type: "date",
            filter: "date",
            width: "auto"
          },
          {
            value: "end_date",
            text: "End Date",
            sortable: true,
            type: "date",
            filter: "date",
            width: "auto"
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
