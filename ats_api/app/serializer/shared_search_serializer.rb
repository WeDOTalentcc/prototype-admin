# frozen_string_literal: true

class SharedSearchSerializer
  include JSONAPI::Serializer

  attributes(
    :id,
    :uid,
    :title,
    :description,
    :query,
    :token,
    :candidate_ids,
    :shared_with_emails,
    :viewed_count,
    :expires_at,
    :is_deleted,
    :created_at,
    :updated_at
  )

  attribute :candidate_count do |object|
    (object.candidate_ids || []).size
  end

  attribute :is_expired do |object|
    object.expired?
  end

  attribute :share_url do |object|
    prefix = ENV.fetch("APP_URL", "http://localhost:3000")
    "#{prefix}/shared-searches/#{object.token}"
  end

  belongs_to :user
  belongs_to :account
end
