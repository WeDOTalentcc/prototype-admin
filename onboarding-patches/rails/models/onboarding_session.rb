# frozen_string_literal: true

class OnboardingSession < ApplicationRecord
  belongs_to :user
  belongs_to :account
  has_many :onboarding_messages, dependent: :destroy

  PHASES = %w[
    pending welcome whatsapp_intro whatsapp_learn awaiting_login
    first_login platform_tour action_choice job_creation complete
  ].freeze

  validates :phase, inclusion: { in: PHASES }

  scope :active, -> { where.not(phase: "complete") }
  scope :for_user, ->(uid) { where(user_id: uid) }
  scope :recent, -> { order(created_at: :desc) }

  def complete?
    phase == "complete"
  end

  def advance_to!(new_phase)
    raise ArgumentError, "Invalid phase: #{new_phase}" unless PHASES.include?(new_phase)

    update!(phase: new_phase)
  end

  def mark_step_completed!(step_id)
    steps = progress_steps || []
    return if steps.include?(step_id)

    update!(progress_steps: steps + [step_id])
  end

  def duration_seconds
    return nil unless completed_at

    (completed_at - created_at).to_i
  end
end
