class CompanySerializer
  include JSONAPI::Serializer

  attributes :id, :name, :linkedin_url, :is_deleted, :account_id, :user_id, :created_at, :updated_at

  attribute :logo do |object|
    if object.logo.attached?
      prefix = ENV["API_URL"] || "http://localhost:8080"
      prefix + Rails.application.routes.url_helpers.rails_blob_url(object.logo, only_path: true)
    end
  end
end
