class EducationSerializer
  include JSONAPI::Serializer

  attributes :id, :study_here, :start_date, :end_date,
             :candidate_id, :institution_id, :study_area_id, :city_id, :account_id

  attribute :city do |object|
    next nil unless object.city_id
    {
      id: object.city_id,
      name: object.city&.name
    }
  end

  attribute :institution_name do |object|
    object.institution&.name
  end

  attribute :study_area_name do |object|
    object.study_area&.name
  end

  attribute :formation_type do |object|
    Education::FORMATION_TYPES[object.formation_type]
  end

  belongs_to :candidate
  belongs_to :institution
  belongs_to :study_area
  belongs_to :city
  belongs_to :account
end
