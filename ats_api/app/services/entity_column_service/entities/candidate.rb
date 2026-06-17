# frozen_string_literal: true

module EntityColumnService
  module Entities
    class Candidate < Base
      def self.structure_old
        [
          {
            value: "action",
            text: "",
            sortable: false,
            type: "actions",
            width: "auto",
            avoid_list: true,
            min_width: "auto"
          },
          {
            value: "avatar_url",
            value_name: "name",
            text: "Avatar",
            sortable: false,
            type: "avatar",
            width: "auto",
            min_width: "auto",
            filter: "text"
          },
          {
            value: "name",
            text: "Name",
            sortable: true,
            type: "internalLink",
            filter: "text",
            width: "auto"
          },
          {
            value: "email",
            text: "Email",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto",
            update_field: "id",
            update_url: "/users/candidates/",
            update_entity: "candidate"
          },
          {
            value: "mobile_phone",
            text: "Phone",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto",
            update_field: "id",
            update_url: "/users/candidates/",
            update_entity: "candidate"
          },
          {
            value: "role_name",
            text: "Position",
            sortable: true,
            type: "text",
            width: "auto",
            filter: "text",
            update_field: "id",
            update_url: "/users/candidates/",
            update_entity: "candidate"
          },
          {
            value: "current_company",
            text: "Current Company",
            sortable: true,
            type: "text",
            filter: "agg",
            update_field: "id",
            update_url: "/users/candidates/",
            update_entity: "candidate",
            width: "auto"
          },
          {
            value: "city",
            text: "City",
            sortable: true,
            width: "auto",
            filter: "agg",
            type: "text",
            update_field: "id",
            update_url: "/users/candidates/",
            update_entity: "candidate",
            update_key: "city",
            search_url: "/users/cities",
            field_response_text: "name",
            field_response_value: "name",
            search_entity: "cities"
          },
          {
            value: "created_at",
            text: "Date Added",
            sortable: true,
            type: "date",
            filter: "date",
            width: "auto"
          },
          {
            value: "updated_at",
            text: "Last Update",
            width: "auto",
            sortable: true,
            type: "date",
            filter: "date"
          },
          {
            value: "ActionsPin",
            text: "Ações",
            sortable: false,
            type: "ActionsPin",
            width: "auto",
            avoid_list: true,
            min_width: "auto"
          }
        ]
      end

      def self.shortlists
        [
          {
            value: "avatar",
            text: "Avatar",
            sortable: false,
            type: "imageViewed",
            width: "auto",
            filter: "text"
          },
          {
            value: "name",
            text: "Candidate",
            sortable: true,
            type: "dynamicLink",
            filter: "text",
            component: "UsersCandidateNew",
            preview_component: "CandidatePreview",
            width: "auto"
          },
          {
            value: "current_company",
            text: "Current Company",
            sortable: true,
            type: "DynamicTextSimple",
            filter: "agg",
            update_field: "id",
            update_url: "/users/candidates/",
            update_entity: "candidate",
            width: "auto"
          },
          {
            value: "role_name",
            text: "Title",
            sortable: true,
            type: "DynamicTextSimple",
            width: "auto",
            filter: "text",
            update_field: "id",
            update_url: "/users/candidates/",
            update_entity: "candidate"
          },
          {
            value: "city",
            text: "City",
            sortable: true,
            width: "auto",
            type: "text",
            filter: "agg"
          },
          {
            value: "linkedin",
            text: "Linkedin",
            sortable: true,
            width: "auto",
            filter: "text",
            type: "DynamicTextSimple",
            update_field: "id",
            update_url: "/users/candidates/",
            update_entity: "candidate"
          }
        ]
      end

      def self.structure
        [
          {
            value: "source",
            text: "Fonte",
            sortable: true,
            type: "sourceBadge",
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
            sortable_field: "name",
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
            value: "mobile_phone",
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
          },
          {
            value: "ActionsFavorite",
            text: "Favorito",
            sortable: false,
            type: "ActionsFavorite",
            width: "60px",
            min_width: "60px",
            align: "center"
          },
          {
            value: "action",
            text: "Ações",
            sortable: false,
            type: "actions",
            width: "auto",
            min_width: "80px",
            avoid_list: true,
            align: "center",
            default_values: [ {
              name: "pin"
            } ]
          }
        ]
      end

      def self.lists
        [
          {
            value: "source",
            text: "Fonte",
            sortable: true,
            type: "sourceBadge",
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
            value: "mobile_phone",
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
          },
          {
            value: "ActionsFavorite",
            text: "Favorito",
            sortable: false,
            type: "ActionsFavorite",
            width: "60px",
            min_width: "60px",
            align: "center"
          }
        ]
      end
    end
  end
end
