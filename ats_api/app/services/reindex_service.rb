class ReindexService
  def self.call(tenant, async: true)
    Apartment::Tenant.switch!(tenant)
    Rails.application.eager_load!

    excluded_model_names = Apartment.excluded_models

    models_to_reindex = ApplicationRecord.descendants.select do |model|
      next false unless model.respond_to?(:reindex)
      next false if tenant != "public" && excluded_model_names.include?(model.name)

      true
    end

    models_to_reindex.each do |model|
      begin
        next if model.count.zero?

        Rails.logger.info "-> Reindexing #{model.name}..."

        if async
          model.reindex(mode: :async, refresh: false)
        else
          model.reindex
        end
      rescue Sidekiq::Shutdown
        raise
      rescue StandardError => e
        Rails.logger.warn "Failed to reindex #{model.name}: #{e.message}"
      end
    end
  end
end
