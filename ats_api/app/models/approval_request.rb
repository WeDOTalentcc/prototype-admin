class ApprovalRequest < ApplicationRecord
  include Searchable

  belongs_to :account
  belongs_to :approver
  belongs_to :requested_by, class_name: "User", optional: true
  belongs_to :approved_by, class_name: "User", optional: true

  STATUSES = { pending: 0, approved: 1, rejected: 2, expired: 3, cancelled: 4 }.freeze

  enum :status, STATUSES

  validates :reference_type, :reference_id, presence: true
  validates :approval_level, presence: true, numericality: { greater_than: 0 }

  scope :active, -> { where(is_deleted: false) }
  scope :pending_approval, -> { active.pending }
  scope :by_reference, ->(type, id) { where(reference_type: type, reference_id: id) }
  scope :ordered, -> { order(:approval_level, :created_at) }

  def search_data
    {
      id: id,
      account_id: account_id,
      approver_id: approver_id,
      approver_name: approver&.display_name,
      approver_email: approver&.display_email,
      requested_by_id: requested_by_id,
      requested_by_name: requested_by&.name,
      approved_by_id: approved_by_id,
      approved_by_name: approved_by&.name,
      reference_type: reference_type,
      reference_id: reference_id,
      reference_name: reference_name,
      approval_level: approval_level,
      status: status,
      status_name: status&.humanize,
      comments: comments,
      approved_at: approved_at,
      rejected_at: rejected_at,
      expires_at: expires_at,
      is_deleted: is_deleted,
      approval_type: approver&.approval_type,
      department_id: approver&.department_id,
      department_name: approver&.department&.name,
      created_at: created_at,
      updated_at: updated_at
    }
  end

  def self.search_fields
    [ :approver_name, :approver_email, :requested_by_name, :reference_name, :comments ]
  end

  def self.agg_search_array(_params = {})
    {
      status: { field: "status", limit: 5 },
      approval_type: { field: "approval_type", limit: 5 },
      approval_level: { field: "approval_level", limit: 10 },
      reference_type: { field: "reference_type", limit: 5 },
      department_id: { field: "department_id", limit: 20 },
      approver_id: { field: "approver_id", limit: 20 }
    }
  end

  def self.default_search_order
    { created_at: :desc }
  end

  def approve!(user:, comments: nil)
    return false unless pending?

    update(
      status: :approved,
      approved_by: user,
      approved_at: Time.current,
      comments: comments
    )
  end

  def reject!(user:, comments: nil)
    return false unless pending?

    update(
      status: :rejected,
      approved_by: user,
      rejected_at: Time.current,
      comments: comments
    )
  end

  def reference
    @reference ||= reference_type.constantize.find_by(id: reference_id)
  end

  REFERENCE_NAME_METHODS = { "Job" => :title, "Candidate" => :name }.freeze

  def reference_name
    return unless reference

    method = REFERENCE_NAME_METHODS[reference_type]
    method ? reference.public_send(method) : (reference.try(:name) || reference.try(:title) || "ID: #{reference_id}")
  end

  def self.create_approval_chain(account:, reference:, approval_type:, requested_by:, department_id: nil)
    approvers = Approver.for_approval(
      account_id: account.id,
      approval_type: approval_type,
      department_id: department_id
    )

    return [] if approvers.empty?

    approvers.map do |approver|
      create!(
        account: account,
        approver: approver,
        reference_type: reference.class.name,
        reference_id: reference.id,
        approval_level: approver.approval_level,
        requested_by: requested_by,
        expires_at: 7.days.from_now
      )
    end
  end

  def next_pending_request
    ApprovalRequest
      .active
      .pending
      .by_reference(reference_type, reference_id)
      .where("approval_level > ?", approval_level)
      .ordered
      .first
  end

  def all_approved_for_reference?
    ApprovalRequest
      .active
      .by_reference(reference_type, reference_id)
      .pending
      .none?
  end
end
