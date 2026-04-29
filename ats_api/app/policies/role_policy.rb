class RolePolicy < ApplicationPolicy
  class Scope < Scope
    def resolve
      if user.has_role?(:admin) || user.has_role?(:super_admin)
        scope.all
      else
        scope.none
      end
    end
  end

  def index?
    user.has_role?(:admin) || user.has_role?(:super_admin)
  end

  def show?
    user.has_role?(:admin) || user.has_role?(:super_admin)
  end

  def create?
    user.has_role?(:admin) || user.has_role?(:super_admin)
  end

  def update?
    user.has_role?(:admin) || user.has_role?(:super_admin)
  end

  def destroy?
    user.has_role?(:admin) || user.has_role?(:super_admin)
  end
end
