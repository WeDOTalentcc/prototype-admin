class Candidates::EmbeddingDeleteJob < ApplicationJob
  queue_as :default

  def perform(candidate_id, account_id)
    return if Rails.env.test?
    account = Account.find(account_id)
    Apartment::Tenant.switch!(account.tenant)

    Embedding.where(reference_type: "Candidate", reference_id: candidate_id).destroy_all
    candidate = Candidate.find_by(id: candidate_id)
    candidate&.update_column(:embedding, nil) if candidate
    Rails.logger.info "EmbeddingDeleteJob: Deleted embedding for candidate #{candidate_id}"
  end
end
