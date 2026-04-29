class Company < ApplicationRecord
  include Searchable

  enable_autocomplete :name

  has_one_attached :logo

  belongs_to :account
  belongs_to :user, optional: true

  validates :name, uniqueness: {
    scope: :account_id,
    conditions: -> { where(is_deleted: false) },
    message: "Empresa já cadastrada"
  }

  before_validation :downcase_name

  def downcase_name
    self.name = name.downcase if name.present?
  end
end
