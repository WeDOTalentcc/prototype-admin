# frozen_string_literal: true

module EntityColumnService
  module Entities
    class Experience < Base
      def self.structure
        [
          {
            value: "actions",
            text: "",
            sortable: false,
            type: "actions",
            filter: "none",
            width: "auto",
            min_width: "200px"
          },
          {
            value: "company_name",
            text: "Company",
            sortable: true,
            type: "text",
            filter: "agg",
            width: "auto"
          },
          {
            value: "occupation_name",
            text: "Position",
            sortable: true,
            type: "text",
            filter: "agg",
            width: "auto"
          },
          {
            value: "description",
            text: "Description",
            sortable: true,
            type: "text",
            filter: "text",
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
            value: "work_here",
            text: "Currently Working",
            sortable: true,
            type: "boolean",
            filter: "agg",
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
