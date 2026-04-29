class AccountPolicy < ApplicationPolicy
  class Scope < Scope
    def resolve
      return scope.all if user.has_role?(:super_admin)
      return scope.where(id: user.account_id) if user.has_role?(:admin)

      scope.none
    end
  end

  def index?
    user.has_role?(:admin) || user.has_role?(:super_admin)
  end

  def show?
    user.has_role?(:admin) || user.has_role?(:super_admin)
  end

  def create?
    user.has_role?(:super_admin)
  end

  def update?
    user.has_role?(:admin) || user.has_role?(:super_admin)
  end

  def destroy?
    user.has_role?(:super_admin)
  end

  def manage_search_credits?
    user.has_role?(:admin) || user.has_role?(:super_admin)
  end
end
