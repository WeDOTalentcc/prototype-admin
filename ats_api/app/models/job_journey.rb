class JobJourney < ApplicationRecord
  include Searchable

  belongs_to :account
  belongs_to :job, optional: true

  validates :name, presence: true
  validates :position, presence: true, numericality: { only_integer: true, greater_than_or_equal_to: 0 }

  scope :active, -> { where(active: true) }
  scope :required, -> { where(required: true) }
  scope :ordered, -> { order(position: :asc) }

  def search_data
    {
      name: name,
      description: description,
      position: position,
      active: active,
      required: required,
      account_id: account_id,
      job_id: job_id
    }
  end

  def self.create_default_journeys_for_account(account)
    default_journeys = [
      { position: 1, name: "Informações Básicas", description: "Título, Confidencialidade, Área", required: true, active: true },
      { position: 2, name: "Remuneração e Benefícios", description: "Salário, Bônus, Benefícios, Benchmarking", required: false, active: true },
      { position: 3, name: "Estrutura Organizacional", description: "Gestor, Linha de reporte, Equipe", required: true, active: true },
      { position: 4, name: "Requisitos Técnicos", description: "Linguagens, Frameworks, Ferramentas", required: true, active: true },
      { position: 5, name: "Competências Comportamentais", description: "Soft skills necessárias", required: false, active: true },
      { position: 6, name: "Estratégia de Busca (Sourcing)", description: "Setores, Segmentos, Experiências", required: true, active: true },
      { position: 7, name: "Idiomas e Senioridade", description: "Idiomas, Nível, Anos de experiência", required: false, active: true },
      { position: 8, name: "Localização e Regime", description: "Local, Remoto/Híbrido, Modelo contrato", required: true, active: true },
      { position: 9, name: "Etapas de Entrevistas", description: "Quem entrevista, Formato, Datas", required: true, active: true },
      { position: 10, name: "Perguntas de Screening", description: "Perguntas técnicas e comportamentais", required: true, active: true },
      { position: 11, name: "Cronograma", description: "Prazo total, Data de entrega shortlist", required: false, active: true },
      { position: 12, name: "Governança do Processo", description: "Autonomia da IA, Feedbacks, Validações", required: true, active: true },
      { position: 13, name: "Templates de Comunicação", description: "Mensagens WhatsApp, E-mails", required: false, active: true },
      { position: 14, name: "Job Description Completa", description: "Descrição final, Análise de viés", required: true, active: true },
      { position: 15, name: "Publicação", description: "Canal de publicação, Data de publicação", required: true, active: true }
    ]

    default_journeys.each do |journey_data|
      JobJourney.find_or_create_by!(
        position: journey_data[:position],
        account_id: account.id
      ) do |journey|
        journey.assign_attributes(journey_data)
      end
    end

    Rails.logger.info "✅ Criadas #{default_journeys.size} jornadas padrão para a conta #{account.name} (tenant: #{account.tenant})"
  end
end
