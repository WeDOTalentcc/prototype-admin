module V1
  module Setups
    class BusinessesController < ApplicationController
      def show
        render_success(@business, serializer: BusinessSerializer)
      end

      def create
        @business = Business.new(business_params)
        @business.account_id = @account.id if @business.account_id.blank?
        @business.logo.attach(params[:business][:logo]) if params[:business][:logo].present?
        @business.cover_image.attach(params[:business][:cover_image]) if params[:business][:cover_image].present?
        if @business.save
          return render_success(@business, serializer: BusinessSerializer)
        end
        render_error(@business, status: :unprocessable_entity)
      end

      def update
        if @business.update(business_params)
          @business.logo.attach(params[:business][:logo]) if params[:business][:logo].present?
          @business.cover_image.attach(params[:business][:cover_image]) if params[:business][:cover_image].present?
          return render_success(@business, serializer: BusinessSerializer)
        end
        render_error(@business, status: :unprocessable_entity)
      end

      def business_params
        params.require(:business).permit(
          :name,
          :cnpj,
          :email,
          :phone,
          :website,
          :industry,
          :size,
          :linkedin,
          :about,
          :is_active,
          :corporate_name,
          :job_amount,
          :logo,
          :cover_image,
          :mission,
          :vision,
          :work_model,
          :growth_opportunities,
          :team_dynamics,
          :leader_style,
          :evp_highlights,
          :diversity_and_inclusion,
          :sustainability,
          :social_impact,
          culture_values: [],
          soft_skills: []
        )
      end
    end
  end
end
