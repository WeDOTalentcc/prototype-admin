module V1
  module Users
    class SkillsController < ApplicationController
      before_action :set_skill, only: %i[show update destroy]
      before_action :ensure_owner, only: %i[update destroy]

      def index
        params[:where] ||= {}
        params[:where][:is_deleted] = false if params[:where][:is_deleted].nil?
        params[:includes] ||= "skill_category"
        perform_search(
          model: Skill,
          serializer: SkillSerializer
        )
      end

      def show
        render_success(@skill, serializer: SkillSerializer)
      end

      def create
        @skill = Skill.find_by(name: skill_params[:name], account_id: @current_user.account_id)
        return render_success(@skill, serializer: SkillSerializer, status: :created) if @skill

        @skill = Skill.create(skill_params.merge(account_id: @current_user.account_id))

        if @skill.save
          return render_success(@skill, serializer: SkillSerializer, status: :created)
        end
        render_error(@skill, status: :unprocessable_entity)
      end

      def update
        @skill.update(skill_params) ? render_success(@skill, serializer: SkillSerializer) : render_error(@skill)
      end

      def destroy
        @skill.is_deleted = true
        @skill.save
        render_success(@skill, serializer: SkillSerializer)
      end

      private

      def set_skill
        @skill = Skill.find_by(id: params[:id])
        render_not_found("Skill") unless @skill
      end

      def ensure_owner
        return unless @skill
        return if @skill.account_id == @current_user.account_id
        render_simple_error("Não autorizado a realizar esta ação nesta skill", status: :forbidden)
      end

      def skill_params
        params.require(:skill).permit(:name, :account_id, :skill_category_id)
      end
    end
  end
end
