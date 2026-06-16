class SearchCreditPolicy < ApplicationPolicy
  def add_credits?
    super_admin?
  end

  def remove_credits?
    super_admin?
  end

  def view_all_transactions?
    super_admin?
  end

  def view_all_statistics?
    super_admin?
  end

  def list_accounts?
    super_admin?
  end

  private

  def super_admin?
    user&.has_role?(:super_admin)
  end
end
