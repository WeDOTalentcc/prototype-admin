class JobFieldTemplatePolicy < ApplicationPolicy
  class Scope < Scope
    def resolve
      scope.where(account_id: user.account_id)
    end
  end

  def index?
    true # Todos os usuários podem listar
  end

  def show?
    same_account?
  end

  def create?
    admin_or_super_admin?
  end

  def update?
    admin_or_super_admin? && same_account?
  end

  def destroy?
    admin_or_super_admin? && same_account?
  end

  def default_fields?
    true # Endpoint público para listar campos disponíveis
  end

  private

  def admin_or_super_admin?
    user&.is_admin? || user&.is_super_admin?
  end

  def same_account?
    record.account_id == user.account_id
  end
end
