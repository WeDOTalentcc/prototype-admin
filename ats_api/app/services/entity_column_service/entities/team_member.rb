module EntityColumnService
  module Entities
    class TeamMember < Base
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
            value: "team_name",
            text: "Team",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "user_name",
            text: "Member",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "role",
            text: "Role",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "joined_at",
            text: "Joined At",
            sortable: true,
            type: "date",
            filter: "date",
            width: "auto"
          },
          {
            value: "left_at",
            text: "Left At",
            sortable: true,
            type: "date",
            filter: "date",
            width: "auto"
          },
          {
            value: "is_active",
            text: "Active",
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
