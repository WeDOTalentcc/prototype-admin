class List < ApplicationRecord
  include Searchable

  enable_autocomplete :name

  belongs_to :user
  belongs_to :account
  has_many :list_relationships, dependent: :destroy

  validates :name, presence: true
  validates :user_id, presence: true
  validates :account_id, presence: true

  after_commit :reindex_associations, on: [ :update ]

  def search_data
    {
      **attributes.deep_symbolize_keys,
      user_name: user&.name || "",
      is_public_text: is_public ? "Yes" : "No",
      candidates_count: candidates_count,
      jobs_count: jobs_count,
      applies_count: applies_count,
      selective_processes_count: selective_processes_count
    }
  end

  def count_relationships
    relationships = list_relationships.where(is_deleted: false)

    candidates_count = relationships.where(reference_type: "Candidate").count || 0
    candidates_count = candidates_count + relationships.where(reference_type: "SourcedProfileSourcing").count || 0

    counts = {
      candidates_count: candidates_count,
      jobs_count: relationships.where(reference_type: "Job").count,
      applies_count: relationships.where(reference_type: "Apply").count,
      selective_processes_count: relationships.where(reference_type: "SelectiveProcess").count
    }

    update_columns(counts)
  end

  def self.count_all_relationships
    find_each(batch_size: 100, &:count_relationships)
  end

  def self.include_base
    select("lists.*, users.name as user_name")
      .joins(:user)
  end

  private

  def reindex_associations
    list_relationships.find_each(&:reindex_entity)
  end
end
