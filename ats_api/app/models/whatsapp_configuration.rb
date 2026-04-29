class WhatsappConfiguration < ApplicationRecord
  include Searchable

  ENVIRONMENTS = %w[development staging production test global].freeze
  ACTION_TYPES = %w[webhook].freeze

  validates :environment, presence: true, inclusion: { in: ENVIRONMENTS }
  validates :action_type, inclusion: { in: ACTION_TYPES }
  validates :phone_number, presence: true, uniqueness: { scope: [ :environment, :action_type ] }
  validates :redirect_url, format: { with: URI::DEFAULT_PARSER.make_regexp(%w[http https]), allow_blank: true }

  scope :active, -> { where(is_deleted: false) }
  scope :for_environment, ->(env) { where(environment: env.to_s) }
  scope :for_action_type, ->(type) { where(action_type: type.to_s) }
  scope :with_redirect, -> { where.not(redirect_url: [ nil, "" ]) }
  scope :ordered, -> { order(:priority, :environment, :phone_number) }

  def self.find_config(phone_number, environment = Rails.env, action_type = "webhook")
    normalized_phone = normalize_phone(phone_number)
    return nil if normalized_phone.blank?

    target_envs = [ environment.to_s, "global" ].compact.uniq

    configs = active
                .for_action_type(action_type)
                .where(environment: target_envs, phone_number: normalized_phone, active: true)
                .to_a

    configs.min_by do |config|
      [ config.environment == environment.to_s ? 0 : 1, config.priority.to_i, config.id ]
    end
  end

  def self.find_configs_for_phone(phone_number, environment = Rails.env)
    normalized_phone = normalize_phone(phone_number)
    return [] if normalized_phone.blank?

    target_envs = [ environment.to_s, "global" ].compact.uniq

    active
      .where(environment: target_envs, phone_number: normalized_phone)
      .ordered
  end

  def self.should_redirect?(phone_number, environment = Rails.env, action_type = "webhook")
    config = find_config(phone_number, environment, action_type)
    config&.active? && config.redirect_url.present?
  end

  def self.redirect_url_for(phone_number, environment = Rails.env, action_type = "webhook")
    config = find_config(phone_number, environment, action_type)
    return unless config&.active?

    config.redirect_url
  end

  def self.should_process?(phone_number, environment = Rails.env)
    config = find_config(phone_number, environment)
    return true unless config

    config.active?
  end

  def self.create_or_update_config(phone_number, environment, action_type: "webhook", redirect_url: nil, description: nil, developer_name: nil, metadata: {}, active: true, priority: nil)
    normalized_phone = normalize_phone(phone_number)
    return nil if normalized_phone.blank?

    config = find_by(phone_number: normalized_phone, environment: environment, action_type: action_type) ||
             new(phone_number: normalized_phone, environment: environment, action_type: action_type)

    metadata_hash = metadata.respond_to?(:to_unsafe_h) ? metadata.to_unsafe_h : metadata
    metadata_hash = nil if metadata_hash.blank?

    attributes = {
      redirect_url: redirect_url,
      description: description,
      developer_name: developer_name,
      active: active,
      priority: priority || config.priority
    }
    attributes[:metadata] = metadata_hash if metadata_hash

    config.assign_attributes(attributes)

    config.save!
    config
  end

  def self.setup_defaults!
    default_configs = [
      {
        phone: "15551924179",
        env: "development",
        action_type: "webhook",
        description: "Webhook desenvolvimento - redireciona via ngrok"
      },
      {
        phone: "5511975205003",
        env: "production",
        action_type: "webhook",
        description: "Webhook produção oficial"
      }
    ]

    default_configs.each do |config|
      create_or_update_config(
        config[:phone],
        config[:env],
        action_type: config[:action_type],
        description: config[:description]
      )
    end
  end

  def soft_delete!
    update!(is_deleted: true)
  end

  def restore!
    update!(is_deleted: false)
  end

  def deleted?
    is_deleted?
  end

  def display_name
    parts = [ developer_name, environment.capitalize, action_type.upcase, formatted_phone ].compact
    parts.join(" - ")
  end

  def formatted_phone
    return phone_number unless phone_number&.start_with?("55")

    country = phone_number[0..1]
    area = phone_number[2..3]
    first = phone_number[4..8]
    second = phone_number[9..12]

    "+#{country} #{area} #{first}-#{second}"
  end

  def webhook?
    action_type == "webhook"
  end

  private

  def self.normalize_phone(phone)
    return nil if phone.blank?

    digits = phone.gsub(/\D/, "")
    digits.length == 11 && !digits.start_with?("55") ? "55#{digits}" : digits
  end
end
