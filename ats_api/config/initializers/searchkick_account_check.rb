# frozen_string_literal: true

Rails.application.config.after_initialize do
  if defined?(Account) && Rails.env.development?
    begin
      Apartment::Tenant.switch("public") do
        index_name = Account.searchkick_index.name

        unless Account.searchkick_index.exists?
          Rails.logger.info "[Searchkick] Account index doesn't exist, creating..."
          Account.reindex
        else
          mapping = Account.searchkick_index.mapping

          unless mapping.dig("properties", "created_at", "type") == "date"
            Rails.logger.warn "[Searchkick] Account index has incorrect mapping for created_at, recreating..."
            Account.searchkick_index.delete
            Account.reindex
          end
        end
      end
    rescue => e
      Rails.logger.error "[Searchkick] Error checking Account index: #{e.message}"
    end
  end
end
