class TemplateCategory < ApplicationRecord
  # ApplicationRecord already includes AccountScopable

  belongs_to :parent, class_name: "TemplateCategory", optional: true
  has_many :children, class_name: "TemplateCategory", foreign_key: :parent_id

  validates :name, presence: true
end
