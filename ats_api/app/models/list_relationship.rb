class ListRelationship < ApplicationRecord
  include Searchable

  belongs_to :reference, polymorphic: true
  belongs_to :list
  belongs_to :account

  validates :reference_id, presence: true
  validates :reference_type, presence: true
  validates :list_id, presence: true
  validates :account_id, presence: true
  validate :validate_existence, on: :create

  after_commit :reindex_entity
  after_destroy :update_list_counts
  after_save :update_list_counts

  scope :active, -> { where(is_deleted: false) }
  scope :by_reference_type, ->(type) { where(reference_type: type) }

  def search_data
    class_name = reference_type.underscore

    search_data_default
      .merge(reference_search_data.except(*search_data_default.keys))
      .merge({
        "#{class_name}_updated_at": reference&.updated_at,
        "#{class_name}_created_at": reference&.created_at
      })
  end

  def search_data_default
    {
      id: id,
      list_id: list_id,
      reference_type: reference_type,
      reference_id: reference_id,
      position: position,
      general_comments: general_comments,
      score: score,
      is_deleted: is_deleted,
      account_id: account_id
    }
  end

  def reference_search_data
    data = reference_type
      &.constantize
      &.find_by(id: reference_id)
      &.try(:search_data)
      &.transform_keys(&:to_sym) || {}

    data[:is_deleted] = is_deleted if data.present?

    data
  rescue StandardError => e
    Rails.logger.error("Error getting reference search data: #{e.message}")
    {}
  end

  def reindex_entity
    return unless reference

    reference.reindex
  rescue StandardError => e
    Rails.logger.error("Error reindexing entity: #{e.message}")
  end

  def self.include_base
    select("list_relationships.*")
  end

  private

  def validate_existence
    return unless ListRelationship.exists?(
      reference_id: reference_id,
      reference_type: reference_type,
      list_id: list_id,
      is_deleted: false
    )

    errors.add(:base, "This relationship already exists in the list")
  end

  def update_list_counts
    list.count_relationships if list.present?
  end
end
