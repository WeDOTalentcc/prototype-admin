class ApprovalRequestSerializer
  include JSONAPI::Serializer

  attributes :id, :account_id, :approver_id, :requested_by_id, :approved_by_id,
             :reference_type, :reference_id, :approval_level, :status,
             :comments, :approved_at, :rejected_at, :expires_at,
             :is_deleted, :created_at, :updated_at

  attribute :approver_name do |obj|
    obj.try(:approver_name) || obj.approver&.display_name
  end

  attribute :approver_email do |obj|
    obj.try(:approver_email) || obj.approver&.display_email
  end

  attribute :requested_by_name do |obj|
    obj.try(:requested_by_name) || obj.requested_by&.name
  end

  attribute :approved_by_name do |obj|
    obj.try(:approved_by_name) || obj.approved_by&.name
  end

  attribute :reference_name do |obj|
    obj.try(:reference_name) || obj.reference_name
  end

  attribute :status_name do |obj|
    obj.status&.humanize
  end

  STATUS_COLORS = { "pending" => "#F5E6B3", "approved" => "#A8D5B7", "rejected" => "#E8B8B8", "expired" => "#E5E7EB", "cancelled" => "#E5C5C5" }.freeze
  APPROVAL_TYPE_LABELS = { "job" => "Vaga", "hiring" => "Contratação", "offer" => "Oferta" }.freeze

  attribute :status_color do |obj|
    STATUS_COLORS[obj.status]
  end

  attribute :approval_type do |obj|
    obj.try(:approval_type) || obj.approver&.approval_type
  end

  attribute :approval_type_label do |obj|
    type = obj.try(:approval_type) || obj.approver&.approval_type
    APPROVAL_TYPE_LABELS[type] || type&.humanize
  end

  attribute :department_id do |obj|
    obj.try(:department_id) || obj.approver&.department_id
  end

  attribute :department_name do |obj|
    obj.try(:department_name) || obj.approver&.department&.name
  end

  attribute :is_expired do |obj|
    obj.expires_at.present? && obj.expires_at < Time.current
  end

  attribute :can_approve do |obj|
    obj.pending? && (obj.expires_at.nil? || obj.expires_at > Time.current)
  end

  attribute :approver do |obj|
    next unless obj.approver

    {
      id: obj.approver.id,
      user_id: obj.approver.user_id,
      name: obj.approver.display_name,
      email: obj.approver.display_email,
      approval_level: obj.approver.approval_level
    }
  end

  attribute :requested_by do |obj|
    next unless obj.requested_by

    {
      id: obj.requested_by.id,
      name: obj.requested_by.name,
      email: obj.requested_by.email
    }
  end

  attribute :approved_by do |obj|
    next unless obj.approved_by

    {
      id: obj.approved_by.id,
      name: obj.approved_by.name,
      email: obj.approved_by.email
    }
  end
end
