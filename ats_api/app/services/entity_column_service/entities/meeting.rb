# frozen_string_literal: true

module EntityColumnService
  module Entities
    class Meeting < Base
      def self.structure
        [
          {
            value: "action",
            text: "",
            sortable: false,
            type: "actions",
            width: "auto",
            avoid_list: true,
            min_width: "auto"
          },
          {
            value: "subject",
            text: "Subject",
            sortable: true,
            type: "internalLink",
            filter: "text",
            width: "200px",
            min_width: "150px"
          },
          {
            value: "provider_text",
            text: "Provider",
            sortable: true,
            type: "badge",
            filter: "agg",
            width: "150px",
            min_width: "120px"
          },
          {
            value: "organizer_name",
            text: "Organizer",
            sortable: true,
            type: "text",
            filter: "agg",
            width: "180px",
            min_width: "150px"
          },
          {
            value: "start_time",
            text: "Start Time",
            sortable: true,
            type: "datetime",
            filter: "date",
            width: "180px",
            min_width: "150px"
          },
          {
            value: "end_time",
            text: "End Time",
            sortable: true,
            type: "datetime",
            filter: "date",
            width: "180px",
            min_width: "150px"
          },
          {
            value: "duration_minutes",
            text: "Duration (min)",
            sortable: true,
            type: "number",
            filter: "number",
            width: "120px",
            min_width: "100px"
          },
          {
            value: "status",
            text: "Status",
            sortable: true,
            type: "badge",
            filter: "agg",
            width: "120px",
            min_width: "100px"
          },
          {
            value: "join_url",
            text: "Join URL",
            sortable: false,
            type: "link",
            filter: false,
            width: "150px",
            min_width: "120px"
          },
          {
            value: "created_at",
            text: "Created At",
            sortable: true,
            type: "datetime",
            filter: "date",
            width: "180px",
            min_width: "150px"
          },
          {
            value: "updated_at",
            text: "Updated At",
            sortable: true,
            type: "datetime",
            filter: "date",
            width: "180px",
            min_width: "150px"
          }
        ]
      end

      def self.default_columns
        [
          "action",
          "subject",
          "provider_text",
          "organizer_name",
          "start_time",
          "duration_minutes",
          "status",
          "join_url"
        ]
      end
    end
  end
end
