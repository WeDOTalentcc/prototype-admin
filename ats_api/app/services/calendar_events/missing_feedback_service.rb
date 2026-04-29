# frozen_string_literal: true

module CalendarEvents
  class MissingFeedbackService
    PER_PAGE_DEFAULT = 20
    PER_PAGE_MAX = 50

    Result = Struct.new(:events, :meta, keyword_init: true)

    def initialize(account_id:, user_id:, params: {})
      @account_id = account_id
      @user_id = user_id
      @params = params
    end

    def call
      events = build_scope
      total = events.count
      paginated = paginate(events)

      enriched = enrich_events(paginated)

      Result.new(
        events: enriched,
        meta: build_meta(total)
      )
    end

    private

    attr_reader :account_id, :user_id, :params

    def build_scope
      scope = CalendarEvent
        .where(account_id: account_id, is_deleted: false, is_cancelled: false)
        .where(event_type: "interview")
        .where("end_time < ?", Time.current)

      scope = scope.where("end_time >= ?", Time.zone.parse(params[:from].to_s).beginning_of_day) if params[:from].present?
      scope = scope.where("end_time <= ?", Time.zone.parse(params[:to].to_s).end_of_day) if params[:to].present?
      scope = scope.where(organizer_id: params[:organizer_id]) if params[:organizer_id].present?
      scope = scope.where(job_id: params[:job_id]) if params[:job_id].present?

      apply_ids_with_feedback = CandidateFeedback.active
        .where(user_id: user_id)
        .where.not(apply_id: nil)
        .pluck(:apply_id)

      candidate_ids_with_feedback = CandidateFeedback.active
        .where(user_id: user_id, apply_id: nil)
        .where.not(candidate_id: nil)
        .pluck(:candidate_id)

      event_ids_with_apply_feedback = CalendarEvent
        .where(account_id: account_id)
        .where("settings->>'apply_id' IS NOT NULL")
        .where("CAST(settings->>'apply_id' AS INTEGER) IN (?)", apply_ids_with_feedback)
        .pluck(:id) if apply_ids_with_feedback.any?

      event_ids_with_candidate_feedback = MeetingRelationship
        .where(reference_type: "Candidate", reference_id: candidate_ids_with_feedback)
        .pluck(:calendar_event_id) if candidate_ids_with_feedback.any?

      exclude_ids = ((event_ids_with_apply_feedback || []) + (event_ids_with_candidate_feedback || [])).uniq
      scope = scope.where.not(id: exclude_ids) if exclude_ids.any?

      scope.order(end_time: :desc)
    end

    def paginate(scope)
      scope.offset(offset).limit(per_page)
    end

    def enrich_events(events)
      apply_ids = events.filter_map { |e| e.settings&.dig("apply_id")&.to_i }
      candidate_ids = events.filter_map { |e| e.settings&.dig("candidate_id")&.to_i }

      applies = Apply.where(id: apply_ids).includes(:candidate, :job).index_by(&:id)

      rel_map = MeetingRelationship
        .where(calendar_event_id: events.map(&:id), reference_type: "Candidate")
        .each_with_object({}) { |r, h| h[r.calendar_event_id] = r }

      all_candidate_ids = (candidate_ids + applies.values.map(&:candidate_id) + rel_map.values.map(&:reference_id)).uniq.compact
      candidates = Candidate.where(id: all_candidate_ids).index_by(&:id)

      all_job_ids = (events.filter_map { |e| e.settings&.dig("job_id")&.to_i } + applies.values.map(&:job_id)).uniq.compact
      jobs = Job.where(id: all_job_ids).index_by(&:id)

      events.map { |event| serialize_event(event, applies, candidates, jobs, rel_map) }
    end

    def serialize_event(event, applies, candidates, jobs, rel_map)
      apply_id = event.settings&.dig("apply_id")&.to_i
      apply = applies[apply_id]
      candidate_id = event.settings&.dig("candidate_id")&.to_i.presence || apply&.candidate_id || rel_map[event.id]&.reference_id
      job_id = event.settings&.dig("job_id")&.to_i.presence || apply&.job_id

      candidate = candidates[candidate_id]
      job = jobs[job_id]

      {
        id: event.id,
        title: event.title,
        event_type: event.event_type,
        start_time: event.start_time.iso8601,
        end_time: event.end_time.iso8601,
        duration_minutes: event.duration_minutes,
        candidate: candidate ? { id: candidate.id, name: candidate.name, email: candidate.email } : nil,
        job: job ? { id: job.id, title: job.title } : nil,
        apply_id: apply&.id,
        days_since_interview: ((Time.current - event.end_time) / 1.day).to_i
      }
    end

    def page
      @page ||= [ params[:page].to_i, 1 ].max
    end

    def per_page
      @per_page ||= begin
        value = params[:per_page].to_i
        return PER_PAGE_DEFAULT if value <= 0
        [ value, PER_PAGE_MAX ].min
      end
    end

    def offset
      (page - 1) * per_page
    end

    def build_meta(total)
      {
        total: total,
        page: page,
        per_page: per_page,
        total_pages: (total.to_f / per_page).ceil
      }
    end
  end
end
