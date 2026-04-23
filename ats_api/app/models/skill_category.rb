class SkillCategory < ApplicationRecord
  include Searchable

  has_many :skills, dependent: :nullify

  validates :name, presence: true, uniqueness: true

  def search_data
    {
      id: id,
      name: name,
      description: description,
      icon: icon,
      color: color,
      is_deleted: is_deleted,
      skills_count: skills.where(is_deleted: false).count,
      created_at: created_at,
      updated_at: updated_at
    }
  end
end
