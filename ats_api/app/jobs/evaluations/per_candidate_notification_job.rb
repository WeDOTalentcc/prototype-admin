# frozen_string_literal: true

module Evaluations
  class PerCandidateNotificationJob < ApplicationJob
    queue_as :default

    def perform(evaluation_candidate_id, account_id = nil)
      return unless account_id

      account = Account.find_by(id: account_id)
      return unless account

      Current.account = account

      tenant_name = account.tenant

      Apartment::Tenant.switch!(tenant_name)

      evaluation_candidate = EvaluationCandidate.find_by(id: evaluation_candidate_id)
      return unless evaluation_candidate

      evaluation = evaluation_candidate.evaluation

      return unless evaluation.notification_enabled?
      return unless evaluation.per_candidate?

      answers_count = Answer.where(
        evaluation_id: evaluation_candidate.evaluation_id,
        candidate_id: evaluation_candidate.candidate_id
      ).count
      if answers_count.zero?
        return
      end

      candidate = evaluation_candidate.candidate
      job = evaluation_candidate.job

      ai_result = Evaluations::AiFeedbackService.call(evaluation_candidate: evaluation_candidate)

      score = calculate_score(evaluation_candidate)

      ai_result[:score] = score
      ai_result[:evaluation_summary] = ai_result[:full_analysis] || ai_result["full_analysis"]

      store_ai_feedback(evaluation_candidate, ai_result)

      send_teams_notification(evaluation_candidate) if ai_result[:status] == "success"

      Rails.logger.info "[PerCandidateNotificationJob] Notification sent for candidate #{candidate.id} in evaluation #{evaluation.id}"
    rescue StandardError => e
      Rails.logger.error "[PerCandidateNotificationJob] Error: #{e.class} - #{e.message}"
      Rails.logger.error e.backtrace.join("\n")
      raise e
    end

    private

    def calculate_score(evaluation_candidate)
      return evaluation_candidate.score.to_f if evaluation_candidate.score.present? && evaluation_candidate.score.to_f > 0

      answers = Answer.where(
        evaluation_id: evaluation_candidate.evaluation_id,
        candidate_id: evaluation_candidate.candidate_id
      )

      total_score = 0
      count_scores = 0

      answers.each do |answer|
        comments = parse_comments_response(answer.comments_response)
        score = comments["score"] || comments[:score] || 0

        if score.is_a?(Numeric) && score > 0
          total_score += score
          count_scores += 1
        end
      end

      count_scores > 0 ? (total_score / count_scores * 10).round(3) : 0.0
    end

    def parse_comments_response(comments_str)
      return {} if comments_str.blank?

      return comments_str if comments_str.is_a?(Hash)

      if comments_str.to_s.strip.start_with?("{")
        normalized = comments_str.to_s
          .gsub(/(\w+):\s*/, '"\1": ')
          .gsub(/:\s*([a-zA-Z]\w+)(?=[\s,}])/, ': "\1"')
        begin
          return JSON.parse(normalized)
        rescue JSON::ParserError
          begin
            return JSON.parse(comments_str.to_s)
          rescue JSON::ParserError
            return {}
          end
        end
      end

      result = {}
      content = comments_str.to_s.strip
      content = content.gsub(/^\{|\}$/, "").strip

      if content.match(/score:\s*([0-9.]+)/)
        result["score"] = $1.to_f
      end

      if content.match(/is_answer_satisfactory:\s*(true|false)/i)
        result["is_answer_satisfactory"] = $1.downcase == "true"
      end

      if content.match(/feedback_for_recruiter:\s*"([^"]+)"/)
        result["feedback_for_recruiter"] = $1.strip
      elsif content.match(/feedback_for_recruiter:\s*([^,}]+?)(?=,\s*\w+:|$|\})/)
        result["feedback_for_recruiter"] = $1.strip
      end

      result
    rescue => e
      Rails.logger.warn "[PerCandidateNotificationJob] Error parsing comments_response: #{e.message}"
      {}
    end

    def store_ai_feedback(evaluation_candidate, api_response)
      return unless api_response.is_a?(Hash)

      macro_distribution = api_response[:wsi_macro_distribution] || api_response["wsi_macro_distribution"]
      macro_distribution ||= Evaluations::WsiDimensionScores.new(evaluation_candidate: evaluation_candidate).macro_distribution_weights

      ai_feedback = {
        candidate_id: api_response[:candidate_id] || api_response["candidate_id"],
        candidate_name: api_response[:candidate_name] || api_response["candidate_name"],
        evaluation_id: api_response[:evaluation_id] || api_response["evaluation_id"],
        request_id: api_response[:request_id] || api_response["request_id"],
        status: api_response[:status] || api_response["status"],
        processing_time_ms: api_response[:processing_time_ms] || api_response["processing_time_ms"],
        methodology: api_response[:methodology] || api_response["methodology"],
        wsi_macro_distribution: macro_distribution,
        wsi_score: api_response[:wsi_score] || api_response["wsi_score"],
        wsi_classification: api_response[:wsi_classification] || api_response["wsi_classification"],
        wsi_level: api_response[:wsi_level] || api_response["wsi_level"],
        dreyfus_level: api_response[:dreyfus_level] || api_response["dreyfus_level"],
        skills_analysis: api_response[:skills_analysis] || api_response["skills_analysis"],
        behavioral_analysis: api_response[:behavioral_analysis] || api_response["behavioral_analysis"],
        approval_criteria: api_response[:approval_criteria] || api_response["approval_criteria"],
        recommendation: api_response[:recommendation] || api_response["recommendation"],
        recommendation_justification: api_response[:recommendation_justification] || api_response["recommendation_justification"],
        summary: api_response[:summary] || api_response["summary"],
        strengths: api_response[:strengths] || api_response["strengths"],
        weaknesses: api_response[:weaknesses] || api_response["weaknesses"],
        next_steps: api_response[:next_steps] || api_response["next_steps"],
        full_analysis: api_response[:full_analysis] || api_response["full_analysis"],
        score: api_response[:score],
        evaluation_summary: api_response[:evaluation_summary]
      }

      evaluation_candidate.update_columns(
        ai_feedback: ai_feedback,
        score: api_response[:score],
        evaluation_summary: api_response[:evaluation_summary]
      )
    rescue StandardError => e
      Rails.logger.error "[PerCandidateNotificationJob] Failed to store AI feedback: #{e.message}"
    end

    def send_teams_notification(evaluation_candidate)
      # Busca o usuário LIA (Inteligência Artificial)
      lia_user = User.find_by(lia_user: true)
      unless lia_user
        Rails.logger.warn "[PerCandidateNotificationJob] LIA user not found - skipping Teams notification"
        return
      end

      # Busca o recrutador responsável (owner da vaga)
      job = evaluation_candidate.job
      recruiter = evaluation_candidate.user
      unless recruiter
        Rails.logger.warn "[PerCandidateNotificationJob] Job owner not found - skipping Teams notification"
        return
      end

      Rails.logger.info "=" * 100
      Rails.logger.info "🤖 [TEAMS NOTIFICATION] SENDER (LIA):"
      Rails.logger.info "   ID: #{lia_user.id}"
      Rails.logger.info "   lia_user flag: #{lia_user.lia_user}"
      Rails.logger.info "-" * 100
      Rails.logger.info "👤 [TEAMS NOTIFICATION] RECIPIENT (Job Owner/Recruiter):"
      Rails.logger.info "   ID: #{recruiter.id}"
      Rails.logger.info "   lia_user flag: #{recruiter.lia_user}"
      Rails.logger.info "-" * 100
      Rails.logger.info "📋 [TEAMS NOTIFICATION] Context:"
      Rails.logger.info "   Job ID: #{job.id}"
      Rails.logger.info "   Job Title: #{job.title}"
      Rails.logger.info "   Evaluation Candidate ID: #{evaluation_candidate.id}"
      Rails.logger.info "=" * 100

      # Evita enviar DM para você mesmo (caso LIA seja o owner da vaga)
      if lia_user.email == recruiter.email
        Rails.logger.error "❌ [TEAMS NOTIFICATION] SELF-DM DETECTED!"
        Rails.logger.error "   Cannot send message to self (same email) — LIA user is also the job owner"
        return
      end

      ai_feedback = evaluation_candidate.ai_feedback
      return unless ai_feedback.present?

      candidate = evaluation_candidate.candidate
      job = evaluation_candidate.job

      # Gera os links para o front-end
      front_url = ENV.fetch("FRONT_URL", "http://localhost:3000")
      candidate_url = "#{front_url}/user/candidates/#{candidate.id}"
      job_url = "#{front_url}/user/jobs/#{job.id}"

      # Monta a mensagem formatada
      message_content = build_teams_message(
        recruiter_name: recruiter.name || recruiter.email.split("@").first,
        candidate_name: ai_feedback["candidate_name"] || candidate.name,
        job_title: job.title,
        recommendation: ai_feedback["recommendation"],
        summary: ai_feedback["summary"],
        strengths: ai_feedback["strengths"],
        weaknesses: ai_feedback["weaknesses"],
        next_steps: ai_feedback["next_steps"],
        candidate_url: candidate_url,
        job_url: job_url
      )

      # Envia mensagem no Teams
      Rails.logger.info "[PerCandidateNotificationJob] Sending Teams notification to recruiter_id=#{recruiter.id}..."

      response = MicrosoftService::Teams.send_message(
        user: lia_user,
        content: message_content,
        content_type: "html",
        to: recruiter.email
      )

      Rails.logger.info "[PerCandidateNotificationJob] Teams notification sent successfully to recruiter_id=#{recruiter.id}"

      register_teams_chat_subscription(lia_user, recruiter, response[:chat_id])
    rescue MicrosoftService::Teams::Error => e
      Rails.logger.error "[PerCandidateNotificationJob] Teams error: #{e.code} - #{e.message}"
      Rails.logger.error "[PerCandidateNotificationJob] Teams error details: #{e.inspect}"
    rescue StandardError => e
      Rails.logger.error "[PerCandidateNotificationJob] Failed to send Teams notification: #{e.message}"
      Rails.logger.error "[PerCandidateNotificationJob] Error backtrace: #{e.backtrace.first(5).join("\n")}"
    end

    def build_teams_message(recruiter_name:, candidate_name:, job_title:, recommendation:, summary:, strengths:, weaknesses:, next_steps:, candidate_url:, job_url:)
      recommendation_emoji = case recommendation
      when "APPROVED" then "✅"
      when "NOT_RECOMMENDED" then "❌"
      else "⚠️"
      end

      recommendation_text = case recommendation
      when "APPROVED" then "Aprovado"
      when "NOT_RECOMMENDED" then "Não Recomendado"
      else "Análise Adicional Necessária"
      end

      strengths_html = if strengths.is_a?(Array) && strengths.any?
        "<ul>" + strengths.map { |s| "<li>#{CGI.escapeHTML(s)}</li>" }.join + "</ul>"
      else
        "<p><em>Nenhum ponto forte identificado</em></p>"
      end

      weaknesses_html = if weaknesses.is_a?(Array) && weaknesses.any?
        "<ul>" + weaknesses.map { |w| "<li>#{CGI.escapeHTML(weakness_line_text(w))}</li>" }.join + "</ul>"
      else
        "<p><em>Nenhum ponto de atenção identificado</em></p>"
      end

      <<~HTML
        <p>Olá, <strong>#{CGI.escapeHTML(recruiter_name)}</strong>! Tudo bom? 👋</p>

        <p>O candidato <strong><a href="#{CGI.escapeHTML(candidate_url)}">#{CGI.escapeHTML(candidate_name)}</a></strong> da vaga <strong><a href="#{CGI.escapeHTML(job_url)}">#{CGI.escapeHTML(job_title)}</a></strong> terminou o screening! Veja minha avaliação sobre ele:</p>

        <hr>

        <h3>#{recommendation_emoji} Minha Recomendação: #{recommendation_text}</h3>

        <h4>📋 Resumo da Análise:</h4>
        <p>#{CGI.escapeHTML(summary || "Não disponível")}</p>

        <h4>💪 Pontos Fortes que identifiquei:</h4>
        #{strengths_html}

        <h4>⚠️ Pontos de Atenção:</h4>
        #{weaknesses_html}

        <h4>🎯 Minha Sugestão de Próximos Passos:</h4>
        <p>#{CGI.escapeHTML(next_steps || "Não disponível")}</p>

        <hr>
        <p>
          <a href="#{CGI.escapeHTML(candidate_url)}">👤 Ver perfil do candidato</a> |#{' '}
          <a href="#{CGI.escapeHTML(job_url)}">💼 Ver detalhes da vaga</a>
        </p>
        <p><em>Qualquer dúvida, estou à disposição! 😊<br>Lia - Inteligência Artificial de Recrutamento</em></p>
      HTML
    end

    def weakness_line_text(w)
      if w.is_a?(Hash)
        text = (w["text"] || w[:text]).to_s
        sev = w["severity"] || w[:severity]
        return text if sev.blank?

        "#{text} (#{sev})"
      else
        w.to_s
      end
    end

    def register_teams_chat_subscription(lia_user, recruiter, chat_id)
      return if chat_id.blank?

      account = Current.account || recruiter.account
      tenant = account&.tenant || (Apartment::Tenant.current rescue "public")

      TeamsChatSubscription.find_or_create_by!(
        lia_user_id: lia_user.id,
        recruiter_user_id: recruiter.id
      ) do |sub|
        sub.account_id = account.id
        sub.chat_id = chat_id
        sub.tenant = tenant
        sub.status = "active"
      end.tap do |sub|
        sub.update!(chat_id: chat_id, status: "active") if sub.chat_id != chat_id
      end

      MicrosoftService::TeamsSubscriptionService.create_or_renew(lia_user, chat_id)
    rescue StandardError => e
      Rails.logger.error "[PerCandidateNotificationJob] Failed to register Teams chat subscription: #{e.message}"
    end
  end
end
