module Apify
  class LinkedinSearchService
    class Query
      MODES = {
        short: "Short",
        full: "Full",
        full_with_email: "Full + email search"
      }.freeze

      attr_reader :search_query, :current_job_titles, :past_job_titles,
                  :locations, :current_companies, :past_companies,
                  :schools, :industries, :years_of_experience,
                  :years_at_current_company, :mode, :start_page,
                  :take_pages, :max_items

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
      end

      def to_actor_input
        {
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
        }.compact
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
          pages: take_pages
        }.compact.to_json
      end

      private

      def has_criteria?
        [
          search_query,
          current_job_titles,
          past_job_titles,
          locations,
          current_companies,
          past_companies,
          schools
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
