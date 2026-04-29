module SearchArchetypes
  class ExecuteSearchService
    def self.call(**args)
      new(**args).call
    end

    def initialize(archetype:, user:, sources:)
      @archetype = archetype
      @user = user
      @account = user.account
      @sources = Array(sources)
    end

    def call
      sourcing = create_sourcing
      enqueue_searches(sourcing)
      sourcing
    end

    private

    def create_sourcing
      provider = determine_provider

      @account.sourcings.create!(
        user: @user,
        search_archetype: @archetype,
        uid: SecureRandom.uuid,
        provider: provider,
        query: @archetype.query,
        parameters: build_parameters,
        status: "processing",
        searched_at: Time.current
      )
    end

    def determine_provider
      return "hybrid" if @sources.size > 1
      @sources.first
    end

    def build_parameters
      {
        sources: @sources,
        archetype_id: @archetype.id,
        archetype_name: @archetype.name,
        local_filters: @archetype.filters_for(:local),
        global_filters: @archetype.filters_for(:global)
      }
    end

    def enqueue_searches(sourcing)
      @sources.each do |source|
        enqueue_for_source(sourcing, source)
      end
    end

    def enqueue_for_source(sourcing, source)
      case source.to_s
      when "local"
        enqueue_local_search(sourcing)
      when "global"
        enqueue_global_search(sourcing)
      end
    end

    def enqueue_local_search(sourcing)
      profile = extract_search_profile
      additional_options = {
        limit: extract_limit(sourcing),
        max_pages: extract_max_pages,
        order: extract_order,
        use_hybrid: extract_boolean("use_hybrid")
      }

      SearchArchetypes::LocalSearchJob.perform_async(
        @account.id,
        @user.id,
        sourcing.id,
        @archetype.id,
        profile,
        additional_options
      )
    end

    def enqueue_global_search(sourcing)
      pearch_params = SearchArchetypes::ToPearchParamsService.call(
        archetype: @archetype,
        profile: extract_search_profile,
        additional_options: {
          limit: extract_limit(sourcing),
          show_emails: extract_boolean(:show_emails),
          show_phone_numbers: extract_boolean(:show_phone_numbers),
          require_emails: extract_boolean(:require_emails)
        }
      )

      Sourcings::PearchJob.perform_async(
        @account.id,
        @user.id,
        sourcing.id,
        pearch_params[:query],
        pearch_params.to_json
      )
    end

    def extract_search_profile
      @archetype.local_filters&.dig("search_profile") ||
        @archetype.global_filters&.dig("search_profile") ||
        "balanced"
    end

    def extract_limit(sourcing = nil)
      from_archetype = [
        @archetype.local_filters&.dig("limit"),
        @archetype.global_filters&.dig("limit")
      ].compact.map(&:to_i).find(&:positive?)

      return from_archetype if from_archetype

      sourcing ? Sourcings::FirstBatchPageSize.for_sourcing(sourcing) : Sourcings::FirstBatchPageSize::BASE
    end

    def extract_max_pages
      @archetype.local_filters&.dig("max_pages")&.to_i || 1
    end

    def extract_order
      @archetype.local_filters&.dig("order")
    end

    def extract_boolean(key)
      value = @archetype.local_filters&.dig(key.to_s) ||
              @archetype.global_filters&.dig(key.to_s)
      return false if value.nil?

      [ "true", true, 1, "1" ].include?(value)
    end
  end
end
