class CandidateSerializer
  include JSONAPI::Serializer

  attributes(
    :id,
    :uid,
    :name,
    :email,
    :secondary_email,
    :mobile_phone,
    :phone,
    :secondary_phone,
    :linkedin,
    :github,
    :portfolio,
    :current_company,
    :role_name,
    :position_level,
    :self_introduction,
    :curriculum_text,
    :date_birth,
    :gender,
    :gender_name,
    :nationality,
    :marital_status,
    :marital_status_name,
    :cpf,
    :street,
    :number,
    :district,
    :zip,
    :city,
    :state,
    :country,
    :complement,
    :clt_expectation,
    :pj_expectation,
    :freelance_expectation,
    :current_salary,
    :desired_salary,
    :currency,
    :remote_work,
    :mobility,
    :interests,
    :comments,
    :source,
    :curriculum_pdf_url,
    :completed_register,
    :accept_terms,
    # :data_raw,
    # :external_profile_data,
    :external_id,
    # :external_provider,
    :created_at,
    :updated_at
  )

  attribute :applies, if: proc { |_record, params|
    params[:includes]&.include?("applies")
  } do |object, _params|
    object.applies.where(is_deleted: [ false, nil ]).map do |apply|
      {
        id: apply.id,
        job_id: apply.job_id,
        job_title: apply.job&.title,
        selective_process_id: apply.selective_process_id,
        is_deleted: apply.is_deleted,
        created_at: apply.created_at,
        updated_at: apply.updated_at
      }
    end
  end

  attribute :url do |object|
    "/user/candidates/" + object.id.to_s
  end

  attribute :gender_name do |object|
    Candidate::GENDER.find { |g| g[:id] == object.gender }&.dig(:name)
  end

  attribute :marital_status_name do |object|
    Candidate::MARITAL_STATUS.find { |m| m[:id] == object.marital_status }&.dig(:name)
  end

  attribute :avatar_url do |object|
    object.avatar_public_url
  end

  attribute :pin do |candidate, params|
    next false unless params[:current_user]
    candidate.pin_user_ids&.include?(params[:current_user].id) || false
  end

  attribute :confidential do |candidate, params|
    next false unless params[:current_user]
    candidate.confidential_user_ids&.include?(params[:current_user].id) || false
  end

  attribute :favorite do |candidate, params|
    next false unless params[:current_user]
    candidate.favorite_user_ids&.include?(params[:current_user].id) || false
  end
end
