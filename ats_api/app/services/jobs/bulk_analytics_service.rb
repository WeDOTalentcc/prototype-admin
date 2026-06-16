# frozen_string_literal: true

module Jobs
  class BulkAnalyticsService
    MAX_JOBS = 50

    def initialize(job_ids: nil, where: nil, force_refresh: false, limit: nil)
      @job_ids = job_ids ? Array(job_ids).compact.uniq.map(&:to_i) : nil
      @where_filters = where || {}
      @force_refresh = force_refresh
      @limit = [ limit&.to_i || MAX_JOBS, MAX_JOBS ].min
    end

    def call
      return { success: false, error: "No job IDs or filters provided" } if @job_ids.blank? && @where_filters.blank?

      jobs = load_jobs
      return { success: false, error: "No jobs found" } if jobs.empty?

      analytics_data = compute_bulk_analytics(jobs)

      {
        success: true,
        data: analytics_data,
        meta: {
          requested_count: @job_ids&.size || jobs.size,
          found_count: jobs.size,
          computed_at: Time.current.iso8601
        }
      }
    rescue StandardError => e
      Rails.logger.error "[Jobs::BulkAnalyticsService] Error: #{e.message}"
      Rails.logger.error e.backtrace.first(5).join("\n")
      { success: false, error: e.message }
    end

    private

    attr_reader :job_ids

    def load_jobs
      scope = Job.where(is_deleted: false)
      scope = scope.where(id: @job_ids) if @job_ids.present?
      scope = scope.where(is_active: @where_filters[:is_active]) if @where_filters.key?(:is_active)
      scope = scope.where(user_id: @where_filters[:user_id]) if @where_filters[:user_id].present?
      scope = scope.where(company_id: @where_filters[:company_id]) if @where_filters[:company_id].present?
      scope = scope.where(department_id: @where_filters[:department_id]) if @where_filters[:department_id].present?
      scope.limit(@limit)
    end

    def compute_bulk_analytics(jobs)
      {
        jobs: jobs.map { |job| build_job_entry(job) }
      }
    end

    def build_job_entry(job)
      analytics = fetch_job_analytics(job)
      {
        job_id: job.id,
        title: job.title,
        applies_count: job.total_applies_count,
        is_active: job.is_active,
        funnel: analytics.dig(:funnel) || {},
        overview: analytics.dig(:overview) || {},
        velocity: analytics.dig(:velocity) || {},
        quality: analytics.dig(:quality) || {},
        computed_at: analytics[:computed_at]
      }
    end

    def fetch_job_analytics(job)
      Jobs::AnalyticsService.new(job: job, force_refresh: @force_refresh).call
    rescue StandardError => e
      Rails.logger.error "[Jobs::BulkAnalyticsService] Failed for Job##{job.id}: #{e.message}"
      { error: e.message, job_id: job.id }
    end
  end
end
