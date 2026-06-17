# frozen_string_literal: true

module EntityColumnService
  module Entities
    class Evaluation < Base
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
            text: "Name",
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
            value: "job_title",
            text: "Job",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "user_name",
            text: "Evaluator",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "is_main",
            text: "Main",
            sortable: true,
            type: "boolean",
            filter: "boolean",
            width: "auto"
          },
          {
            value: "is_chatbot",
            text: "Chatbot",
            sortable: true,
            type: "boolean",
            filter: "boolean",
            width: "auto"
          },
          {
            value: "ai_enabled",
            text: "AI Enabled",
            sortable: true,
            type: "boolean",
            filter: "boolean",
            width: "auto"
          },
          {
            value: "status",
            text: "Active",
            sortable: true,
            type: "boolean",
            filter: "boolean",
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
