# app/services/job_service/embedding_service.rb
class JobService::EmbeddingService
  def initialize(job_id)
    @job = Job.find(job_id)
  end

  def call
    return if Rails.env.test?
    text = [
      @job.title,
      @job.description,
      [ @job.city, @job.state, @job.country ].compact.join(", "),
      @job.workplace_type
    ].compact.join("\n\n")

    vec = Embeddings::Encoder.call(text, dimensions: EMBEDDING_DIM)
    raise "embedding vazio" unless vec&.any?
    raise "dimensão inválida: got=#{vec.length} expected=#{EMBEDDING_DIM}" unless vec.length == EMBEDDING_DIM

    ns = VectorStores::Namespaces.for_account(@job.account_id, :jobs)
  end
end
