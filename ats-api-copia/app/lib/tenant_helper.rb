module TenantHelper
  def switch_tenant(account, staging: false, &block)
    schema = staging ? account.staging_tenant : account.tenant
    Apartment::Tenant.switch!(schema, &block)
  end
end
