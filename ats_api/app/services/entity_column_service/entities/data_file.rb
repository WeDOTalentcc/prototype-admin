# frozen_string_literal: true

module EntityColumnService
  module Entities
    class DataFile < Base
      def self.structure
        [
          {
            value: "name",
            text: "Name",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "file_size",
            text: "File Size",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "content_type",
            text: "Content Type",
            sortable: true,
            type: "text",
            filter: "agg",
            width: "auto"
          },
          {
            value: "user_name",
            text: "Uploaded By",
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
