# frozen_string_literal: true

module Dashboard
  class BriefingService
    MAX_ITEMS_PER_SECTION = 10

    def initialize(user:, since: 24.hours.ago, timezone: "America/Sao_Paulo")
      @user = user
      @since = since
      @timezone = timezone
    end

    def call
      {
        generated_at: Time.current.in_time_zone(@timezone),
        user_name: @user.name,
        summary: build_summary,
        alerts: fetch_alerts,
        new_applies: fetch_new_applies,
        todays_agenda: fetch_todays_agenda,
        completed_evaluations: fetch_completed_evaluations,
        aging_applies: fetch_aging_applies,
        recent_movements: fetch_recent_movements,
        no_shows: fetch_no_shows,
        chat_abandonment: fetch_chat_abandonment
      }
    end

    private

    def build_summary
      {
        new_applies: Apply.where(is_deleted: false).where("applies.created_at >= ?", @since).count,
        pipeline_movements: ApplyStatus.where("apply_statuses.created_at >= ?", @since).count,
        interviews_today: todays_events_scope.count,
        evaluations_completed: EvaluationCandidate.where(completed: true).where("evaluation_candidates.updated_at >= ?", @since).count,
        pending_alerts: pending_alerts_count,
        active_jobs: Job.where(is_active: true, is_deleted: false, is_archived: false).count
      }
    end

    def fetch_alerts
      Jobs::AlertsService.new(account_id: @user.account_id).call
    end

    def fetch_new_applies
      Apply.where(is_deleted: false)
           .where("applies.created_at >= ?", @since)
           .joins(:candidate, :job)
           .select(
             "applies.id as apply_id",
             "candidates.name as candidate_name",
             "jobs.title as job_title",
             "applies.cv_match",
             "candidates.source",
             "applies.created_at"
           )
           .order("applies.cv_match DESC NULLS LAST")
           .limit(MAX_ITEMS_PER_SECTION)
           .map do |a|
             {
               apply_id: a.apply_id,
               candidate_name: a.candidate_name,
               job_title: a.job_title,
               cv_match: a.cv_match&.to_f,
               source: a.source,
               created_at: a.created_at
             }
           end
    end

    def fetch_todays_agenda
      today = Time.current.in_time_zone(@timezone)
      day_start = today.beginning_of_day
      day_end = today.end_of_day

      CalendarEvent.where(is_deleted: false, is_cancelled: false)
                   .where(start_time: day_start..day_end)
                   .left_joins(:apply)
                   .joins("LEFT JOIN candidates ON applies.candidate_id = candidates.id")
                   .joins("LEFT JOIN jobs ON calendar_events.job_id = jobs.id")
                   .select(
                     "calendar_events.start_time",
                     "calendar_events.end_time",
                     "calendar_events.title",
                     "calendar_events.event_type",
                     "calendar_events.provider",
                     "calendar_events.sub_status",
                     "candidates.name as candidate_name",
                     "jobs.title as job_title"
                   )
                   .order(:start_time)
                   .limit(MAX_ITEMS_PER_SECTION)
                   .map do |ce|
                     {
                       time: ce.start_time&.in_time_zone(@timezone)&.strftime("%H:%M"),
                       end_time: ce.end_time&.in_time_zone(@timezone)&.strftime("%H:%M"),
                       candidate_name: ce.try(:candidate_name),
                       job_title: ce.try(:job_title),
                       type: ce.event_type,
                       provider: ce.provider,
                       sub_status: ce.sub_status
                     }
                   end
    end

    def fetch_completed_evaluations
      EvaluationCandidate.where(completed: true)
                         .where("evaluation_candidates.updated_at >= ?", @since)
                         .joins(:candidate, :evaluation)
                         .joins("LEFT JOIN jobs ON evaluation_candidates.job_id = jobs.id")
                         .select(
                           "candidates.name as candidate_name",
                           "evaluations.name as evaluation_name",
                           "jobs.title as job_title",
                           "evaluation_candidates.score",
                           "evaluation_candidates.wsi_classification",
                           "evaluation_candidates.wsi_summary",
                           "evaluation_candidates.updated_at as completed_at"
                         )
                         .order("evaluation_candidates.updated_at DESC")
                         .limit(MAX_ITEMS_PER_SECTION)
                         .map do |ec|
                           {
                             candidate_name: ec.candidate_name,
                             evaluation_name: ec.evaluation_name,
                             job_title: ec.try(:job_title),
                             score: ec.score&.to_f,
                             wsi_classification: ec.wsi_classification,
                             wsi_summary: ec.wsi_summary,
                             completed_at: ec.completed_at
                           }
                         end
    end

    def fetch_aging_applies
      Applies::AgingQuery.new(days: 3)
                         .call
                         .limit(MAX_ITEMS_PER_SECTION)
                         .map do |a|
                           {
                             candidate_name: a.candidate_name,
                             job_title: a.job_title,
                             current_stage: a.stage_name,
                             days_in_stage: a.days_in_stage.to_i,
                             severity: classify_severity(a.days_in_stage.to_i)
                           }
                         end
    end

    def fetch_recent_movements
      ApplyStatus.where("apply_statuses.created_at >= ?", @since)
                 .joins(apply: [ :candidate, :job ])
                 .joins(:selective_process)
                 .joins("LEFT JOIN users ON apply_statuses.user_id = users.id")
                 .select(
                   "candidates.name as candidate_name",
                   "jobs.title as job_title",
                   "selective_processes.name as to_stage",
                   "users.name as moved_by",
                   "apply_statuses.created_at as moved_at"
                 )
                 .order("apply_statuses.created_at DESC")
                 .limit(MAX_ITEMS_PER_SECTION)
                 .map do |as|
                   {
                     candidate_name: as.candidate_name,
                     job_title: as.job_title,
                     to_stage: as.to_stage,
                     moved_by: as.try(:moved_by),
                     moved_at: as.moved_at
                   }
                 end
    end

    def fetch_no_shows
      Meeting.where(is_deleted: false, sub_status: "no_show")
             .where("meetings.start_time >= ?", @since)
             .joins("LEFT JOIN applies ON meetings.apply_id = applies.id")
             .joins("LEFT JOIN candidates ON applies.candidate_id = candidates.id")
             .joins("LEFT JOIN jobs ON meetings.job_id = jobs.id")
             .select(
               "candidates.name as candidate_name",
               "jobs.title as job_title",
               "meetings.start_time as scheduled_at"
             )
             .order("meetings.start_time DESC")
             .limit(MAX_ITEMS_PER_SECTION)
             .map do |m|
               {
                 candidate_name: m.try(:candidate_name),
                 job_title: m.try(:job_title),
                 scheduled_at: m.scheduled_at
               }
             end
    end

    def fetch_chat_abandonment
      alerts = Jobs::AlertsService.new(account_id: @user.account_id).call
      alerts[:chat_abandonment] || []
    end

    def todays_events_scope
      today = Time.current.in_time_zone(@timezone)
      CalendarEvent.where(is_deleted: false, is_cancelled: false)
                   .where(start_time: today.beginning_of_day..today.end_of_day)
    end

    def pending_alerts_count
      alerts = Jobs::AlertsService.new(account_id: @user.account_id).call
      alerts[:summary][:total_alerts]
    rescue StandardError
      0
    end

    def classify_severity(days)
      return "critical" if days >= 5
      return "warning" if days >= 3

      "attention"
    end
  end
end
