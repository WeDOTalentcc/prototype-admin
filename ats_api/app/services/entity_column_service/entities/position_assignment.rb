module EntityColumnService
  module Entities
    class PositionAssignment < Base
      def self.structure
        [
          {
            value: "action",
            text: "",
            sortable: false,
            type: "actions",
            width: "auto",
            avoid_list: true,
            min_width: "200px"
          },
          {
            value: "id",
            text: "ID",
            sortable: true,
            type: "text",
            filter: "text",
            width: "100px"
          },
          {
            value: "user_name",
            text: "User",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "organizational_position_title",
            text: "Position",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "employment_type",
            text: "Employment Type",
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
            value: "is_current",
            text: "Current",
            sortable: true,
            type: "boolean",
            filter: "agg",
            width: "120px"
          }
        ]
      end
    end
  end
end
