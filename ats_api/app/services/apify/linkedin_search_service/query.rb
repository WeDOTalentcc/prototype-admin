module Apify
  class LinkedinSearchService
    class Query
      MODES = {
        short: "Short",
        full: "Full",
        full_with_email: "Full + email search"
      }.freeze

      SENIORITY_LEVELS = {
        unpaid: 100, training: 110, entry: 120, senior: 130,
        manager: 200, director: 210, vp: 220,
        cxo: 300, partner: 310, owner: 320
      }.freeze

      FUNCTIONS = {
        accounting: 1, administrative: 2, arts_and_design: 3, business_development: 4,
        community_and_social_services: 5, consulting: 6, education: 7,
        engineering: 8, entrepreneurship: 9, finance: 10, healthcare_services: 11,
        human_resources: 12, information_technology: 13, legal: 14,
        marketing: 15, media_and_communication: 16, military_and_protective_services: 17,
        operations: 18, product_management: 19, program_and_project_management: 20,
        purchasing: 21, quality_assurance: 22, real_estate: 23,
        research: 24, sales: 25, support: 26
      }.freeze

      COMPANY_HEADCOUNT = {
        self_employed: "A", tiny: "B", small: "C", medium_small: "D",
        medium: "E", medium_large: "F", large: "G", very_large: "H", enterprise: "I"
      }.freeze

      DEDUPLICATION_MODES = %w[none disabled duplicates_only unique_only].freeze

      attr_reader :search_query, :current_job_titles, :past_job_titles,
                  :locations, :current_companies, :past_companies,
                  :schools, :industries, :years_of_experience,
                  :years_at_current_company, :mode, :start_page,
                  :take_pages, :max_items,
                  :seniority_levels, :functions, :company_headcount,
                  :profile_languages, :first_names, :last_names,
                  :recently_changed_jobs, :company_headquarter_locations,
                  :exclude_locations, :exclude_current_companies,
                  :exclude_past_companies, :exclude_schools,
                  :exclude_current_job_titles, :exclude_past_job_titles,
                  :exclude_industry_ids, :exclude_seniority_levels,
                  :exclude_function_ids, :exclude_company_headquarter_locations,
                  :auto_query_segmentation, :auto_query_segmentation_levels,
                  :auto_query_segmentation_target_countries,
                  :deduplication_mode, :mongodb_connection_string,
                  :post_filter_query, :post_filter_aggregation

      def initialize(**options)
        @search_query = options[:search_query]
        @current_job_titles = Array(options[:current_job_titles]).compact
        @past_job_titles = Array(options[:past_job_titles]).compact
        @locations = Array(options[:locations]).compact
        @current_companies = Array(options[:current_companies]).compact
        @past_companies = Array(options[:past_companies]).compact
        @schools = Array(options[:schools]).compact
        @industries = Array(options[:industries]).compact
        @years_of_experience = Array(options[:years_of_experience]).compact
        @years_at_current_company = Array(options[:years_at_current_company]).compact
        @mode = (options[:mode] || :short).to_sym
        @start_page = (options[:start_page] || 1).to_i
        @take_pages = (options[:take_pages] || 1).to_i
        @max_items = (options[:max_items] || 0).to_i

        @seniority_levels = Array(options[:seniority_levels]).compact
        @functions = Array(options[:functions]).compact
        @company_headcount = Array(options[:company_headcount]).compact
        @profile_languages = Array(options[:profile_languages]).compact
        @first_names = Array(options[:first_names]).compact
        @last_names = Array(options[:last_names]).compact
        @recently_changed_jobs = options[:recently_changed_jobs]
        @company_headquarter_locations = Array(options[:company_headquarter_locations]).compact

        @exclude_locations = Array(options[:exclude_locations]).compact
        @exclude_current_companies = Array(options[:exclude_current_companies]).compact
        @exclude_past_companies = Array(options[:exclude_past_companies]).compact
        @exclude_schools = Array(options[:exclude_schools]).compact
        @exclude_current_job_titles = Array(options[:exclude_current_job_titles]).compact
        @exclude_past_job_titles = Array(options[:exclude_past_job_titles]).compact
        @exclude_industry_ids = Array(options[:exclude_industry_ids]).compact
        @exclude_seniority_levels = Array(options[:exclude_seniority_levels]).compact
        @exclude_function_ids = Array(options[:exclude_function_ids]).compact
        @exclude_company_headquarter_locations = Array(options[:exclude_company_headquarter_locations]).compact

        @auto_query_segmentation = options[:auto_query_segmentation]
        @auto_query_segmentation_levels = options[:auto_query_segmentation_levels]
        @auto_query_segmentation_target_countries = Array(options[:auto_query_segmentation_target_countries]).compact

        @deduplication_mode = options[:deduplication_mode]
        @mongodb_connection_string = options[:mongodb_connection_string]
        @post_filter_query = options[:post_filter_query]
        @post_filter_aggregation = options[:post_filter_aggregation]
      end

      def to_actor_input
        input = {
          searchQuery: search_query,
          currentJobTitles: current_job_titles,
          pastJobTitles: past_job_titles,
          locations: locations,
          currentCompanies: current_companies,
          pastCompanies: past_companies,
          schools: schools,
          industries: industries,
          yearsOfExperience: years_of_experience,
          yearsAtCurrentCompany: years_at_current_company,
          profileScraperMode: MODES.fetch(mode, "Short"),
          startPage: start_page,
          takePages: take_pages,
          maxItems: max_items
        }

        append_advanced_filters!(input)
        append_exclusion_filters!(input)
        append_segmentation_options!(input)
        append_deduplication_options!(input)

        input.compact
      end

      def valid?
        has_criteria? && valid_pagination? && valid_mode?
      end

      def estimated_cost
        CostCalculator.new(self).calculate
      end

      def log_summary
        {
          query: search_query,
          titles: current_job_titles,
          locations: locations,
          mode: mode,
          pages: take_pages,
          seniority: seniority_levels,
          functions: functions
        }.compact.to_json
      end

      private

      def append_advanced_filters!(input)
        input[:seniorityLevelIds] = seniority_levels.map(&:to_s) if seniority_levels.present?
        input[:functionIds] = functions.map(&:to_s) if functions.present?
        input[:companyHeadcount] = company_headcount if company_headcount.present?
        input[:profileLanguages] = profile_languages if profile_languages.present?
        input[:firstNames] = first_names if first_names.present?
        input[:lastNames] = last_names if last_names.present?
        input[:recentlyChangedJobs] = recently_changed_jobs unless recently_changed_jobs.nil?
        input[:companyHeadquarterLocations] = company_headquarter_locations if company_headquarter_locations.present?
      end

      def append_exclusion_filters!(input)
        input[:excludeLocations] = exclude_locations if exclude_locations.present?
        input[:excludeCurrentCompanies] = exclude_current_companies if exclude_current_companies.present?
        input[:excludePastCompanies] = exclude_past_companies if exclude_past_companies.present?
        input[:excludeSchools] = exclude_schools if exclude_schools.present?
        input[:excludeCurrentJobTitles] = exclude_current_job_titles if exclude_current_job_titles.present?
        input[:excludePastJobTitles] = exclude_past_job_titles if exclude_past_job_titles.present?
        input[:excludeIndustryIds] = exclude_industry_ids.map(&:to_s) if exclude_industry_ids.present?
        input[:excludeSeniorityLevelIds] = exclude_seniority_levels.map(&:to_s) if exclude_seniority_levels.present?
        input[:excludeFunctionIds] = exclude_function_ids.map(&:to_s) if exclude_function_ids.present?
        input[:excludeCompanyHeadquarterLocations] = exclude_company_headquarter_locations if exclude_company_headquarter_locations.present?
      end

      def append_segmentation_options!(input)
        input[:autoQuerySegmentation] = auto_query_segmentation unless auto_query_segmentation.nil?
        input[:autoQuerySegmentationLevels] = auto_query_segmentation_levels if auto_query_segmentation_levels.present?
        input[:autoQuerySegmentationTargetCountries] = auto_query_segmentation_target_countries if auto_query_segmentation_target_countries.present?
      end

      def append_deduplication_options!(input)
        input[:profileDeduplicationMode] = deduplication_mode if deduplication_mode.present?
        input[:mongoDbConnectionString] = mongodb_connection_string if mongodb_connection_string.present?
        input[:postFilteringMongoDbQuery] = post_filter_query if post_filter_query.present?
        input[:postFilteringMongoDbAggregation] = post_filter_aggregation if post_filter_aggregation.present?
      end

      def has_criteria?
        [
          search_query,
          current_job_titles,
          past_job_titles,
          locations,
          current_companies,
          past_companies,
          schools,
          first_names,
          last_names
        ].any?(&:present?)
      end

      def valid_pagination?
        start_page.positive? && take_pages.positive? && take_pages <= 100
      end

      def valid_mode?
        MODES.key?(mode)
      end
    end
  end
end
