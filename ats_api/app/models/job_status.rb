class JobStatus < ApplicationRecord
  include Searchable

  enable_autocomplete :name

  validates :name, presence: true, uniqueness: { case_sensitive: false }
  validates :color, presence: true

  has_many :jobs, dependent: :nullify

  DEFAULT_STATUSES = [
    { name: "Ativa",                 color: "#A8D5B7", is_main: true  },
    { name: "Aprovada",              color: "#B8E0D2", is_main: false },
    { name: "Aguardando aprovação",  color: "#F5E6B3", is_main: false },
    { name: "Reaberta",              color: "#F5D6A8", is_main: false },
    { name: "Paralisada",            color: "#D5BFA8", is_main: true  },
    { name: "Interna",               color: "#C5D9ED", is_main: false },
    { name: "Fechada (preenchida)",  color: "#B8C5D0", is_main: false },
    { name: "Fechada (expirada)",    color: "#E8B8B8", is_main: false },
    { name: "Cancelada",             color: "#E5C5C5", is_main: true  },
    { name: "Rascunho",              color: "#E8E4E0", is_main: true },
    { name: "Arquivada",             color: "#E5E7EB", is_main: false },
    { name: "Concluída",             color: "#A8CED5", is_main: true  }
  ].freeze


  def self.create_default_statuses
    DEFAULT_STATUSES.each do |status_attributes|
      status = JobStatus.find_by(name: status_attributes[:name])

      if status.nil?
        status = JobStatus.new(name: status_attributes[:name])
        status.color = status_attributes[:color]
        status.is_main = status_attributes[:is_main]
        status.save!
      end
    end
  end
end
