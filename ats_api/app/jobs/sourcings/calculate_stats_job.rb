# frozen_string_literal: true

require "timeout"

module Sourcings
  class CalculateStatsJob < ApplicationJob
    queue_as :default

    EXECUTION_TIMEOUT = 30.seconds
    RECALCULATION_COOLDOWN = 5.minutes

    def perform(sourcing_id, options = {})
      @sourcing_id = sourcing_id
      @options = normalize_options(options)
      @started_at = Process.clock_gettime(Process::CLOCK_MONOTONIC)

      with_logging do
        with_timeout do
          with_tenant { execute }
        end
      end
    end

    private

    def with_tenant
      account_id = @options[:account_id]
      return yield unless account_id

      account = Account.find_by(id: account_id)
      return yield unless account&.tenant.present?

      Apartment::Tenant.switch(account.tenant) { yield }
    end

    def execute
      sourcing = find_sourcing
      return skip(:not_found) unless sourcing

      with_lock(sourcing) do
        return skip(:recently_calculated) if skip_recent_calculation?(sourcing)

        calculate_stats(sourcing)
      end
    end

    def find_sourcing
      Sourcing.find_by(id: @sourcing_id)
    end

    def with_lock(sourcing)
      sourcing.with_lock do
        yield
      end
    end

    def calculate_stats(sourcing)
      log_step(:calculating)
      stats = sourcing.refresh_aggregated_stats!
      log_step(:completed, stats: stats_summary(stats))
      stats
    end

    def skip_recent_calculation?(sourcing)
      return false if @options[:force]

      calculated_at = parsed_calculated_at(sourcing)
      calculated_at && calculated_at > RECALCULATION_COOLDOWN.ago
    end

    def parsed_calculated_at(sourcing)
      value = sourcing.aggregated_stats&.fetch("calculated_at", nil)
      return if value.blank?

      Time.zone.parse(value)
    rescue ArgumentError, TypeError
      nil
    end

    def stats_summary(stats)
      return {} if stats.blank?

      {
        total: stats.dig(:counts, :total) || stats.dig("counts", "total"),
        with_score: stats.dig(:counts, :with_score) || stats.dig("counts", "with_score"),
        avg_score: stats.dig(:score_stats, :average) || stats.dig("score_stats", "average")
      }
    end

    # === Helpers de logging e controle ===

    def with_logging
      log_step(:started)
      yield
    rescue => e
      log_error(e)
      raise
    ensure
      log_step(:finished, duration_ms: elapsed_ms)
    end

    def with_timeout
      Timeout.timeout(EXECUTION_TIMEOUT) { yield }
    rescue Timeout::Error => e
      log_error(e, context: "Job exceeded #{EXECUTION_TIMEOUT}s timeout")
      raise
    end

    def skip(reason)
      log_step(:skipped, reason: reason)
      nil
    end

    def log_step(step, extra = {})
      data = {
        job: self.class.name,
        sourcing_id: @sourcing_id,
        step: step,
        elapsed_ms: elapsed_ms
      }.merge(extra)

      Rails.logger.info("[CalculateStatsJob] #{data.to_json}")
    end

    def log_error(error, extra = {})
      data = {
        job: self.class.name,
        sourcing_id: @sourcing_id,
        error: error.class.name,
        message: error.message,
        elapsed_ms: elapsed_ms
      }.merge(extra)

      Rails.logger.error("[CalculateStatsJob] #{data.to_json}")
      Rails.logger.error(error.backtrace.first(10).join("\n"))
    end

    def elapsed_ms
      ((Process.clock_gettime(Process::CLOCK_MONOTONIC) - @started_at) * 1000).round
    end

    def normalize_options(options)
      return {} unless options.respond_to?(:symbolize_keys)

      options.symbolize_keys
    end
  end
end
