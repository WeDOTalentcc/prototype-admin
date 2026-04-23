# frozen_string_literal: true

class EntityColumnPolicy < ApplicationPolicy
  def index?
    true
  end

  def show?
    record_belongs_to_user? || record_is_public?
  end

  def create?
    true
  end

  def update?
    record_belongs_to_user?
  end

  def destroy?
    record_belongs_to_user?
  end

  def save?
    true
  end

  def create_view?
    true
  end

  def update_view?
    true
  end

  def delete_view?
    record_belongs_to_user?
  end

  def show_structure?
    true
  end

  class Scope < Scope
    def resolve
      if user.has_role?(:super_admin)
        scope.all
      else
        scope.where(account_id: user.account_id)
             .where(
               "(is_public = :is_public) OR (user_id = :user_id AND is_public = :is_not_public)",
               is_public: true, is_not_public: false, user_id: user.id
             )
      end
    end
  end

  private

  def record_belongs_to_user?
    record.user_id == user.id
  end

  def record_is_public?
    record.is_public?
  end

  def same_account?
    record.account_id == user.account_id
  end
end
