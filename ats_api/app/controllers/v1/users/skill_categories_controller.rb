module V1
  module Users
    class SkillCategoriesController < ApplicationController
      before_action :set_skill_category, only: [ :show, :update, :destroy ]
      before_action :authorize_admin!, only: [ :create, :update, :destroy ]

      def index
        params[:where] ||= {}
        params[:where][:is_deleted] = false if params[:where][:is_deleted].nil?

        perform_search(
          model: SkillCategory,
          serializer: SkillCategorySerializer
        )
      end

      def show
        render_success(@skill_category, serializer: SkillCategorySerializer)
      end

      def create
        @skill_category = SkillCategory.new(skill_category_params)

        return render_success(@skill_category, serializer: SkillCategorySerializer, status: :created) if @skill_category.save

        render_error(@skill_category, status: :unprocessable_entity)
      end

      def update
        return render_success(@skill_category, serializer: SkillCategorySerializer) if @skill_category.update(skill_category_params)

        render_error(@skill_category, status: :unprocessable_entity)
      end

      def destroy
        @skill_category.update(is_deleted: true)
        render json: { message: "Categoria removida com sucesso" }
      end

      private

      def set_skill_category
        @skill_category = SkillCategory.find_by(id: params[:id])
        render_not_found("SkillCategory") unless @skill_category
      end

      def skill_category_params
        params.require(:skill_category).permit(:name, :description, :icon, :color)
      end

      def authorize_admin!
        return if @current_user&.admin? || @current_user&.super_admin?

        render_simple_error("Apenas administradores podem realizar esta ação", status: :forbidden)
      end
    end
  end
end
