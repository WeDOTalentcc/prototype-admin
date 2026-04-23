# frozen_string_literal: true

require "set"

module EntityColumnService
  module Entities
    class Apply < Base
      def self.structure(job_id = nil)
        base_columns + evaluation_columns(job_id)
      end

      def self.base_columns
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
            width: "auto"
          },
          {
            value: "external_id",
            text: "ID Externo",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "candidate_feedback",
            text: "",
            sortable: true,
            type: "LikeDislike",
            filter: "agg",
            width: "auto",
            align: "center",
            context: "apply"
          },
          {
            value: "total_score",
            text: "Triagem LIA",
            sortable: true,
            type: "IaScore",
            filter: "range",
            width: "auto"
          },
          {
            value: "cv_match",
            text: "Nota LIA CV",
            sortable: true,
            type: "IaScore",
            filter: "range",
            width: "auto"
          },
          {
            value: "name",
            text: "Candidato",
            sortable: true,
            type: "User",
            filter: "text",
            width: "auto"
          },
          {
            value: "role_name",
            text: "Cargo",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "current_company",
            text: "Empresa",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "selective_process_name",
            text: "Status",
            sortable: true,
            type: "selectiveProcess",
            filter: "agg",
            width: "auto"
          },
          {
            value: "alerts",
            text: "Alertas",
            sortable: false,
            type: "ApplyAlerts",
            filter: "agg",
            width: "auto"
          },
          {
            value: "evaluation_candidate_status",
            text: "Status da Avaliação",
            sortable: true,
            type: "enum",
            filter: "agg",
            width: "auto",
            options: [
              { value: "not_sent", text: "Não enviado" },
              { value: "sent", text: "Enviado" },
              { value: "answered", text: "Respondido" }
            ]
          },
          {
            value: "email",
            text: "E-mail",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "phone",
            text: "Telefone",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "linkedin",
            text: "LinkedIn",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "github",
            text: "GitHub",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "portfolio",
            text: "Portfolio",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "date_birth",
            text: "Data de Nascimento",
            sortable: false,
            type: "date",
            filter: "date",
            width: "auto"
          },
          {
            value: "gender",
            text: "Gênero",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "nationality",
            text: "Nacionalidade",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "cpf",
            text: "CPF",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "street",
            text: "Rua",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "number",
            text: "Número",
            sortable: false,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "district",
            text: "Bairro",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "zip",
            text: "CEP",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "city",
            text: "Cidade",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "state",
            text: "Estado",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "country",
            text: "País",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "complement",
            text: "Complemento",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "clt_expectation",
            text: "Expectativa CLT",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "pj_expectation",
            text: "Expectativa PJ",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "freelance_expectation",
            text: "Expectativa Freelance",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "current_salary",
            text: "Salário",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "desired_salary",
            text: "Salário Desejado",
            sortable: false,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "currency",
            text: "Moeda",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "remote_work",
            text: "Trabalho Remoto",
            sortable: true,
            type: "boolean",
            filter: "agg",
            width: "auto"
          },
          {
            value: "mobility",
            text: "Mobilidade",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "source",
            text: "Origem",
            sortable: true,
            type: "text",
            filter: "text",
            width: "auto"
          },
          {
            value: "completed_register",
            text: "Registro Completo?",
            sortable: true,
            type: "boolean",
            filter: "agg",
            width: "auto"
          },
          {
            value: "accept_terms",
            text: "Aceitou Termos?",
            sortable: true,
            type: "boolean",
            filter: "agg",
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
            width: "auto",
            sortable: true,
            type: "date",
            filter: "date"
          }
        ]
      end

      def self.evaluation_columns(job_id = nil)
        columns = []
        evaluations = []
        begin
          if job_id.present?
            evaluations = ::Evaluation.where(job_id: job_id)
          end

          evaluation_names = []
          evaluations.each do |evaluation|
            normalized_name = normalize_evaluation_name(evaluation.name, evaluation.id)
            evaluation_names << normalized_name
          end

          evaluation_names.each do |field_name|
            readable_name = field_name.gsub("_", " ").split.map(&:capitalize).join(" ")
            columns << {
              value: field_name,
              text: readable_name,
              sortable: true,
              type: "ApplyEvaluation",
              filter: "range",
              width: "auto"
            }
          end
        rescue => e
          Rails.logger.warn "Erro ao carregar colunas de avaliação: #{e.message}"
        end

        columns
      end

      private

      def self.normalize_evaluation_name(evaluation_name, evaluation_id)
        name = evaluation_name.split(" ").join("_").downcase + "_#{evaluation_id}"
        normalized = name.to_s.unicode_normalize(:nfd).gsub(/[\u0300-\u036f]/, "")
        normalized.downcase.gsub(/[^a-z0-9_]/, "_").squeeze("_").gsub(/^_+|_+$/, "")
      end

      public

      def self.default(job_id = nil)
        base_columns + evaluation_columns(job_id)
      end

      def self.job(job_id = nil)
        base_columns + evaluation_columns(job_id)
      end
    end
  end
end
