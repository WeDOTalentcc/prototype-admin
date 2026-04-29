# frozen_string_literal: true

module EntityColumnService
  module Entities
    class RemunerationRelationship < Base
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
            value: "name",
            text: "Remuneration Type",
            sortable: true,
            type: "text",
            filter: "agg",
            width: "auto"
          },
          {
            value: "amount",
            text: "Amount",
            sortable: true,
            type: "DynamicText",
            filter: "Text",
            width: "auto",
            update_url: "/users/remuneration_relationships/",
            update_entity: "remuneration_relationship",
            update_field: "id",
            object_key: "amount"
          },
          {
            value: "currency",
            text: "Currency",
            sortable: true,
            type: "DynamicSelect",
            filter: "agg",
            width: "auto",
            update_url: "/users/remuneration_relationships/",
            update_entity: "remuneration_relationship",
            update_field: "id",
            object_key: "currency",
            default_values: ::RemunerationRelationship::CURRENCY_LIST
          },
          {
            value: "period",
            text: "Period",
            sortable: true,
            type: "DynamicText",
            filter: "text",
            width: "auto",
            update_url: "/users/remuneration_relationships/",
            update_entity: "remuneration_relationship",
            update_field: "id",
            object_key: "period"
          },
          {
            value: "comments",
            text: "Comments",
            sortable: false,
            type: "DynamicText",
            filter: "text",
            width: "auto",
            update_url: "/users/remuneration_relationships/",
            update_entity: "remuneration_relationship",
            update_field: "id",
            object_key: "comments"
          },
          {
            value: "value",
            text: "Value",
            sortable: true,
            type: "DynamicCurrency",
            filter: "text",
            width: "auto",
            update_url: "/users/remuneration_relationships/",
            update_entity: "remuneration_relationship",
            update_field: "id",
            object_key: "value"
          },
          {
            value: "contract_type",
            text: "Contract Type",
            sortable: true,
            type: "DynamicAutocomplete",
            filter: "agg",
            width: "auto",
            search_url: "/users/remuneration_relationships/contract_types",
            search_entity: "contract_types",
            field_response_text: "name",
            field_response_value: "name",
            update_url: "/users/remuneration_relationships/",
            update_entity: "remuneration_relationship",
            update_field: "id",
            object_key: "contract_type",
            entity_key: "name"
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
            text: "Last Updated",
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
