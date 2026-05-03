# frozen_string_literal: true

module MicrosoftService
  class TeamsProactiveOutreachService
    DEFAULT_GREETING = <<~HTML
      <p>Olá, <strong>%{recruiter_name}</strong>! 👋</p>

      <p>Eu sou a <strong>Lia</strong>, sua assistente de inteligência artificial de recrutamento da <strong>WeDO Talent</strong>.</p>

      <p>Estou aqui para te ajudar no dia a dia! Você pode me perguntar sobre:</p>
      <ul>
        <li>📋 <strong>Vagas</strong> — status, candidatos, processos seletivos</li>
        <li>👤 <strong>Candidatos</strong> — buscar perfis, ver avaliações, histórico</li>
        <li>📊 <strong>Relatórios</strong> — métricas, analytics, dashboards</li>
        <li>🔍 <strong>Busca inteligente</strong> — encontrar candidatos por skills, experiência, localização</li>
        <li>💡 <strong>Dicas</strong> — melhores práticas de recrutamento</li>
      </ul>

      <p>É só me mandar uma mensagem aqui mesmo no Teams! 😊</p>

      <hr>
      <p><em>Lia — Inteligência Artificial de Recrutamento | WeDO Talent</em></p>
    HTML

    def self.call(domain:, message: nil, dry_run: false)
      new(domain: domain, message: message, dry_run: dry_run).call
    end

    def initialize(domain:, message: nil, dry_run: false)
      @domain = domain
      @message = message
      @dry_run = dry_run
    end

    def call
      results = { sent: 0, skipped: 0, failed: 0, errors: [], dry_run: @dry_run }

      Account.find_each do |account|
        Apartment::Tenant.switch(account.tenant) do
          lia_user = User.find_by(lia_user: true)
          unless lia_user
            Rails.logger.warn "[TeamsProactiveOutreach] No LIA user in tenant #{account.tenant}"
            next
          end

          token_status = validate_lia_token(lia_user, account.tenant)
          unless token_status[:ready]
            results[:errors] << { tenant: account.tenant, error: token_status[:reason] }
            next
          end

          recruiters = find_recruiters(account)
          Rails.logger.info "[TeamsProactiveOutreach] Found #{recruiters.count} recruiters in #{account.tenant}"

          recruiters.each do |recruiter|
            process_recruiter(lia_user, recruiter, account, results)
          end
        end
      rescue StandardError => e
        Rails.logger.error "[TeamsProactiveOutreach] Error in tenant #{account.tenant}: #{e.message}"
        results[:errors] << { tenant: account.tenant, error: e.message }
      end

      log_results(results)
      results
    end

    private

    def validate_lia_token(lia_user, tenant)
      if lia_user.ms_refresh_token.blank?
        Rails.logger.error "[TeamsProactiveOutreach] ❌ LIA user_id=#{lia_user.id} in #{tenant} has NO refresh token — needs OAuth login"
        return { ready: false, reason: "LIA needs Microsoft OAuth re-authentication" }
      end

      if lia_user.microsoft_token_needs_refresh?
        Rails.logger.info "[TeamsProactiveOutreach] 🔄 Refreshing token for LIA user_id=#{lia_user.id} in #{tenant}"
        MicrosoftService::Api.refresh_expires_at(lia_user)
        lia_user.reload
      end

      unless lia_user.ms_access_token.present?
        Rails.logger.error "[TeamsProactiveOutreach] ❌ LIA token refresh failed in #{tenant}"
        return { ready: false, reason: "LIA token refresh failed" }
      end

      Rails.logger.info "[TeamsProactiveOutreach] ✅ LIA token valid in #{tenant} (expires in #{lia_user.microsoft_token_expires_in_minutes}min)"
      { ready: true }
    rescue StandardError => e
      Rails.logger.error "[TeamsProactiveOutreach] ❌ Token validation error in #{tenant}: #{e.message}"
      { ready: false, reason: e.message }
    end

    def find_recruiters(account)
      User.where("email LIKE ?", "%@#{ActiveRecord::Base.sanitize_sql_like(@domain)}")
          .where.not(lia_user: true)
          .where(status: 1)
          .where(account_id: account.id)
    end

    def process_recruiter(lia_user, recruiter, account, results)
      if already_has_chat?(lia_user, recruiter)
        Rails.logger.info "[TeamsProactiveOutreach] Chat already exists for recruiter_id=#{recruiter.id} — skipping"
        results[:skipped] += 1
        return
      end

      if @dry_run
        Rails.logger.info "[TeamsProactiveOutreach] [DRY RUN] Would send to recruiter_id=#{recruiter.id}"
        results[:sent] += 1
        return
      end

      Microsoft::TeamsProactiveMessageJob.perform_async(
        lia_user.id,
        recruiter.id,
        account.id,
        @message
      )
      results[:sent] += 1
    rescue StandardError => e
      Rails.logger.error "[TeamsProactiveOutreach] Failed to enqueue for recruiter_id=#{recruiter.id}: #{e.class}"
      results[:failed] += 1
      results[:errors] << { recruiter_id: recruiter.id, error: e.class.to_s }
    end

    def already_has_chat?(lia_user, recruiter)
      TeamsChatSubscription.exists?(lia_user_id: lia_user.id, recruiter_user_id: recruiter.id)
    end

    def log_results(results)
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.info "🚀 [TeamsProactiveOutreach] Completed"
      Rails.logger.info "   Mode: #{@dry_run ? 'DRY RUN' : 'LIVE'}"
      Rails.logger.info "   Domain: #{@domain}"
      Rails.logger.info "   Enqueued: #{results[:sent]}"
      Rails.logger.info "   Skipped: #{results[:skipped]}"
      Rails.logger.info "   Failed: #{results[:failed]}"
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    end
  end
end
