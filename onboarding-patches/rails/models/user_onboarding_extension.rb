# frozen_string_literal: true

# Patch to add to User model (app/models/user.rb)
# Add these lines inside the User class:

# == ONBOARDING EXTENSIONS ==
# Add to User model after existing associations:
#
#   has_many :magic_links, dependent: :destroy
#   has_many :onboarding_sessions, dependent: :destroy
#
#   belongs_to :invited_by, class_name: "User", optional: true, foreign_key: :invited_by_user_id
#
#   ACTIVATION_STATES = %w[pending invited onboarding active suspended].freeze
#
#   validates :activation_state, inclusion: { in: ACTIVATION_STATES }, allow_nil: true
#
#   scope :pending_onboarding, -> { where(activation_state: %w[pending invited onboarding]) }
#   scope :active_users, -> { where(activation_state: "active") }
#
#   def onboarding_lia_enabled?
#     # User override takes precedence, then account setting
#     if onboarding_lia_override.nil?
#       account&.onboarding_lia_enabled? || false
#     else
#       onboarding_lia_override
#     end
#   end
#
#   def onboarding_complete?
#     onboarding_completed_at.present?
#   end
#
#   def complete_onboarding!
#     update!(
#       activation_state: "active",
#       onboarding_completed_at: Time.current
#     )
#   end
#
# == Update user_payload in SessionsController ==
# In app/controllers/v1/sessions_controller.rb, update user_payload:
#
#   def user_payload(user)
#     {
#       id: user.id,
#       email: user.email,
#       name: user.name,
#       activation_state: user.activation_state,
#       first_login: user.first_login_at.nil?,
#       onboarding_completed: user.onboarding_complete?,
#       onboarding_session_id: user.onboarding_sessions.active.first&.id
#     }
#   end
