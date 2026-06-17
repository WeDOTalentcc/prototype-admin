module EntityColumnService
  module Entities
    class WhatsappConfiguration < Base
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
            width: "auto"
          },
          {
            value: "phone_number",
            text: "Phone Number",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "environment",
            text: "Environment",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "redirect_url",
            text: "Redirect URL",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "action_type",
            text: "Action Type",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "developer_name",
            text: "Developer",
            sortable: true,
            type: "text",
            filter: "text",
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
            value: "active",
            text: "Active",
            sortable: true,
            type: "boolean",
            filter: "boolean",
            width: "auto"
          },
          {
            value: "priority",
            text: "Priority",
            sortable: true,
            type: "number",
            filter: "number",
            width: "auto"
          },
          {
            value: "is_deleted",
            text: "Deleted?",
            sortable: true,
            type: "boolean",
            filter: "boolean",
            width: "auto"
          },
          {
            value: "deleted_at",
            text: "Deleted At",
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
    end
  end
end
