class ListPolicy < ApplicationPolicy
  class Scope < Scope
    def resolve
      scope.where(account_id: user.account_id)
    end
  end

  def index?
    user.present?
  end

  def show?
    user.present? && record.account_id == user.account_id
  end

  def create?
    user.present?
  end

  def update?
    user.present? && record.account_id == user.account_id
  end

  def destroy?
    user.present? && record.account_id == user.account_id
  end
end
