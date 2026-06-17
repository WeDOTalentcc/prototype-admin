class EmailFollowupCheckerJob < ApplicationJob
  queue_as :default

  MAX_ATTEMPTS = 7
  INTERVAL_HOURS = 24

  def perform
    dispatch_ids = EmailFollowupStatus.pending.distinct.pluck(:dispatch_id)
    account_ids = Dispatch.where(id: dispatch_ids).distinct.pluck(:account_id)
    Account.where(id: account_ids).find_each do |account|
      next unless account.tenant.present?

      Apartment::Tenant.switch(account.tenant) do
        process_tenant_followups(account)
      end
    end
  end

  private

  def process_tenant_followups(account)
    due_followups = EmailFollowupStatus.due_for_retry
      .includes(dispatch: :user, candidate: [ :emails ])
      .limit(100)

    due_followups.find_each do |followup|
      next unless followup.can_retry?
      next if skip_followup?(followup, account)

      send_followup_email(followup)
      followup.schedule_next_attempt!
    end

    create_followups_for_recent_dispatches(account)
  end

  def skip_followup?(followup, account)
    return true if EmailUnsubscribe.unsubscribed?(account.id, followup.candidate.email)
    false
  end

  def send_followup_email(followup)
    original_dispatch = followup.dispatch
    user = original_dispatch.user

    Dispatches::CreateService.new(
      user: user,
      account: original_dispatch.account,
      params: {
        channel_type: "email",
        target_type: "ids",
        target_payload: { ids: [ followup.candidate_id ] },
        subject: followup_subject(followup.attempt_count, original_dispatch),
        body: followup_body(followup.attempt_count, original_dispatch),
        reference_type: original_dispatch.reference_type,
        reference_id: original_dispatch.reference_id,
        is_followup: true
      }
    ).call
  end

  def create_followups_for_recent_dispatches(account)
    recent_dispatches = Dispatch
      .where(created_at: 1.hour.ago..Time.current)
      .where(channel_type: "email")
      .where.not(reference_type: nil)
      .where.missing(:email_followup_status)

    recent_dispatches.find_each do |dispatch|
      next if dispatch.is_followup

      dispatch.candidates.find_each do |candidate|
        next if EmailUnsubscribe.unsubscribed?(account.id, candidate.email)

        EmailFollowupStatus.create!(
          dispatch: dispatch,
          candidate: candidate,
          account: account,
          next_attempt_at: INTERVAL_HOURS.hours.from_now
        )
      end
    end
  end

  def followup_subject(attempt, original_dispatch)
    case attempt
    when 1..3
      "Lembrete: #{original_dispatch.subject}"
    when 4..5
      "Segundo lembrete: #{original_dispatch.subject}"
    else
      "Última chance: #{original_dispatch.subject}"
    end
  end

  def followup_body(attempt, original_dispatch)
    base_body = original_dispatch.body

    intro = case attempt
    when 1
      "Oi, passei para lembrar sobre o email abaixo."
    when 2
      "Oi, vi que ainda não respondeu. Alguma novidade?"
    when 3
      "Oi, só confirmar se recebeu meus emails anteriores."
    when 4
      "Oi, gostaria muito de sua resposta sobre esta oportunidade."
    when 5
      "Oi, esta é minha última tentativa de contato."
    else
      "Oi, infelizmente não tive resposta. Vou arquivar seu contato."
    end

    "#{intro}\n\n---\n\n#{base_body}"
  end
end
