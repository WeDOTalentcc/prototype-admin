module EntityColumnService
  module Entities
    class Account < Base
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
            value: "name",
            text: "Name",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "setup_url",
            text: "Setup URL",
            sortable: true,
            type: "link",
            target: "_blank",
            filter: "text",
            min_width: "400px"
          },
          {
            value: "setup_token_expires_at",
            text: "Token Expiration",
            sortable: true,
            type: "date",
            filter: "date"
          },
          {
            value: "tenant",
            text: "Tenant",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "staging_tenant",
            text: "Staging Tenant",
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
          }
        ]
      end
    end
  end
end
