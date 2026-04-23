# frozen_string_literal: true

class EntityColumnSerializer
  include JSONAPI::Serializer

  attributes :id, :entity, :label, :columns_view, :user_id, :requested,
             :shortlist_id, :job_id, :is_main, :is_views, :is_public,
             :business_ids, :created_at, :updated_at

  attribute :available_columns do |object|
    object.available_columns
  end

  attribute :all_columns do |object|
    object.all_columns
  end

  belongs_to :user, serializer: UserSerializer, if: proc { |record| record.user.present? }
  belongs_to :shortlist, if: proc { |record| record.shortlist.present? }
  belongs_to :job, if: proc { |record| record.job.present? }
end
