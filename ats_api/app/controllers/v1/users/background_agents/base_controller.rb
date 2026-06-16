# frozen_string_literal: true

module V1
  module Users
    module BackgroundAgents
      class BaseController < ApplicationController
        include RenderDefault

        before_action :authorize_request

        private

        def require_service_token
          return if service_request?

          render_forbidden("Service token required")
        end

        def set_background_agent
          scope = BackgroundAgent.where(is_deleted: false)
          scope = scope.where(account: @current_user.account) if @current_user && !service_request?
          @background_agent = scope.find_by(id: params[:background_agent_id].presence || params[:id])
          render_not_found("BackgroundAgent") unless @background_agent
        end

        def current_account_agents
          BackgroundAgent.where(account: @current_user.account, is_deleted: false)
        end

        def service_request?
          %w[service one_time_token].include?(@jwt_payload&.dig(:role).to_s)
        end

        def safe_jsonb_param(param, max_bytes: 50_000)
          return {} unless param.present?

          raw = param.respond_to?(:to_unsafe_h) ? param.to_unsafe_h : param.to_h
          return {} if raw.to_json.bytesize > max_bytes

          raw.deep_stringify_keys
        end
      end
    end
  end
end
