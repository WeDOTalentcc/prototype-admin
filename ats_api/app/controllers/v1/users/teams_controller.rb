module V1
  module Users
    class TeamsController < ApplicationController
      before_action :set_team, only: %i[show update destroy composition]

      def index
        enforce_limit!
        params[:where] ||= {}
        params[:where][:account_id] = @current_user.account_id
        params[:where][:is_active] = true unless params[:where].key?(:is_active)

        perform_search(
          model: Team,
          serializer: TeamSerializer,
          include_aggregators: true
        )
      end

      def show
        render_success(@team, serializer: TeamSerializer)
      end

      def create
        team = Team.new(team_params)
        team.account_id = @current_user.account_id
        if team.save
          render_success(team, serializer: TeamSerializer, status: :created)
        else
          render_error(team)
        end
      end

      def update
        if @team.update(team_params)
          render_success(@team, serializer: TeamSerializer)
        else
          render_error(@team)
        end
      end

      def destroy
        @team.update(is_active: false)
        render_success(@team, serializer: TeamSerializer)
      end

      def composition
        render json: {
          team_id: @team.id,
          composition: @team.current_composition
        }
      end

      private

      def team_params
        params.require(:team).permit(:name, :description, :department_id, :team_lead_id, :member_count, :is_active)
      end

      def set_team
        @team = Team.where(account_id: @current_user.account_id).find(params[:id])
      rescue ActiveRecord::RecordNotFound
        render_not_found("Time")
      end

      def enforce_limit!(max = 100)
        limit_value = params[:limit].presence || params[:per_page].presence
        limit_value = limit_value.to_i if limit_value
        limit_value = max if limit_value.blank? || limit_value <= 0 || limit_value > max
        params[:limit] = limit_value
      end
    end
  end
end
