module Apify
  class LinkedinSearchService
    class CostCalculator
      COST_PER_PAGE = 0.10
      COST_PER_PROFILE = {
        short: 0,
        full: 0.004,
        full_with_email: 0.01
      }.freeze

      attr_reader :query

      def initialize(query)
        @query = query
      end

      def calculate
        page_cost = query.take_pages * COST_PER_PAGE
        profile_cost = estimated_profiles * profile_unit_cost

        {
          pages: format_cost(page_cost),
          profiles: format_cost(profile_cost, estimated: true),
          total: format_cost(page_cost + profile_cost, estimated: true),
          breakdown: {
            pages: query.take_pages,
            estimated_profiles: estimated_profiles,
            cost_per_page: COST_PER_PAGE,
            cost_per_profile: profile_unit_cost
          }
        }
      end

      private

      def estimated_profiles
        max_per_query = query.take_pages * 25
        return max_per_query if query.max_items.zero?

        [ max_per_query, query.max_items ].min
      end

      def profile_unit_cost
        COST_PER_PROFILE.fetch(query.mode, 0)
      end

      def format_cost(value, estimated: false)
        prefix = estimated ? "~" : ""
        "#{prefix}$#{'%.2f' % value}"
      end
    end
  end
end
