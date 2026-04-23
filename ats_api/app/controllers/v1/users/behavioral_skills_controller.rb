# frozen_string_literal: true

module V1
  module Users
    class BehavioralSkillsController < ApplicationController
      before_action :set_behavioral_skill, only: %i[show update destroy]
      before_action :ensure_owner, only: %i[update destroy]

      def index
        params[:where] ||= {}
        params[:where][:is_deleted] = false if params[:where][:is_deleted].nil?
        perform_search(
          model: BehavioralSkill,
          serializer: BehavioralSkillSerializer
        )
      end

      def show
        render_success(@behavioral_skill, serializer: BehavioralSkillSerializer)
      end

      def create
        @behavioral_skill = BehavioralSkill.find_by(name: behavioral_skill_params[:name], account_id: @current_user.account_id)
        return render_success(@behavioral_skill, serializer: BehavioralSkillSerializer, status: :created) if @behavioral_skill

        @behavioral_skill = BehavioralSkill.create(behavioral_skill_params.merge(account_id: @current_user.account_id))

        if @behavioral_skill.save
          render_success(@behavioral_skill, serializer: BehavioralSkillSerializer, status: :created)
        else
          render_error(@behavioral_skill, status: :unprocessable_entity)
        end
      end

      def update
        if @behavioral_skill.update(behavioral_skill_params)
          render_success(@behavioral_skill, serializer: BehavioralSkillSerializer)
        else
          render_error(@behavioral_skill)
        end
      end

      def destroy
        @behavioral_skill.update(is_deleted: true)
        render_success(@behavioral_skill, serializer: BehavioralSkillSerializer)
      end

      private

      def set_behavioral_skill
        @behavioral_skill = BehavioralSkill.find_by(id: params[:id], account_id: @current_user.account_id)
        render_not_found("BehavioralSkill") unless @behavioral_skill
      end

      def ensure_owner
        return if @behavioral_skill&.account_id == @current_user.account_id

        render_simple_error("Não autorizado a realizar esta ação", status: :forbidden)
      end

      def behavioral_skill_params
        params.require(:behavioral_skill).permit(:name, :skill_category_id, :is_deleted)
      end
    end
  end
end
