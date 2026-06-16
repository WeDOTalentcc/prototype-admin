class BusinessPolicy < ApplicationPolicy
  class Scope < Scope
    def resolve
      if user.has_role?(:super_admin)
        return scope.all
      end

      scope.where(account_id: user.account_id)
    end
  end

  def index?
    true
  end

  def show?
    user.has_role?(:super_admin) || record.account_id == user.account_id
  end

  def create?
    user.has_role?(:super_admin)
  end

  def update?
    user.has_role?(:super_admin) || record.account_id == user.account_id
  end

  def destroy?
    user.has_role?(:super_admin)
  end

  def generate_big_five?
    user.has_role?(:super_admin) || record.account_id == user.account_id
  end
end
