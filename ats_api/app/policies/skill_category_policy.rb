class SkillCategoryPolicy < ApplicationPolicy
  def index?
    true # Todos podem listar
  end

  def show?
    true # Todos podem ver
  end

  def create?
    user.admin? || user.super_admin?
  end

  def update?
    user.admin? || user.super_admin?
  end

  def destroy?
    user.admin? || user.super_admin?
  end
end
