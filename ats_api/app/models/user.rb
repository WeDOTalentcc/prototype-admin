class User < ApplicationRecord
  include Searchable

  enable_autocomplete :name

  belongs_to :account, optional: true
  belongs_to :department, optional: true
  belongs_to :city, optional: true
  belongs_to :state, optional: true
  has_many :jobs, dependent: :destroy
  has_many :entity_columns, dependent: :destroy
  has_many :activity_logs, dependent: :destroy
  has_secure_password

  PEPPER = ENV.fetch("PASSWORD_PEPPER", "")

  validates :email, uniqueness: { case_sensitive: false, allow_nil: true }
  validates :password, length: { minimum: 6, maximum: 72 }, if: :password_required?
  validates :status, inclusion: { in: 0..2 }, allow_nil: true

  before_create :set_pepper_migrated

  has_many :user_roles
  has_many :roles, through: :user_roles
  has_many :role_permissions, through: :roles
  has_many :data_files
  has_many :password_reset_tokens, dependent: :destroy
  has_many :workspaces, dependent: :destroy

  has_many :dispatches
  has_many :user_permissions
  has_many :direct_permissions, through: :user_permissions, source: :permission
  has_many :approvers, dependent: :destroy
  has_many :approval_requests_as_requester, class_name: "ApprovalRequest", foreign_key: :requested_by_id, dependent: :nullify
  has_many :approval_requests_as_approver, class_name: "ApprovalRequest", foreign_key: :approved_by_id, dependent: :nullify
  has_many :audit_logs, dependent: :destroy
  has_many :candidate_feedbacks, dependent: :destroy
  has_one :scheduling_setting, dependent: :destroy
  has_one :notification_preference, dependent: :destroy
  has_many :agent_notifications, dependent: :destroy
  has_many :scheduling_links, foreign_key: :created_by_id, dependent: :destroy
  has_many :cached_availabilities, dependent: :destroy

  STATUSES = [
    "Inativo",
    "Ativo",
    "Pendente"
  ]

  def search_data
    {
      **attributes.deep_symbolize_keys,
      status_name: STATUSES[status] || nil,
      is_admin: is_admin?,
      account_name: account&.name
    }
  end

  def can?(permission_name)
    permissions.exists?(name: permission_name) || direct_permissions.exists?(name: permission_name)
  end

  def effective_permissions
    (permissions + direct_permissions).uniq
  end

  def has_role?(name)
    roles.exists?(name: name.to_s)
  end

  def is_admin?
    has_role?(:admin) || has_role?(:super_admin)
  end

  def microsoft_connected?
    ms_access_token.present? &&
    ms_expires_at.present? &&
    ms_expires_at > Time.current
  end

  def google_connected?
    false
  end

  def microsoft_token_expires_in_minutes
    return nil unless ms_expires_at.present?
    ((ms_expires_at - Time.current) / 60).round
  end

  def microsoft_token_needs_refresh?
    return false unless ms_refresh_token.present?
    return true if ms_expires_at.nil?
    ms_expires_at < 10.minutes.from_now
  end

  def microsoft_connection_status
    return :not_connected if ms_refresh_token.blank?
    return :expired if ms_expires_at.present? && ms_expires_at < Time.current
    return :expiring_soon if microsoft_token_needs_refresh?
    :active
  end

  def test_microsoft_refresh!
    raise "User has no refresh token" if ms_refresh_token.blank?

    Rails.logger.info "🧪 [User#test_microsoft_refresh!] Testing refresh for user_id=#{id}"
    Rails.logger.info "   Current expires_at: #{ms_expires_at}"
    Rails.logger.info "   Status: #{microsoft_connection_status}"

    updated_user = MicrosoftService::Api.refresh_expires_at(self)
    reload

    Rails.logger.info "✅ [User#test_microsoft_refresh!] Success! New expires_at: #{ms_expires_at}"
    Rails.logger.info "   New status: #{microsoft_connection_status}"
    Rails.logger.info "   Expires in: #{microsoft_token_expires_in_minutes} minutes"

    true
  rescue => e
    if e.message.include?("needs to re-authenticate")
      Rails.logger.error "⚠️ [User#test_microsoft_refresh!] Token expired - user needs to login again"
      Rails.logger.info "   Tokens cleared: ms_access_token=#{ms_access_token.present?}, ms_refresh_token=#{ms_refresh_token.present?}"
    else
      Rails.logger.error "❌ [User#test_microsoft_refresh!] Error: #{e.class} #{e.message}"
    end
    false
  end

  def microsoft_needs_reauth?
    ms_refresh_token.blank? && (ms_access_token.present? || ms_expires_at.present?)
  end

  def clear_microsoft_tokens!
    update(
      ms_access_token: nil,
      ms_refresh_token: nil,
      ms_expires_at: nil
    )
  end

  def workos_connected?
    workos_access_token.present? &&
    workos_expires_at.present? &&
    workos_expires_at > Time.current
  end

  def status_name
    return nil if status.nil?
    STATUSES[status]
  end

  def password=(unencrypted)
    if unencrypted.present? && PEPPER.present?
      super(peppered(unencrypted))
    else
      super
    end
  end

  def authenticate(unencrypted)
    if PEPPER.blank?
      return super(unencrypted)
    end

    result = super(peppered(unencrypted))
    return result if result

    legacy_concat = "#{unencrypted}#{PEPPER}"
    legacy_result = BCrypt::Password.new(password_digest).is_password?(legacy_concat)
    return false unless legacy_result

    self.password = unencrypted
    save!(validate: false)
    self
  end

  def authenticate_with_migration(unencrypted)
    if pepper_migrated?
      return authenticate(unencrypted)
    end

    legacy_valid = BCrypt::Password.new(password_digest).is_password?(unencrypted)
    if legacy_valid
      self.pepper_migrated = true
      self.password = unencrypted
      save!
      return self
    end

    false
  end

  private

  def set_pepper_migrated
    self.pepper_migrated = true if PEPPER.present? && password_digest.present?
  end

  def peppered(plain)
    OpenSSL::HMAC.hexdigest("SHA256", PEPPER, plain)
  end

  def password_required?
    password.present?
  end
end
