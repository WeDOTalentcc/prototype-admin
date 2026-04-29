class PermissionPolicy < ApplicationPolicy
  class Scope < Scope
    def resolve
      if user.is_admin?
        scope.all
      else
        scope.none
      end
    end
  end

  def index?
    user.is_admin?
  end

  def show?
    user.is_admin?
  end
end
