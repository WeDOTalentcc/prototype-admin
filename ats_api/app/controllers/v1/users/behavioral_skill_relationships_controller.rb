# frozen_string_literal: true

module V1
  module Users
    class BehavioralSkillRelationshipsController < ApplicationController
      before_action :set_behavioral_skill_relationship, only: %i[show update destroy]
      before_action :ensure_owner, only: %i[update destroy]

      def index
        params[:where] ||= {}
        params[:where][:is_deleted] = false if params[:where][:is_deleted].nil?
        perform_search(
          model: BehavioralSkillRelationship,
          serializer: BehavioralSkillRelationshipSerializer
        )
      end

      def show
        render_success(@behavioral_skill_relationship, serializer: BehavioralSkillRelationshipSerializer)
      end

      def create
        @behavioral_skill_relationship = BehavioralSkillRelationship.new(
          behavioral_skill_relationship_params.merge(
            account_id: @current_user.account_id,
            user_id: @current_user.id
          )
        )

        if @behavioral_skill_relationship.save
          render_success(@behavioral_skill_relationship, serializer: BehavioralSkillRelationshipSerializer, status: :created)
        else
          render_error(@behavioral_skill_relationship)
        end
      end

      def update
        if @behavioral_skill_relationship.update(behavioral_skill_relationship_params)
          render_success(@behavioral_skill_relationship, serializer: BehavioralSkillRelationshipSerializer)
        else
          render_error(@behavioral_skill_relationship)
        end
      end

      def destroy
        @behavioral_skill_relationship.update(is_deleted: true)
        render_success(@behavioral_skill_relationship, serializer: BehavioralSkillRelationshipSerializer)
      end

      def get_experience_times
        experience_times = BehavioralSkillRelationship::EXPERIENCE_TIMES.map { |e| OpenStruct.new(e) }
        render_success(experience_times, serializer: ExperienceTimeSerializer)
      end

      def get_skill_levels
        skill_levels = BehavioralSkillRelationship::SKILL_LEVELS.map { |s| OpenStruct.new(s) }
        render_success(skill_levels, serializer: SkillLevelSerializer)
      end

      private

      def set_behavioral_skill_relationship
        @behavioral_skill_relationship = BehavioralSkillRelationship.find_by(id: params[:id])
        render_not_found("BehavioralSkillRelationship") unless @behavioral_skill_relationship
      end

      def ensure_owner
        return if @behavioral_skill_relationship&.account_id == @current_user.account_id

        render_simple_error("Não autorizado a realizar esta ação", status: :forbidden)
      end

      def behavioral_skill_relationship_params
        params.require(:behavioral_skill_relationship).permit(
          :behavioral_skill_id,
          :reference_type,
          :reference_id,
          :is_deleted,
          :priority,
          :min_value,
          :max_value,
          :description,
          :main,
          :experience_time,
          :level_skill
        )
      end
    end
  end
end
