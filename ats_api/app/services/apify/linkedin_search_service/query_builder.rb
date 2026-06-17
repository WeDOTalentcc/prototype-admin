module Apify
  class LinkedinSearchService
    class QueryBuilder
      def initialize
        @options = { mode: :short, start_page: 1, take_pages: 1, max_items: 0 }
      end

      def with_query(query)
        @options[:search_query] = query
        self
      end

      def with_titles(*titles)
        @options[:current_job_titles] = titles.flatten.compact
        self
      end

      def with_past_titles(*titles)
        @options[:past_job_titles] = titles.flatten.compact
        self
      end

      def in_locations(*locations)
        @options[:locations] = locations.flatten.compact
        self
      end

      def at_companies(*urls)
        @options[:current_companies] = urls.flatten.compact
        self
      end

      def at_past_companies(*urls)
        @options[:past_companies] = urls.flatten.compact
        self
      end

      def from_schools(*urls)
        @options[:schools] = urls.flatten.compact
        self
      end

      def in_industries(*ids)
        @options[:industries] = ids.flatten.compact
        self
      end

      def with_experience(*ranges)
        @options[:years_of_experience] = ranges.flatten.compact
        self
      end

      def with_tenure(*ranges)
        @options[:years_at_current_company] = ranges.flatten.compact
        self
      end

      def with_seniority_levels(*levels)
        @options[:seniority_levels] = levels.flatten.compact
        self
      end

      def with_functions(*ids)
        @options[:functions] = ids.flatten.compact
        self
      end

      def with_company_headcount(*sizes)
        @options[:company_headcount] = sizes.flatten.compact
        self
      end

      def with_profile_languages(*langs)
        @options[:profile_languages] = langs.flatten.compact
        self
      end

      def with_first_names(*names)
        @options[:first_names] = names.flatten.compact
        self
      end

      def with_last_names(*names)
        @options[:last_names] = names.flatten.compact
        self
      end

      def recently_changed_jobs(value = true)
        @options[:recently_changed_jobs] = value
        self
      end

      def with_hq_locations(*locations)
        @options[:company_headquarter_locations] = locations.flatten.compact
        self
      end

      def exclude_locations(*locations)
        @options[:exclude_locations] = locations.flatten.compact
        self
      end

      def exclude_current_companies(*urls)
        @options[:exclude_current_companies] = urls.flatten.compact
        self
      end

      def exclude_past_companies(*urls)
        @options[:exclude_past_companies] = urls.flatten.compact
        self
      end

      def exclude_schools(*urls)
        @options[:exclude_schools] = urls.flatten.compact
        self
      end

      def exclude_current_titles(*titles)
        @options[:exclude_current_job_titles] = titles.flatten.compact
        self
      end

      def exclude_past_titles(*titles)
        @options[:exclude_past_job_titles] = titles.flatten.compact
        self
      end

      def exclude_industries(*ids)
        @options[:exclude_industry_ids] = ids.flatten.compact
        self
      end

      def exclude_seniority_levels(*ids)
        @options[:exclude_seniority_levels] = ids.flatten.compact
        self
      end

      def exclude_functions(*ids)
        @options[:exclude_function_ids] = ids.flatten.compact
        self
      end

      def exclude_hq_locations(*locations)
        @options[:exclude_company_headquarter_locations] = locations.flatten.compact
        self
      end

      def with_auto_segmentation(levels: nil, target_countries: nil)
        @options[:auto_query_segmentation] = true
        @options[:auto_query_segmentation_levels] = levels if levels
        @options[:auto_query_segmentation_target_countries] = Array(target_countries).compact if target_countries
        self
      end

      def with_deduplication(mode_name, mongodb_url: nil)
        @options[:deduplication_mode] = mode_name.to_s
        @options[:mongodb_connection_string] = mongodb_url if mongodb_url
        self
      end

      def with_post_filter(query: nil, aggregation: nil)
        @options[:post_filter_query] = query if query
        @options[:post_filter_aggregation] = aggregation if aggregation
        self
      end

      def mode(mode_sym)
        @options[:mode] = mode_sym
        self
      end

      def pages(count)
        @options[:take_pages] = count
        self
      end

      def start_from_page(page)
        @options[:start_page] = page
        self
      end

      def max_results(count)
        @options[:max_items] = count
        self
      end

      def estimated_cost
        Query.new(**@options).estimated_cost
      end

      def execute
        LinkedinSearchService.new.search(**@options)
      end

      alias_method :run, :execute
    end
  end
end
