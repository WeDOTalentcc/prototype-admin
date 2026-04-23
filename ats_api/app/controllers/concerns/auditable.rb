module Auditable
  extend ActiveSupport::Concern

  included do
    after_action :log_action, if: :should_log_action?
  end

  private

  def should_log_action?
    return false unless @current_user
    return false if request.get? && !log_get_requests?

    loggable_actions.include?(action_name.to_sym)
  end

  def log_action
    Workos::AuditService.log(
      action: build_action_name,
      user: @current_user,
      resource: find_resource,
      metadata: build_metadata,
      request: request
    )
  end

  def build_action_name
    "#{controller_name}##{action_name}"
  end

  def find_resource
    instance_variable_get("@#{controller_name.singularize}")
  end

  def build_metadata
    {
      controller: controller_name,
      action: action_name,
      params: filtered_params
    }
  end

  def filtered_params
    params.except(:controller, :action, :password, :password_confirmation).to_unsafe_h
  end

  def loggable_actions
    [ :create, :update, :destroy ]
  end

  def log_get_requests?
    false
  end
end
