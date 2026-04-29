# frozen_string_literal: true

class SourcedProfileSourcingSerializer
  include JSONAPI::Serializer

  attributes(
    :id,
    :sourced_profile_id,
    :sourcing_id,
    :account_id,
    :user_id,
    :analysis,
    :score,
    :search_source,
    :search_score,
    :is_deleted,
    :languages_attributes,
    :created_at,
    :updated_at
  )

  attribute :candidate_id do |object|
    object.sourced_profile&.candidate_id
  end

  attribute :uid do |object|
    object.sourced_profile&.uid
  end

  attribute :provider do |object|
    object.sourced_profile&.provider
  end

  attribute :external_id do |object|
    object.sourced_profile&.external_id
  end

  attribute :linkedin_slug do |object|
    object.sourced_profile&.linkedin_slug
  end

  attribute :linkedin_url do |object|
    object.sourced_profile&.linkedin_url
  end

  attribute :name do |object|
    object.sourced_profile&.name
  end

  attribute :first_name do |object|
    object.sourced_profile&.first_name
  end

  attribute :last_name do |object|
    object.sourced_profile&.last_name
  end

  attribute :email do |object|
    object.sourced_profile&.email
  end

  attribute :phone do |object|
    object.sourced_profile&.phone
  end

  attribute :title do |object|
    object.sourced_profile&.title
  end

  attribute :picture_url do |object|
    object.sourced_profile&.picture_url
  end

  attribute :avatar_url do |object|
    object.sourced_profile&.picture_url
  end

  attribute :location do |object|
    object.sourced_profile&.location
  end

  attribute :city do |object|
    object.sourced_profile&.city
  end

  attribute :state do |object|
    object.sourced_profile&.state
  end

  attribute :current_company do |object|
    object.sourced_profile&.current_company
  end

  attribute :current_title do |object|
    object.sourced_profile&.current_title
  end

  attribute :role_name do |object|
    object.sourced_profile&.role_name
  end

  attribute :total_experience_years do |object|
    object.sourced_profile&.total_experience_years
  end

  attribute :estimated_age do |object|
    object.sourced_profile&.estimated_age
  end

  attribute :status do |object|
    object.sourced_profile&.status
  end

  attribute :sourcing_score do |object|
    object.score
  end

  attribute :similarity_score do |object|
    object.similarity_score
  end

  attribute :rating do |object|
    object.sourced_profile&.rating
  end

  attribute :candidate_feedback do |object|
    object.get_candidate_feedback_type
  end

  attribute :likes do |object|
    object.candidate_feedbacks.active.likes.map do |feedback|
      {
        id: feedback.id,
        user_id: feedback.user_id,
        created_at: feedback.created_at
      }
    end
  end

  attribute :dislikes do |object|
    object.candidate_feedbacks.active.dislikes.map do |feedback|
      {
        id: feedback.id,
        user_id: feedback.user_id,
        reason: feedback.reason,
        created_at: feedback.created_at
      }
    end
  end

  attribute :remote_work do |object|
    object.sourced_profile&.remote_work
  end

  attribute :mobility do |object|
    object.sourced_profile&.mobility
  end

  attribute :has_emails do |object|
    object.sourced_profile&.has_emails
  end

  attribute :has_phone_numbers do |object|
    object.sourced_profile&.has_phone_numbers
  end

  attribute :internal_notes do |object|
    object.sourced_profile&.internal_notes
  end

  attribute :tags do |object|
    object.sourced_profile&.tags
  end

  attribute :cpf do |object|
    object.sourced_profile&.cpf
  end

  attribute :date_birth do |object|
    object.sourced_profile&.date_birth
  end

  attribute :gender do |object|
    object.sourced_profile&.gender
  end

  attribute :marital_status do |object|
    object.sourced_profile&.marital_status
  end

  attribute :summary do |object|
    object.sourced_profile&.summary
  end

  attribute :country do |object|
    object.sourced_profile&.country
  end

  attribute :address do |object|
    object.sourced_profile&.address
  end

  attribute :zip_code do |object|
    object.sourced_profile&.zip_code
  end

  attribute :position_level do |object|
    object.sourced_profile&.position_level
  end

  attribute :currency do |object|
    object.sourced_profile&.currency
  end

  attribute :clt_expectation do |object|
    object.sourced_profile&.clt_expectation
  end

  attribute :pj_expectation do |object|
    object.sourced_profile&.pj_expectation
  end

  attribute :freelance_expectation do |object|
    object.sourced_profile&.freelance_expectation
  end

  attribute :is_decision_maker do |object|
    object.sourced_profile&.is_decision_maker
  end

  attribute :is_top_universities do |object|
    object.sourced_profile&.is_top_universities
  end

  attribute :followers_count do |object|
    object.sourced_profile&.followers_count
  end

  attribute :connections_count do |object|
    object.sourced_profile&.connections_count
  end

  attribute :emails do |object|
    object.sourced_profile&.emails
  end

  attribute :phones do |object|
    object.sourced_profile&.phones
  end

  attribute :emails_enriched_at do |object|
    object.sourced_profile&.emails_enriched_at
  end

  attribute :phones_enriched_at do |object|
    object.sourced_profile&.phones_enriched_at
  end

  attribute :last_viewed_at do |object|
    object.sourced_profile&.last_viewed_at
  end

  attribute :profile_created_at do |object|
    object.sourced_profile&.created_at
  end

  attribute :profile_updated_at do |object|
    object.sourced_profile&.updated_at
  end

  attribute :full_name do |object|
    object.sourced_profile&.full_name
  end

  attribute :current_company_name do |object|
    object.sourced_profile&.current_company_name
  end

  attribute :current_role do |object|
    object.sourced_profile&.current_role
  end

  attribute :age_range do |object|
    object.sourced_profile&.calculate_age_range
  end

  attribute :salary_range do |object|
    object.sourced_profile&.calculate_salary_range
  end

  attribute :expertise do |object|
    object.sourced_profile&.expertise || []
  end

  attribute :skills do |object|
    profile = object.sourced_profile
    next [] unless profile
    (profile.skills_data || []).map { |skill| skill.is_a?(Hash) ? skill["name"] : skill }.compact
  end

  attribute :languages do |object|
    object.sourced_profile&.languages_data || []
  end

  attribute :behavioral_skills_list do |object|
    object.sourced_profile&.behavioral_skills_list || []
  end

  attribute :imported do |object|
    object.sourced_profile&.imported?
  end

  attribute :overall_summary do |object|
    object.sourced_profile&.overall_summary
  end

  attribute :experiences do |object|
    profile = object.sourced_profile
    next [] unless profile
    (profile.experiences_data || []).map do |experience|
      company_info = experience["company_info"] || {}
      company_roles = experience["company_roles"] || []

      company_roles.map do |role|
        {
          company: role["company"] || company_info["name"],
          role: role["title"],
          start_date: role["start_date"],
          end_date: role["end_date"],
          is_current: role["is_current_experience"] || false,
          location: role["location"],
          duration_years: role["duration_years"],
          summary: role["experience_summary"],
          company_info: {
            name: company_info["name"],
            domain: company_info["domain"],
            website: company_info["website"],
            linkedin_url: company_info["linkedin_url"],
            num_employees: company_info["num_employees"],
            num_employees_range: company_info["num_employees_range"],
            is_startup: company_info["is_startup"],
            founded_in: company_info["founded_in"],
            description: company_info["description"]
          }
        }
      end
    end.flatten
  end

  attribute :educations do |object|
    profile = object.sourced_profile
    next [] unless profile
    (profile.educations_data || []).map do |education|
      {
        institution: education["campus"],
        degree: education["major"],
        start_date: education["start_date"],
        end_date: education["end_date"],
        description: education["specialization"],
        university_linkedin_url: education["university_linkedin_url"]
      }
    end
  end

  attribute :certifications do |object|
    profile = object.sourced_profile
    next [] unless profile
    (profile.certifications_data || []).map do |certification|
      {
        title: certification["title"],
        name: certification["name"],
        issuer: certification["issuer"],
        date: certification["date"],
        url: certification["url"]
      }
    end
  end

  attribute :awards do |object|
    object.sourced_profile&.awards_data || []
  end

  attribute :linkedin do |object|
    object.sourced_profile&.linkedin
  end

  attribute :github do |object|
    object.sourced_profile&.github
  end

  attribute :portfolio do |object|
    object.sourced_profile&.portfolio
  end

  attribute :secondary_email do |object|
    object.sourced_profile&.secondary_email
  end

  attribute :mobile_phone do |object|
    object.sourced_profile&.mobile_phone
  end

  attribute :secondary_phone do |object|
    object.sourced_profile&.secondary_phone
  end

  attribute :street do |object|
    object.sourced_profile&.street
  end

  attribute :number do |object|
    object.sourced_profile&.number
  end

  attribute :district do |object|
    object.sourced_profile&.district
  end

  attribute :complement do |object|
    object.sourced_profile&.complement
  end

  attribute :zip do |object|
    object.sourced_profile&.zip
  end

  attribute :nationality do |object|
    object.sourced_profile&.nationality
  end

  attribute :self_introduction do |object|
    object.sourced_profile&.self_introduction
  end

  attribute :curriculum_text do |object|
    object.sourced_profile&.curriculum_text
  end

  attribute :current_salary do |object|
    object.sourced_profile&.current_salary
  end

  attribute :desired_salary do |object|
    object.sourced_profile&.desired_salary
  end

  attribute :interests do |object|
    object.sourced_profile&.interests
  end

  attribute :comments do |object|
    object.sourced_profile&.comments
  end

  attribute :source do |object|
    object.sourced_profile&.source
  end

  attribute :curriculum_pdf_url do |object|
    object.sourced_profile&.curriculum_pdf_url
  end

  attribute :completed_register do |object|
    object.sourced_profile&.completed_register
  end

  attribute :accept_terms do |object|
    object.sourced_profile&.accept_terms
  end

  attribute :profile_origin do |object|
    profile = object.sourced_profile
    next nil unless profile
    profile.provider == "local" ? "local" : "global"
  end

  attribute :ai_analysis do |object|
    object.analysis
  end

  attribute :ai_analyzed_at do |object|
    object.ai_metadata&.[]("ran_at")
  end

  attribute :ai_metadata do |object|
    object.ai_metadata
  end

  attribute :pin_user_ids do |object|
    object.sourced_profile&.pin_user_ids || []
  end

  attribute :confidential_user_ids do |object|
    object.sourced_profile&.confidential_user_ids || []
  end

  attribute :middle_name do |object|
    object.sourced_profile&.middle_name
  end

  attribute :linkedin_slug do |object|
    object.sourced_profile&.linkedin_slug
  end

  belongs_to :sourcing
  belongs_to :candidate, if: proc { |object| object.sourced_profile&.candidate_id.present? }
end
