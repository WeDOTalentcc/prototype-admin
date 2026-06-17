# frozen_string_literal: true

module BackgroundAgents
  class ProfileDeduplicator
    def self.extract_linkedin_slug(url)
      return nil if url.blank?

      match = url.match(%r{linkedin\.com/in/([^/?]+)})
      match&.[](1)
    end

    def self.find_existing_external(account_id:, external_id:, data:)
      scope = SourcedProfile.where(account_id: account_id, is_deleted: false)

      by_ext = scope.find_by(external_id: external_id)
      return by_ext if by_ext

      if data[:linkedin_url].present?
        slug = extract_linkedin_slug(data[:linkedin_url])
        if slug.present?
          by_linkedin = scope.find_by(linkedin_slug: slug)
          return by_linkedin if by_linkedin
        end
      end

      if data[:email].present?
        by_email = scope.find_by(email: data[:email])
        return by_email if by_email
      end

      if data[:name].present? && data[:company].present? && data[:title].present?
        scope.where(
          "LOWER(name) = ? AND LOWER(current_company) = ? AND LOWER(role_name) = ?",
          data[:name].to_s.downcase,
          data[:company].to_s.downcase,
          data[:title].to_s.downcase
        ).first
      end
    end
  end
end
