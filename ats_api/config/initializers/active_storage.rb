Rails.application.config.to_prepare do
  ActiveStorage::Current.url_options = {
    host: ENV.fetch("APP_HOST", "localhost"),
    port: ENV.fetch("APP_PORT", 8080),
    protocol: ENV.fetch("APP_PROTOCOL", "http")
  }

  ActiveStorage::Blob.class_eval do
    private

    def generate_key_with_tenant_prefix
      token = self.class.generate_unique_secure_token(length: self.class::MINIMUM_TOKEN_LENGTH)
      tenant = Apartment::Tenant.current

      if tenant.present? && tenant != "public"
        "#{tenant}/#{token}"
      else
        token
      end
    end
  end

  ActiveStorage::Blob.before_create do
    self[:key] ||= generate_key_with_tenant_prefix
  end
end
