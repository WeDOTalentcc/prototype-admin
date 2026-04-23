module EntityColumnService
  module Entities
    class BenefitRelationship < Base
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
          },
          {
            value: "type_description",
            text: "Type Description",
            sortable: true,
            type: "DynamicText",
            filter: "text",
            width: "auto",
            update_url: "/users/benefit_relationships/",
            update_entity: "benefit_relationship",
            update_field: "id",
            object_key: "type_description"
          },
          {
            value: "description",
            text: "Description",
            sortable: true,
            type: "DynamicText",
            filter: "text",
            width: "auto",
            update_url: "/users/benefit_relationships/",
            update_entity: "benefit_relationship",
            update_field: "id",
            object_key: "description"
          },
          {
            value: "is_company",
            text: "Is Company",
            sortable: true,
            type: "DynamicSwitch",
            filter: "agg",
            width: "auto",
            update_url: "/users/benefit_relationships/",
            update_entity: "benefit_relationship",
            update_field: "id",
            object_key: "is_company"
          },
          {
            value: "details",
            text: "Details",
            sortable: true,
            type: "DynamicText",
            filter: "text",
            width: "auto",
            update_url: "/users/benefit_relationships/",
            update_entity: "benefit_relationship",
            update_field: "id",
            object_key: "details"
          }, {
            value: "is_extendable_to_dependents",
            text: "Extendable to Dependents",
            sortable: true,
            type: "DynamicSwitch",
            filter: "agg",
            width: "auto",
            update_url: "/users/benefit_relationships/",
            update_entity: "benefit_relationship",
            update_field: "id",
            object_key: "is_extendable_to_dependents"
          },
          {
            value: "dependents_count",
            text: "Dependents Count",
            sortable: true,
            type: "DynamicText",
            filter: "text",
            width: "auto",
            update_url: "/users/benefit_relationships/",
            update_entity: "benefit_relationship",
            update_field: "id",
            object_key: "dependents_count"
          },
          {
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
