# frozen_string_literal: true

module BackgroundAgents
  class DeliverCandidatesService
    EXTERNAL_PROVIDERS = %w[pearch linkedin].freeze

    def initialize(background_agent:, sourcing:, candidates_data:)
      @background_agent = background_agent
      @sourcing = sourcing
      @account = background_agent.account
      @candidates_data = candidates_data || []
    end

    def call
      return { created: 0, skipped: 0 } if @candidates_data.blank? || @sourcing.blank?

      created = 0
      skipped = 0

      @candidates_data.each do |candidate_data|
        provider = candidate_data[:source_provider].to_s

        profile = if EXTERNAL_PROVIDERS.include?(provider)
                    external_creator.call(candidate_data, provider)
                  else
                    local_creator.call(candidate_data)
                  end

        unless profile
          skipped += 1
          next
        end

        sps = profile.ensure_sourced_profile_sourcing(@sourcing, @account, @sourcing.user)
        unless sps
          skipped += 1
          next
        end

        update_sps_with_agent_data(sps, candidate_data)
        add_to_list(sps) if @background_agent.list_agent?
        created += 1
      rescue StandardError => e
        Rails.logger.error "[BackgroundAgent:#{@background_agent.id}] Failed for candidate #{candidate_data[:candidate_id]}: #{e.message}"
        skipped += 1
      end

      { created: created, skipped: skipped }
    end

    private

    def local_creator
      @local_creator ||= LocalProfileCreator.new(
        account: @account, sourcing: @sourcing, background_agent: @background_agent
      )
    end

    def external_creator
      @external_creator ||= ExternalProfileCreator.new(
        account: @account, sourcing: @sourcing, background_agent: @background_agent
      )
    end

    def update_sps_with_agent_data(sps, data)
      sps.update!(
        search_source: "background_agent",
        search_score: data[:score],
        score: data[:score],
        ai_metadata: {
          category: data[:category],
          justification: data[:justification],
          strengths: data[:strengths],
          concerns: data[:concerns],
          requirement_coverage: data[:requirement_coverage],
          source_query: data[:source_query],
          source_provider: data[:source_provider],
          found_in_iteration: data[:found_in_iteration]
        }
      )
    end

    def add_to_list(sps)
      list = @background_agent.list
      return unless list

      ListRelationship.find_or_create_by!(
        list_id: list.id,
        reference_type: "SourcedProfileSourcing",
        reference_id: sps.id,
        account_id: @account.id
      ) do |lr|
        lr.score = sps.score
        lr.general_comments = "Adicionado pelo agente: #{@background_agent.name}"
      end
    rescue ActiveRecord::RecordInvalid
      nil
    end
  end
end
