# frozen_string_literal: true

module V1
  module Users
    class AgentCyclesController < ApplicationController
      include RenderDefault

      before_action :authorize_request
      before_action :set_background_agent
      before_action :set_cycle, only: [:show]

      def index
        per_page = (params[:per_page] || 20).to_i
        page = (params[:page] || 1).to_i
        offset = (page - 1) * per_page

        cycles = @background_agent.agent_cycles
          .includes(:agent_feedbacks)
          .order(cycle_number: :desc)
          .limit(per_page)
          .offset(offset)

        render_success(cycles, serializer: AgentCycleSerializer)
      end

      def show
        render_success(@cycle, serializer: AgentCycleSerializer)
      end

      private

      def set_background_agent
        @background_agent = BackgroundAgent.where(account: @current_user.account, is_deleted: false)
                                           .find_by(id: params[:background_agent_id])
        render_not_found("BackgroundAgent") unless @background_agent
      end

      def set_cycle
        @cycle = @background_agent.agent_cycles.find_by(id: params[:id])
        render_not_found("AgentCycle") unless @cycle
      end
    end
  end
end
