require "gemini-ai"

class GeminiClient
  DEFAULT_CHAT_MODEL = "gemini-2.5-flash"
  DEFAULT_EMBEDDING_MODEL = "gemini-embedding-001"

  def initialize(api_key: ENV.fetch("GOOGLE_API_KEY"))
    @api_key = api_key
  end

  def chat(model:, messages:, temperature: 0.7, max_tokens: nil, response_format: nil, tracking: nil)
    enforce_rate_limit!(tracking)

    # responseMimeType JSON is only accepted on v1beta; v1 returns 400.
    credentials = { service: "generative-language-api", api_key: @api_key }
    credentials[:version] = "v1beta" if json_response_format?(response_format)

    client = Gemini.new(credentials: credentials, options: { model: model })

    contents = messages.map do |msg|
      { role: map_role(msg[:role]), parts: { text: msg[:content] } }
    end

    generation_config = { temperature: temperature }
    generation_config[:maxOutputTokens] = max_tokens if max_tokens
    if json_response_format?(response_format)
      generation_config[:responseMimeType] = "application/json"
    end

    start_time = Time.current

    result = client.generate_content(
      { contents: contents, generationConfig: generation_config }
    )

    full_text = extract_generate_content_text(result)
    h = result.is_a?(Hash) ? result.deep_stringify_keys : {}
    finish = h.dig("candidates", 0, "finishReason")
    if full_text.blank?
      Rails.logger.warn("[GeminiClient] empty model text finishReason=#{finish.inspect}")
    elsif finish == "MAX_TOKENS"
      Rails.logger.warn("[GeminiClient] output may be truncated (finishReason=MAX_TOKENS, #{full_text.length} chars)")
    end
    usage_metadata = extract_usage_metadata(result)

    response = {
      "choices" => [
        {
          "message" => { "content" => full_text },
          "finish_reason" => finish
        }
      ],
      "usage" => {
        "prompt_tokens" => usage_metadata["promptTokenCount"] || 0,
        "completion_tokens" => usage_metadata["candidatesTokenCount"] || 0,
        "total_tokens" => usage_metadata["totalTokenCount"] || 0
      }
    }

    track_usage(model: model, response: response, start_time: start_time, tracking: tracking)

    response
  rescue => e
    Rails.logger.error "GeminiClient chat error: #{e.message}"
    raise
  end

  def embeddings(text:, model: DEFAULT_EMBEDDING_MODEL, dimensions: 768, tracking: nil)
    enforce_rate_limit!(tracking)

    client = Gemini.new(
      credentials: { service: "generative-language-api", api_key: @api_key, version: "v1beta" },
      options: { model: model, server_sent_events: false }
    )

    params = { content: { parts: { text: text } } }
    params[:outputDimensionality] = dimensions if dimensions

    start_time = Time.current

    result = client.embed_content(params)
    embedding = result.dig("embedding", "values")

    embedding = embedding.take(dimensions) if dimensions && embedding.length > dimensions

    estimated_tokens = Llm::CostCalculator.estimate_tokens(text)

    track_usage(
      model: model,
      response: {
        "usage" => {
          "prompt_tokens" => estimated_tokens,
          "completion_tokens" => 0,
          "total_tokens" => estimated_tokens
        }
      },
      start_time: start_time,
      tracking: tracking
    )

    { "data" => [ { "embedding" => embedding } ] }
  rescue => e
    Rails.logger.error "GeminiClient embeddings error: #{e.message}"
    raise
  end

  private

  def json_response_format?(response_format)
    return false if response_format.blank?

    t = response_format[:type] || response_format["type"]
    t.to_s == "json_object"
  end

  def extract_generate_content_text(result)
    return "" if result.blank?

    h = result.is_a?(Hash) ? result.deep_stringify_keys : {}
    parts = h.dig("candidates", 0, "content", "parts")
    text = extract_parts_text(parts)
    return text if text.present?

    h.dig("candidates", 0, "content", "parts", 0, "text").to_s
  end

  def extract_parts_text(parts)
    case parts
    when Array
      parts.map do |p|
        next unless p.is_a?(Hash)

        p.stringify_keys["text"].to_s
      end.compact.join
    when Hash
      parts.stringify_keys["text"].to_s
    else
      ""
    end
  end

  def extract_usage_metadata(result)
    return {} if result.blank?

    h = result.is_a?(Hash) ? result.deep_stringify_keys : {}
    h["usageMetadata"] || {}
  end

  def map_role(openai_role)
    { "system" => "user", "user" => "user", "assistant" => "model" }[openai_role] || "user"
  end

  def track_usage(model:, response:, start_time:, tracking:)
    return unless tracking

    user = Current.user
    account = user&.account || Current.account
    return unless user && account

    usage = response.dig("usage") || {}
    input_tokens = usage["prompt_tokens"] || 0
    output_tokens = usage["completion_tokens"] || 0
    total_tokens = usage["total_tokens"] || 0
    latency_ms = ((Time.current - start_time) * 1000).round(2)

    cost = Llm::CostCalculator.calculate(
      model: model,
      input_tokens: input_tokens,
      output_tokens: output_tokens
    )

    Apartment::Tenant.switch("public") do
      LlmUsage.create!(
        user: user,
        account: account,
        model: model,
        operation: tracking[:operation],
        input_tokens: input_tokens,
        output_tokens: output_tokens,
        total_tokens: total_tokens,
        cost_usd: cost,
        latency_ms: latency_ms,
        success: true,
        context: tracking.except(:operation)
      )

      record_quota_usage!(account.id, cost, total_tokens, tracking)
    end
  rescue => e
    Rails.logger.error "[GeminiClient] Failed to track usage: #{e.message}"
  end

  def enforce_rate_limit!(tracking)
    return unless tracking

    user = Current.user
    account = user&.account || Current.account
    return unless account

    bypass = tracking[:bypass_rate_limit] == true

    Apartment::Tenant.switch("public") do
      Llm::RateLimiter.check!(account_id: account.id, user_id: user&.id, bypass: bypass)
    end
  end

  def record_quota_usage!(account_id, cost, total_tokens, tracking)
    bypass = tracking[:bypass_rate_limit] == true
    Llm::RateLimiter.new(account_id: account_id, bypass: bypass)
                     .record_usage!(cost: cost, tokens: total_tokens)
  rescue => e
    Rails.logger.error "[GeminiClient] Failed to record quota usage: #{e.message}"
  end
end
