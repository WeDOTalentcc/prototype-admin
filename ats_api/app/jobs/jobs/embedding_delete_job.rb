class Jobs::EmbeddingDeleteJob < ApplicationJob
  queue_as :default

  def perform(job_id, account_id, _unused = nil)
    return if Rails.env.test?
    account = Account.find_by(id: account_id)
    return unless account

    Apartment::Tenant.switch!(account.tenant) do
      Embedding.where(reference_type: "Job", reference_id: job_id).destroy_all
      job = Job.find_by(id: job_id)
      job&.update_column(:embedding, nil) if job
      Rails.logger.info "Jobs::EmbeddingDeleteJob: Deleted embedding for job #{job_id}"
    end
  end
end
