# frozen_string_literal: true

class EmailTemplatePolicy < ApplicationPolicy
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

  def categories?
    user.present?
  end

  def tags?
    user.present?
  end

  def generate_suggestion?
    return true if user.present? && (record.nil? || record.is_a?(Class))
    user.present? && record.account_id == user.account_id
  end

  def duplicate?
    user.present? && record.account_id == user.account_id
  end

  def render_preview?
    return true if user.present? && (record.nil? || record.is_a?(Class))
    user.present? && record.account_id == user.account_id
  end

  def send_email?
    return true if user.present? && (record.nil? || record.is_a?(Class))
    user.present? && record.account_id == user.account_id
  end
end
