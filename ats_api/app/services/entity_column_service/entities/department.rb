module EntityColumnService
  module Entities
    class Department < Base
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
            value: "level",
            text: "Level",
            sortable: true,
            type: "number",
            filter: "number",
            width: "120px"
          },
          {
            value: "parent_department_name",
            text: "Parent Department",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "manager_name",
            text: "Manager",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "children_count",
            text: "Children",
            sortable: true,
            type: "number",
            filter: "number",
            width: "120px"
          },
          {
            value: "created_at",
            text: "Created At",
            sortable: true,
            type: "date",
            filter: "date",
            width: "auto"
          },
          {
            value: "updated_at",
            text: "Updated At",
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
