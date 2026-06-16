
class DataFileSerializer
  include JSONAPI::Serializer

  attributes(
    :id,
    :user_id,
    :name,
    :reference_type,
    :reference_id,
    :file_type,
    :is_downloaded,
    :is_deleted,
    :account_id,
    :created_at,
    :updated_at
  )

  attribute :download_url do |data_file|
    if data_file.file.attached?
      prefix = ENV.fetch("API_URL", "http://localhost:8080")
      prefix + Rails.application.routes.url_helpers.rails_blob_url(data_file.file, only_path: true)
    end
  end
end
