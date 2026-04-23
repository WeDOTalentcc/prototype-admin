class WhatsappTenantMapping < ApplicationRecord
  include PhoneNormalizable

  belongs_to :account

  validates :phone_number, presence: true
  validates :account_id, presence: true
  validates :phone_number, uniqueness: { scope: :account_id }

  scope :recent_first, -> { order(last_interaction_at: :desc, updated_at: :desc) }
  scope :for_phone, ->(phone) { where(phone_number: normalize_phone_number(phone)) }

  def self.upsert_mapping(phone_number:, account_id:)
    normalized_phone = normalize_phone_number(phone_number)
    return nil if normalized_phone.blank?

    Apartment::Tenant.switch("public") do
      mapping = find_or_initialize_by(
        phone_number: normalized_phone,
        account_id: account_id
      )

      mapping.last_interaction_at = Time.current
      mapping.save!
      mapping
    end
  rescue => e
    Rails.logger.error "WhatsappTenantMapping: Error upserting mapping for #{normalized_phone}: #{e.message}"
    nil
  end

  def self.find_tenant_for_phone(phone_number)
    normalized_phone = normalize_phone_number(phone_number)
    return nil if normalized_phone.blank?

    Apartment::Tenant.switch("public") do
      for_phone(normalized_phone)
        .recent_first
        .joins(:account)
        .first
    end
  rescue => e
    Rails.logger.error "WhatsappTenantMapping: Error finding tenant for #{normalized_phone}: #{e.message}"
    nil
  end

  def self.normalize_phone_number(phone)
    PhoneNormalizable.normalize_phone(phone)
  end
end
