# frozen_string_literal: true

module CalendarEvents
  class DailyAgendaService
    PER_PAGE_DEFAULT = 20
    PER_PAGE_MAX = 50

    Result = Struct.new(:days, :meta, keyword_init: true)

    def initialize(account_id:, params: {})
      @account_id = account_id
      @params = params
    end

    def call
      events = build_scope
      total = events.count
      paginated = paginate(events)

      Result.new(
        days: group_and_serialize(paginated),
        meta: build_meta(total)
      )
    end

    private

    attr_reader :account_id, :params

    def build_scope
      scope = base_scope
      scope = apply_time_filter(scope)
      scope = apply_search(scope)
      scope = apply_filters(scope)
      apply_ordering(scope)
    end

    def base_scope
      CalendarEvent
        .where(account_id: account_id)
        .includes(:organizer, :attendees, :meeting)
    end

    def apply_time_filter(scope)
      return scope.where("start_time >= :from AND end_time <= :to", from: from_date, to: to_date) if from_date && to_date
      return scope.where("start_time >= ?", from_date) if from_date
      return scope.where("end_time <= ?", to_date) if to_date

      case kind
      when "history"
        scope.where("end_time < ?", Time.current)
      else
        scope.where("start_time >= ?", Time.current.beginning_of_day)
      end
    end

    def apply_search(scope)
      return scope if search_term.blank?

      term = "%#{search_term.downcase}%"
      attendee_event_ids = CalendarEventAttendee
        .where("LOWER(name) LIKE ? OR LOWER(email) LIKE ?", term, term)
        .select(:calendar_event_id)

      scope.where(
        'LOWER(calendar_events.title) LIKE :term
         OR LOWER(calendar_events.description) LIKE :term
         OR LOWER(calendar_events.location) LIKE :term
         OR calendar_events.id IN (:ids)',
        term: term,
        ids: attendee_event_ids
      )
    end

    def apply_filters(scope)
      scope = scope.where(event_type: params[:event_type]) if params[:event_type].present?
      scope = scope.where(provider: params[:provider]) if params[:provider].present?
      scope = scope.where(is_cancelled: params[:is_cancelled]) if params[:is_cancelled].present?
      scope = scope.where(organizer_id: params[:organizer_id]) if params[:organizer_id].present?
      scope
    end

    def apply_ordering(scope)
      kind == "history" ? scope.order(start_time: :desc) : scope.order(start_time: :asc)
    end

    def paginate(scope)
      scope.offset(offset).limit(per_page)
    end

    def group_and_serialize(events)
      apply_map, candidate_map, job_map, relationship_candidate_map, feedback_lookup = preload_associations(events)

      events
        .group_by { |e| e.start_time.in_time_zone(timezone).to_date }
        .map { |date, day_events| serialize_day(date, day_events, apply_map, candidate_map, job_map, relationship_candidate_map, feedback_lookup) }
    end

    def preload_associations(events)
      event_ids = events.map(&:id)

      apply_ids = events.filter_map { |e| e.settings&.dig("apply_id")&.to_i }
      candidate_ids = events.filter_map { |e| e.settings&.dig("candidate_id")&.to_i }
      job_ids = events.filter_map { |e| e.settings&.dig("job_id")&.to_i }

      applies = Apply.where(id: apply_ids).index_by(&:id)
      candidate_ids_from_applies = applies.values.map(&:candidate_id)
      job_ids_from_applies = applies.values.map(&:job_id)

      relationships = MeetingRelationship
        .where(calendar_event_id: event_ids, reference_type: "Candidate")
        .select(:calendar_event_id, :reference_id, :apply_id)

      relationship_candidate_ids = relationships.map(&:reference_id)
      relationship_apply_ids = relationships.filter_map(&:apply_id)

      applies_from_relationships = Apply.where(id: relationship_apply_ids).index_by(&:id)
      job_ids_from_relationships = applies_from_relationships.values.map(&:job_id)

      all_candidate_ids = (candidate_ids + candidate_ids_from_applies + relationship_candidate_ids).uniq.compact
      all_job_ids = (job_ids + job_ids_from_applies + job_ids_from_relationships).uniq.compact

      candidates = Candidate.where(id: all_candidate_ids).index_by(&:id)
      jobs = Job.where(id: all_job_ids).index_by(&:id)

      relationship_candidate_map = relationships.each_with_object({}) do |rel, map|
        map[rel.calendar_event_id] = candidates[rel.reference_id]
      end

      applies.merge!(applies_from_relationships)

      all_apply_ids = applies.keys.compact
      feedback_apply_ids = CandidateFeedback.active
        .where(apply_id: all_apply_ids)
        .distinct
        .pluck(:apply_id)
        .to_set

      feedback_candidate_ids = CandidateFeedback.active
        .where(candidate_id: all_candidate_ids, apply_id: nil)
        .distinct
        .pluck(:candidate_id)
        .to_set

      feedback_lookup = { apply_ids: feedback_apply_ids, candidate_ids: feedback_candidate_ids }

      [ applies, candidates, jobs, relationship_candidate_map, feedback_lookup ]
    end

    def serialize_day(date, events, apply_map, candidate_map, job_map, relationship_candidate_map, feedback_lookup)
      {
        date: date.iso8601,
        events: events.map { |e| serialize_event(e, apply_map, candidate_map, job_map, relationship_candidate_map, feedback_lookup) }
      }
    end

    def serialize_event(event, apply_map, candidate_map, job_map, relationship_candidate_map, feedback_lookup)
      {
        id: event.id,
        title: event.title,
        description: event.description,
        provider: event.provider,
        provider_text: event.provider_text,
        event_type: event.event_type,
        event_type_text: event.event_type_text,
        start_time: event.start_time.iso8601,
        end_time: event.end_time.iso8601,
        timezone: event.timezone,
        duration_minutes: event.duration_minutes,
        is_all_day: event.is_all_day,
        is_cancelled: event.is_cancelled,
        is_deleted: event.is_deleted,
        importance: event.importance,
        status: event.status.to_s,
        sub_status: event.sub_status,
        sub_status_text: event.sub_status_text,
        join_url: event.join_url,
        has_online_meeting: event.has_online_meeting?,
        location: event.location,
        settings: event.settings,
        organizer: serialize_organizer(event),
        attendees: serialize_attendees(event),
        **enrich_with_references(event, apply_map, candidate_map, job_map, relationship_candidate_map, feedback_lookup)
      }
    end

    def serialize_organizer(event)
      {
        id: event.organizer_id,
        name: event.organizer&.name,
        email: event.organizer&.email
      }
    end

    def serialize_attendees(event)
      event.attendees.map do |a|
        {
          id: a.id,
          name: a.name,
          email: a.email,
          response_status: a.response_status,
          is_organizer: a.is_organizer
        }
      end
    end

    def enrich_with_references(event, apply_map, candidate_map, job_map, relationship_candidate_map, feedback_lookup)
      apply_id = event.settings&.dig("apply_id")&.to_i
      candidate_id = event.settings&.dig("candidate_id")&.to_i
      job_id = event.settings&.dig("job_id")&.to_i

      apply = apply_map[apply_id]
      resolved_candidate_id = candidate_id.presence || apply&.candidate_id
      resolved_job_id = job_id.presence || apply&.job_id

      candidate = candidate_map[resolved_candidate_id] || relationship_candidate_map[event.id]

      if candidate && apply.nil?
        rel_apply_id = MeetingRelationship
          .where(calendar_event_id: event.id, reference_type: "Candidate", reference_id: candidate.id)
          .pick(:apply_id)
        apply = apply_map[rel_apply_id] if rel_apply_id
        resolved_job_id ||= apply&.job_id
      end

      has_feedback = resolve_has_feedback(apply, resolved_candidate_id, feedback_lookup)

      {
        apply: apply ? serialize_apply(apply) : nil,
        candidate: candidate ? serialize_candidate(candidate) : nil,
        job: job_map[resolved_job_id] ? serialize_job(job_map[resolved_job_id]) : nil,
        has_feedback: has_feedback
      }
    end

    def resolve_has_feedback(apply, candidate_id, feedback_lookup)
      return feedback_lookup[:apply_ids].include?(apply.id) if apply
      return feedback_lookup[:candidate_ids].include?(candidate_id) if candidate_id.present?

      false
    end

    def serialize_apply(apply)
      {
        id: apply.id,
        total_score: apply.total_score,
        cv_match: apply.cv_match,
        selective_process_status: apply.selective_process_status,
        evaluation_candidate_status: apply.evaluation_candidate_status
      }
    end

    def serialize_candidate(candidate)
      profile_data = candidate.external_profile_data.presence || {}

      {
        id: candidate.id,
        uid: candidate.uid,
        name: candidate.name,
        email: candidate.email,
        avatar_url: candidate.avatar_url,
        role_name: candidate.role_name,
        current_company: candidate.current_company,
        city: candidate.city,
        state: candidate.state,
        external_profile_data: profile_data.present? ? {
          headline: profile_data["headline"] || profile_data["title"],
          current_position: profile_data.dig("positions", 0) || profile_data.dig("experience", 0),
          positions: profile_data["positions"] || profile_data["experience"]
        } : nil
      }
    end

    def serialize_job(job)
      {
        id: job.id,
        external_id: job.external_id,
        title: job.title,
        city: job.city,
        state: job.state
      }
    end

    def kind
      @kind ||= params[:kind].to_s.downcase == "history" ? "history" : "upcoming"
    end

    def search_term
      @search_term ||= params[:search].presence
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

    def timezone
      @timezone ||= ActiveSupport::TimeZone[params[:timezone].to_s] ||
                    ActiveSupport::TimeZone["America/Sao_Paulo"]
    end

    def from_date
      return nil if params[:from].blank?
      Time.zone.parse(params[:from].to_s).beginning_of_day
    rescue ArgumentError
      nil
    end

    def to_date
      return nil if params[:to].blank?
      Time.zone.parse(params[:to].to_s).end_of_day
    rescue ArgumentError
      nil
    end

    def build_meta(total)
      total_pages = total.zero? ? 1 : (total.to_f / per_page).ceil
      {
        total: total,
        page: page,
        per_page: per_page,
        total_pages: total_pages,
        kind: kind
      }
    end
  end
end
