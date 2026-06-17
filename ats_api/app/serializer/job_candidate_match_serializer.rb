class JobCandidateMatchSerializer
  include JSONAPI::Serializer
  set_type :candidate_match

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
    :nationality,
    :marital_status,
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
    :avatar_url,
    :curriculum_pdf_url,
    :completed_register,
    :accept_terms,
    :created_at,
    :updated_at,
    :score,
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
end
