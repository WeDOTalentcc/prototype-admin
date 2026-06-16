class ExperienceSerializer
  include JSONAPI::Serializer
  attributes(
    :id,
    :work_here,
    :start_date,
    :end_date,
    :candidate_id,
    :occupation_id,
    :company_id,
    :city_id,
    :description,
    :reasons_leaving,
    :contract_type,
    :parse_language,
    :is_deleted,
    :account_id,
    :user_id,
    :created_at,
    :updated_at
  )

  attribute :occupation_name do |object|
    object.occupation&.name
  end

  attribute :company_name do |object|
    object.company&.name
  end

  attribute :city do |object|
    next nil unless object.city_id
    {
      id: object.city_id,
      name: object.city&.name,
      state_uf: object.city&.state&.uf
    }
  end
end
