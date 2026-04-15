# frozen_string_literal: true

module V1
  module Users
    class CompanyProfilesController < ApplicationController
      before_action :authorize_request
      before_action :require_manager!, only: %i[create update destroy]
      before_action :set_company_profile, only: %i[show update destroy]

      def index
        perform_search(
          model: CompanyProfile,
          serializer: CompanyProfileSerializer
        )
      end

      def show
        render_success(@company_profile, serializer: CompanyProfileSerializer)
      end

      def create
        @company_profile = CompanyProfile.new(company_profile_params.merge(account_id: @current_user.account_id))

        if @company_profile.save
          return render_success(@company_profile, serializer: CompanyProfileSerializer, status: :created)
        end
        render_error(@company_profile, status: :unprocessable_entity)
      end

      def update
        @company_profile.update(company_profile_params) ? render_success(@company_profile, serializer: CompanyProfileSerializer) : render_error(@company_profile)
      end

      def destroy
        @company_profile.destroy
        render_no_content
      end

      private

      def set_company_profile
        @company_profile = CompanyProfile.find_by(id: params[:id])
        render_not_found("CompanyProfile") unless @company_profile
      end

      def company_profile_params
        params.require(:company_profile).permit(
          :company_id, :name, :trade_name, :cnpj, :industry, :sector, :size, :employee_count,
          :website, :phone, :email, :address_street, :address_number, :address_complement,
          :address_district, :address_city, :address_state, :address_zip, :address_country,
          :description, :mission, :vision, :values, :culture_insights, :ats_insights,
          :logo_url, :cover_url, :social_media, :founded_year, :revenue_range, :growth_stage
        )
      end
    end
  end
end
