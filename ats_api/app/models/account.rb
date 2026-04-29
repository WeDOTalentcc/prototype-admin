class Account < ApplicationRecord
  include UidGeneratable
  include Searchable
  has_many :users, dependent: :destroy
  has_many :jobs, dependent: :destroy
  has_many :candidates
  has_many :password_reset_tokens, dependent: :destroy
  has_many :workspaces, dependent: :destroy
  has_many :job_journeys, dependent: :destroy
  has_many :pearch_credit_transactions, dependent: :destroy
  has_many :pearch_search_logs, dependent: :destroy
  has_many :sourcings, dependent: :destroy
  has_many :sourced_profiles, dependent: :destroy
  has_many :sourced_profile_sourcings, dependent: :destroy
  has_many :search_archetypes, dependent: :destroy
  has_many :approvers, dependent: :destroy
  has_many :approval_requests, dependent: :destroy
  has_many :audit_logs, dependent: :destroy
  has_many :interview_sessions, dependent: :destroy
  has_one :llm_quota, dependent: :destroy
  has_one :llm_configuration, dependent: :destroy

  validates :name, presence: true, uniqueness: { case_sensitive: false }

  def workos_enabled?
    workos_enabled == true && workos_organization_id.present?
  end

  def auth_config
    super || {}
  end

  def password_login_enabled?
    auth_config.fetch("password_login_enabled", true)
  end

  def microsoft_sso_enabled?
    return false unless workos_enabled?
    auth_config.fetch("microsoft_sso_enabled", true)
  end

  def google_sso_enabled?
    return false unless workos_enabled?
    auth_config.fetch("google_sso_enabled", true)
  end

  def available_auth_methods
    methods = []
    methods << "password" if password_login_enabled?
    methods << "microsoft_entra_id" if microsoft_sso_enabled?
    methods << "google_oauth" if google_sso_enabled?
    methods
  end

  def only_sso?
    !password_login_enabled? && (microsoft_sso_enabled? || google_sso_enabled?)
  end

  def only_password?
    password_login_enabled? && !microsoft_sso_enabled? && !google_sso_enabled?
  end

  def mfa_enabled?
    self[:mfa_enabled] == true
  end

  def mfa_required_for_admins?
    self[:mfa_required_for_admins] == true
  end

  def pearch_config
    sourcing_config.dig("pearch") || default_pearch_config
  end

  def default_pearch_config
    { "limit" => 10, "type" => "fast" }
  end

  def all_allowed_domains
    ([ domain ] + (allowed_domains || [])).compact.uniq.map(&:downcase)
  end

  def available_sso_providers
    return [] unless workos_enabled?
    sso_providers || []
  end

  def sso_active?
    workos_enabled? && available_sso_providers.any?
  end

  def email_domain_allowed?(email)
    return true if all_allowed_domains.empty?

    email_domain = email.to_s.split("@").last&.downcase
    return false unless email_domain

    all_allowed_domains.include?(email_domain)
  end

  def sso_enforced?
    sso_enforced == true
  end

  def jit_provisioning_enabled?
    jit_provisioning_enabled != false
  end

  def search_data
    {
      id: id,
      uid: uid,
      name: name&.downcase,
      tenant: tenant,
      staging_tenant: staging_tenant,
      domain: domain&.downcase,
      allowed_domains: allowed_domains,
      ats_provider: ats_provider,
      signup_email: signup_email&.downcase,
      pearch_credits: pearch_credits,
      pearch_total_consumed: pearch_total_consumed,
      workos_enabled: workos_enabled,
      workos_organization_id: workos_organization_id,
      sso_enforced: sso_enforced,
      jit_provisioning_enabled: jit_provisioning_enabled,
      mfa_enabled: mfa_enabled,
      mfa_method: mfa_method,
      mfa_required_for_admins: mfa_required_for_admins,
      microsoft_sso_enabled: microsoft_sso_enabled?,
      google_sso_enabled: google_sso_enabled?,
      password_login_enabled: password_login_enabled?,
      created_at: created_at,
      updated_at: updated_at
    }
  end

  def self.search_fields
    %i[name tenant domain signup_email uid ats_provider]
  end

  DEFAULT_SATURATION = {
    web_saturation_amount: 20,
    sourcing_saturation_amount: 20,
    saturation_amount_increase: 10,
    saturation_release_hours: 0
  }.freeze

  before_validation :generate_tenant_slug, on: :create
  before_validation :set_default_saturation, on: :create
  before_create :generate_setup_token
  after_create :ensure_slug
  after_create_commit :queue_tenant_creation
  after_create_commit :send_signup_email
  after_create_commit :provision_llm_quota
  belongs_to :business, optional: true

  private

  def ensure_slug
    return if slug.present?

    update_column(:slug, SecureRandom.alphanumeric(8))
  end

  def set_default_saturation
    return unless respond_to?(:web_saturation_amount)

    DEFAULT_SATURATION.each do |attr, value|
      current = read_attribute(attr)
      next if current.present? && current != 0

      write_attribute(attr, value)
    end
  end

  def generate_tenant_slug
    return unless name.present? && tenant.blank?
    slug = name.parameterize

    if self.class.exists?(tenant: slug)
      self.tenant = "#{slug}-#{Time.now.to_i}"
      return
    end

    self.tenant = slug
  end

  def generate_setup_token
    self.setup_token = SecureRandom.hex(20)
    self.setup_token_expires_at = 7.days.from_now
  end

  def queue_tenant_creation
    CreateTenantJob.perform_later(self.tenant)
  end

  def send_signup_email
    return unless signup_email.present?
    return unless signup_email_content.present?

    domain = ENV["FRONT_URL"].presence || "localhost:3000"
    setup_url = if Rails.env.development?
      "http://localhost:3000/setups/#{setup_token}"
    else
      "https://#{domain}/setups/#{setup_token}"
    end

    email_body = "#{signup_email_content}\n\n"

    AccountMailer.signup_email(
      to: signup_email,
      account_name: name,
      setup_url: setup_url,
      content: email_body
    ).deliver_later

    Rails.logger.info "Signup email enqueued for account #{id} to #{signup_email}"
  rescue => e
    Rails.logger.error "Failed to send signup email for account #{id}: #{e.message}"
  end

  def provision_llm_quota
    defaults = Llm::QuotaPlan.defaults_for(Llm::QuotaPlan::DEFAULT_PLAN)
    LlmQuota.find_or_create_by!(account_id: id) do |quota|
      quota.plan = Llm::QuotaPlan::DEFAULT_PLAN
      quota.monthly_cost_limit_usd = defaults[:monthly_cost_limit_usd]
      quota.monthly_request_limit = defaults[:monthly_request_limit]
      quota.burst_rpm = defaults[:burst_rpm]
      quota.extra_budget_usd = 0.0
      quota.notify_at_percentage = 80
      quota.enabled = true
      quota.hard_limit = false
      quota.metadata = {}
    end
  rescue => e
    Rails.logger.error "Failed to provision LLM quota for account #{id}: #{e.message}"
  end
end
