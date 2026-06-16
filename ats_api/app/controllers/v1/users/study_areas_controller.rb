module V1
  module Users
    class StudyAreasController < ApplicationController
      before_action :set_study_area, only: [ :show, :update, :destroy ]

      def index
        perform_search(model: StudyArea, serializer: StudyAreaSerializer)
      end

      def show
        render_success(@study_area, serializer: StudyAreaSerializer)
      end

      def create
        @study_area = StudyArea.new(study_area_params)
        if @study_area.save
          render_success(@study_area, serializer: StudyAreaSerializer, status: :created)
        else
          render_error(@study_area, status: :unprocessable_entity)
        end
      end

      def update
        if @study_area.update(study_area_params)
          render_success(@study_area, serializer: StudyAreaSerializer)
        else
          render_error(@study_area, status: :unprocessable_entity)
        end
      end

      def destroy
        @study_area.destroy
        render_success(@study_area, serializer: StudyAreaSerializer)
      end

      private

      def set_study_area
        @study_area = StudyArea.find_by(id: params[:id])
        render_not_found("StudyArea") unless @study_area
      end

      def study_area_params
        params.require(:study_area).permit(
          :name,
          :approved,
          :reference_type,
          :reference_id,
          :account_id
        )
      end
    end
  end
end
