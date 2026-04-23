# frozen_string_literal: true

class ChatbotTimeoutCheckWorker
  include Sidekiq::Worker

  sidekiq_options queue: :default, retry: 2

  def perform
    timestamp = Time.current.strftime("%Y-%m-%d %H:%M:%S")

    Account.find_each do |account|
      process_account(account)
    rescue StandardError => e
      Rails.logger.error "❌ [ChatbotTimeoutCheckWorker] Erro na conta #{account.id}: #{e.class} - #{e.message}"
      Rails.logger.error e.backtrace.first(5).join("\n")
    end

    Rails.logger.info "✅ [ChatbotTimeoutCheckWorker] Verificação concluída em #{timestamp}"
  end

  private

  def process_account(account)
    return if account.tenant.blank?

    Apartment::Tenant.switch(account.tenant) do
      Chatbot::Evaluation::TimeoutManager.new(account_id: account.id).call
    end
  rescue Apartment::TenantNotFound => e
    Rails.logger.warn "⚠️ [ChatbotTimeoutCheckWorker] Tenant não encontrado: #{account.tenant} - #{e.message}"
  end
end
