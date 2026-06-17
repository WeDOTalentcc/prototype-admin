class ApproverSerializer
  include JSONAPI::Serializer

  attributes :id, :account_id, :user_id, :department_id, :approval_type,
             :approval_level, :limit_value, :name, :email, :title,
             :is_active, :is_deleted, :created_at, :updated_at

  attribute :user_name do |obj|
    obj.try(:user_name) || obj.user&.name
  end

  attribute :user_email do |obj|
    obj.try(:user_email) || obj.user&.email
  end

  attribute :department_name do |obj|
    obj.try(:department_name) || obj.department&.name
  end

  attribute :display_name do |obj|
    obj.name.presence || obj.try(:user_name) || obj.user&.name
  end

  attribute :display_email do |obj|
    obj.email.presence || obj.try(:user_email) || obj.user&.email
  end

  attribute :is_global do |obj|
    obj.department_id.nil?
  end

  APPROVAL_TYPE_LABELS = { "job" => "Vaga", "hiring" => "Contratação", "offer" => "Oferta" }.freeze

  attribute :approval_type_label do |obj|
    APPROVAL_TYPE_LABELS[obj.approval_type] || obj.approval_type&.humanize
  end

  attribute :user do |obj|
    next unless obj.user

    {
      id: obj.user.id,
      name: obj.user.name,
      email: obj.user.email
    }
  end

  attribute :department do |obj|
    next unless obj.department

    {
      id: obj.department.id,
      name: obj.department.name,
      color: obj.department.color
    }
  end
end
