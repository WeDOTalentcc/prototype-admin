class Embeddings::Encoder
  def initialize(dimensions: 768)
    @dimensions = dimensions
  end

  # Convenience: Embeddings::Encoder.call(text, dimensions: EMBEDDING_DIM)
  def self.call(text, **opts)
    new(**opts).call(text)
  end

  def call(text)
    # Do not hit external APIs during tests
    return [] if Rails.env.test?

    input_text = text.to_s.strip
    if input_text.blank?
      Rails.logger.error "Embeddings::Encoder: Empty text provided"
      raise "text is empty"
    end

    if input_text.length > 8000
      Rails.logger.warn "Embeddings::Encoder: Text too long (#{input_text.length} chars), truncating"
      input_text = input_text[0, 8000]
    end

    Rails.logger.debug "Embeddings::Encoder: Making request with dimensions=#{@dimensions}, text_length=#{input_text.length}"

    begin
      response = Llm::Gateway.embed(text: input_text, dimensions: @dimensions, tracking: { operation: "embeddings.encode" })
    rescue => e
      Rails.logger.error "Embeddings::Encoder: Gemini error - #{e.message}"
      Rails.logger.error "Embeddings::Encoder: Request params: dimensions=#{@dimensions}"
      Rails.logger.error "Embeddings::Encoder: Text sample: #{input_text[0, 200].inspect}..."
      raise e
    end

    embedding = response.dig("data", 0, "embedding")
    raise "embedding is nil" unless embedding

    if @dimensions.present? && embedding.length != @dimensions
      raise "embedding dimension #{embedding.length} does not match expected #{@dimensions}"
    end

    embedding
  end
end
