# frozen_string_literal: true

# You can have Apartment route to the appropriate Tenant by adding some Rack middleware.
# Apartment can support many different "Elevators" that can take care of this routing to your data.
# Require whichever Elevator you're using below or none if you have a custom one.
#
# require 'apartment/elevators/generic'
# require 'apartment/elevators/domain'
# require 'apartment/elevators/subdomain'
# require 'apartment/elevators/first_subdomain'
# require 'apartment/elevators/host'

#
# Apartment Configuration
#
# require "apartment"

Apartment.configure do |config|
  # Keep the 'extensions' schema on search_path so pg extensions (e.g., pgvector) are visible in all tenants
  # Avoid persisting 'public' to prevent accidental table drops during tenant bootstrap
  config.persistent_schemas = %w[extensions]
  # Models that should live in the global/public schema (not tenantized)
  # Add ApiClient and RequestKey so credentials and idempotency keys are shared across tenants
  # Add WhatsappTenantMapping to map phone numbers to tenants globally
  config.excluded_models = %w[ Sector Account User Role UserRole Language City State Country ApiClient RequestKey WhatsappTenantMapping WhatsappConfiguration LlmUsage LlmQuota LlmQuotaUsage LlmConfiguration ]
  # config.persistent_schemas = %w{ public }
  config.tenant_names = lambda { Account.pluck :tenant }
  config.default_tenant = "public"
  # config.tenant_names = -> { ToDo_Tenant_Or_User_Model.pluck :database }
end

# Setup a custom Tenant switching middleware. The Proc should return the name of the Tenant that
# you want to switch to.
# Rails.application.config.middleware.use Apartment::Elevators::Generic, lambda { |request|
#   request.host.split('.').first
# }

# Rails.application.config.middleware.use Apartment::Elevators::Domain
# Rails.application.config.middleware.use Apartment::Elevators::Subdomain
# Rails.application.config.middleware.use Apartment::Elevators::FirstSubdomain
# Rails.application.config.middleware.use Apartment::Elevators::Host
