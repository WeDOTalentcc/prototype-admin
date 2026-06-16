module V1
  module Users
    class InstitutionsController < ApplicationController
      before_action :set_institution, only: [ :show, :update, :destroy ]

      def index
        perform_search(model: Institution, serializer: InstitutionSerializer)
      end

      def show
        render_success(@institution, serializer: InstitutionSerializer)
      end

      def create
        @institution = Institution.new(institution_params)
        if @institution.save
          render_success(@institution, serializer: InstitutionSerializer, status: :created)
        else
          render_error(@institution, status: :unprocessable_entity)
        end
      end

      def update
        if @institution.update(institution_params)
          render_success(@institution, serializer: InstitutionSerializer)
        else
          render_error(@institution, status: :unprocessable_entity)
        end
      end

      def destroy
        @institution.destroy
        render_success(@institution, serializer: InstitutionSerializer)
      end

      private

      def set_institution
        @institution = Institution.find_by(id: params[:id])
        render_not_found("Institution") unless @institution
      end

      def institution_params
        params.require(:institution).permit(
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
