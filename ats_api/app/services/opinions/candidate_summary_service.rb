module Opinions
  class CandidateSummaryService
    def self.call(candidate:, account_id:)
      new(candidate: candidate, account_id: account_id).call
    end

    def initialize(candidate:, account_id:)
      @candidate = candidate
      @account_id = account_id
    end

    def call
      return empty_payload unless @candidate

      active = Opinion.active.by_candidate(@candidate.id).where(account_id: @account_id)

      {
        candidate_id: @candidate.id,
        current_general_opinion: serialize(active.general.order(created_at: :desc).first),
        vacancy_opinions: active.where.not(job_id: nil).order(created_at: :desc).map { |o| serialize(o) },
        total_opinions: active.count,
        has_pending_review: active.where(status: "pending_review").exists?
      }
    end

    private

    def empty_payload
      {
        candidate_id: nil,
        current_general_opinion: nil,
        vacancy_opinions: [],
        total_opinions: 0,
        has_pending_review: false
      }
    end

    def serialize(opinion)
      return nil unless opinion

      {
        id: opinion.id,
        uid: opinion.uid,
        candidate_id: opinion.candidate_id,
        job_id: opinion.job_id,
        user_id: opinion.user_id,
        content: opinion.content,
        status: opinion.status,
        metadata: opinion.metadata,
        author_name: opinion.user&.name,
        job_title: opinion.job&.title,
        created_at: opinion.created_at,
        updated_at: opinion.updated_at
      }
    end
  end
end
