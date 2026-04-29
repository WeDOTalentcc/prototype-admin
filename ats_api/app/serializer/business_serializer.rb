# app/serializers/business_serializer.rb
class BusinessSerializer
  include JSONAPI::Serializer

  attributes :id,
             :name,
             :cnpj,
             :email,
             :phone,
             :website,
             :address,
             :industry,
             :size,
             :linkedin,
             :about,
             :is_active,
             :corporate_name,
             :job_amount,
             :mission,
             :vision,
             :culture_values,
             :soft_skills,
             :work_model,
             :growth_opportunities,
             :team_dynamics,
             :leader_style,
             :evp_highlights,
             :diversity_and_inclusion,
             :sustainability,
             :social_impact,
             :openness,
             :conscientiousness,
             :extraversion,
             :agreeableness,
             :stability,
             :created_at,
             :updated_at

  attribute :logo do |object|
    if object.logo.attached?
      prefix = ENV["API_URL"] || "http://localhost:8080"
      prefix + Rails.application.routes.url_helpers.rails_blob_url(object.logo, only_path: true)
    end
  end

  attribute :cover_image do |object|
    if object.cover_image.attached?
      prefix = ENV["API_URL"] || "http://localhost:8080"
      prefix + Rails.application.routes.url_helpers.rails_blob_url(object.cover_image, only_path: true)
    end
  end
end
