class WhatsappConfigurationPolicy < ApplicationPolicy
  class Scope < Scope
    def resolve
      admin? ? scope.all : scope.none
    end

    private

    def admin?
      user&.is_admin?
    end
  end

  def index?
    admin?
  end

  def show?
    admin?
  end

  def create?
    admin?
  end

  def update?
    admin?
  end

  def destroy?
    admin?
  end

  def restore?
    admin?
  end

  def quick_update_url?
    admin?
  end

  private

  def admin?
    user&.is_admin?
  end
end
