# frozen_string_literal: true

class EntityColumn < ApplicationRecord
  include Searchable

  belongs_to :user, optional: true
  belongs_to :account
  belongs_to :shortlist, optional: true
  belongs_to :job, optional: true

  validates :entity, presence: true
  validates :requested, presence: true
  validates :label, presence: true, if: :is_views?
  validates :entity, format: {
    with: /\A[a-z_]+\z/,
    message: "must contain only lowercase letters and underscores"
  }


  before_validation :normalize_entity
  before_save :merge_shortlist_columns, if: -> { should_merge_shortlist_columns? }

  def search_data
    {
      id: id,
      entity: entity,
      user_id: user_id,
      requested: requested,
      shortlist_id: shortlist_id,
      is_main: is_main,
      label: label,
      is_views: is_views,
      is_public: is_public,
      created_at: created_at,
      account_id: account_id,
      is_deleted: is_deleted
    }
  end

  def self.find_or_create_by_entity(entity_string, user_id, requested: "default", shortlist_id: nil, job_id: nil, account_id:)
    entity_name = entity_string.singularize.downcase

    existing_column = find_existing_column(entity_name, user_id, requested, shortlist_id, job_id)
    return existing_column if existing_column

    create_default_column(entity_name, user_id, requested, shortlist_id, job_id, account_id)
  end

  def available_columns
    return [] unless EntityColumnService::Structure.supported_entity?(entity)

    EntityColumnService::Structure.entity_columns(
      entity,
      requested,
      only_active: true,
      entity_id: job_id
    )
  end

  def all_columns
    return [] unless EntityColumnService::Structure.supported_entity?(entity)

    EntityColumnService::Structure.entity_columns(
      entity,
      requested,
      only_active: false,
      entity_id: job_id
    )
  end

  private

  def normalize_entity
    self.entity = entity&.singularize&.downcase
  end

  def should_merge_shortlist_columns?
    shortlist_requesters.include?(requested) && persisted?
  end

  def shortlist_requesters
    %w[shortlists candidate_shortlists mapped]
  end

  def merge_shortlist_columns
    Report.where(is_deleted: false, is_main: true, account_id: account_id).find_each do |report|
      report_column = build_report_column(report)
      next if column_already_exists?(report_column)

      columns_view << report_column
    end
  end

  def build_report_column(report)
    {
      value: report.name.downcase.split(" ").join(""),
      text: report.name.capitalize,
      sortable: true,
      type: "ShortlistText",
      filter: "text"
    }.with_indifferent_access
  end

  def column_already_exists?(new_column)
    normalized_columns = columns_view.map { |column| column.sort_by(&:first).to_h }
    normalized_columns.include?(new_column.sort_by(&:first).to_h)
  end

  def self.find_existing_column(entity_name, user_id, requested, shortlist_id, job_id)
    query = {
      entity: entity_name,
      user_id: user_id,
      requested: requested,
      is_views: false
    }

    query[:shortlist_id] = shortlist_id if shortlist_id
    query[:job_id] = job_id if job_id

    where(query).first
  end

  def self.create_default_column(entity_name, user_id, requested, shortlist_id, job_id, account_id)
    columns = EntityColumnService::Structure.entity_columns(
      entity_name,
      requested,
      only_active: true,
      entity_id: job_id
    )

    create!(
      entity: entity_name,
      user_id: user_id,
      columns_view: columns,
      requested: requested,
      shortlist_id: shortlist_id,
      job_id: job_id,
      is_main: true,
      is_views: false,
      account_id: account_id
    )
  end
end
