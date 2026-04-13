# frozen_string_literal: true

class ClientAccountSerializer
  include JSONAPI::Serializer

  attributes(
    :id,
    :name,
    :trade_name,
    :cnpj,
    :website,
    :logo_url,
    :address,
    :primary_email,
    :primary_phone,
    :status,
    :plan_id,
    :contract_start_date,
    :contract_end_date,
    :user_limit,
    :job_limit,
    :ai_credits_monthly,
    :settings,
    :features_enabled,
    :account_manager_id,
    :implementation_manager_id,
    :industry,
    :company_size,
    :onboarding_completed_at,
    :welcome_email_sent,
    :welcome_email_sent_at,
    :workos_organization_created,
    :workos_organization_created_at,
    :sso_configured,
    :sso_configured_at,
    :is_deleted,
    :deleted_at,
    :deleted_by,
    :created_at,
    :updated_at
  )
end
