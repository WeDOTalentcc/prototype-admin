class Education < ApplicationRecord
  include Searchable
  attr_accessor :institution_name, :study_area_name

  belongs_to :candidate
  belongs_to :account
  belongs_to :institution, optional: true
  belongs_to :study_area, optional: true
  belongs_to :city, optional: true

  before_validation :find_or_create_associations_by_name, on: [ :create, :update ]

  FORMATION_TYPES =  [
    "Ensino Médio",
    "Curso Técnico",
    "Curso Online",
    "Graduação",
    "Pós-Graduação",
    "Mestrado",
    "Doutorado",
    "Phd",
    "Outros"
  ]

  private

  def find_or_create_associations_by_name
    find_or_create_institution_by_name
    find_or_create_study_area_by_name
  end

  def find_or_create_institution_by_name
    return if institution_name.blank?

    institution = Institution.find_or_create_by(name: institution_name) do |i|
      i.account_id = self.account_id
      i.approved = false
    end
    self.institution = institution
  end

  def find_or_create_study_area_by_name
    return if study_area_name.blank?

    study_area = StudyArea.find_or_create_by(name: study_area_name) do |sa|
      sa.account_id = self.account_id
      sa.approved = false
    end

    self.study_area = study_area
    self.study_area_id = study_area.id
  end
end
