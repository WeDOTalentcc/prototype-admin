# frozen_string_literal: true

class EvaluationChannel < ApplicationCable::Channel
  LGPD_BANNER = "Ao continuar, você concorda com nossa Política de Privacidade. " \
                "Seus dados serão tratados conforme a LGPD. " \
                "Responda 'NÃO' para recusar."

  def subscribed
    account_uid = params[:account_uid].to_s
    evaluation_candidate_uid = params[:evaluation_candidate_uid].to_s

    return reject if account_uid.blank? || evaluation_candidate_uid.blank?

    @account = Account.find_by(uid: account_uid)
    return reject unless @account&.tenant.present?

    Apartment::Tenant.switch(@account.tenant) do
      @evaluation_candidate = EvaluationCandidate.find_by(uid: evaluation_candidate_uid)
      return reject unless @evaluation_candidate

      @account_uid = account_uid
      @evaluation_candidate_uid = evaluation_candidate_uid

      stream_from self.class.stream_name(account_uid, evaluation_candidate_uid)

      send_lgpd_banner if first_interaction?
    end
  end

  def receive(data)
    return unless @evaluation_candidate && @account

    Apartment::Tenant.switch(@account.tenant) do
      text = (data["message"] || data[:message]).to_s
      return if text.blank?

      # Rate limit check
      if Chatbot::WsRateLimiter.check_and_record!(@evaluation_candidate_uid)
        transmit(type: "error", code: "rate_limited", message: "Limite de mensagens excedido. Aguarde um momento.")
        return
      end

      # Prompt injection guard
      result = Security::PromptInjectionGuard.safe_process(text)
      unless result[:safe]
        transmit(type: "error", code: "blocked", message: Security::PromptInjectionGuard::INJECTION_RESPONSE)
        return
      end

      # TODO: delegate to message processing flow
      transmit(type: "ack", message: "Mensagem recebida")
    end
  end

  def self.stream_name(account_uid, evaluation_candidate_uid)
    "evaluations:#{account_uid}:#{evaluation_candidate_uid}"
  end

  private

  def first_interaction?
    return false unless @evaluation_candidate

    Message.where(
      reference: @evaluation_candidate,
      entity: Message::ROLE_CANDIDATE
    ).none?
  end

  def send_lgpd_banner
    privacy_url = Rails.env.production? ? "https://wedotalent.cc/terms/" : "http://localhost:3000/terms/"
    transmit(type: "lgpd", message: LGPD_BANNER, privacy_url: privacy_url)
  end
end
