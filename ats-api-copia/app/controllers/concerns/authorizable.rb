# frozen_string_literal: true

# Authorizable concern — role-based access control for controllers.
#
# Adds role-checking helpers that return 403 Forbidden when the
# authenticated user lacks the required role. Works alongside
# authorize_request (JWT auth → 401) as a separate layer.
#
# Usage in controllers:
#   before_action :require_admin!, only: [:destroy, :bulk_delete]
#   before_action :require_manager!, only: [:update_settings]
#   before_action :require_recruiter!
#
# Role hierarchy (highest to lowest):
#   super_admin > admin > owner > manager > recruiter > viewer
#
# Item: PX08-088 — Wave 6, item 6.8

module Authorizable
  extend ActiveSupport::Concern

  ROLE_HIERARCHY = %w[viewer recruiter manager owner admin super_admin].freeze

  private

  # Check if current user has at least the specified minimum role.
  # Compares position in ROLE_HIERARCHY — higher index = more privilege.
  def authorize_minimum_role!(minimum_role)
    user_role = resolve_user_role
    min_index = ROLE_HIERARCHY.index(minimum_role.to_s) || 0
    user_index = ROLE_HIERARCHY.index(user_role) || 0

    return if user_index >= min_index

    render json: {
      error: "Permissao insuficiente",
      code: "INSUFFICIENT_PERMISSIONS",
      required_role: minimum_role.to_s,
    }, status: :forbidden
  end

  def require_admin!
    authorize_minimum_role!(:admin)
  end

  def require_manager!
    authorize_minimum_role!(:manager)
  end

  def require_recruiter!
    authorize_minimum_role!(:recruiter)
  end

  def require_viewer!
    # Any authenticated user can view — this is a no-op placeholder
    # for documentation purposes. authorize_request already ensures auth.
  end

  def resolve_user_role
    return "viewer" unless @current_user

    # Try .role attribute first (string field on user)
    if @current_user.respond_to?(:role) && @current_user.role.present?
      return @current_user.role.to_s.downcase
    end

    # Try roles association (has_many through)
    if @current_user.respond_to?(:roles) && @current_user.roles.any?
      role_names = @current_user.roles.map { |r| r.name.to_s.downcase }
      # Return highest role in hierarchy
      ROLE_HIERARCHY.reverse.each do |h_role|
        return h_role if role_names.include?(h_role)
      end
      return role_names.first
    end

    # Try is_admin flag
    return "admin" if @current_user.respond_to?(:is_admin) && @current_user.is_admin

    "recruiter" # default — authenticated users are at least recruiters
  end
end
