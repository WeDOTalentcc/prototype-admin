# frozen_string_literal: true

module EntityColumnService
  module Entities
    class SourcedProfile < Base
      def self.structure
        [
          {
            value: "enrichment_badges",
            text: "Contato",
            sortable: false,
            type: "EnrichmentBadges",
            filter: nil,
            width: "70px",
            min_width: "70px",
            align: "center"
          },
          {
            value: "candidate_feedback",
            text: "",
            sortable: true,
            type: "LikeDislike",
            filter: "agg",
            width: "auto",
            align: "center",
            context: "sourcing",
            min_width: "40px"
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
            value: "score",
            text: "Match",
            sortable: true,
            type: "matchScore",
            filter: "text",
            width: "60px",
            min_width: "60px",
            align: "center"
          },
          {
            value: "avatar_url",
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
    end
  end
end
