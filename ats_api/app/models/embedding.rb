# frozen_string_literal: true

class Embedding < ApplicationRecord
  belongs_to :reference, polymorphic: true

  has_neighbors :embedding if Rails.env.development? || Rails.env.production?

  validates :reference_type, presence: true
  validates :reference_id, presence: true
  validates :embedding, presence: true
  validates :reference_id, uniqueness: { scope: :reference_type }

  scope :for_candidates, -> { where(reference_type: "Candidate") }
  scope :for_jobs, -> { where(reference_type: "Job") }

  def self.nearest_for_type(reference_type, query_vector, limit: 100, distance: "cosine")
    where(reference_type: reference_type)
      .nearest_neighbors(:embedding, query_vector, distance: distance)
      .limit(limit)
  end
end
