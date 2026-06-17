module Candidates
  class ProfileAnalysesService
    def self.call(candidate:, account_id:)
      new(candidate: candidate, account_id: account_id).call
    end

    def initialize(candidate:, account_id:)
      @candidate = candidate
      @account_id = account_id
    end

    def call
      return empty_payload unless @candidate

      analyses = sourced_profile_sourcings.map { |link| serialize(link) }
      { analyses: analyses, total: analyses.size }
    end

    private

    def sourced_profile_sourcings
      profile_ids = SourcedProfile
        .where(candidate_id: @candidate.id, account_id: @account_id)
        .pluck(:id)

      return SourcedProfileSourcing.none if profile_ids.empty?

      SourcedProfileSourcing
        .where(sourced_profile_id: profile_ids, is_deleted: false)
        .where.not(analysis: nil)
        .order(created_at: :desc)
    end

    def serialize(link)
      {
        id: link.id,
        sourcing_id: link.sourcing_id,
        sourced_profile_id: link.sourced_profile_id,
        analysis: link.analysis,
        score: link.score,
        ai_metadata: link.ai_metadata,
        created_at: link.created_at,
        updated_at: link.updated_at
      }
    end

    def empty_payload
      { analyses: [], total: 0 }
    end
  end
end
