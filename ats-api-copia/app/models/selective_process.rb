class SelectiveProcess < ApplicationRecord
  include Searchable
  belongs_to :job
  belongs_to :account
  validates :name, presence: true
  validates :status, presence: true

  enum status: {
    web_submission: 0,
    screening: 1,
    interview: 2,
    rejected: 3,
    hired: 4
  }

  def self.default_process
    [
      { name: "Inscrição Web", position: 0, status: statuses[:web_submission] },
      { name: "Triagem", position: 1, status: statuses[:screening] },
      { name: "Entrevista", position: 2, status: statuses[:interview] },
      { name: "Rejeitados", position: 3, status: statuses[:rejected] },
      { name: "Contratados", position: 4, status: statuses[:hired] }
    ]
  end

  def display_name
    name.presence || status.humanize
  end
end
