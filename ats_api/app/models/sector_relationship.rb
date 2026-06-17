# frozen_string_literal: true

class SectorRelationship < ApplicationRecord
  include Searchable

  belongs_to :sector
  belongs_to :account
  belongs_to :reference, polymorphic: true

  validates :sector_id, presence: true
  validates :sector_name, presence: true
  validates :reference_type, presence: true
  validates :reference_id, presence: true
  validates :account_id, presence: true

  validates :sector_id, uniqueness: {
    scope: [ :reference_type, :reference_id, :account_id ],
    conditions: -> { where(is_deleted: false) },
    message: "já possui relacionamento com esta referência"
  }

  before_validation :set_sector_name, if: -> { sector.present? && (sector_name.blank? || sector_id_changed?) }

  private

  def set_sector_name
    self.sector_name = sector.name
  end
end
