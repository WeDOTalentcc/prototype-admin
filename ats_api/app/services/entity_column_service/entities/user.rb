module EntityColumnService
  module Entities
    class User < Base
      def self.structure
        [
          {
            value: "id",
            text: "ID",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "name",
            text: "Usuário",
            sortable: true,
            type: "User",
            filter: "text",
            width: "auto",
            default_values: [
              "email"
            ]
          },
          {
            value: "role_name",
            text: "Cargo",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "status_name",
            text: "Status",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "is_admin",
            text: "Admin",
            sortable: true,
            type: "boolean",
            filter: "boolean",
            width: "auto"
          },
          {
            value: "account_name",
            text: "Conta",
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
          },
          {
            value: "updated_at",
            text: "Date Updated",
            sortable: true,
            type: "date",
            filter: "date",
            width: "auto"
          },
          {
            value: "action",
            text: "",
            sortable: false,
            type: "actions",
            width: "auto",
            avoid_list: true,
            min_width: "200px",
            default_values: [
              { name: "edit" },
              { name: "destroy" }
            ]
          }
        ]
      end

      def self.default
        [
          {
            value: "id",
            text: "ID",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "name",
            text: "Usuário",
            sortable: true,
            type: "User",
            filter: "text",
            width: "auto",
            default_values: [
              "email"
            ]
          },
          {
            value: "role_name",
            text: "Cargo",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "status_name",
            text: "Status",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "is_admin",
            text: "Admin",
            sortable: true,
            type: "boolean",
            filter: "boolean",
            width: "auto"
          },
          {
            value: "account_name",
            text: "Conta",
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
          },
          {
            value: "updated_at",
            text: "Date Updated",
            sortable: true,
            type: "date",
            filter: "date",
            width: "auto"
          },
          {
            value: "action",
            text: "",
            sortable: false,
            type: "actions",
            width: "auto",
            avoid_list: true,
            min_width: "200px",
            default_values: [
              { name: "edit" },
              { name: "destroy" }
            ]
          }
        ]
      end
    end
  end
end
