module WhatsappService
  class MessageRouter
    LOCAL_NUMBER_FALLBACK = ENV["WHATSAPP_LOCAL_NUMBER"]&.gsub(/\D/, "") || "15551924179"
    PRODUCTION_NUMBER_FALLBACK = ENV["WHATSAPP_PRODUCTION_NUMBER"]&.gsub(/\D/, "") || "5511975205003"
    LOCAL_REDIRECT_URL_FALLBACK = ENV["WHATSAPP_LOCAL_REDIRECT_URL"]

    ENVIRONMENT_PROCESSORS = {
      "production" => ->(_phone) { true },
      "development" => ->(_phone) { true },
      "staging" => ->(_phone) { true },
      "test" => ->(_phone) { true }
    }.freeze

    def self.should_redirect_to_local?(sender_phone)
      normalized_phone = normalize_phone(sender_phone)

      if WhatsappConfiguration.table_exists?
        return WhatsappConfiguration.should_redirect?(normalized_phone, Rails.env)
      end

      return false unless Rails.env.development? || ENV["RAILS_ENV_LOCAL_WHATSAPP"] == "true"
      return false if LOCAL_REDIRECT_URL_FALLBACK.blank?

      normalized_phone == LOCAL_NUMBER_FALLBACK
    end

    def self.should_process_locally?(sender_phone)
      normalized_phone = normalize_phone(sender_phone)

      if WhatsappConfiguration.table_exists?
        config = WhatsappConfiguration.find_config(normalized_phone, Rails.env)
        return false if config&.active? && config.redirect_url.present?
        return config&.active? if config
      end

      processor = ENVIRONMENT_PROCESSORS[Rails.env] || ENVIRONMENT_PROCESSORS["staging"]
      processor.call(normalized_phone)
    end

    def self.redirect_to_local(webhook_params, sender_phone = nil)
      redirect_url = get_redirect_url(sender_phone)
      return nil unless redirect_url.present?

      begin
        response = Faraday.post(redirect_url) do |req|
          req.headers["Content-Type"] = "application/json"
          req.body = webhook_params.to_json
        end

        response
      rescue => e
        nil
      end
    end

    def self.get_redirect_url(sender_phone = nil)
      return LOCAL_REDIRECT_URL_FALLBACK unless sender_phone.present?

      if WhatsappConfiguration.table_exists?
        normalized_phone = normalize_phone(sender_phone)
        url = WhatsappConfiguration.redirect_url_for(normalized_phone, Rails.env)
        return url if url.present?
      end

      LOCAL_REDIRECT_URL_FALLBACK
    end

    def self.update_local_url(new_url, developer_name: nil, phone_number: nil, environment: Rails.env)
      return false unless WhatsappConfiguration.table_exists?

      normalized_phone = normalize_phone(phone_number.presence || LOCAL_NUMBER_FALLBACK)
      raise ArgumentError, "phone_number is required" if normalized_phone.blank?

      description = "#{developer_name || 'N/A'} - #{environment.to_s.capitalize} - Updated #{Time.current.strftime('%d/%m %H:%M')}"

      config = WhatsappConfiguration.create_or_update_config(
        normalized_phone,
        environment,
        redirect_url: new_url,
        developer_name: developer_name,
        description: description,
        metadata: { updated_from: "quick_update_url", updated_at: Time.current.iso8601 }
      )

      config
    end

    def self.list_configurations
      return WhatsappConfiguration.search("*", page: 1, per_page: 100) if WhatsappConfiguration.table_exists?

      []
    end

    def self.current_config_summary
      summary = {}

      if WhatsappConfiguration.table_exists?
        configs = WhatsappConfiguration.search("*", page: 1, per_page: 100)
        configs.each do |config|
          key = "#{config.environment}_#{config.phone_number}"
          summary[key] = {
            phone: config.formatted_phone,
            environment: config.environment,
            redirect_url: config.redirect_url,
            developer: config.developer_name,
            description: config.description
          }
        end
      end

      summary[:env_fallback] = {
        local_number: LOCAL_NUMBER_FALLBACK,
        production_number: PRODUCTION_NUMBER_FALLBACK,
        local_redirect_url: LOCAL_REDIRECT_URL_FALLBACK
      }

      summary
    end

    private

    def self.normalize_phone(phone)
      return nil if phone.blank?

      digits = phone.gsub(/\D/, "")
      digits.length == 11 && !digits.start_with?("55") ? "55#{digits}" : digits
    end
  end
end
