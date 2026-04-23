module EntityColumnService
  module Entities
    class Team < Base
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
            value: "department_name",
            text: "Department",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "team_lead_name",
            text: "Team Lead",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "member_count",
            text: "Members",
            sortable: true,
            type: "number",
            filter: "number",
            width: "120px"
          },
          {
            value: "is_active",
            text: "Active",
            sortable: true,
            type: "boolean",
            filter: "agg",
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
