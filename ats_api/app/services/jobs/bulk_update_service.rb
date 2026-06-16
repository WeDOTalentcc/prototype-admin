# frozen_string_literal: true

module Jobs
  class BulkUpdateService
    ALLOWED_FIELDS = %w[
      hiring_manager_id department_id job_status_id priority urgency_level
      is_urgent workplace_type employment_type seniority user_id
    ].freeze

    BATCH_SIZE = 50

    def initialize(job_ids:, fields:, user:)
      @job_ids = job_ids
      @fields = sanitize_fields(fields)
      @user = user
      @batch_id = SecureRandom.uuid
    end

    def call
      return error("Nenhum campo válido informado") if fields.empty?
      return error("Nenhuma vaga informada") if job_ids.blank?

      results = process_updates
      success(results)
    end

    attr_reader :batch_id

    private

    attr_reader :job_ids, :fields, :user

    def sanitize_fields(raw_fields)
      return {} unless raw_fields.is_a?(Hash)

      raw_fields.stringify_keys.slice(*ALLOWED_FIELDS)
    end

    def process_updates
      updated = 0
      failed = 0
      errors_list = []

      Job.where(id: job_ids, is_deleted: false).find_each(batch_size: BATCH_SIZE) do |job|
        job.log_activity_with_category("bulk_update:#{batch_id}") do
          job.update!(fields)
        end
        updated += 1
      rescue StandardError => e
        failed += 1
        errors_list << { job_id: job.id, error: e.message }
      end

      { updated: updated, failed: failed, errors: errors_list, batch_id: batch_id }
    end

    def success(results)
      { success: true, **results }
    end

    def error(message)
      { success: false, error: message }
    end
  end
end
