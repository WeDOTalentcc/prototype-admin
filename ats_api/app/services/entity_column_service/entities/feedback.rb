# frozen_string_literal: true

module EntityColumnService
  module Entities
    class Feedback < Base
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
            value: "description",
            text: "Description",
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
            value: "job_title",
            text: "Job",
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
