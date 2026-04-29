# frozen_string_literal: true

module Jobs
  class PipelineHealthService
    BOTTLENECK_THRESHOLD_DAYS = 5
    CONVERSION_THRESHOLD = 0.5

    def initialize(job_ids: nil, include_inactive: false, aging_threshold_days: nil, limit: nil)
      @job_ids = job_ids ? Array(job_ids).compact.uniq.map(&:to_i) : nil
      @include_inactive = include_inactive
      @aging_threshold_days = aging_threshold_days&.to_i || BOTTLENECK_THRESHOLD_DAYS
      @limit = limit&.to_i
    end

    def call
      jobs = load_jobs
      return { success: true, data: [], meta: { total: 0 } } if jobs.empty?

      results = jobs.map { |job| compute_job_health(job) }.compact

      {
        success: true,
        data: results,
        meta: { total: results.size, aging_threshold_days: @aging_threshold_days, computed_at: Time.current.iso8601 }
      }
    rescue StandardError => e
      Rails.logger.error "[Jobs::PipelineHealthService] Error: #{e.message}"
      Rails.logger.error e.backtrace.first(5).join("\n")
      { success: false, error: e.message }
    end

    private

    attr_reader :job_ids

    def load_jobs
      scope = @job_ids ? Job.where(id: @job_ids) : Job.where(is_deleted: false)
      scope = scope.where(is_active: true) unless @include_inactive
      scope = scope.limit(@limit) if @limit
      scope.includes(:selective_processes, :applies)
    end

    def compute_job_health(job)
      applies_scope = job.applies.where(is_deleted: false)
      total_candidates = applies_scope.count

      return nil if total_candidates.zero?

      stages_data = build_stages_health(job, applies_scope)
      bottleneck = find_bottleneck_stage(stages_data)

      conversion_rate = compute_conversion_rate(stages_data)
      rejection_rate = compute_rejection_rate(stages_data, total_candidates)
      avg_time_to_hire = compute_avg_time_to_hire(applies_scope)

      {
        job_id: job.id,
        title: job.title,
        external_id: job.external_id,
        is_active: job.is_active,
        total_candidates: total_candidates,
        by_stage: stages_data,
        bottleneck_stage: bottleneck,
        conversion_rate: conversion_rate,
        rejection_rate: rejection_rate,
        avg_time_to_hire_days: avg_time_to_hire,
        health_score: compute_health_score(stages_data, conversion_rate, avg_time_to_hire)
      }
    end

    def build_stages_health(job, applies_scope)
      stages = job.selective_processes.where(is_deleted: false).order(:position)
      apply_ids = applies_scope.pluck(:id)

      return [] if apply_ids.empty?

      transitions = load_transitions(apply_ids)
      stage_metrics = compute_stage_metrics(transitions, applies_scope)

      stages.map do |stage|
        metrics = stage_metrics[stage.id] || {}
        avg_days = (metrics[:avg_hours] || 0) / 24.0

        {
          stage_id: stage.id,
          stage: stage.name,
          status: stage.status,
          position: stage.position,
          count: metrics[:current_count] || 0,
          avg_days: avg_days.round(2),
          median_days: ((metrics[:median_hours] || 0) / 24.0).round(2),
          max_days: ((metrics[:max_hours] || 0) / 24.0).round(2),
          conversion_rate: metrics[:conversion_rate] || 0.0,
          is_bottleneck: is_bottleneck?(avg_days, metrics[:conversion_rate] || 0.0)
        }
      end
    end

    def load_transitions(apply_ids)
      ApplyStatus
        .where(apply_id: apply_ids, is_deleted: false)
        .joins("INNER JOIN selective_processes ON selective_processes.id = apply_statuses.selective_process_id")
        .select(
          "apply_statuses.apply_id",
          "apply_statuses.selective_process_id",
          "apply_statuses.created_at",
          "selective_processes.position AS stage_position",
          "selective_processes.status AS stage_status"
        )
        .order("apply_statuses.apply_id, apply_statuses.created_at")
    end

    def compute_stage_metrics(transitions, applies_scope)
      metrics = Hash.new { |h, k| h[k] = { times: [], entered: 0, exited: 0 } }
      current_counts = applies_scope.group(:selective_process_id).count

      by_apply = transitions.group_by(&:apply_id)

      by_apply.each_value do |statuses|
        statuses.each_cons(2) do |current, nxt|
          duration_hours = (nxt.created_at - current.created_at) / 1.hour
          metrics[current.selective_process_id][:times] << duration_hours
          metrics[current.selective_process_id][:exited] += 1
        end

        statuses.each do |s|
          metrics[s.selective_process_id][:entered] += 1
        end
      end

      metrics.each do |sp_id, data|
        data[:current_count] = current_counts[sp_id] || 0
        times = data[:times]
        data[:avg_hours] = times.any? ? (times.sum / times.size).round(2) : 0
        data[:median_hours] = times.any? ? percentile(times, 50) : 0
        data[:max_hours] = times.any? ? times.max.round(2) : 0

        entered = data[:entered]
        exited = data[:exited]
        data[:conversion_rate] = entered.positive? ? ((exited.to_f / entered) * 100).round(2) : 0.0
      end

      metrics
    end

    def is_bottleneck?(avg_days, conversion_rate)
      avg_days > @aging_threshold_days || (conversion_rate < (CONVERSION_THRESHOLD * 100))
    end

    def find_bottleneck_stage(stages_data)
      advancing_stages = stages_data.reject { |s| s[:status].to_s.in?(%w[rejected hired]) }
      return nil if advancing_stages.empty?

      bottleneck = advancing_stages.max_by { |s| s[:avg_days] }
      bottleneck[:is_bottleneck] ? bottleneck[:stage] : nil
    end

    def compute_conversion_rate(stages_data)
      first_stage = stages_data.first
      last_stage = stages_data.find { |s| s[:status] == "hired" }

      return 0.0 unless first_stage && last_stage

      first_count = first_stage[:count]
      return 0.0 if first_count.zero?

      ((last_stage[:count].to_f / first_count) * 100).round(2)
    end

    def compute_rejection_rate(stages_data, total_candidates)
      rejected_stage = stages_data.find { |s| s[:status] == "rejected" }
      return 0.0 unless rejected_stage

      rejected_count = rejected_stage[:count]
      return 0.0 if total_candidates.zero?

      ((rejected_count.to_f / total_candidates) * 100).round(2)
    end

    def compute_avg_time_to_hire(applies_scope)
      result = applies_scope.joins(:selective_process)
        .where(selective_processes: { status: "hired" })
        .pick(Arel.sql("AVG(EXTRACT(EPOCH FROM (applies.updated_at - applies.created_at)) / 86400.0)"))

      result&.round(2)
    end

    def compute_health_score(stages_data, conversion_rate, avg_time_to_hire)
      bottleneck_count = stages_data.count { |s| s[:is_bottleneck] }
      bottleneck_penalty = bottleneck_count * 15

      conversion_score = [ conversion_rate, 100 ].min
      time_score = avg_time_to_hire ? [ 100 - (avg_time_to_hire * 2), 0 ].max : 50

      score = (conversion_score * 0.5 + time_score * 0.5 - bottleneck_penalty).round(2)
      [ score, 0 ].max
    end

    def percentile(values, pct)
      return nil if values.blank?

      sorted = values.sort
      k = ((pct / 100.0) * (sorted.size - 1)).round
      sorted[k]&.round(2)
    end
  end
end
