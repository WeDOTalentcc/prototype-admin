# frozen_string_literal: true

module EntityColumnService
  module Entities
    class Question < Base
      def self.structure
        [
          {
            value: "title",
            text: "Title",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "response_type",
            text: "Response Type",
            sortable: true,
            type: "text",
            filter: "agg",
            width: "auto"
          },
          {
            value: "evaluation_title",
            text: "Evaluation",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "parent_question_title",
            text: "Parent Question",
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
          }
        ]
      end
    end
  end
end
