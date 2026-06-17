# frozen_string_literal: true

class SourcedProfileSerializer
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
    :created_at,
    :updated_at
  )

  attribute :url do |object|
    object.url
  end

  attribute :gender_name do |object|
    object.gender_name
  end

  attribute :marital_status_name do |object|
    object.marital_status_name
  end

  attribute :avatar_url do |object|
    object.avatar_url
  end

  attribute :pin do |_profile, params|
    next false unless params[:current_user]
    false
  end

  attribute :confidential do |_profile, params|
    next false unless params[:current_user]
    false
  end

  attribute :profile_origin do |profile|
    profile.provider == "local" ? "local" : "global"
  end

  attribute :experiences do |profile|
    (profile.experiences_data || []).flat_map do |experience|
      company_info = experience["company_info"] || {}
      company_roles = experience["company_roles"] || []

      company_roles.map do |role|
        {
          id: nil,
          company: role["company"] || company_info["name"],
          role: role["title"],
          start_date: role["start_date"],
          end_date: role["end_date"],
          is_current: role["is_current_experience"] || false,
          location: role["location"],
          description: role["experience_summary"]
        }
      end
    end
  rescue
    []
  end

  attribute :educations do |profile|
    (profile.educations_data || []).map do |education|
      {
        id: nil,
        institution: education["campus"],
        education_level: education["major"],
        study_area: education["specialization"] || education["major"],
        start_date: education["start_date"],
        end_date: education["end_date"]
      }
    end
  rescue
    []
  end

  attribute :skills do |profile|
    next [] unless profile.skills_data || profile.expertise

    skills_from_data = (profile.skills_data || []).map do |skill|
      skill.is_a?(Hash) ? skill["name"] : skill
    end.compact

    skills_from_expertise = profile.expertise || []

    (skills_from_data + skills_from_expertise).uniq.map do |skill_name|
      { id: nil, name: skill_name }
    end
  rescue
    []
  end

  attribute :behavioral_skills_list do |profile|
    profile.behavioral_skills_list || []
  end

  attribute :languages do |profile|
    (profile.languages_data || []).map do |language|
      {
        id: nil,
        name: language.is_a?(Hash) ? language["language"] : language,
        level: language.is_a?(Hash) ? language["proficiency"] : nil
      }
    end
  rescue
    []
  end

  attribute :certifications do |profile|
    (profile.certifications_data || []).map do |certification|
      {
        title: certification["title"],
        name: certification["name"],
        issuer: certification["issuer"],
        date: certification["date"],
        url: certification["url"]
      }
    end
  rescue
    []
  end

  attribute :awards do |profile|
    profile.awards_data || []
  rescue
    []
  end

  belongs_to :sourcing
  belongs_to :candidate, if: proc { |profile| profile.candidate_id.present? }
end
