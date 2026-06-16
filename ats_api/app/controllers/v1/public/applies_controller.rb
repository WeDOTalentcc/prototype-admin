# frozen_string_literal: true

module V1
  module Public
    class AppliesController < V1::Users::ApplicationController
      skip_before_action :authorize_request
      before_action :switch_tenant_or_find_by_slug
      before_action :set_job

      def create
        return render_not_found("Job") unless @job
        return render_not_found("Job") unless @job.is_published

        result = ::Public::CreateCandidateAndApplyService.call(
          job: @job,
          name: apply_params[:name],
          email: apply_params[:email],
          mobile_phone: apply_params[:mobile_phone],
          curriculum_file: curriculum_file_param,
          curriculum_text: apply_params[:curriculum_text],
          accept_terms: apply_params[:accept_terms]
        )

        if result[:success]
          apply = Apply.include_base.find(result[:apply].id)
          render_success(apply, serializer: PublicApplySerializer, status: :created)
        elsif result[:already_applied]
          render_error({ errors: [ result[:error] ] }, status: :conflict)
        else
          render_error({ errors: [ result[:error] ] }, status: :unprocessable_entity)
        end
      end

      private

      def switch_tenant_or_find_by_slug
        @account = Account.find_by(slug: params[:account_slug])
        return render_not_found("Account") unless @account

        Apartment::Tenant.switch!(@account.tenant)
      end

      def set_job
        @job = Job.include_base.find_by(slug: params[:slug])
      end

      def apply_params
        base = params[:application] || params
        base.permit(:name, :email, :mobile_phone, :curriculum_text, :accept_terms)
      end

      def curriculum_file_param
        params[:curriculum] || params[:resume] || params.dig(:application, :curriculum) || params.dig(:application, :resume)
      end
    end
  end
end
