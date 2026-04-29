module EntityColumnService
  module Entities
    class Address < Base
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
            value: "street",
            text: "Street",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "number",
            text: "Number",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "complement",
            text: "Complement",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "neighborhood",
            text: "Neighborhood",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "zip_code",
            text: "Zip Code",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "city_id",
            text: "City",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "state_id",
            text: "State",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "country_id",
            text: "Country",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "title",
            text: "Title",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "address_type",
            text: "Address Type",
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
            value: "worksite",
            text: "Worksite",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "bill_to",
            text: "Bill To",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "sold_to",
            text: "Sold To",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          }
        ]
      end
    end
  end
end
