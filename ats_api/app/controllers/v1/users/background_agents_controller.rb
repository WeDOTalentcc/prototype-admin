# frozen_string_literal: true

module V1
  module Users
    class BackgroundAgentsController < ApplicationController
      include RenderDefault

      before_action :authorize_request
      before_action :set_background_agent, only: %i[show update destroy]
      before_action :set_target_for_create, only: %i[create]

      def index
        agents = current_account_agents
          .includes(:job, :list, :agent_cycles)
          .order(created_at: :desc)

        agents = agents.where(job_id: where_params[:job_id]) if where_params[:job_id].present?
        agents = agents.where(list_id: where_params[:list_id]) if where_params[:list_id].present?
        agents = agents.where(target_type: where_params[:target_type]) if where_params[:target_type].present?
        agents = agents.where(status: where_params[:status]) if where_params[:status].present?

        render_success(agents, serializer: BackgroundAgentSerializer)
      end

      def show
        render_success(@background_agent, serializer: BackgroundAgentSerializer)
      end

      def create
        permitted = agent_params
        permitted[:target_type] = permitted[:list_id].present? ? "List" : "Job"
        permitted[:name] = default_agent_name(permitted) if permitted[:name].blank?
        permitted[:mode] = "review" unless BackgroundAgent::MODES.include?(permitted[:mode])

        agent = BackgroundAgent.new(
          permitted.merge(user: @current_user, account: @current_user.account)
        )

        return render_error(agent, status: :unprocessable_entity) unless agent.save

        BackgroundAgents::SetupJob.perform_in(2, agent.id, @current_user.account_id)
        render_success(agent, serializer: BackgroundAgentSerializer, status: :created)
      end

      def update
        return render_error(@background_agent, status: :unprocessable_entity) unless @background_agent.update(agent_params)

        render_success(@background_agent, serializer: BackgroundAgentSerializer)
      end

      def destroy
        @background_agent.agent_cycles.running.update_all(status: "cancelled")
        @background_agent.update!(is_deleted: true, status: "stopped", stopped_at: Time.current)
        render_success(@background_agent, serializer: BackgroundAgentSerializer)
      end

      private

      def set_target_for_create
        @job = Job.find_by(id: params.dig(:background_agent, :job_id))
        @list = List.find_by(id: params.dig(:background_agent, :list_id))
      end

      def default_agent_name(permitted)
        if permitted[:list_id].present?
          @list&.name || "Agent #{Time.current.strftime('%d/%m %H:%M')}"
        else
          @job&.title || "Agent #{Time.current.strftime('%d/%m %H:%M')}"
        end
      end

      def set_background_agent
        scope = BackgroundAgent.where(is_deleted: false, account: @current_user.account)
        @background_agent = scope.find_by(id: params[:id])
        render_not_found("BackgroundAgent") unless @background_agent
      end

      def current_account_agents
        BackgroundAgent.where(account: @current_user.account, is_deleted: false)
      end

      def agent_params
        params.require(:background_agent).permit(
          :name, :job_id, :list_id, :criteria_text, :mode, :daily_limit,
          :min_score_threshold, :auto_pause_days,
          sources: [],
          search_iteration_config: [
            :max_search_iterations, :min_quality_score, :min_candidates_target,
            enabled_providers: [],
            provider_config: {}
          ]
        )
      end

      def where_params
        return {} unless params[:where].present?

        parsed = params[:where].is_a?(String) ? JSON.parse(params[:where]).symbolize_keys : params[:where].to_unsafe_h.symbolize_keys
        parsed.slice(:job_id, :list_id, :target_type, :status, :is_deleted)
      rescue JSON::ParserError
        {}
      end
    end
  end
end
