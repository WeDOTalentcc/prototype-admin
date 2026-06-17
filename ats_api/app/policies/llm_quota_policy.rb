# frozen_string_literal: true

class LlmQuotaPolicy < ApplicationPolicy
  class Scope < Scope
    def resolve
      return scope.all if user.has_role?(:admin) || user.has_role?(:super_admin)

      scope.none
    end
  end

  def index?
    user.has_role?(:admin) || user.has_role?(:super_admin)
  end

  def show?
    user.has_role?(:admin) || user.has_role?(:super_admin)
  end

  def update?
    user.has_role?(:admin) || user.has_role?(:super_admin)
  end

  def create?
    user.has_role?(:super_admin)
  end

  def destroy?
    user.has_role?(:super_admin)
  end
end
