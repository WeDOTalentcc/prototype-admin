class Workspace < ApplicationRecord
  include Searchable

  belongs_to :user
  belongs_to :account
  has_many :messages, dependent: :destroy

  validates :user, presence: true
  validates :account, presence: true
  validates :is_deleted, inclusion: { in: [ true, false ] }
  validates :domain_reference_id, presence: true, if: -> { domain.present? && !singleton_domain? }

  SINGLETON_DOMAINS = %w[lia_general].freeze

  scope :active, -> { where(is_deleted: false) }
  scope :for_domain, ->(domain) { where(domain: domain) }
  scope :for_domain_reference, ->(domain, reference_id) { where(domain: domain, domain_reference_id: reference_id) }

  def self.find_or_create_for_domain(user:, account:, domain:, domain_reference_id: nil)
    return nil if domain.blank?
    return nil if domain_reference_id.blank? && !singleton_domain?(domain)

    lookup = { user_id: user.id, account_id: account.id, domain: domain }
    lookup[:domain_reference_id] = domain_reference_id unless singleton_domain?(domain)

    workspace = active.find_by(lookup)
    return workspace if workspace

    workspace = new(user: user, account: account, domain: domain, domain_reference_id: domain_reference_id)
    workspace.uid = SecureRandom.uuid
    workspace.name = generate_domain_workspace_name(domain, domain_reference_id)
    workspace.save!
    workspace
  rescue ActiveRecord::RecordNotUnique
    active.find_by!(lookup)
  end

  def self.singleton_domain?(domain)
    SINGLETON_DOMAINS.include?(domain.to_s)
  end

  def singleton_domain?
    self.class.singleton_domain?(domain)
  end

  def self.generate_domain_workspace_name(domain, domain_reference_id = nil)
    return "Lia" if domain.to_s == "lia_general"

    base = domain.to_s.titleize.gsub("_", " ")
    domain_reference_id ? "#{base} ##{domain_reference_id}" : base
  end

  def domain_channel_name
    return nil unless domain.present? && domain_reference_id.present?
    "domain_messages_user_#{user_id}_#{domain}_#{domain_reference_id}"
  end

  def update_last_message!
    update!(last_message_date: Time.current)
  end

  def has_messages?
    messages.exists?
  end

  def last_activity
    last_message_date || updated_at
  end

  def generate_fields(message_content)
    self.uid = SecureRandom.uuid
    self.name = "Workspace #{id || SecureRandom.hex(4)}"
    save!

    WorkspaceNameGenerationJob.perform_later(id, message_content, Apartment::Tenant.current)
  end

  def generate_name_from_content(message_content)
    base_name = RecruitAgentService.generate_workspace_name(message_content) || "Workspace #{id}"

    existing_workspaces = Workspace.where(
      user_id: user_id,
      account_id: account_id,
      is_deleted: false
    ).where("name LIKE ?", "#{base_name}%")
    .pluck(:name)

    self.name = if existing_workspaces.include?(base_name)
      max_number = existing_workspaces.map do |name|
        match = name.match(/#{Regexp.escape(base_name)}\s*#?(\d+)/)
        match ? match[1].to_i : 0
      end.max || 0

      "#{base_name} ##{max_number + 1}"
    else
      base_name
    end

    retries = 0
    max_retries = 3

    begin
      save!
    rescue ActiveRecord::RecordNotUnique => e
      retries += 1
      if retries <= max_retries
        self.name = "#{base_name} ##{Time.current.to_i % 10000}"
        retry
      else
        raise e
      end
    end

    broadcast_workspace_updated
  end

  private

  def broadcast_workspace_updated
    ActionCable.server.broadcast(
      "messages_user_#{user_id}",
      {
        type: "workspace_updated",
        workspace_id: id,
        name: name,
        updated_at: updated_at&.iso8601
      }
    )
  end
end
