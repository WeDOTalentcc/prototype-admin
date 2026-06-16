# frozen_string_literal: true

module AtsSync
  class BaseService
    attr_reader :record, :client

    def initialize(record)
      @record = record
      @client = ApiClient.new
    end

    def sync
      return log_skip("sync disabled") unless AtsSync.config.enabled?
      return log_skip("no ATS provider") unless ats_provider.present?

      validation_error = validate_required_data
      return log_skip(validation_error) if validation_error

      start_time = Time.current
      log_start

      payload = build_payload
      response = execute_sync(payload)

      save_ats_ids(response.ats_ids)

      duration = (Time.current - start_time).round(3)
      log_success(response, duration)

      response
    rescue AtsSync::ApiClient::ApiError => e
      duration = (Time.current - start_time).round(3)
      log_error(e, duration)
      raise
    end

    private

    def execute_sync(_payload)
      raise NotImplementedError, "Subclass must implement #execute_sync"
    end

    def ats_provider
      raise NotImplementedError, "Subclass must implement #ats_provider"
    end

    def build_payload
      raise NotImplementedError, "Subclass must implement #build_payload"
    end

    def save_ats_ids(_ats_ids)
      raise NotImplementedError, "Subclass must implement #save_ats_ids"
    end

    def validate_required_data
      nil
    end

    def log_start
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.info "🔄 [ATS_SYNC] Starting sync"
      Rails.logger.info "   Record: #{record.class.name}##{record.id}"
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    end

    def log_success(response, duration)
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.info "✅ [ATS_SYNC] Success"
      Rails.logger.info "   Record: #{record.class.name}##{record.id}"
      Rails.logger.info "   Message: #{response.message}"
      Rails.logger.info "   Warnings: #{response.warnings.count}"
      Rails.logger.info "   ⏱️  Duration: #{duration}s"
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    end

    def log_error(error, duration)
      Rails.logger.error "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.error "❌ [ATS_SYNC] Error"
      Rails.logger.error "   Record: #{record.class.name}##{record.id}"
      Rails.logger.error "   Error: #{error.class.name}"
      Rails.logger.error "   Message: #{error.message}"
      Rails.logger.error "   ⏱️  Duration: #{duration}s"
      Rails.logger.error "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    end

    def log_skip(reason)
      Rails.logger.warn "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.warn "⏭️  [ATS_SYNC] Skipped sync"
      Rails.logger.warn "   Record: #{record.class.name}##{record.id}"
      Rails.logger.warn "   Reason: #{reason}"
      Rails.logger.warn "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      nil
    end
  end
end
