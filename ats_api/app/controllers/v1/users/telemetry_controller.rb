# frozen_string_literal: true

module V1
  module Users
    class TelemetryController < ApplicationController
      MAX_EVENTS_PER_BATCH = 50
      MAX_META_BYTES = 4_000
      ALLOWED_LEVELS = %w[debug info warn error].freeze

      def create
        events = Array(params[:events])
        return head :no_content if events.empty?
        return render(json: { error: "too_many_events", max: MAX_EVENTS_PER_BATCH }, status: :payload_too_large) if events.size > MAX_EVENTS_PER_BATCH

        session_id = sanitized(params[:session_id])
        user_agent = request.user_agent.to_s[0, 200]
        remote_ip = request.remote_ip
        user_id = @current_user&.id

        lines = events.map { |raw| build_line(raw, session_id: session_id, user_agent: user_agent, remote_ip: remote_ip, user_id: user_id) }

        Thread.new { lines.each { |level, line| Rails.logger.public_send(level, line) } }

        head :no_content
      end

      private

      def build_line(raw, session_id:, user_agent:, remote_ip:, user_id:)
        level = ALLOWED_LEVELS.include?(raw[:level]) ? raw[:level] : "info"
        event = sanitized(raw[:event]) || "unknown"
        route = sanitized(raw[:route])
        ts = sanitized(raw[:ts])
        meta = truncate_meta(raw[:meta])

        line = [
          "[FE]",
          "[#{level}]",
          event,
          meta.presence && meta.to_json,
          route && "route=#{route}",
          user_id && "user=#{user_id}",
          session_id && "session=#{session_id}",
          ts && "client_ts=#{ts}",
          "ip=#{remote_ip}",
          "ua=\"#{user_agent}\""
        ].compact.join(" ")

        [ level, line ]
      end

      def sanitized(value)
        return nil if value.nil?
        str = value.to_s
        return nil if str.empty?
        str.gsub(/[\r\n\t]/, " ")[0, 500]
      end

      def truncate_meta(meta)
        return nil unless meta.is_a?(ActionController::Parameters) || meta.is_a?(Hash)
        hash = meta.respond_to?(:to_unsafe_h) ? meta.to_unsafe_h : meta
        json = hash.to_json
        return hash if json.bytesize <= MAX_META_BYTES
        { _truncated: true, bytes: json.bytesize }
      end
    end
  end
end
