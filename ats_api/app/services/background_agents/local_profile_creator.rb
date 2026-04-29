# frozen_string_literal: true

module BackgroundAgents
  class LocalProfileCreator
    def initialize(account:, sourcing:, background_agent:)
      @account = account
      @sourcing = sourcing
      @background_agent = background_agent
    end

    def call(candidate_data)
      candidate = Candidate.find_by(id: candidate_data[:candidate_id])
      return nil unless candidate

      existing = find_existing(candidate)
      return existing if existing

      SourcedProfile.create!(
        sourcing: @sourcing,
        account: @account,
        candidate: candidate,
        uid: SecureRandom.uuid,
        provider: "local",
        external_id: "internal_#{@sourcing.id}_#{candidate.id}",
        name: candidate.name,
        email: candidate.email,
        phone: candidate.phone || candidate.mobile_phone,
        title: candidate.role_name,
        city: candidate.city,
        state: candidate.state,
        location: [candidate.city, candidate.state].compact.join(", "),
        current_company: candidate.current_company,
        role_name: candidate.role_name,
        status: "new",
        has_emails: candidate.email.present?,
        has_phone_numbers: (candidate.phone || candidate.mobile_phone).present?
      )
    rescue StandardError => e
      Rails.logger.error "[BackgroundAgent:#{@background_agent.id}] Local profile creation failed: #{e.message}"
      nil
    end

    private

    def find_existing(candidate)
      by_candidate = SourcedProfile.find_by(account_id: @account.id, candidate_id: candidate.id, is_deleted: false)
      return by_candidate if by_candidate

      scope = SourcedProfile.where(account_id: @account.id, is_deleted: false)

      phone = candidate.phone.presence || candidate&.mobile_phone
      if phone.present?
        by_phone = scope.find_by(phone: phone)
        return by_phone if by_phone
      end

      if candidate.email.present?
        by_email = scope.find_by(email: candidate.email)
        return by_email if by_email
      end

      linkedin_url = candidate&.linkedin_url || candidate&.linkedin
      if linkedin_url.present?
        slug = ProfileDeduplicator.extract_linkedin_slug(linkedin_url)
        by_linkedin = scope.find_by(linkedin_slug: slug) if slug.present?
        return by_linkedin if by_linkedin
      end

      if candidate.name.present? && candidate.current_company.present? && candidate.role_name.present?
        scope.where(
          "LOWER(name) = ? AND LOWER(current_company) = ? AND LOWER(role_name) = ?",
          candidate.name.downcase,
          candidate.current_company.downcase,
          candidate.role_name.downcase
        ).first
      end
    end
  end
end
