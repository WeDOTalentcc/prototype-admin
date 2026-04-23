module V1
  module Users
    class ExperiencesController < ApplicationController
      before_action :set_experience, only: %i[show update destroy]

      def index
        params[:where] = parse_json_param(params[:where])
        params[:where] ||= {}
        params[:where][:is_deleted] = false if params[:where][:is_deleted].nil?
        perform_search(
          model: Experience,
          serializer: ExperienceSerializer
        )
      end

      def show
        render_success(@experience, serializer: ExperienceSerializer)
      end

      def create
        @experience = Experience.new(experience_params.merge(
          account_id: @current_user.account_id,
          user_id: @current_user.id
        ))

        if @experience.save
          return render_success(@experience, serializer: ExperienceSerializer, status: :created)
        end
        render_error(@experience, status: :unprocessable_entity)
      end

      def update
        if @experience.update(experience_params)
          render_success(@experience, serializer: ExperienceSerializer)
        else
          render_error(@experience)
        end
      end

      def destroy
        @experience.is_deleted = true
        @experience.save
        render_success(@experience, serializer: ExperienceSerializer)
      end

      private

      def set_experience
        @experience = Experience.find_by(id: params[:id])
        render_not_found("Experience") unless @experience
      end

      def experience_params
        params.require(:experience).permit(:work_here, :start_date, :end_date, :candidate_id,
                                          :occupation_id, :company_id, :city_id, :description, :reasons_leaving,
                                          :contract_type, :parse_language, :is_deleted, :company_name, :occupation_name
                                         )
      end
    end
  end
end
