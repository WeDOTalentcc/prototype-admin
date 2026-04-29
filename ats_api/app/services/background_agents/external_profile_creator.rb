# frozen_string_literal: true

module BackgroundAgents
  class ExternalProfileCreator
    def initialize(account:, sourcing:, background_agent:)
      @account = account
      @sourcing = sourcing
      @background_agent = background_agent
    end

    def call(data, provider)
      ext_id = data[:external_id].to_s.presence || data[:candidate_id].to_s
      return nil if ext_id.blank?

      existing = ProfileDeduplicator.find_existing_external(
        account_id: @account.id, external_id: ext_id, data: data
      )
      return existing if existing

      raw = (data[:raw_profile] || {}).with_indifferent_access
      linkedin_slug = data[:linkedin_slug].presence || ProfileDeduplicator.extract_linkedin_slug(data[:linkedin_url]) || ext_id

      skills = Array(data[:skills])
      skills_data = skills.map do |s|
        { name: s, level: "mentioned", source: "background_agent", added_at: Time.current.iso8601 }
      end

      experiences = Array(data[:experiences].presence || raw[:experiences])
      educations = Array(data[:educations].presence || raw[:educations])
      certifications = Array(data[:certifications].presence || raw[:certifications])
      awards = Array(data[:awards].presence || raw[:awards])
      expertise = Array(data[:expertise].presence || raw[:expertise])
      languages = Array(data[:languages].presence || raw[:languages])

      current_company = data[:company].presence || extract_current_company(experiences)
      current_title = extract_current_title(experiences) || data[:title]

      curriculum_text = CurriculumTextBuilder.call(
        data: data, experiences: experiences, skills: skills,
        certifications: certifications, languages: languages
      )

      profile_data = raw.presence || build_profile_data(data, experiences)

      SourcedProfile.create!(
        sourcing: @sourcing,
        account: @account,
        uid: SecureRandom.uuid,
        provider: provider,
        external_id: ext_id,
        linkedin_slug: linkedin_slug,
        linkedin_url: data[:linkedin_url],
        name: data[:name],
        first_name: data[:first_name].presence || raw[:first_name],
        last_name: data[:last_name].presence || raw[:last_name],
        email: data[:email],
        title: data[:title],
        summary: data[:summary],
        picture_url: data[:picture_url].presence || raw[:picture_url],
        estimated_age: data[:estimated_age] || raw[:estimated_age],
        city: data[:city].presence || raw[:city],
        state: data[:state].presence || raw[:state],
        country: data[:country].presence || raw[:country],
        location: data[:location],
        remote_work: data[:remote_work] || raw[:remote_work],
        current_company: current_company,
        current_title: current_title,
        role_name: data[:title],
        position_level: data[:position_level].presence || raw[:position_level],
        total_experience_years: data[:experience_years] || raw[:total_experience_years],
        is_decision_maker: data[:is_decision_maker] || raw[:is_decision_maker] || false,
        expertise: expertise,
        skills_data: skills_data,
        languages_data: languages,
        experiences_data: experiences,
        educations_data: educations,
        certifications_data: certifications,
        awards_data: awards,
        followers_count: data[:followers_count] || raw[:followers_count],
        connections_count: data[:connections_count] || raw[:connections_count],
        profile_data: profile_data,
        curriculum_text: curriculum_text,
        status: "new",
        has_emails: data[:email].present?,
        has_phone_numbers: false,
        profile_updated_at: Time.current
      )
    rescue StandardError => e
      Rails.logger.error "[BackgroundAgent:#{@background_agent.id}] External profile creation failed (#{provider}, ext_id=#{ext_id}): #{e.message}"
      nil
    end

    private

    def extract_current_company(experiences)
      experiences.each do |exp|
        roles = exp.dig("company_roles") || []
        current = roles.find { |r| r["is_current_experience"] }
        return exp.dig("company_info", "name") if current
      end
      nil
    end

    def extract_current_title(experiences)
      experiences.each do |exp|
        roles = exp.dig("company_roles") || []
        current = roles.find { |r| r["is_current_experience"] }
        return current["title"] if current
      end
      nil
    end

    def build_profile_data(data, experiences)
      {
        docid: data[:external_id],
        title: data[:title],
        summary: data[:summary],
        location: data[:location],
        first_name: data[:first_name],
        last_name: data[:last_name],
        experiences: experiences,
        picture_url: data[:picture_url],
        linkedin_slug: data[:linkedin_slug],
        total_experience_years: data[:experience_years],
        has_emails: data[:email].present?,
        has_phone_numbers: false
      }
    end
  end
end
