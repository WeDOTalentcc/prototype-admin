module V1
  module Users
    class EducationsController < ApplicationController
      before_action :set_education, only: %i[show update destroy]

      def index
        perform_search(model: Education, serializer: EducationSerializer)
      end

      def show
        render_success(@education, serializer: EducationSerializer)
      end

      def create
        @education = Education.new(education_params.merge(account_id: @current_user.account_id))

        if @education.save
          render_success(@education, serializer: EducationSerializer, status: :created)
        else
          render_error(@education, status: :unprocessable_entity)
        end
      end

      def update
        if @education.update(education_params)
          render_success(@education, serializer: EducationSerializer)
        else
          render_error(@education)
        end
      end

      def destroy
        @education.destroy
        render_success(@education, serializer: EducationSerializer)
      end

      private

      def set_education
        # Scope to current account for security if needed
        @education = Education.find_by(id: params[:id])
        render_not_found("Education") unless @education
      end

      def education_params
        params.require(:education).permit(
          :study_here, :start_date, :end_date, :candidate_id,
          :institution_id, :study_area_id, :city_id, :formation_type,
          :institution_name, :study_area_name # Permitting virtual attributes
        )
      end
    end
  end
end
