# frozen_string_literal: true

module V1
  module Public
    class JobsController < V1::Users::ApplicationController
      skip_before_action :authorize_request
      before_action :switch_tenant_or_find_by_slug
      before_action :set_job

      def show
        return render_not_found("Job") unless @job
        return render_not_found("Job") unless @job.is_published

        render_success(@job, serializer: PublicJobSerializer, status: :ok)
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
    end
  end
end
