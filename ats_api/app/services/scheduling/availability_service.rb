# frozen_string_literal: true

module Scheduling
  class AvailabilityService
    SCHEDULE_ENDPOINT = "/me/calendar/getSchedule"

    def initialize(user:)
      @user = user
      @settings = user.scheduling_setting
    end

    def available_slots(date:, duration_minutes: nil)
      duration = duration_minutes || @settings&.default_duration_minutes || 60
      target_date = date.to_date

      return { slots: [], busy_periods: [] } unless within_lookahead?(target_date)

      cached = fetch_cached(target_date)
      return cached.all_slots if cached&.fresh?

      busy_periods = fetch_busy_periods(target_date)
      slots = generate_slots(target_date, duration, busy_periods)
      cache_slots(target_date, slots, busy_periods)

      { slots: slots, busy_periods: format_busy_periods(busy_periods) }
    end

    def available_slots_for_range(start_date:, end_date:, duration_minutes: nil)
      result = { slots: [], busy_periods: [] }

      (start_date.to_date..end_date.to_date).each do |date|
        day_result = available_slots(date: date, duration_minutes: duration_minutes)

        day_result[:slots].each do |slot|
          result[:slots] << slot.merge(date: date.iso8601)
        end

        day_result[:busy_periods].each do |bp|
          result[:busy_periods] << bp.merge(date: date.iso8601)
        end
      end

      result
    end

    private

    attr_reader :user, :settings

    def within_lookahead?(date)
      lookahead = settings&.lookahead_days || 14
      date <= Date.current + lookahead.days
    end

    def fetch_cached(date)
      CachedAvailability.find_by(user: user, date: date)
    end

    def cache_slots(date, slots, busy_periods)
      CachedAvailability.find_or_initialize_by(user: user, date: date).tap do |cache|
        cache.slots_data = {
          "slots" => slots,
          "busy_periods" => format_busy_periods(busy_periods)
        }
        cache.fetched_at = Time.current
        cache.save!
      end
    rescue ActiveRecord::RecordNotUnique
      retry
    end

    def fetch_busy_periods(date)
      timezone = settings&.timezone || "America/Sao_Paulo"
      zone = ActiveSupport::TimeZone[timezone]
      day_start = zone.parse("#{date} 00:00:00")
      day_end = zone.parse("#{date} 23:59:59")

      body = {
        schedules: [ user.email ],
        startTime: { dateTime: day_start.utc.iso8601, timeZone: "UTC" },
        endTime: { dateTime: day_end.utc.iso8601, timeZone: "UTC" },
        availabilityViewInterval: 15
      }

      response = MicrosoftService::Api.post(SCHEDULE_ENDPOINT, user, body: body)
      parse_busy_periods(response)
    rescue StandardError => e
      Rails.logger.error "❌ [AvailabilityService] Failed to fetch busy periods: #{e.message}"
      []
    end

    def parse_busy_periods(response)
      return [] unless response.is_a?(Hash)

      schedules = response.dig("value") || []
      return [] if schedules.empty?

      schedule_items = schedules.first&.dig("scheduleItems") || []
      schedule_items.map do |item|
        {
          start: Time.parse(item.dig("start", "dateTime")),
          end: Time.parse(item.dig("end", "dateTime"))
        }
      end
    end

    def generate_slots(date, duration, busy_periods)
      timezone = settings&.timezone || "America/Sao_Paulo"
      zone = ActiveSupport::TimeZone[timezone]

      work_start = settings&.work_hours_start
      work_end = settings&.work_hours_end
      buffer = settings&.buffer_minutes || 15

      start_hour = work_start.respond_to?(:hour) ? work_start.hour : 9
      start_min = work_start.respond_to?(:min) ? work_start.min : 0
      end_hour = work_end.respond_to?(:hour) ? work_end.hour : 18
      end_min = work_end.respond_to?(:min) ? work_end.min : 0

      slot_start = zone.parse("#{date} #{format('%02d:%02d', start_hour, start_min)}")
      day_end = zone.parse("#{date} #{format('%02d:%02d', end_hour, end_min)}")

      slots = []
      while slot_start + duration.minutes <= day_end
        slot_end = slot_start + duration.minutes
        status = slot_status(slot_start, slot_end, busy_periods)

        slots << {
          start_time: slot_start.iso8601,
          end_time: slot_end.iso8601,
          status: status
        }

        slot_start = slot_end + buffer.minutes
      end

      slots
    end

    def slot_status(slot_start, slot_end, busy_periods)
      return "past" if slot_start < Time.current
      return "busy" if overlaps_busy?(slot_start, slot_end, busy_periods)

      "available"
    end

    def overlaps_busy?(slot_start, slot_end, busy_periods)
      busy_periods.any? do |busy|
        slot_start < busy[:end] && slot_end > busy[:start]
      end
    end

    def format_busy_periods(busy_periods)
      busy_periods.map do |bp|
        {
          start_time: bp[:start].iso8601,
          end_time: bp[:end].iso8601
        }
      end
    end
  end
end
