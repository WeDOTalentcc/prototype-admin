class SkillRelationship < ApplicationRecord
  include Searchable

  belongs_to :skill
  belongs_to :reference, polymorphic: true
  belongs_to :account
  belongs_to :user, optional: true

  validates :reference_type, :reference_id, presence: true
  validates :skill_id, uniqueness: {
    scope: [ :reference_type, :reference_id ],
    conditions: -> { where(is_deleted: false) },
    message: "Skill already exists for this reference"
  }
  EXPERIENCE_TIMES = [
    { id: 0, name: "Sem tempo de experiência" },
    { id: 1, name: "de 0 a 1 ano" },
    { id: 2, name: "de 1 a 2 anos" },
    { id: 3, name: "de 2 a 3 anos" },
    { id: 4, name: "de 3 a 4 anos" },
    { id: 5, name: "de 4 a 5 anos" },
    { id: 6, name: "de 5 a 6 anos" },
    { id: 7, name: "de 6 a 7 anos" },
    { id: 8, name: "mais de 7 anos" }
  ]
  SKILL_LEVELS = [
    { id: 0, name: "Nenhum conhecimento", description: "Eu não tenho experiência profissional nesta habilidade" },
    { id: 1, name: "Iniciante", description: "Eu não tenho experiência profissional nesta habilidade, mas gostaria de usar mais" },
    { id: 2, name: "Com experiência", description: "Eu usei esta habilidade profissional com alguma frequência" },
    { id: 3, name: "Avançado", description: "Eu usei essa habilidade profissionalmente pelo menos uma vez por semana" },
    { id: 4, name: "Especialista", description: "Eu tenho usado essa habilidade profissionalmente diariamente" }
  ]
end
