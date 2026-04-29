module V1
  module Users
    class SkillRelationshipsController < ApplicationController
      before_action :set_skill_relationship, only: %i[show update destroy]
      before_action :ensure_owner, only: %i[update destroy]

      def index
        params[:where] ||= {}
        params[:where][:is_deleted] = false if params[:where][:is_deleted].nil?
        perform_search(
          model: SkillRelationship,
          serializer: SkillRelationshipSerializer
        )
      end

      def show
        render_success(@skill_relationship, serializer: SkillRelationshipSerializer)
      end

      def create
        params_hash = skill_relationship_params.to_h
        skill_id = find_or_create_skill_id(params_hash)
        return unless skill_id

        params_hash[:skill_id] = skill_id
        params_hash.delete(:skill_name)

        @skill_relationship = SkillRelationship.new(params_hash.merge(
          account_id: @current_user.account_id,
          user_id: @current_user.id
        ))

        if @skill_relationship.save
          return render_success(@skill_relationship, serializer: SkillRelationshipSerializer, status: :created)
        end
        render_error(@skill_relationship, status: :unprocessable_entity)
      end

      def update
        params_hash = skill_relationship_params.to_h
        if params_hash[:skill_name].present?
          skill_id = find_or_create_skill_id(params_hash)
          return unless skill_id

          params_hash[:skill_id] = skill_id
          params_hash.delete(:skill_name)
        end

        if @skill_relationship.update(params_hash)
          render_success(@skill_relationship, serializer: SkillRelationshipSerializer)
        else
          render_error(@skill_relationship)
        end
      end

      def destroy
        @skill_relationship.is_deleted = true
        @skill_relationship.save
        render_success(@skill_relationship, serializer: SkillRelationshipSerializer)
      end

      def get_experience_times
        experience_times = ::SkillRelationship::EXPERIENCE_TIMES.map { |e| OpenStruct.new(e) }
        render_success(experience_times, serializer: ExperienceTimeSerializer)
      end

      def get_skill_levels
        skill_levels = ::SkillRelationship::SKILL_LEVELS.map { |s| OpenStruct.new(s) }
        render_success(skill_levels, serializer: SkillLevelSerializer)
      end

      private

      def set_skill_relationship
        @skill_relationship = SkillRelationship.find_by(id: params[:id])
        render_not_found("SkillRelationship") unless @skill_relationship
      end

      def ensure_owner
        return if @skill_relationship.account_id == @current_user.account_id
        render_simple_error("Não autorizado a realizar esta ação nesta skill relationship", status: :forbidden)
      end

      def skill_relationship_params
        params.require(:skill_relationship).permit(:skill_id, :skill_name, :account_id, :user_id,
                                                   :reference_type, :reference_id, :is_deleted,
                                                   :priority, :min_value, :max_value,
                                                   :description, :main, :experience_time, :level_skill
                                                  )
      end

      def find_or_create_skill_id(params_hash)
        return params_hash[:skill_id] if params_hash[:skill_id].present?
        return nil unless params_hash[:skill_name].present?

        skill_name = params_hash[:skill_name].to_s.strip
        return nil if skill_name.blank?

        skill = Skill.find_by(name: skill_name, account_id: @current_user.account_id, is_deleted: false)

        unless skill
          skill = Skill.create(name: skill_name, account_id: @current_user.account_id)
          unless skill.persisted?
            render_error(skill, status: :unprocessable_entity)
            return nil
          end
        end

        skill.id
      end
    end
  end
end
