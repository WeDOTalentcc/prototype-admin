# frozen_string_literal: true

module EntityColumnService
  module Entities
    class Job < Base
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
            value: "id",
            text: "ID",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto",
            min_width: "50px"
          },
          # {
          #   value: 'external_id',
          #   text: 'ID Externo',
          #   sortable: true,
          #   type: 'text',
          #   filter: 'text',
          #   width: 'auto'
          # },
          {
            value: "title",
            text: "Vaga",
            sortable: true,
            type: "internalLink",
            filter: "text",
            component: "UsersJobNew",
            width: "auto"
          },
          {
            value: "applies_count",
            text: "Candidatos",
            sortable: true,
            type: "JobCandidatesCount",
            width: "auto",
            min_width: "80px"
          },
          {
            value: "applies_by_status_count",
            text: "Performance LIA Triagens",
            sortable: false,
            type: "JobLiaPerformance",
            filter: "number",
            width: "auto"
          },
          {
            value: "job_status",
            text: "Status",
            sortable: true,
            type: "JobStatus",
            filter: "number",
            width: "auto"
          },
          # {
          #   value: 'job_nps',
          #   text: 'NPS',
          #   sortable: true,
          #   type: 'Nps',
          #   filter: 'text',
          #   width: '48px',
          #   min_width: '48px',
          # },
          {
            value: "user_name",
            text: "Recrutador(a)",
            sortable: true,
            type: "User",
            filter: "text",
            width: "auto"
          },
          {
            value: "screening_deadline",
            text: "Prazo Triagem",
            sortable: false,
            type: "date",
            width: "auto",
            min_width: "auto",
            align: "center",
            format: "DD/MM"
          },
          {
            value: "shortlist_deadline",
            text: "Prazo Short List",
            sortable: false,
            type: "date",
            width: "auto",
            min_width: "auto",
            align: "center",
            format: "DD/MM"
          },
          {
            value: "closing_deadline",
            text: "Prazo Encerramento",
            sortable: false,
            type: "date",
            width: "auto",
            min_width: "auto",
            align: "center",
            format: "DD/MM"
          },
          {
            value: "screening_script",
            text: "Roteiro Triagem",
            sortable: false,
            type: "ScreeningScript",
            width: "40px",
            min_width: "40px",
            align: "center"
          },
          {
            value: "action",
            text: "Ações",
            sortable: false,
            type: "actions",
            width: "auto",
            min_width: "120px",
            avoid_list: true,
            align: "center",
            default_values: [
              {
                name: "show"
              },
              {
                name: "edit"
              },
              {
                name: "pin"
              },
              {
                name: "urgent"
              },
              {
                name: "share"
              }
            ]
          }
        ]
      end
    end
  end
end
