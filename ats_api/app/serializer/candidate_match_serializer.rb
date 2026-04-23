# frozen_string_literal: true

class CandidateMatchSerializer
  include JSONAPI::Serializer
  set_type :candidate_match

  attributes(
    :id,
    :uid,
    :name,
    :linkedin,
    :github,
    :portfolio,
    :current_company,
    :role_name,
    :position_level,
    :self_introduction,
    :city,
    :state,
    :country,
    :remote_work,
    :mobility,
    :interests,
    :source,
    :completed_register,
    :created_at,
    :updated_at,
    :score
  )

  attribute :avatar_url do |object|
    object.avatar_public_url
  end

  attribute :curriculum_pdf_url do |object|
    object.curriculum_pdf_url
  end

  attribute :gender_name do |object|
    Candidate::GENDER.find { |g| g[:id] == object.gender }&.dig(:name)
  end

  attribute :marital_status_name do |object|
    Candidate::MARITAL_STATUS.find { |m| m[:id] == object.marital_status }&.dig(:name)
  end

  attribute :url do |object|
    "/user/candidates/#{object.id}"
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

  attribute :applies, if: proc { |_record, params|
    params[:includes]&.include?("applies")
  } do |object, _params|
    object.applies.includes(:job).where(is_deleted: [false, nil]).map do |apply|
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
