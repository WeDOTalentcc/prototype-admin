module V1
  class EmailOptOutsController < ApplicationController
    skip_before_action :authorize_request, only: %i[show create], raise: false
    skip_before_action :verify_authenticity_token, only: %i[show create], raise: false

    def show
      @unsubscribe = EmailUnsubscribe.find_by(token: params[:token])
      redirect_to(root_path, alert: "Link inválido ou expirado") unless @unsubscribe
    end

    def create
      @unsubscribe = EmailUnsubscribe.find_by(token: params[:token])
      return redirect_to(root_path, alert: "Link inválido") unless @unsubscribe

      if @unsubscribe.unsubscribed_at.present?
        return redirect_to(root_path, notice: "Você já estava descadastrado.")
      end

      @unsubscribe.update(
        unsubscribed_at: Time.current,
        reason: params[:reason],
        ip_address: request.remote_ip,
        user_agent: request.user_agent
      )

      Apartment::Tenant.switch!(@unsubscribe.account.tenant) do
        EmailFollowupStatus
          .for_candidate(@unsubscribe.candidate_id)
          .pending
          .find_each { |fs| fs.complete!("unsubscribed") }
      end

      redirect_to(root_path, notice: "Seu email foi descadastrado com sucesso.")
    end
  end
end
