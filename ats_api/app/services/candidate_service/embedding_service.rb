# app/services/candidates_service/embedding_service.rb
class CandidateService::EmbeddingService
  def initialize(candidate_id)
    @candidate = Candidate.find(candidate_id)
  end

  def call
    return if Rails.env.test?
    text = CandidateService::TextBuilder.call(@candidate)
    raise "texto vazio para embedding (candidate_id=#{@candidate.id})" if text.blank?

    vec = Embeddings::Encoder.new.call(text) # => Array<Float>
    raise "embedding vazio" unless vec&.any?
    ns = VectorStores::Namespaces.for_account(@candidate.account_id, :candidates)   # <-- aqui

    metadata = {
      candidate_id: @candidate.id,
      account_id: @candidate.account_id,
      name: @candidate.name.to_s[0, 128],
      role_name: @candidate.role_name.to_s[0, 64],
      position_level: @candidate.position_level.to_s[0, 32],
      city: @candidate.city.to_s[0, 48],
      state: @candidate.state.to_s[0, 48],
      country: @candidate.country.to_s[0, 48],
      remote_work: !!@candidate.remote_work,
      updated_at: @candidate.updated_at.to_i
    }.compact
  end
end
