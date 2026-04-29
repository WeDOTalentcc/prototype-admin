# frozen_string_literal: true

module Elasticsearch
  class ReindexAllJob
    include Sidekiq::Job

    sidekiq_options queue: :low, retry: 1

    REDIS_KEY = "elasticsearch:reindex_all:progress"

    def perform(scope = "all")
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.info "🔍 [ReindexAllJob] Starting full reindex (scope: #{scope})"
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

      @stats = { successful: 0, skipped: 0, failed: 0, errors: [] }
      @total = calculate_total(scope)
      @processed = 0
      @started_at = Time.current

      update_progress(status: "running", scope: scope)

      reindex_public_models if %w[all public].include?(scope)
      reindex_tenant_models if %w[all tenants].include?(scope)

      update_progress(status: "completed")
      log_summary
    rescue StandardError => e
      Rails.logger.error "❌ [ReindexAllJob] Fatal error: #{e.message}"
      update_progress(status: "failed", error: e.message)
      raise
    end

    def self.progress
      raw = Sidekiq.redis { |r| r.get(REDIS_KEY) }
      return { status: "idle" } unless raw

      JSON.parse(raw, symbolize_names: true)
    end

    private

    def searchable_models
      Rails.application.eager_load! unless Rails.application.config.eager_load
      ApplicationRecord.descendants.select { |m| m.respond_to?(:searchkick_index) }
    end

    def public_model?(model)
      Apartment.excluded_models.map(&:to_s).include?(model.name)
    end

    def calculate_total(scope)
      tenants_count = %w[all tenants].include?(scope) ? Account.count : 0
      tenant_models = searchable_models.reject { |m| public_model?(m) }.size
      public_models = %w[all public].include?(scope) ? searchable_models.count { |m| public_model?(m) } : 0

      public_models + (tenants_count * tenant_models)
    end

    def reindex_public_models
      Rails.logger.info "🔄 [ReindexAllJob] Reindexing public schema models..."

      searchable_models.select { |m| public_model?(m) }.each do |model|
        reindex_model(model, "public")
      end
    end

    def reindex_tenant_models
      tenant_models = searchable_models.reject { |m| public_model?(m) }

      Account.pluck(:tenant).each do |tenant|
        Rails.logger.info "🔄 [ReindexAllJob] Reindexing tenant: #{tenant}"

        Apartment::Tenant.switch(tenant) do
          tenant_models.each do |model|
            reindex_model(model, tenant)
          end
        end
      end
    end

    def reindex_model(model, tenant)
      @processed += 1

      unless table_has_records?(model)
        @stats[:skipped] += 1
        Rails.logger.debug "   ⏭️  #{model.name} (#{tenant}): no records"
        update_progress(current_model: "#{model.name} (#{tenant})", note: "skipped")
        return
      end

      update_progress(current_model: "#{model.name} (#{tenant})")
      model.reindex
      @stats[:successful] += 1
      Rails.logger.info "   ✅ #{model.name} (#{tenant})"
    rescue StandardError => e
      @stats[:failed] += 1
      @stats[:errors] << "#{tenant}/#{model.name}: #{e.message}"
      Rails.logger.error "   ❌ #{model.name} (#{tenant}): #{e.message}"
    end

    def table_has_records?(model)
      return false unless model.table_exists?

      model.unscoped.exists?
    rescue StandardError
      false
    end

    def update_progress(extra = {})
      elapsed = Time.current - @started_at
      pct = @total.positive? ? ((@processed.to_f / @total) * 100).round(1) : 0

      data = {
        status: extra[:status] || "running",
        processed: @processed,
        total: @total,
        percent: pct,
        successful: @stats[:successful],
        skipped: @stats[:skipped],
        failed: @stats[:failed],
        elapsed_seconds: elapsed.round(1),
        current_model: extra[:current_model],
        updated_at: Time.current.iso8601
      }.compact

      Sidekiq.redis do |r|
        r.set(REDIS_KEY, data.to_json)
        r.expire(REDIS_KEY, 3600)
      end
    end

    def log_summary
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.info "✅ [ReindexAllJob] Reindex complete in #{(Time.current - @started_at).round(1)}s"
      Rails.logger.info "   ✅ Successful: #{@stats[:successful]}"
      Rails.logger.info "   ⏭️  Skipped: #{@stats[:skipped]}"
      Rails.logger.info "   ❌ Failed: #{@stats[:failed]}"
      if @stats[:errors].any?
        Rails.logger.info "   Errors:"
        @stats[:errors].first(20).each { |e| Rails.logger.info "     - #{e}" }
      end
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    end
  end
end
