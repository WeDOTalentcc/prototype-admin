# frozen_string_literal: true

module BackgroundAgents
  class BuildSearchContextService
    def initialize(background_agent:)
      @agent = background_agent
    end

    def call
      {
        agent: agent_context,
        target_type: @agent.target_type,
        job: @agent.job_agent? ? job_context : nil,
        list: @agent.list_agent? ? list_context : nil,
        feedback_history: feedback_context,
        feedback_summary: build_feedback_summary,
        presented_profile_ids: presented_profile_ids,
        presented_external_identifiers: presented_external_identifiers,
        candidates_already_in_job: candidates_already_in_job,
        candidates_already_in_list: @agent.list_agent? ? candidates_already_in_list : [],
        search_history: @agent.search_history.last(10),
        search_config: @agent.search_iteration_config
      }
    end

    private

    def agent_context
      {
        id: @agent.id,
        name: @agent.name,
        criteria_text: @agent.criteria_text,
        criteria_structured: @agent.criteria_structured,
        calibration_state: @agent.calibration_state,
        mode: @agent.mode,
        sources: @agent.sources,
        min_score_threshold: @agent.min_score_threshold,
        extracted_preferences: @agent.extracted_preferences,
        diversity_queries: @agent.diversity_queries,
        remaining_today: @agent.remaining_today,
        total_delivered: @agent.total_delivered,
        total_approved: @agent.total_approved,
        total_rejected: @agent.total_rejected,
        approval_rate: @agent.approval_rate
      }
    end

    def job_context
      job = @agent.job
      {
        id: job.id,
        title: job.title,
        description: job.description,
        city: job.city,
        state: job.state,
        country: job.country,
        seniority: job.seniority,
        skills: job.skills.pluck(:name),
        has_embedding: job.has_embedding?
      }
    end

    def feedback_context
      recent_feedbacks = @agent.agent_feedbacks
        .includes(sourced_profile_sourcing: :sourced_profile)
        .order(created_at: :desc)
        .limit(50)

      {
        recent: recent_feedbacks.map { |f| serialize_feedback(f) },
        summary: {
          total_approved: @agent.total_approved,
          total_rejected: @agent.total_rejected,
          approval_rate: @agent.approval_rate
        }
      }
    end

    def serialize_feedback(feedback)
      sps = feedback.sourced_profile_sourcing
      profile = sps&.sourced_profile
      {
        action: feedback.action,
        reason: feedback.reason,
        score: sps&.score,
        profile_name: profile&.name,
        profile_title: profile&.headline || profile&.title,
        profile_company: profile&.current_company,
        profile_location: [profile&.city, profile&.state].compact.join(", ").presence,
        profile_skills: (profile&.skills_data || []).first(10)
      }
    end

    def build_feedback_summary
      feedbacks = @agent.agent_feedbacks
        .includes(sourced_profile_sourcing: :sourced_profile)
        .order(created_at: :desc)
        .limit(30)

      approved = feedbacks.select { |f| f.action == "approved" }
      rejected = feedbacks.select { |f| f.action == "rejected" }

      approved_profiles = approved.filter_map { |f| f.sourced_profile_sourcing&.sourced_profile }
      rejected_profiles = rejected.filter_map { |f| f.sourced_profile_sourcing&.sourced_profile }

      {
        approved_count: @agent.total_approved,
        rejected_count: @agent.total_rejected,
        approved_patterns: extract_patterns(approved_profiles),
        top_rejection_reasons: extract_rejection_reasons(rejected),
        approved_examples: approved.first(5).map { |f| serialize_feedback(f) },
        rejected_examples: rejected.first(5).map { |f| serialize_feedback(f) }
      }
    end

    def extract_patterns(profiles)
      return {} if profiles.empty?

      skills = profiles.flat_map { |p| Array(p.skills_data) }.tally.sort_by { |_, v| -v }.first(10).map(&:first)
      companies = profiles.filter_map(&:current_company).tally.sort_by { |_, v| -v }.first(5).map(&:first)
      titles = profiles.filter_map { |p| p.headline || p.title }.tally.sort_by { |_, v| -v }.first(5).map(&:first)

      {
        common_skills: skills,
        common_companies: companies,
        common_titles: titles,
        avg_experience_years: avg_experience(profiles)
      }
    end

    def avg_experience(profiles)
      years = profiles.filter_map(&:total_experience_years)
      return nil if years.empty?

      (years.sum.to_f / years.size).round(1)
    end

    def extract_rejection_reasons(rejected_feedbacks)
      rejected_feedbacks
        .filter_map(&:reason)
        .reject(&:blank?)
        .tally
        .sort_by { |_, v| -v }
        .first(5)
        .map { |reason, count| { reason: reason, count: count } }
    end

    def presented_profile_ids
      sourcing = @agent.sourcings.first
      return [] unless sourcing

      sourcing.sourced_profile_sourcings
        .joins(:sourced_profile)
        .where(is_deleted: false)
        .where.not(sourced_profiles: { candidate_id: nil })
        .pluck("sourced_profiles.candidate_id")
        .uniq
    end

    def presented_external_identifiers
      sourcing = @agent.sourcings.first
      return { emails: [], linkedin_urls: [], external_ids: [] } unless sourcing

      rows = sourcing.sourced_profile_sourcings
        .joins(:sourced_profile)
        .where(is_deleted: false)
        .where(sourced_profiles: { candidate_id: nil })
        .pluck("sourced_profiles.email", "sourced_profiles.linkedin_url", "sourced_profiles.external_id")

      {
        emails: rows.map(&:first).compact.reject(&:blank?).map(&:downcase).uniq,
        linkedin_urls: rows.map(&:second).compact.reject(&:blank?).map(&:downcase).uniq,
        external_ids: rows.map(&:third).compact.reject(&:blank?).uniq
      }
    end

    def candidates_already_in_job
      job = @agent.job
      return [] unless job

      job.applies
        .where(is_deleted: false)
        .pluck(:candidate_id)
        .uniq
    end

    def list_context
      list = @agent.list
      return {} unless list

      {
        id: list.id,
        name: list.name,
        description: list.description,
        candidates_count: list.candidates_count
      }
    end

    def candidates_already_in_list
      list = @agent.list
      return [] unless list

      list.list_relationships
        .where(is_deleted: false, reference_type: %w[Candidate SourcedProfileSourcing])
        .pluck(:reference_id)
        .uniq
    end
  end
end
