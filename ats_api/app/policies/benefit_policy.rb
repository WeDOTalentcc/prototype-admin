class BenefitPolicy < ApplicationPolicy
  class Scope < Scope
    def resolve
      scope.all
    end
  end

  def index?; user.present?; end
  def show?; user.present?; end
  def create?; user.present?; end
  def update?; user.present?; end
  def destroy?; user.present?; end
  def grouped_by_category?; user.present?; end
end
