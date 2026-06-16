# frozen_string_literal: true

InterviewTagContext = Struct.new(:formatted_date, :formatted_deadline, keyword_init: true)

module PostInterview
  class DispatchService
    TRIGGER_EVENT = "interview_ended"

    def initialize(calendar_event: nil, interview_session: nil)
      @calendar_event = calendar_event
      @interview_session = interview_session
    end

    def call
      current_tenant = Apartment::Tenant.current rescue "unknown"

      template = find_template
      unless template
        return
      end

      ctx = resolve_context(template)
      unless ctx[:candidate]&.email.present?
        return
      end

      cancel_existing_pending_dispatches

      dispatch = create_dispatch(template, ctx)
      message = create_dispatch_message(dispatch, ctx)
      schedule_delivery(dispatch, message)
      dispatch
    end

    private

    attr_reader :calendar_event, :interview_session

    def find_template
      scope = EmailTemplate
        .where(is_automated: true, trigger_event: TRIGGER_EVENT, is_deleted: false)
        .order(updated_at: :desc)
      count = scope.count
      scope.first
    end

    def triggerable
      calendar_event || interview_session
    end

    def cancel_existing_pending_dispatches
      Dispatch
        .where(reference: triggerable, status: :pending)
        .where("target_payload->>'trigger_event' = ?", TRIGGER_EVENT)
        .update_all(status: :failed)
    end

    def resolve_context(template)
      if calendar_event
        resolve_calendar_event_context(template)
      else
        resolve_interview_session_context(template)
      end
    end

    def resolve_calendar_event_context(template)
      apply = Apply.find_by(id: calendar_event.apply_id)
      candidate = apply&.candidate
      job = apply&.job || Job.find_by(id: calendar_event.job_id)
      recruiter = calendar_event.organizer || apply&.user
      account = Account.find_by(id: calendar_event.account_id)

      build_context(
        candidate: candidate,
        job: job,
        recruiter: recruiter,
        account: account,
        event_date: calendar_event.start_time,
        template: template
      )
    end

    def resolve_interview_session_context(template)
      build_context(
        candidate: interview_session.candidate,
        job: interview_session.job,
        recruiter: interview_session.created_by,
        account: interview_session.account,
        event_date: Time.current,
        template: template
      )
    end

    def build_context(candidate:, job:, recruiter:, account:, event_date:, template:)
      interview_context = InterviewTagContext.new(
        formatted_date: I18n.l(event_date.to_date, format: :long),
        formatted_deadline: humanize_deadline(template.response_deadline_days || 7)
      )

      {
        candidate: candidate,
        job: job,
        recruiter: recruiter,
        account: account,
        entities: {
          candidate: candidate,
          job: job,
          user: recruiter,
          account: account,
          interview: interview_context
        }
      }
    end

    def create_dispatch(template, ctx)
      base_time = calendar_event ? calendar_event.end_time : Time.current
      delay = template.delay_hours || 0
      scheduled_for = delay.zero? ? Time.current : base_time + delay.hours

      rendered_subject = render_tags(template.subject, ctx[:entities])
      rendered_body = render_tags(template.content, ctx[:entities])

      Dispatch.create!(
        account_id: ctx[:account].id,
        user: ctx[:recruiter],
        reference: triggerable,
        channel_type: "email",
        status: :pending,
        name: template.name,
        subject: rendered_subject,
        body: rendered_body,
        scheduled_for: scheduled_for,
        provider: "mailgun",
        target_type: "ids",
        target_payload: {
          email_template_id: template.id,
          trigger_event: TRIGGER_EVENT,
          automated: true
        }
      )
    end

    def create_dispatch_message(dispatch, ctx)
      dispatch.dispatch_messages.create!(
        account_id: ctx[:account].id,
        recipient: ctx[:candidate],
        recipient_address: ctx[:candidate].email,
        status: :pending,
        subject: dispatch.subject,
        body: dispatch.body
      )
    end

    def schedule_delivery(dispatch, message)
      dispatch.update!(status: :processing)

      if dispatch.scheduled_for <= Time.current
        EmailWorker.perform_later(message.id, dispatch.account_id)
      else
        EmailWorker.set(wait_until: dispatch.scheduled_for).perform_later(message.id, dispatch.account_id)
      end
    end

    def render_tags(content, entities)
      TagReplacer::Service.call(content, record: entities)
    end

    def humanize_deadline(days)
      return "#{days} dias" if days.nil? || days <= 0

      case days
      when 1..3 then "#{days} dias úteis"
      when 4..7 then "1 semana"
      when 8..14 then "2 semanas"
      else "#{days} dias"
      end
    end
  end
end
