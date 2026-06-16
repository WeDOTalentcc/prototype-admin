# frozen_string_literal: true

module EntityColumnService
  module Entities
    class JobUser < Base
      def self.structure
        [
          {
            value: "select",
            text: "",
            sortable: false,
            type: "select",
            width: "70px",
            min_width: "70px",
            avoid_list: true
          },
          {
            value: "action",
            text: "Ações",
            sortable: false,
            type: "actions",
            width: "auto",
            min_width: "200px",
            avoid_list: true,
            default_values: [ {
              name: "show"
            }, {
              name: "edit"
            }, {
              name: "delete"
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
            value: "user_name",
            text: "Recrutador",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "user_email",
            text: "Email",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "job_title",
            text: "Vaga",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "person_function",
            text: "Função",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "split",
            text: "Split (%)",
            sortable: true,
            type: "number",
            filter: "number",
            width: "auto"
          },
          {
            value: "created_at",
            text: "Criado em",
            sortable: true,
            type: "date",
            filter: "date",
            width: "auto"
          },
          {
            value: "updated_at",
            text: "Atualizado em",
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
