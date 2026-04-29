module V1
  module Users
    class CompaniesController < ApplicationController
      before_action :set_company, only: %i[show update destroy]

      def index
        params[:where] ||= {}
        params[:where][:is_deleted] = false if params[:where][:is_deleted].nil?
        perform_search(
          model: Company,
          serializer: CompanySerializer
        )
      end

      def show
        render_success(@company, serializer: CompanySerializer)
      end

      def create
        @company = Company.find_by(name: company_params[:name]&.downcase, account_id: @current_user.account_id, is_deleted: false)
        if @company
          @company.logo.attach(company_params[:logo]) if company_params[:logo].present?
          return render_success(@company, serializer: CompanySerializer, status: :ok)
        end

        @company = Company.create(company_params.merge(account_id: @current_user.account_id))
        if @company
          @company.logo.attach(company_params[:logo]) if company_params[:logo].present?
        end

        if @company.save
          return render_success(@company, serializer: CompanySerializer, status: :created)
        end
        render_error(@company, status: :unprocessable_entity)
      end

      def update
        @company.logo.attach(company_params[:logo]) if company_params[:logo].present?
        @company.update(company_params) ? render_success(@company, serializer: CompanySerializer) : render_error(@company)
      end

      def destroy
        @company.is_deleted = true
        @company.save
        render_success(@company, serializer: CompanySerializer)
      end

      private

      def set_company
        @company = Company.find_by(id: params[:id])
        render_not_found("Company") unless @company
      end

      def company_params
        params.require(:company).permit(:name, :linkedin_url, :account_id, :user_id, :logo)
      end
    end
  end
end
