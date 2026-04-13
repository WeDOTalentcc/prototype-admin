# frozen_string_literal: true

module TenantScoped
  extend ActiveSupport::Concern

  included do
    before_action :set_tenant_scope
  end

  private

  def set_tenant_scope
    @current_account_id = @current_user&.account_id
  end

  def scope_to_tenant(relation)
    return relation unless @current_account_id
    return relation unless relation.column_names.include?("account_id")

    relation.where(account_id: @current_account_id)
  end

  def verify_tenant!(record)
    return unless @current_account_id
    return unless record.respond_to?(:account_id)
    return if record.account_id.nil? || record.account_id == @current_account_id

    render_simple_error("Access denied", status: :forbidden)
  end
end
