class UserSerializer
  include JSONAPI::Serializer

  attributes(
    :id,
    :name,
    :email,
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
    :microsoft_connected,
    :created_at,
    :updated_at,
    :lia_user,
    :account_id
  )

  attribute :is_admin do |user|
    user.is_admin?
  end

  attribute :microsoft_connected do |user|
    user.microsoft_connected?
  end

  attribute :status_name do |user|
    user.status_name
  end

  attribute :city_name do |user|
    user.city&.name
  end

  attribute :state_name do |user|
    user.city&.state&.name
  end

  attribute :department do |user|
    next unless user.department

    {
      id: user.department.id,
      name: user.department.name
    }
  end

  attribute :account do |user|
    next unless user.account

    {
      id: user.account.id,
      name: user.account.name
    }
  end

  attribute :account_name do |user|
    user.try(:account_name) || user.account&.name
  end

  attribute :permission_ids do |user|
    user.user_permissions.map do |user_permission|
      {
        id: user_permission.permission_id
      }
    end
  end
end
