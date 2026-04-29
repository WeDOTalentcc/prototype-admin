# frozen_string_literal: true

module EntityColumnService
  module Entities
    class SelectiveProcess < Base
      def self.structure
        [
          {
            value: "name",
            text: "Name",
            sortable: true,
            type: "text",
            filter: "text",
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
            value: "position",
            text: "Position",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "job_title",
            text: "Job",
            sortable: true,
            type: "text",
            filter: "text",
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
