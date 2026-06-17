module Apify
  class LinkedinSearchService
    class Profile
      class ParseError < StandardError; end

      # Campos obrigatorios para criar um SourcedProfile valido.
      # Ausencia de qualquer um desses = perfil inutilizavel — falhar alto, nao silencio.
      REQUIRED_FIELDS = {
        publicIdentifier: "public_identifier",
        linkedinUrl: "linkedin_url"
      }.freeze

      attr_reader :raw_data

      def initialize(data)
        @raw_data = data.deep_symbolize_keys
        validate!
      end

      def valid?
        REQUIRED_FIELDS.all? { |key, _| raw_data[key].present? }
      end

      private

      def validate!
        missing = REQUIRED_FIELDS.filter_map { |key, label| label unless raw_data[key].present? }
        return if missing.empty?

        raise ParseError, "Perfil Apify invalido — campos obrigatorios ausentes: #{missing.join(", ")} " \
                          "(raw keys: #{raw_data.keys.first(10).inspect})"
      end

      public

      def id
        raw_data[:id]
      end

      def public_identifier
        raw_data[:publicIdentifier]
      end

      def linkedin_url
        raw_data[:linkedinUrl]
      end

      def object_urn
        raw_data[:objectUrn]
      end

      def first_name
        raw_data[:firstName]
      end

      def last_name
        raw_data[:lastName]
      end

      def full_name
        "#{first_name} #{last_name}".strip
      end

      def headline
        raw_data[:headline]
      end

      def about
        raw_data[:about]
      end

      def photo_url
        raw_data[:photo]
      end

      def profile_picture
        @profile_picture ||= raw_data[:profilePicture]
      end

      def profile_picture_url(size: nil)
        return photo_url unless profile_picture.is_a?(Hash)

        sizes = profile_picture[:sizes]
        return photo_url unless sizes.is_a?(Hash)
        return sizes[size.to_s] if size && sizes[size.to_s]

        sizes.values.last
      end

      def cover_picture
        raw_data[:coverPicture]
      end

      def open_to_work?
        raw_data[:openToWork] == true
      end

      def hiring?
        raw_data[:hiring] == true
      end

      def premium?
        raw_data[:premium] == true
      end

      def influencer?
        raw_data[:influencer] == true
      end

      def verified?
        raw_data[:verified] == true
      end

      def memorialized?
        raw_data[:memorialized] == true
      end

      def connections_count
        raw_data[:connectionsCount]
      end

      def follower_count
        raw_data[:followerCount]
      end

      def registered_at
        raw_data[:registeredAt]
      end

      def top_skills_text
        raw_data[:topSkills]
      end

      def location
        @location ||= Location.new(raw_data[:location] || {})
      end

      def current_company
        raw_data.dig(:currentPosition, 0, :companyName)
      end

      def current_position
        experience.first
      end

      def current_positions
        @current_positions ||= (raw_data[:currentPosition] || []).map { |e| Experience.new(e) }
      end

      def top_education
        @top_education ||= raw_data[:profileTopEducation] ? Education.new(raw_data[:profileTopEducation]) : nil
      end

      def experience
        @experience ||= (raw_data[:experience] || []).map { |e| Experience.new(e) }
      end

      def education
        @education ||= (raw_data[:education] || []).map { |e| Education.new(e) }
      end

      def skills
        @skills ||= (raw_data[:skills] || []).map { |s| s[:name] }.compact
      end

      def top_skills(limit = 5)
        skills.first(limit)
      end

      def languages
        @languages ||= (raw_data[:languages] || []).map { |l| l[:name] }.compact
      end

      def certifications
        @certifications ||= (raw_data[:certifications] || []).map { |c| Certification.new(c) }
      end

      def projects
        @projects ||= (raw_data[:projects] || []).map { |p| Project.new(p) }
      end

      def volunteering
        @volunteering ||= (raw_data[:volunteering] || []).map { |v| Volunteering.new(v) }
      end

      def publications
        @publications ||= (raw_data[:publications] || []).map { |p| Publication.new(p) }
      end

      def courses
        @courses ||= raw_data[:courses] || []
      end

      def patents
        @patents ||= raw_data[:patents] || []
      end

      def honors_and_awards
        @honors_and_awards ||= raw_data[:honorsAndAwards] || []
      end

      def causes
        @causes ||= raw_data[:causes] || []
      end

      def received_recommendations
        @received_recommendations ||= raw_data[:receivedRecommendations] || []
      end

      def featured
        @featured ||= raw_data[:featured] || []
      end

      def more_profiles
        @more_profiles ||= raw_data[:moreProfiles] || []
      end

      def email
        raw_data[:email]
      end

      def has_email?
        email.present?
      end

      def years_of_experience
        return nil if experience.empty?

        earliest = experience.filter_map do |exp|
          year = exp.raw_data.dig(:startDate, :year)
          year.present? ? year.to_i : nil
        end.min

        return nil unless earliest

        Time.current.year - earliest
      end

      def page_number
        raw_data.dig(:_meta, :pagination, :pageNumber)
      end

      def to_h
        raw_data
      end

      def to_json(*args)
        to_h.to_json(*args)
      end

      def raw_json
        JSON.pretty_generate(raw_data)
      end

      def inspect
        "#<Apify::LinkedinSearch::Profile #{full_name} (#{current_company})>"
      end
    end

    class Location
      attr_reader :data

      def initialize(data)
        @data = data.deep_symbolize_keys
      end

      def text
        data[:linkedinText]
      end

      def country_code
        data[:countryCode]
      end

      def country
        data.dig(:parsed, :country)
      end

      def state
        data.dig(:parsed, :state)
      end

      def city
        data.dig(:parsed, :city)
      end

      def to_s
        text
      end
    end

    class Experience
      attr_reader :raw_data

      def initialize(data)
        @raw_data = data.deep_symbolize_keys
      end

      def title
        raw_data[:position]
      end

      def company
        raw_data[:companyName]
      end

      def company_url
        raw_data[:companyLinkedinUrl]
      end

      def company_id
        raw_data[:companyId]
      end

      def company_universal_name
        raw_data[:companyUniversalName]
      end

      def company_logo_url
        raw_data.dig(:companyLogo, :url) || raw_data.dig(:companyLogo)
      end

      def location
        raw_data[:location]
      end

      def employment_type
        raw_data[:employmentType]
      end

      def workplace_type
        raw_data[:workplaceType]
      end

      def duration
        raw_data[:duration]
      end

      def description
        raw_data[:description]
      end

      def current?
        raw_data.dig(:endDate, :text) == "Present"
      end

      def start_date
        raw_data[:startDate]
      end

      def end_date
        raw_data[:endDate]
      end

      def skills
        @skills ||= (raw_data[:skills] || []).map { |s| s.is_a?(Hash) ? s[:name] : s }.compact
      end

      def experience_group_id
        raw_data[:experienceGroupId]
      end
    end

    class Education
      attr_reader :data

      def initialize(data)
        @data = data.deep_symbolize_keys
      end

      def school
        data[:schoolName]
      end

      def school_linkedin_url
        data[:schoolLinkedinUrl]
      end

      def school_id
        data[:schoolId]
      end

      def school_logo_url
        data.dig(:schoolLogo, :url) || data.dig(:schoolLogo)
      end

      def degree
        data[:degree]
      end

      def field
        data[:fieldOfStudy]
      end

      def description
        data[:description]
      end

      def start_date
        data[:startDate]
      end

      def end_date
        data[:endDate]
      end

      def period
        data[:period]
      end

      def skills
        @skills ||= (data[:skills] || []).map { |s| s.is_a?(Hash) ? s[:name] : s }.compact
      end
    end

    class Certification
      attr_reader :data

      def initialize(data)
        @data = data.deep_symbolize_keys
      end

      def name
        data[:name]
      end

      def authority
        data[:authority]
      end

      def url
        data[:url]
      end

      def start_date
        data[:startDate]
      end

      def end_date
        data[:endDate]
      end

      def to_h
        { name: name, authority: authority, url: url, start_date: start_date, end_date: end_date }.compact
      end
    end

    class Project
      attr_reader :data

      def initialize(data)
        @data = data.deep_symbolize_keys
      end

      def title
        data[:title]
      end

      def description
        data[:description]
      end

      def url
        data[:url]
      end

      def start_date
        data[:startDate]
      end

      def end_date
        data[:endDate]
      end

      def members
        data[:members] || []
      end

      def to_h
        { title: title, description: description, url: url, start_date: start_date, end_date: end_date, members: members }.compact
      end
    end

    class Volunteering
      attr_reader :data

      def initialize(data)
        @data = data.deep_symbolize_keys
      end

      def role
        data[:role]
      end

      def organization
        data[:organization] || data[:companyName]
      end

      def cause
        data[:cause]
      end

      def description
        data[:description]
      end

      def start_date
        data[:startDate]
      end

      def end_date
        data[:endDate]
      end

      def to_h
        { role: role, organization: organization, cause: cause, description: description, start_date: start_date, end_date: end_date }.compact
      end
    end

    class Publication
      attr_reader :data

      def initialize(data)
        @data = data.deep_symbolize_keys
      end

      def title
        data[:title] || data[:name]
      end

      def publisher
        data[:publisher]
      end

      def url
        data[:url]
      end

      def date
        data[:date] || data[:publishedDate]
      end

      def description
        data[:description]
      end

      def to_h
        { title: title, publisher: publisher, url: url, date: date, description: description }.compact
      end
    end
  end
end
