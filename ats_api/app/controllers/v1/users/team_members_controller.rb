module V1
  module Users
    class TeamMembersController < ApplicationController
      before_action :set_team

      def index
        enforce_limit!
        params[:where] ||= {}
        params[:where][:account_id] = @current_user.account_id
        params[:where][:team_id] = @team.id

        include_inactive = ActiveModel::Type::Boolean.new.cast(params[:include_inactive])
        params[:where][:is_active] = true unless include_inactive || params[:where].key?(:is_active)

        perform_search(
          model: TeamMember,
          serializer: TeamMemberSerializer,
          include_aggregators: true
        )
      end

      def create
        attributes = team_member_params.to_h.symbolize_keys
        user_id = attributes.delete(:user_id)
        return render_simple_error("Usuário obrigatório") unless user_id
        member = @team.team_members.new(attributes)
        member.account_id = @current_user.account_id
        member.joined_at ||= Date.current
        member.user = User.where(id: user_id, account_id: @current_user.account_id).first

        return render_simple_error("Usuário não encontrado") unless member.user

        if member.save
          update_member_count
          render_success(member, serializer: TeamMemberSerializer, status: :created)
        else
          render_error(member)
        end
      end

      def destroy
        member = @team.team_members.find(params[:id])
        if member.update(is_active: false, left_at: Date.current)
          update_member_count
          render_success(member, serializer: TeamMemberSerializer)
        else
          render_error(member)
        end
      end

      private

      def set_team
        @team = Team.where(account_id: @current_user.account_id).find(params[:team_id])
      rescue ActiveRecord::RecordNotFound
        render_not_found("Time")
      end

      def team_member_params
        params.require(:team_member).permit(:user_id, :role, :joined_at, :left_at, :is_active, :name, :email, :phone, :position, :linkedin_url)
      end

      def update_member_count
        active_count = @team.team_members.where(is_active: true).count
        @team.update(member_count: active_count)
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
