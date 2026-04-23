# frozen_string_literal: true

class EmailTemplate < ApplicationRecord
  include Searchable

  belongs_to :account
  belongs_to :user

  validates :name, presence: true
  validates :subject, presence: true
  validates :content, presence: true
  validates :category_id, presence: true

  CATEGORIES = [
    { id: 1, name: "Aprovação", color: "#35ab86" },
    { id: 2, name: "Rejeição", color: "#df3939" },
    { id: 3, name: "Agendamento", color: "#3e75ed" },
    { id: 4, name: "Follow-up", color: "#dc8117" },
    { id: 5, name: "Feedback", color: "#1195b5" },
    { id: 6, name: "Contato Inicial", color: "#9e9e9e" },
    { id: 7, name: "Pós-Entrevista", color: "#60BED1" }
  ].freeze

  scope :automated, -> { where(is_automated: true) }
  scope :for_trigger, ->(event) { automated.where(trigger_event: event) }

  def search_data
    {
      name: name,
      subject: subject,
      content: content,
      category: CATEGORIES.find { |c| c[:id] == category_id }&.dig(:name),
      category_id: category_id,
      category_color: CATEGORIES.find { |c| c[:id] == category_id }&.dig(:color),
      account_id: account_id,
      user_id: user_id,
      is_deleted: is_deleted,
      is_automated: is_automated,
      trigger_event: trigger_event,
      created_at: created_at,
      updated_at: updated_at
    }
  end

  def self.search_fields
    [ :name, :subject, :content, :category ]
  end

  def self.include_base
    includes(:account, :user)
  end

  def self.default_search_order
    { created_at: :desc }
  end

  def self.tag_array
    {
      Candidate: [
        { text: "Candidato - E-mail", tag: "{{candidate_email}}", field: "email" },
        { text: "Candidato - Nome", tag: "{{candidate_name}}", field: "name" }
      ],
      SourcedProfile: [
        { text: "Candidato Sourced - E-mail", tag: "{{sourced_profile_email}}", field: "email" },
        { text: "Candidato Sourced - Nome", tag: "{{sourced_profile_name}}", field: "name" }
      ],
      User: [
        { text: "Usuário - E-mail", tag: "{{user_email}}", field: "email" },
        { text: "Usuário - Nome", tag: "{{user_name}}", field: "name" }
      ],
      Job: [
        { text: "Vaga - Título", tag: "{{job_title}}", field: "title" },
        { text: "Vaga - Descrição", tag: "{{job_description}}", field: "description" }
      ],
      Interview: [
        { text: "Entrevista - Data", tag: "{{interview_date}}", field: "formatted_date" },
        { text: "Entrevista - Prazo de Resposta", tag: "{{response_deadline}}", field: "formatted_deadline" }
      ]
    }
  end

  def self.replace_tags(content, entities)
    return "" unless content

    result = content.dup

    self.tag_array.each do |entity, tags|
      next unless entities[entity]

      tags.each do |tag_info|
        tag = tag_info[:tag]
        value = entities[entity].send(tag_info[:field]) if entities[entity].respond_to?(tag_info[:field])
        result.gsub!(tag, value.to_s) if value
      end
    end

    result
  end
end
