class Candidates::EmbeddingSyncJob < ApplicationJob
  queue_as :default

  EMBEDDING_DIM = 768
  MAX_RETRIES = 5
  INITIAL_BACKOFF = 2   # segundos
  MAX_BACKOFF = 90      # segundos

  def perform(candidate_id, expected_updated_at = nil, account_id)
    return if Rails.env.test?

    account = Account.find_by(id: account_id)
    return unless account

    Current.account = account

    Apartment::Tenant.switch!(account.tenant)

    # Eager load all associations used by TextBuilder
    candidate = Candidate
      .includes(
        :skills,
        experiences: [ :occupation, :company ],
        educations: [ :institution, :study_area ],
        language_relationships: :language
      )
      .find_by(id: candidate_id)

    return unless candidate
    return if candidate.is_deleted?
    return if expected_updated_at && candidate.updated_at.to_i > expected_updated_at.to_i

    text = CandidateService::TextBuilder.call(candidate)
    return if text.blank?

    begin
      vec = call_encoder_with_retry(text)
      raise "embedding vazio" unless vec&.any?
      raise "dimensão inválida: got=#{vec.length} expected=#{EMBEDDING_DIM}" unless vec.length == EMBEDDING_DIM

      record = candidate.embedding_record || candidate.build_embedding_record
      record.update!(
        embedding: vec,
        model_version: Llm::ClientFactory.embedding_model,
        dimensions: EMBEDDING_DIM
      )
      Rails.logger.info "EmbeddingSyncJob: Successfully updated embedding for candidate #{candidate_id}"
      update_applies_cv_match(candidate)
    rescue Faraday::BadRequestError => e
      Rails.logger.error "EmbeddingSyncJob: Gemini 400 error for candidate #{candidate_id}: #{e.message}"
      Rails.logger.error "EmbeddingSyncJob: Text length: #{text.length}"
      Rails.logger.error "EmbeddingSyncJob: Text sample: #{text[0, 200].inspect}..."
      raise StandardError, "Gemini request failed: #{e.message}"
    rescue => e
      Rails.logger.error "EmbeddingSyncJob: Unexpected error for candidate #{candidate_id}: #{e.message}"
      Rails.logger.error "EmbeddingSyncJob: #{e.backtrace.first(3).join('\n')}"
      raise e
    end
  end

  private

  def update_applies_cv_match(candidate)
    Apply.where(candidate_id: candidate.id, is_deleted: false).find_each do |apply|
      apply.update_cv_match_score
    end
  end

  def rate_limit_error?(e)
    return true if e.message.to_s.include?("429")

    if e.respond_to?(:response) && e.response
      return e.response.status == 429 if e.response.respond_to?(:status)
      return e.response[:status] == 429 if e.response.is_a?(Hash) && e.response[:status]
      return e.response["status"] == 429 if e.response.is_a?(Hash) && e.response["status"]
    end

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
