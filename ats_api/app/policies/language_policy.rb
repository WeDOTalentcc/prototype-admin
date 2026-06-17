class LanguagePolicy < ApplicationPolicy
  class Scope < Scope
    def resolve
      scope.all
    end
  end

  def index?
    user.present?
  end

  def show?
    user.present?
  end

  def create?
    admin_roles?
  end

  def update?
    admin_roles?
  end

  def destroy?
    admin_roles?
  end

  private

  def admin_roles?
    user.has_role?(:admin) || user.has_role?(:super_admin)
  end
end
