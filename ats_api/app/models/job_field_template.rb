# frozen_string_literal: true

class JobFieldTemplate < ApplicationRecord
  include Searchable

  belongs_to :account

  validates :name, presence: true
  validates :account_id, presence: true
  validates :fields, presence: true

  validate :validate_fields_structure

  scope :default_templates, -> { where(is_default: true) }
  scope :for_account, ->(account_id) { where(account_id: account_id) }


  def self.default_for_account(account_id)
    find_by(account_id: account_id, is_default: true)
  end

  def self.create_default_template(account)
    create!(
      account: account,
      name: "Template Padrão",
      is_default: true,
      fields: default_fields
    )
  end

  def self.default_fields
    [
      {
        field_name: "title",
        label: "Nome da Posição",
        is_required: true,
        category: "critical",
        priority: 1,
        job_journey_position: 1
      },
      {
        field_name: "seniority",
        label: "Nível/Senioridade",
        is_required: true,
        category: "critical",
        priority: 2,
        job_journey_position: 1
      },
      {
        field_name: "is_confidential_set",
        label: "Confidencial (Sim/Não)",
        is_required: true,
        category: "critical",
        priority: 3,
        job_journey_position: 1
      },
      {
        field_name: "department",
        label: "Área/Departamento",
        is_required: true,
        category: "critical",
        priority: 4,
        job_journey_position: 1
      },
      {
        field_name: "user_id",
        label: "Criador da Vaga",
        is_required: true,
        category: "critical",
        priority: 5,
        job_journey_position: 1
      },
      {
        field_name: "salary_from",
        label: "Salário Base (De)",
        is_required: true,
        category: "critical",
        priority: 6,
        job_journey_position: 2
      },
      {
        field_name: "salary_to",
        label: "Salário Base (Até)",
        is_required: true,
        category: "critical",
        priority: 7,
        job_journey_position: 2
      },
      # {
      #   field_name: "bonus_from",
      #   label: "Bônus/Variável (De)",
      #   is_required: false,
      #   category: "optional",
      #   priority: 8,
      #   job_journey_position: 2
      # },
      # {
      #   field_name: "bonus_to",
      #   label: "Bônus/Variável (Até)",
      #   is_required: false,
      #   category: "optional",
      #   priority: 9,
      #   job_journey_position: 2
      # },
      {
        field_name: "benefits_data",
        label: "Benefícios",
        is_required: true,
        category: "critical",
        priority: 10,
        job_journey_position: 3
      },
      {
        field_name: "has_hiring_manager",
        label: "Gestor da Vaga",
        is_required: true,
        category: "critical",
        priority: 11,
        job_journey_position: 1
      },
      {
        field_name: "has_team_composition",
        label: "Composição do Time",
        is_required: true,
        category: "critical",
        priority: 12,
        job_journey_position: 1
      },
      {
        field_name: "location",
        label: "Localização",
        is_required: true,
        category: "critical",
        priority: 13,
        job_journey_position: 4
      },
      {
        field_name: "workplace_type",
        label: "Modelo de Trabalho",
        is_required: true,
        category: "critical",
        priority: 14,
        job_journey_position: 4
      },
      {
        field_name: "employment_type",
        label: "Modelo de Contratação",
        is_required: true,
        category: "critical",
        priority: 15,
        job_journey_position: 5
      },
      {
        field_name: "languages",
        label: "Idiomas Requeridos",
        is_required: false,
        category: "optional",
        priority: 16,
        job_journey_position: 6
      },
      {
        field_name: "years_of_experience",
        label: "Anos de Experiência",
        is_required: true,
        category: "critical",
        priority: 17,
        job_journey_position: 7
      },
      {
        field_name: "technical_requirements",
        label: "Requisitos Técnicos",
        is_required: true,
        category: "critical",
        priority: 18,
        job_journey_position: 8
      },
      {
        field_name: "behavioral_competencies",
        label: "Competências Comportamentais",
        is_required: true,
        category: "critical",
        priority: 19,
        job_journey_position: 9
      },
      {
        field_name: "shortlist_deadline",
        label: "Data Prevista Entrega Shortlist",
        is_required: true,
        category: "critical",
        priority: 20,
        job_journey_position: 10
      },
      {
        field_name: "description",
        label: "Descrição da Vaga",
        is_required: true,
        category: "critical",
        priority: 21,
        job_journey_position: 11
      }
    ]
  end

  private

  def validate_fields_structure
    return if fields.blank?
    return unless fields.is_a?(Array)

    fields.each_with_index do |field, index|
      unless field.is_a?(Hash)
        errors.add(:fields, "Item #{index} deve ser um objeto")
        next
      end

      unless field["field_name"].present?
        errors.add(:fields, "Item #{index} deve ter 'field_name'")
      end

      unless field["label"].present?
        errors.add(:fields, "Item #{index} deve ter 'label'")
      end

      unless [ true, false ].include?(field["is_required"])
        errors.add(:fields, "Item #{index} deve ter 'is_required' (boolean)")
      end
    end
  end
end
