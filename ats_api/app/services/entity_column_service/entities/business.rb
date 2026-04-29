module EntityColumnService
  module Entities
    class Business < Base
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
            value: "corporate_name",
            text: "Corporate Name",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "cnpj",
            text: "CNPJ",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "email",
            text: "Email",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "phone",
            text: "Phone",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "website",
            text: "Website",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "industry",
            text: "Industry",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "size",
            text: "Size",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "linkedin",
            text: "LinkedIn",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "about",
            text: "About",
            sortable: false,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "is_active",
            text: "Active",
            sortable: true,
            type: "boolean",
            filter: "boolean",
            width: "auto"
          },
          {
            value: "job_amount",
            text: "Job Amount",
            sortable: true,
            type: "number",
            filter: "number",
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
