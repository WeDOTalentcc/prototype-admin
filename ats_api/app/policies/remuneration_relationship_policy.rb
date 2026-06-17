class RemunerationRelationshipPolicy < ApplicationPolicy
  def index?
    true
  end

  def show?
    true
  end

  def create?
    true
  end

  def update?
    record.account_id == user.account_id
  end

  def destroy?
    record.account_id == user.account_id
  end

  def bulk_upsert?
    true
  end
end
