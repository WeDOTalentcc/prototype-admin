# app/policies/user_policy.rb
class UserPolicy < ApplicationPolicy
  def index?
    user.is_admin?
  end

  def show?
    user.is_admin?
  end

  def create?
    user.is_admin?
  end

  def update?
    user.is_admin?
  end

  def destroy?
    user.is_admin?
  end

  def send_invite?
    user.is_admin?
  end

  def update_admin_fields?
    user.is_admin?
  end

  def update_lia_user?
    user.has_role?(:super_admin)
  end

  def permitted_attributes
    attrs = [
      :email,
      :password,
      :name,
      :role_name,
      :phone,
      :position_level,
      :whatsapp,
      :status,
      :is_manager,
      :email_signature,
      :department_id,
      :city_id,
      :state_id,
      :account_id,
      role_ids: [],
      permission_ids: []
    ]

    attrs << :is_admin if update_admin_fields?

    attrs << :lia_user if update_lia_user?

    attrs
  end
end
