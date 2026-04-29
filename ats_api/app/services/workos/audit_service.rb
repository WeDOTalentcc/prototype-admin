module Workos
  class AuditService
    def self.log(action:, user:, resource: nil, metadata: {}, request: nil)
      new(user: user).log(
        action: action,
        resource: resource,
        metadata: metadata,
        request: request
      )
    end

    def initialize(user:)
      @user = user
    end

    def log(action:, resource: nil, metadata: {}, request: nil)
      return unless @user

      audit_log = AuditLog.create!(
        user_id: @user.id,
        account_id: @user.account_id,
        action: action,
        resource_type: resource&.class&.name,
        resource_id: resource&.id,
        metadata: build_metadata(metadata, resource),
        ip_address: extract_ip(request),
        user_agent: extract_user_agent(request)
      )

      sync_to_workos(audit_log) if workos_enabled?

      audit_log
    rescue => e
      Rails.logger.error("[Workos::AuditService] Failed to log: #{e.message}")
      nil
    end

    private

    attr_reader :user

    def build_metadata(custom_metadata, resource)
      base_metadata = {
        user_email: user.email,
        user_name: user.name,
        timestamp: Time.current.iso8601
      }

      if resource
        base_metadata[:resource_changes] = resource.previous_changes if resource.respond_to?(:previous_changes)
      end

      base_metadata.merge(custom_metadata)
    end

    def extract_ip(request)
      return nil unless request

      request.remote_ip || request.headers["X-Forwarded-For"]&.split(",")&.first
    end

    def extract_user_agent(request)
      return nil unless request

      request.headers["User-Agent"]
    end

    def workos_enabled?
      return false unless user&.account

      user.account.workos_enabled?
    end

    def sync_to_workos(audit_log)
      return unless configured?
      return unless user.workos_user_id.present?

      organization_id = user.workos_organization_id.presence || user.account&.workos_organization_id
      return unless organization_id.present?

      idempotency_key = SecureRandom.uuid

      ::WorkOS::AuditLogs.create_event(
        organization: organization_id,
        idempotency_key: idempotency_key,
        event: {
          action: audit_log.action,
          occurred_at: audit_log.created_at.iso8601,
          actor: {
            type: "user",
            id: user.workos_user_id,
            name: user.name,
            email: user.email
          },
          targets: build_targets(audit_log),
          context: {
            location: audit_log.ip_address || "unknown",
            user_agent: audit_log.user_agent
          }.compact,
          metadata: audit_log.metadata
        }
      )

      audit_log.update(workos_event_id: idempotency_key)
    rescue => e
      Rails.logger.error("[Workos::AuditService] Failed to sync to WorkOS: #{e.message}")
    end

    def build_targets(audit_log)
      if audit_log.resource_type && audit_log.resource_id
        return [ { type: audit_log.resource_type.downcase, id: audit_log.resource_id.to_s } ]
      end

      [ { type: "account", id: user.account_id.to_s } ]
    end

    def configured?
      api_key.present?
    end

    def api_key
      ENV["WORKOS_API_KEY"]
    end
  end
end
