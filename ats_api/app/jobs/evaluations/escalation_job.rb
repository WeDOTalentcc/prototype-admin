# frozen_string_literal: true

module Evaluations
  class EscalationJob
    include Sidekiq::Job

    sidekiq_options queue: :default, retry: 2

    def perform
      Account.find_each do |account|
        next unless account.tenant.present?

        Apartment::Tenant.switch(account.tenant) do
          process_tenant(account)
        end
      rescue StandardError => e
        Rails.logger.error "❌ [EscalationJob] Erro no tenant #{account&.tenant}: #{e.class} - #{e.message}"
        Rails.logger.error e.backtrace.first(5).join("\n")
      end

      Rails.logger.info "✅ [EscalationJob] Processamento concluído"
    end

    private

    def process_tenant(account)
      unless ActiveRecord::Base.connection.column_exists?(:evaluation_candidates, :chatbot_channel)
        return
      end

      scope = EvaluationCandidate
        .where(completed: false, is_deleted: false, chatbot_channel: EvaluationCandidate.chatbot_channels[:internal])
        .where("created_at <= ?", 48.hours.ago)

      scope.find_each do |ec|
        process_candidate(ec)
      rescue StandardError => e
        Rails.logger.error "❌ [EscalationJob] Erro em evaluation_candidate #{ec.id}: #{e.class} - #{e.message}"
      end
    end

    def process_candidate(evaluation_candidate)
      escalations = evaluation_candidate.escalations || {}
      created_at = evaluation_candidate.created_at

      Rails.logger.info "🔍 [EscalationJob] process_candidate ec=#{evaluation_candidate.id} created_at=#{created_at} escalations=#{escalations.keys}"

      if created_at <= 96.hours.ago && escalations["96h"].blank?
        send_96h(evaluation_candidate)
      elsif created_at <= 72.hours.ago && escalations["72h"].blank?
        send_72h(evaluation_candidate)
      elsif created_at <= 48.hours.ago && escalations["48h"].blank?
        send_48h(evaluation_candidate)
      else
        Rails.logger.info "⏭️ [EscalationJob] skip ec=#{evaluation_candidate.id} (não atende critérios)"
      end
    end

    def send_48h(evaluation_candidate)
      return unless evaluation_candidate.candidate&.email.present?

      user = creator_user(evaluation_candidate)
      return unless user

      mail = EvaluationMailer.with(
        candidate: evaluation_candidate.candidate,
        evaluation_candidate: evaluation_candidate,
        job: evaluation_candidate.job,
        user: user
      ).escalation_continue_screening

      body_html = mail.html_part&.body&.to_s || mail.body.to_s
      dispatch_and_record(evaluation_candidate, "48h", user) do
        {
          target_type: "ids",
          target_payload: { ids: [ evaluation_candidate.candidate_id ] },
          candidate_ids: [ evaluation_candidate.candidate_id ],
          subject: "#{evaluation_candidate.account&.name || 'WeDO Talent'} — Continue sua triagem",
          body: body_html
        }
      end
    end

    def send_72h(evaluation_candidate)
      return unless evaluation_candidate.candidate&.email.present?

      user = creator_user(evaluation_candidate)
      return unless user

      mail = EvaluationMailer.with(
        candidate: evaluation_candidate.candidate,
        evaluation_candidate: evaluation_candidate,
        job: evaluation_candidate.job,
        user: user
      ).escalation_last_chance

      body_html = mail.html_part&.body&.to_s || mail.body.to_s
      dispatch_and_record(evaluation_candidate, "72h", user) do
        {
          target_type: "ids",
          target_payload: { ids: [ evaluation_candidate.candidate_id ] },
          candidate_ids: [ evaluation_candidate.candidate_id ],
          subject: "#{evaluation_candidate.account&.name || 'WeDO Talent'} — Última chance: complete sua triagem",
          body: body_html
        }
      end
    end

    def send_96h(evaluation_candidate)
      user = evaluation_candidate.user || creator_user(evaluation_candidate)
      unless user
        return
      end

      mail = EvaluationMailer.with(
        evaluation_candidate: evaluation_candidate,
        user: user
      ).escalation_alert_consultant

      body_html = mail.html_part&.body&.to_s || mail.body.to_s
      extra = { completed: true, declined_at: Time.current, declined_reason: "Candidato não participou da triagem" }
      dispatch_and_record(evaluation_candidate, "96h", user, extra_attrs: extra) do
        {
          target_type: "ids",
          target_payload: { ids: [ user.id ] },
          user_ids: [ user.id ],
          subject: "Alerta: Triagem não concluída — #{evaluation_candidate.candidate&.name} (#{evaluation_candidate.job&.title})",
          body: body_html
        }
      end

      ec_reloaded = evaluation_candidate.reload
    end

    def dispatch_and_record(evaluation_candidate, key, user, extra_attrs: {})
      params = yield
      dispatch_params = {
        account_id: evaluation_candidate.account_id,
        user_id: user.id,
        channel_type: "email",
        name: "Escalação #{key} - Triagem",
        **params
      }

      service = Dispatches::CreateService.new(
        user: user,
        account: evaluation_candidate.account,
        params: dispatch_params
      )

      service.call
      dispatch_id = service.dispatch&.id
      if dispatch_id.nil?
        return
      end

      sended_at = Time.current.strftime("%Y-%m-%dT%H:%M:%S")
      new_escalations = (evaluation_candidate.escalations || {}).merge(
        key => { "dispatch_id" => dispatch_id, "sended_at" => sended_at }
      )

      evaluation_candidate.update!(escalations: new_escalations)

      if extra_attrs.any?
        evaluation_candidate.update_columns(extra_attrs.merge(updated_at: Time.current))
      end
    rescue ActiveRecord::RecordInvalid, StandardError => e
      Rails.logger.error "❌ [EscalationJob] Falha ao enviar escalação #{key} — evaluation_candidate #{evaluation_candidate.id}: #{e.message}"
      raise
    end

    def creator_user(evaluation_candidate)
      evaluation_candidate.user ||
        evaluation_candidate.job&.user ||
        evaluation_candidate.account&.users&.find_by(is_admin: true) ||
        evaluation_candidate.account&.users&.first
    end
  end
end
