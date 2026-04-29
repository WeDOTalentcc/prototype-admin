# frozen_string_literal: true

class SectorRelationshipPolicy < ApplicationPolicy
  class Scope < Scope
    def resolve
      scope.active.for_account(user.account_id)
    end
  end

  def index?
    user.present?
  end

  def show?
    user.present? && same_account?
  end

  def create?
    user.present?
  end

  def update?
    user.present? && same_account?
  end

  def destroy?
    user.present? && same_account?
  end

  private

  def same_account?
    record.account_id == user.account_id
  end
end
