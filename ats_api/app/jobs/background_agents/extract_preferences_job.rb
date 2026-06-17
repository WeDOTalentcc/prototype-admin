# frozen_string_literal: true

module BackgroundAgents
  class ExtractPreferencesJob
    include Sidekiq::Job

    sidekiq_options queue: :background_agents, retry: 2

    def perform(agent_id, account_id)
      account = Account.find_by(id: account_id)
      return unless account

      Apartment::Tenant.switch(account.tenant) do
        agent = BackgroundAgent.find_by(id: agent_id)
        return unless agent
        return unless agent.calibrated?

        preferences = extract_preferences(agent)
        agent.update!(extracted_preferences: preferences)

        Rails.logger.info "✅ [BackgroundAgents::ExtractPreferencesJob] Preferences extracted for agent #{agent.id}"
      end
    rescue StandardError => e
      Rails.logger.error "❌ [BackgroundAgents::ExtractPreferencesJob] #{e.message}"
      raise
    end

    private

    def extract_preferences(agent)
      approved = recent_feedbacks(agent, "approved")
      rejected = recent_feedbacks(agent, "rejected")

      approved_profiles = load_profiles(approved)
      rejected_profiles = load_profiles(rejected)

      build_preferences(approved_profiles, rejected_profiles, agent)
    end

    def recent_feedbacks(agent, action)
      agent.agent_feedbacks
        .where(action: action)
        .order(created_at: :desc)
        .limit(10)
        .includes(:sourced_profile_sourcing)
    end

    def load_profiles(feedbacks)
      feedbacks.filter_map do |fb|
        sps = fb.sourced_profile_sourcing
        next unless sps

        sp = sps.sourced_profile
        next unless sp

        {
          name: sp.name,
          title: sp.title,
          current_company: sp.current_company,
          location: [sp.city, sp.state, sp.country].compact.join(", "),
          skills: sp.skills_data || [],
          experience_years: sp.total_experience_years,
          score: sps.score,
          reason: fb.reason
        }
      end
    end

    def build_preferences(approved, rejected, agent)
      preferred_skills = extract_common_values(approved, :skills)
      avoided_patterns = rejected.filter_map { |r| r[:reason] }.uniq.first(5)

      preferred_titles = approved.filter_map { |p| p[:title] }.tally.sort_by { |_, v| -v }.first(5).map(&:first)
      preferred_companies = approved.filter_map { |p| p[:current_company] }.tally.sort_by { |_, v| -v }.first(3).map(&:first)
      preferred_locations = approved.filter_map { |p| p[:location] }.reject(&:blank?).tally.sort_by { |_, v| -v }.first(3).map(&:first)

      avg_experience = approved.filter_map { |p| p[:experience_years] }
      experience_range = avg_experience.any? ? { min: avg_experience.min, max: avg_experience.max } : {}

      {
        preferred_skills: preferred_skills,
        preferred_titles: preferred_titles,
        preferred_companies: preferred_companies,
        preferred_locations: preferred_locations,
        experience_range: experience_range,
        avoid_patterns: avoided_patterns,
        sample_size: { approved: approved.size, rejected: rejected.size },
        extracted_at: Time.current.iso8601
      }
    end

    def extract_common_values(profiles, key)
      profiles
        .flat_map { |p| Array(p[key]) }
        .tally
        .sort_by { |_, v| -v }
        .first(10)
        .map(&:first)
    end
  end
end
