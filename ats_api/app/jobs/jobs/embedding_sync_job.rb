class Jobs::EmbeddingSyncJob < ApplicationJob
  queue_as :default

  EMBEDDING_DIM = 768
  MAX_RETRIES = 5
  INITIAL_BACKOFF = 2
  MAX_BACKOFF = 90

  def perform(job_id, expected_updated_at = nil, account_id)
    return if Rails.env.test?
    account = Account.find_by(id: account_id)
    return unless account

    Current.account = account

    Apartment::Tenant.switch(account.tenant) do
      job = Job.find_by(id: job_id)
      return unless job
      return if job.is_deleted?
      return if expected_updated_at && job.updated_at.to_i > expected_updated_at.to_i

      text = [
        job.title,
        job.description,
        [ job.city, job.state, job.country ].compact.join(", "),
        job.workplace_type
      ].compact.join("\n\n")

      vec = call_encoder_with_retry(text)
      raise "embedding vazio" unless vec&.any?
      raise "dimensão inválida: got=#{vec.length} expected=#{EMBEDDING_DIM}" unless vec.length == EMBEDDING_DIM

      record = job.embedding_record || job.build_embedding_record
      record.update!(
        embedding: vec,
        model_version: Llm::ClientFactory.embedding_model,
        dimensions: EMBEDDING_DIM
      )
    end
  end

  private

  def rate_limit_error?(e)
    return true if e.message.to_s.include?("429")
    return e.response&.status == 429 if e.respond_to?(:response) && e.response
    false
  end

  def call_encoder_with_retry(text)
    attempt = 0
    begin
      Embeddings::Encoder.call(text, dimensions: EMBEDDING_DIM)
    rescue => e
      attempt += 1
      if rate_limit_error?(e) && attempt <= MAX_RETRIES
        delay = [ INITIAL_BACKOFF * (2 ** (attempt - 1)), MAX_BACKOFF ].min
        Rails.logger.warn "EmbeddingSyncJob: 429 rate limit (attempt #{attempt}/#{MAX_RETRIES}), retrying in #{delay}s..."
        sleep delay
        retry
      end
      raise e
    end
  end
end
