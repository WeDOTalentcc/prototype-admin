# frozen_string_literal: true

module Candidates
  class ProcessLinkedinProfilesJob
    include Sidekiq::Job

    sidekiq_options queue: :default, retry: 2

    def perform(account_id, sourcing_id, linkedin_profile_urls, include_email = false)
      account = Account.find(account_id)

      Current.account = account

      Apartment::Tenant.switch(account.tenant) do
        sourcing = Sourcing.find(sourcing_id)
        user = sourcing.user

        Current.user = user

        profiles = Apify::LinkedinProfileParserService.parse(
          linkedin_profile_urls: linkedin_profile_urls,
          include_email: include_email,
          sourcing: sourcing
        )

        concatenated_texts = profiles.map do |profile|
          next if profile.is_a?(Hash) && profile[:error]
          profile[:concatenated_text] || profile["concatenated_text"]
        end.compact

        if concatenated_texts.any?
          linkedin_profile_parse = concatenated_texts.join("\n\n")

          generated_query = Candidates::SuggestionService.generate_query_from_files(linkedin_profile_parse)

          if generated_query.present?
            current_query = sourcing.query.to_s
            new_query = current_query.present? ? "#{current_query}\n\n#{generated_query}" : generated_query
            sourcing.update(query: new_query)
          end
        end

        sources = sourcing.sources

        sources.each do |source|
          params = sourcing.parameters.deep_symbolize_keys.merge(source: source)

          Sourcings::JobEnqueuerService.new(
            user: user,
            sourcing: sourcing,
            query: sourcing.query,
            params: params
          ).call
        end

        sourcing.update!(status: "done")
        broadcast_sourcing_completed(sourcing)
      end
    rescue => e
      Rails.logger.error "[ProcessLinkedinProfilesJob] Failed: #{e.message}"
      Rails.logger.error e.backtrace.join("\n")
      raise
    end

    private

    def broadcast_sourcing_completed(sourcing)
      serialized = SourcingSerializer.new(sourcing).serializable_hash[:data][:attributes]

      SourcingChannel.broadcast_to(
        "#{sourcing.user_id}_sourcing_#{sourcing.id}",
        {
          type: "sourcing_completed",
          sourcing: serialized,
          success: true,
          error: nil
        }
      )
    end
  end
end
