module Apify
  class LinkedinSearchService
    class ResultSet
      include Enumerable

      attr_reader :profiles, :query, :run_metadata

      def initialize(profiles:, query:, run_metadata: {})
        @profiles = profiles.map { |p| Profile.new(p) }
        @query = query
        @run_metadata = run_metadata.deep_symbolize_keys
      end

      def each(&block)
        profiles.each(&block)
      end

      def size
        profiles.size
      end

      alias_method :count, :size
      alias_method :length, :size

      def first
        profiles.first
      end

      def last
        profiles.last
      end

      def [](index)
        profiles[index]
      end

      def total_count
        profiles.first&.raw_data&.dig(:_meta, :pagination, :totalElements) || count
      end

      def pages_scraped
        query.take_pages
      end

      def current_page
        query.start_page + pages_scraped - 1
      end

      def next_page
        current_page + 1
      end

      def has_more?
        total_count > (query.start_page - 1) * 25 + count
      end

      def run_id
        run_metadata[:id]
      end

      def run_status
        run_metadata[:status]
      end

      def rate_limited?
        run_metadata[:statusMessage] == "rate limited"
      end

      def to_a
        profiles.map(&:to_h)
      end

      def to_json(*args)
        to_a.to_json(*args)
      end

      def with_email
        filtered = profiles.select(&:has_email?).map(&:raw_data)
        self.class.new(profiles: filtered, query: query, run_metadata: run_metadata)
      end

      def in_location(location_text)
        filtered = profiles.select do |p|
          p.location.text&.downcase&.include?(location_text.downcase)
        end.map(&:raw_data)

        self.class.new(profiles: filtered, query: query, run_metadata: run_metadata)
      end

      def at_company(company_name)
        filtered = profiles.select do |p|
          p.current_company&.downcase&.include?(company_name.downcase)
        end.map(&:raw_data)

        self.class.new(profiles: filtered, query: query, run_metadata: run_metadata)
      end
    end
  end
end
