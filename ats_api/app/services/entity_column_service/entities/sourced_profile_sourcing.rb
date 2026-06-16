# frozen_string_literal: true

module EntityColumnService
  module Entities
    class SourcedProfileSourcing < Base
      def self.structure
        [
          {
            value: "candidate_feedback",
            text: "Feedback",
            sortable: true,
            type: "LikeDislike",
            filter: "agg",
            width: "auto",
            align: "center",
            context: "sourcing"
          },
          {
            value: "sourcing_score",
            text: "Score IA",
            sortable: true,
            type: "matchScore",
            filter: "text",
            width: "60px",
            min_width: "60px",
            align: "center"
          },
          {
            value: "profile_origin",
            text: "Fonte",
            sortable: true,
            type: "sourceBadge",
            filter: "text",
            width: "60px",
            min_width: "60px",
            align: "center"
          },
          {
            value: "picture_url",
            value_name: "name",
            text: "Candidato",
            sortable: true,
            type: "avatarWithName",
            filter: "text",
            width: "60px"
          },
          {
            value: "role_name",
            text: "Cargo atual",
            sortable: true,
            type: "text",
            is_bold: true,
            width: "auto",
            filter: "text",
            update_field: "id",
            update_url: "/users/candidates/",
            update_entity: "candidate"
          },
          {
            value: "current_company",
            text: "Empresa atual",
            sortable: true,
            type: "text",
            filter: "agg",
            update_field: "id",
            update_url: "/users/candidates/",
            update_entity: "candidate",
            width: "auto"
          },
          {
            value: "current_salary",
            text: "Salário atual",
            sortable: true,
            type: "currency",
            filter: "text",
            width: "auto"
          },
          {
            value: "current_salary",
            text: "Expectativa salarial",
            sortable: true,
            type: "currency",
            filter: "text",
            width: "auto"
          },
          {
            value: "phone",
            text: "Celular",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto",
            update_field: "id",
            update_url: "/users/candidates/",
            update_entity: "candidate"
          },
          {
            value: "email",
            text: "E-mail",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto",
            update_field: "id",
            update_url: "/users/candidates/",
            update_entity: "candidate"
          },
          {
            value: "city",
            text: "Cidade",
            sortable: true,
            width: "auto",
            filter: "agg",
            type: "textWithIcon",
            icon: "lucide-map-pin"
          },
          {
            value: "linkedin",
            text: "LinkedIn",
            sortable: true,
            type: "iconWithLink",
            filter: "text",
            icon: "lucide-linkedin",
            color: "#0A66C2",
            width: "40px",
            min_width: "40px",
            align: "center"
          }
        ]
      end

      def self.similarity
        base = structure.deep_dup

        similarity_column = {
          value: "similarity_score",
          text: "Match semântico",
          sortable: true,
          type: "matchScore",
          filter: "text",
          width: "60px",
          min_width: "60px",
          align: "center"
        }

        [ base[0], similarity_column ] + base[1..-1]
      end
    end
  end
end
