class AccountSerializer
  include JSONAPI::Serializer

  attributes(
    :id,
    :name,
    :setup_token,
    :setup_token_expires_at,
    :tenant,
    :staging_tenant,
    :signup_email,
    :signup_email_content,
    :sourcing_config,
    :auth_config,
    :domain,
    :allowed_domains,
    :sso_providers,
    :sso_enforced,
    :jit_provisioning_enabled,
    :workos_enabled,
    :workos_organization_id,
    :workos_connection_id,
    :ats_provider,
    :uid,
    :created_at,
    :updated_at,
    :web_saturation_amount,
    :sourcing_saturation_amount,
    :saturation_amount_increase,
    :saturation_release_hours
  )

  attribute :search_credits do |account|
    account.pearch_credits
  end

  attribute :search_total_consumed do |account|
    account.pearch_total_consumed
  end

  attribute :setup_url do |account|
    "#{ENV['FRONT_URL']}/setups/#{account.setup_token}" if account.setup_token.present? && ENV["FRONT_URL"].present?
  end
end
