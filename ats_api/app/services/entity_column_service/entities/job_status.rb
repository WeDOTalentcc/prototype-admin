module EntityColumnService
  module Entities
    class JobStatus < Base
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
            value: "color",
            text: "Color",
            sortable: true,
            type: "dynamicColor",
            filter: "agg",
            width: "auto",
            update_url: "/users/job_statuses/",
            update_entity: "job_status",
            update_field: "id",
            object_key: "color"
          }
        ]
      end
    end
  end
end
