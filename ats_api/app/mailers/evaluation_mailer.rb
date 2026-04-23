class EvaluationMailer < ApplicationMailer
  default from: ENV.fetch("MAILGUN_EMAIL", "contato@wedotalent.cc")

  layout false

  helper_method :evaluation_candidate_url

  def invitation
    set_common_variables
    mail(to: @recipient_email, subject: "#{@company_name} — Convite para conversa sobre #{@job_title}")
  end

  def microsoft_invitation
    set_common_variables
    mail(to: @recipient_email, subject: "#{@company_name} — Convite para conversa sobre #{@job_title}")
  end

  def unified_invitation
    set_common_variables
    @channels = params[:channels] || []
    @decline_url = params[:decline_url]
    mail(to: @recipient_email, subject: "#{@company_name} — Convite para conversa sobre #{@job_title}")
  end

  def completion_notification
    @evaluation_candidate = params[:evaluation_candidate]
    @user = params[:user]
    @account = @user&.account
    @candidate_name = @evaluation_candidate.candidate&.name || "Candidato"
    @evaluation_name = @evaluation_candidate.evaluation&.name || "Avaliação"
    @job_title = @evaluation_candidate.job&.title || "a vaga"
    @company_name = @account&.name || "WeDO Talent"
    @front_url = ENV.fetch("FRONT_URL", "http://localhost:3000")
    @candidate_url = "#{@front_url}/user/candidates/#{@evaluation_candidate.candidate_id}"
    @completed_at = @evaluation_candidate.updated_at&.strftime("%d/%m/%Y %H:%M") || Time.now.strftime("%d/%m/%Y %H:%M")

    mail(
      to: @user.email,
      subject: "#{@candidate_name} concluiu a avaliação — #{@job_title}"
    )
  end

  def escalation_continue_screening
    set_common_variables
    mail(to: @recipient_email, subject: "#{@company_name} — Continue sua triagem")
  end

  def escalation_last_chance
    set_common_variables
    mail(to: @recipient_email, subject: "#{@company_name} — Última chance: complete sua triagem")
  end

  def escalation_alert_consultant
    @evaluation_candidate = params[:evaluation_candidate]
    @user = params[:user]
    @account = @user&.account
    @candidate_name = @evaluation_candidate.candidate&.name || "Candidato"
    @evaluation_name = @evaluation_candidate.evaluation&.name || "Avaliação"
    @job_title = @evaluation_candidate.job&.title || "a vaga"
    @company_name = @account&.name || "WeDO Talent"
    @front_url = ENV.fetch("FRONT_URL", "http://localhost:3000")
    @candidate_url = "#{@front_url}/user/candidates/#{@evaluation_candidate.candidate_id}"
    @created_at = @evaluation_candidate.created_at&.strftime("%d/%m/%Y %H:%M") || Time.now.strftime("%d/%m/%Y %H:%M")

    mail(
      to: @user.email,
      subject: "Alerta: Triagem não concluída — #{@candidate_name} (#{@job_title})"
    )
  end

  def decline_notification
    @evaluation_candidate = params[:evaluation_candidate]
    @user = params[:user]
    @account = @user&.account
    @candidate_name = @evaluation_candidate.candidate&.name || "Candidato"
    @candidate_email = @evaluation_candidate.candidate&.email || ""
    @evaluation_name = @evaluation_candidate.evaluation&.name || "Avaliação"
    @job_title = @evaluation_candidate.job&.title || "a vaga"
    @company_name = @account&.name || "WeDO Talent"
    @declined_reason = @evaluation_candidate.declined_reason
    @declined_at = @evaluation_candidate.declined_at&.strftime("%d/%m/%Y %H:%M") || Time.now.strftime("%d/%m/%Y %H:%M")
    @front_url = ENV.fetch("FRONT_URL", "http://localhost:3000")
    @candidate_url = "#{@front_url}/user/candidates/#{@evaluation_candidate.candidate_id}"

    mail(
      to: @user.email,
      subject: "#{@candidate_name} recusou a avaliação — #{@job_title}"
    )
  end

  private

  def set_common_variables
    @candidate = params[:candidate]
    @evaluation_candidate = params[:evaluation_candidate]
    @job = params[:job]
    @user = params[:user]

    @candidate_name = @candidate&.name&.split(" ")&.first || "Candidato"
    @candidate_full_name = @candidate&.name || @candidate&.email || "Candidato"
    @job_title = @job&.title || "a vaga"
    @evaluation_url = evaluation_candidate_url(@evaluation_candidate)
    @front_url = ENV.fetch("FRONT_URL", "http://localhost:3000")
    @recipient_email = @candidate&.email
    @company_name = @user&.account&.name || "WeDO Talent"
    @recruiter_name = @user&.name || "Equipe de Recrutamento"
    @recruiter_role = "Recrutador(a)"
  end

  def evaluation_candidate_url(evaluation_candidate)
    evaluation_candidate.get_evaluation_candidate_url
  end
end
