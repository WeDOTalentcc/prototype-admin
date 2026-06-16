class SearchArchetypeSerializer
  include JSONAPI::Serializer

  attributes :uid, :name, :emoji, :description, :query

  attributes :seniority, :min_experience_years, :industry, :location
  attributes :work_model, :contract_type

  attributes :languages, :skills, :tags

  attributes :local_filters, :global_filters

  attributes :is_default, :is_public
  attributes :usage_count, :last_used_at

  attributes :created_at, :updated_at

  attribute :seniority_label do |archetype|
    archetype.seniority&.humanize
  end

  attribute :work_model_label do |archetype|
    archetype.work_model&.humanize
  end

  attribute :contract_type_label do |archetype|
    archetype.contract_type&.humanize
  end

  belongs_to :user, serializer: UserSerializer, if: Proc.new { |archetype| archetype.user.present? }
  belongs_to :account
end
