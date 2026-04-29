# frozen_string_literal: true

class SectorPolicy < ApplicationPolicy
  class Scope < Scope
    def resolve
      scope.active
    end
  end

  def index?
    user.present?
  end

  def show?
    user.present?
  end

  def create?
    super_admin?
  end

  def update?
    super_admin?
  end

  def destroy?
    super_admin?
  end

  def tree?
    user.present?
  end

  def autocomplete?
    user.present?
  end

  private

  def super_admin?
    user.has_role?(:super_admin)
  end
end
