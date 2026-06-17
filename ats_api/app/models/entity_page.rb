# frozen_string_literal: true

class EntityPage < ApplicationRecord
  MAX_PAGES_PER_USER = 100
  MAX_PAGES_BYTESIZE = 512.kilobytes
  STRIPPED_KEYS = %w[data].freeze

  belongs_to :user
  belongs_to :account, optional: true

  validates :entity, presence: true
  validates :type_view, presence: true
  validates :entity, uniqueness: { scope: %i[user_id type_view link custom_entity] }
  validate :pages_size_limit
  validate :max_pages_per_user, on: :create

  before_validation :strip_heavy_keys_from_pages

  scope :for_user, ->(user_id) { where(user_id: user_id).order(id: :asc) }

  def self.upsert_page(user, params)
    record = find_or_initialize_by(
      user_id: user.id,
      entity: params[:entity],
      type_view: params[:type_view],
      link: params[:link],
      custom_entity: params[:custom_entity]
    )

    record.assign_attributes(
      account_id: user.account_id,
      job_id: params[:job_id],
      label: params[:label],
      icon: params[:icon],
      pages: params[:pages]
    )

    record.save!
    record
  end

  private

  def pages_size_limit
    return if pages.blank?

    errors.add(:pages, "is too large (max 512KB)") if pages.to_json.bytesize > MAX_PAGES_BYTESIZE
  end

  def max_pages_per_user
    return if EntityPage.where(user_id: user_id).count < MAX_PAGES_PER_USER

    errors.add(:base, "maximum entity pages reached")
  end

  def strip_heavy_keys_from_pages
    return if pages.blank?

    self.pages = pages.except(*STRIPPED_KEYS)
  end
end
