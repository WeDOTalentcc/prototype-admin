# frozen_string_literal: true

module Meetings
  class StatsService
    def initialize(start_date:, end_date:, job_id: nil, organizer_id: nil)
      @start_date = start_date
      @end_date = end_date
      @job_id = job_id
      @organizer_id = organizer_id
    end

    def call
      {
        totals: build_totals,
        by_sub_status: count_by_sub_status,
        by_provider: count_by_provider,
        by_period: count_by_period,
        no_show_rate: calculate_rate("no_show"),
        cancellation_rate: cancellation_rate,
        avg_per_week: average_per_week,
        upcoming_24h: upcoming_24h_count,
        period: { start_date: @start_date.to_s, end_date: @end_date.to_s }
      }
    end

    private

    def base_meeting_scope
      scope = Meeting.where(is_deleted: false)
                     .where(start_time: @start_date.beginning_of_day..@end_date.end_of_day)
      scope = scope.where(job_id: @job_id) if @job_id
      scope = scope.where(organizer_id: @organizer_id) if @organizer_id
      scope
    end

    def base_calendar_scope
      scope = CalendarEvent.where(is_deleted: false, is_cancelled: false, event_type: "interview")
                           .where(start_time: @start_date.beginning_of_day..@end_date.end_of_day)
      scope = scope.where(job_id: @job_id) if @job_id
      scope = scope.where(organizer_id: @organizer_id) if @organizer_id
      scope
    end

    def build_totals
      meetings = base_meeting_scope
      total = meetings.count
      sub_status_counts = meetings.group(:sub_status).count

      {
        total: total,
        completed: sub_status_counts["completed"] || 0,
        scheduled: sub_status_counts["scheduled"] || 0,
        cancelled: base_meeting_scope.unscope(where: :is_deleted).where(is_deleted: true).count,
        no_show: sub_status_counts["no_show"] || 0
      }
    end

    def count_by_sub_status
      base_meeting_scope.group(:sub_status).count.transform_keys { |k| k || "unknown" }
    end

    def count_by_provider
      base_meeting_scope.group(:provider).count
    end

    def count_by_period
      base_meeting_scope
        .group(Arel.sql("DATE_TRUNC('week', start_time)::date"))
        .order(Arel.sql("DATE_TRUNC('week', start_time)::date"))
        .count
        .map do |week, total|
          week_scope = base_meeting_scope.where(start_time: week.beginning_of_week..week.end_of_week)
          sub_counts = week_scope.group(:sub_status).count

          {
            week: week.to_s,
            total: total,
            completed: sub_counts["completed"] || 0,
            no_show: sub_counts["no_show"] || 0,
            cancelled: 0
          }
        end
    end

    def calculate_rate(sub_status)
      total = base_meeting_scope.count
      return 0.0 if total.zero?

      count = base_meeting_scope.where(sub_status: sub_status).count
      (count.to_f / total).round(3)
    end

    def cancellation_rate
      all_meetings = Meeting.where(start_time: @start_date.beginning_of_day..@end_date.end_of_day)
      all_meetings = all_meetings.where(job_id: @job_id) if @job_id
      all_meetings = all_meetings.where(organizer_id: @organizer_id) if @organizer_id

      total = all_meetings.count
      return 0.0 if total.zero?

      cancelled = all_meetings.where(is_deleted: true).count
      (cancelled.to_f / total).round(3)
    end

    def average_per_week
      weeks = ((@end_date - @start_date).to_f / 7).ceil
      return 0.0 if weeks.zero?

      total = base_meeting_scope.count
      (total.to_f / weeks).round(2)
    end

    def upcoming_24h_count
      Meeting.where(is_deleted: false)
             .where(start_time: Time.current..24.hours.from_now)
             .then { |s| @job_id ? s.where(job_id: @job_id) : s }
             .then { |s| @organizer_id ? s.where(organizer_id: @organizer_id) : s }
             .count
    end
  end
end
