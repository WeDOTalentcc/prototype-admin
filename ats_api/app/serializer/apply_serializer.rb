# app/serializers/apply_serializer.rb
# frozen_string_literal: true

class ApplySerializer
  include JSONAPI::Serializer

  attributes(
    :id,
    :candidate_id,
    :job_id,
    :selective_process_id,
    :selective_process_name,
    :selective_process_status,
    :evaluation_candidate_status,
    :name,
    :email,
    :phone,
    :secondary_phone,
    :linkedin,
    :github,
    :avatar_url,
    :curriculum_pdf_url,
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
    :completed_register,
    :accept_terms,
    :is_deleted,
    :evaluation_candidate_scores,
    :evaluation_candidate_summaries,
    :cv_match,
    :total_score,
    :alerts,
    :color,
    :is_candidate_favorite,
    :created_at,
    :updated_at,
    :external_id,
    :sub_status,
    :is_screening_sent
  )

  attribute :meetings do |apply|
    apply.meeting_relationships.map do |mr|
      {
        id: mr.id,
        reference_type: mr.reference_type,
        reference_id: mr.reference_id,
        role: mr.role,
        meeting_id: mr.meeting_id,
        calendar_event_id: mr.calendar_event_id,
        join_url: mr.join_url,
        provider_text: mr.provider_text
      }
    end
  end

  def serializable_hash
    hash = super

    if @resource.respond_to?(:evaluation_candidate_scores)
      evaluation_scores = @resource.evaluation_candidate_scores
      evaluation_scores.each do |field_name, score|
        hash[:data][:attributes][field_name.to_sym] = score
      end
    end

    if @resource.respond_to?(:evaluation_summary)
      evaluation_summaries = @resource.evaluation_summary
      evaluation_summaries.each do |field_name, summary|
        summary_field_name = "#{field_name}_summary"
        hash[:data][:attributes][summary_field_name.to_sym] = summary
      end
    end

    hash
  end

  attribute :url do |object|
    "/user/jobs/" + object.job_id.to_s + "/applies/" + object.id.to_s
  end

  attribute :pin do |apply, params|
    next false unless params && params[:current_user]
    apply.pin_user_ids&.include?(params[:current_user].id) || false
  end

  attribute :confidential do |apply, params|
    next false unless params && params[:current_user]
    apply.confidential_user_ids&.include?(params[:current_user].id) || false
  end

  attribute :candidate_feedback do |object|
    object.get_candidate_feedback_type
  end
end
