module EntityColumnService
  module Entities
    class Benefit < Base
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
            value: "name",
            text: "Name",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "category",
            text: "Category",
            sortable: true,
            type: "text",
            filter: "agg",
            width: "auto"
          },
          {
            value: "is_possible_extend_to_dependents",
            text: "Extend to Dependents",
            sortable: true,
            type: "boolean",
            filter: "agg",
            width: "auto"
          },
          {
            value: "is_per_day",
            text: "Per Day",
            sortable: true,
            type: "boolean",
            filter: "agg",
            width: "auto"
          },
          {
            value: "days_of_month",
            text: "Days of Month",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "enable_value_editing",
            text: "Enable Value Editing",
            sortable: true,
            type: "boolean",
            filter: "agg",
            width: "auto"
          }, {
            value: "types",
            text: "Types",
            sortable: true,
            type: "array",
            filter: "agg",
            width: "auto"
          }, {
            value: "created_at",
            text: "Created At",
            sortable: true,
            type: "date",
            filter: "date",
            width: "200px"
          }, {
            value: "updated_at",
            text: "Updated At",
            sortable: true,
            type: "date",
            filter: "date",
            width: "200px"
          }
        ]
      end
    end
  end
end
