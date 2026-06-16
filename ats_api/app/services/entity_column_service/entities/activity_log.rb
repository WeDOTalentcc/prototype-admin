# frozen_string_literal: true

module EntityColumnService
  module Entities
    class ActivityLog < Base
      def self.structure
        [
          {
            value: "action",
            text: "",
            sortable: false,
            type: "actions",
            width: "auto",
            min_width: "200px",
            avoid_list: true,
            default_values: [ {
              name: "show"
            } ]
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
            value: "reference_type",
            text: "Tipo de Referência",
            sortable: true,
            type: "text",
            filter: "agg",
            width: "auto"
          },
          {
            value: "reference_id",
            text: "ID da Referência",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "action",
            text: "Ação",
            sortable: true,
            type: "text",
            filter: "agg",
            width: "auto"
          },
          {
            value: "user_name",
            text: "Usuário",
            sortable: true,
            type: "text",
            filter: "agg",
            width: "auto"
          },
          {
            value: "account_name",
            text: "Conta",
            sortable: true,
            type: "text",
            filter: "agg",
            width: "auto"
          },
          {
            value: "changeset_summary",
            text: "Resumo das Mudanças",
            sortable: false,
            type: "text",
            filter: "text",
            width: "auto",
            min_width: "300px"
          },
          {
            value: "ip_address",
            text: "Endereço IP",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "created_at",
            text: "Data de Criação",
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
