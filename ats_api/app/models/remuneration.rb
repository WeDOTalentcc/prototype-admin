class Remuneration < ApplicationRecord
  include Searchable

  belongs_to :account, optional: false
  belongs_to :user, optional: true

  validates :name, presence: true
  validates :name, uniqueness: { scope: [ :account_id, :description, :entity ], message: "Remuneration name must be unique for the account" }

  REMUNERATION_TYPES_JOB = [
    { id: 1, name: "Salário (De)" },
    { id: 2, name: "Salário (Até)" },
    { id: 3, name: "Comissão (De)" },
    { id: 4, name: "Comissão (Até)" },
    { id: 5, name: "Pacote de Bônus (De)" },
    { id: 6, name: "Pacote de Bônus (Até)" },
    { id: 7, name: "Opções de Ações (De)" },
    { id: 8, name: "Opções de Ações (Até)" },
    { id: 9, name: "Plano de Aposentadoria (De)" },
    { id: 10, name: "Plano de Aposentadoria (Até)" },
    { id: 11, name: "Bônus de Contratação (De)" },
    { id: 12, name: "Bônus de Contratação (Até)" },
    { id: 13, name: "Bônus de Retenção (De)" },
    { id: 14, name: "Bônus de Retenção (Até)" },
    { id: 15, name: "Bônus de Meta (De)" },
    { id: 16, name: "Bônus de Meta (Até)" },
    { id: 17, name: "Bônus de Entrada (De)" },
    { id: 18, name: "Bônus de Entrada (Até)" },
    { id: 19, name: "Outros" }
  ]

  REMUNERATION_TYPES_CANDIDATE = [
    { id: 1, name: "Salário" },
    { id: 2, name: "Comissão" },
    { id: 3, name: "Pacote de Bônus" },
    { id: 4, name: "Opções de Ações" },
    { id: 5, name: "Plano de Aposentadoria" },
    { id: 6, name: "Bônus de Contratação" },
    { id: 7, name: "Bônus de Retenção" },
    { id: 8, name: "Bônus de Meta" },
    { id: 9, name: "Bônus de Entrada" },
    { id: 10, name: "Outros" }
  ]

  def self.create_default_remunerations(account_id, user_id = nil)
    REMUNERATION_TYPES_JOB.each do |remuneration_type|
      Remuneration.find_or_create_by!(
        name: remuneration_type[:name],
        account_id: account_id,
        entity: "Job"
      )
    end
    REMUNERATION_TYPES_CANDIDATE.each do |remuneration_type|
      Remuneration.find_or_create_by!(
        name: remuneration_type[:name],
        account_id: account_id,
        entity: "Candidate"
      )
    end
  end
end
