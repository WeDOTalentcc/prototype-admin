class OpenaiClient
  DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"

  def initialize(api_key: ENV.fetch("OPENAI_API_KEY", nil))
    @api_key = api_key
    raise "OPENAI_API_KEY not set" unless @api_key
  end

  def embeddings(text:, model: DEFAULT_EMBEDDING_MODEL, dimensions: 1536)
    uri = URI("https://api.openai.com/v1/embeddings")
    http = Net::HTTP.new(uri.host, uri.port)
    http.use_ssl = true
    http.read_timeout = 10

    request = Net::HTTP::Post.new(uri.path)
    request["Authorization"] = "Bearer #{@api_key}"
    request["Content-Type"] = "application/json"
    request.body = {
      input: text,
      model: model,
      dimensions: dimensions
    }.to_json

    response = http.request(request)

    raise "OpenAI API error: #{response.code} - #{response.body}" unless response.code == "200"

    JSON.parse(response.body)
  rescue => e
    Rails.logger.error "OpenAIClient embeddings error: #{e.message}"
    raise
  end
end
