module SourcedProfiles
  class ProfileMatchingService
    def initialize(account_id:)
      @account_id = account_id
    end

    def find_duplicate(
      email: nil,
      phone: nil,
      cpf: nil,
      linkedin_url: nil,
      external_id: nil,
      **_unused
    )
      return nil unless @account_id.present?

      query = SourcedProfile.active.where(account_id: @account_id)
      find_by_unique_identifiers(query, external_id, cpf, email, linkedin_url, phone)
    end

    private

    def find_by_unique_identifiers(query, external_id, cpf, email, linkedin_url, phone)
      return query.find_by(external_id: external_id) if external_id.present?
      return query.find_by(cpf: cpf) if cpf.present?

      if email.present?
        profile = query.where("LOWER(email) = LOWER(?)", email).first
        return profile if profile
      end

      if linkedin_url.present?
        slug = extract_linkedin_slug(linkedin_url)
        profile = query.where("linkedin_url = ? OR linkedin_slug = ?", linkedin_url, slug).first
        return profile if profile
      end

      if phone.present?
        normalized = normalize_phone(phone)
        profile = query.where("phone = ? OR phone = ?", phone, normalized).first
        return profile if profile
      end

      nil
    end

    def extract_linkedin_slug(url)
      return nil unless url.present?
      return url if url.exclude?("/")
      url.split("/").last&.split("?")&.first
    end

    def normalize_phone(phone)
      return nil unless phone.present?
      phone.gsub(/\D/, "")
    end
  end
end
