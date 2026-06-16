class InternalApi
  def initialize(account:, user: nil, caller: "agent-orchestrator", prefer_text_default: false)
    @account = account
    @user    = user
    @prefer_text_default = prefer_text_default

    base_url = ENV.fetch("APP_BASE_URL")
    base_url = "http://#{base_url}" unless base_url.to_s.match?(/\Ahttps?:\/\//i)
    begin
      uri = URI.parse(base_url)
      if inside_container? && [ "localhost", "127.0.0.1", "::1" ].include?(uri.host)
        internal_host = ENV.fetch("APP_INTERNAL_HOST", "web")
        internal_port = (ENV["APP_INTERNAL_PORT"] || 3000).to_i
        uri.host = internal_host
        # If mapped host port 8080 was used, prefer app port 3000 internally
        uri.port = internal_port if uri.port.nil? || uri.port == 8080
        base_url = uri.to_s
      end
    rescue URI::InvalidURIError
      # keep original base_url
    end
    @conn = Faraday.new(url: base_url) do |f|
      f.request :json
      f.response :json, content_type: /\bjson$/
      f.adapter Faraday.default_adapter
    end

    @conn.headers["Authorization"]      = "Bearer #{service_jwt_for(@account, @user)}"
    @conn.headers["X-Tenant"]           = @account.tenant.to_s
    @conn.headers["X-Internal-Caller"]  = caller
    @conn.headers["Content-Type"]       = "application/json"
    @conn.headers["Accept"]             = "application/json"
  end

  def get(path, query: {}, idempotency_key: nil, prefer_text: false)
    do_request(:get, path, query: query, body: nil, idempotency_key: idempotency_key, prefer_text: prefer_text)
  end

  def post(path, body: {}, query: {}, idempotency_key: nil, prefer_text: false)
    do_request(:post, path, query: query, body: body, idempotency_key: idempotency_key, prefer_text: prefer_text)
  end

  def put(path, body: {}, query: {}, idempotency_key: nil, prefer_text: false)
    do_request(:put, path, query: query, body: body, idempotency_key: idempotency_key, prefer_text: prefer_text)
  end

  def patch(path, body: {}, query: {}, idempotency_key: nil, prefer_text: false)
    do_request(:patch, path, query: query, body: body, idempotency_key: idempotency_key, prefer_text: prefer_text)
  end

  def delete(path, body: nil, query: {}, idempotency_key: nil, prefer_text: false)
    do_request(:delete, path, query: query, body: body, idempotency_key: idempotency_key, prefer_text: prefer_text)
  end

  private

  def with_idempotency(key)
    @conn.headers["Idempotency-Key"] = key if key.present?
    resp = yield
    raise(StandardError, "InternalApi error: #{resp.status} #{resp.body}") unless resp.success?
    resp.body
  ensure
    @conn.headers.delete("Idempotency-Key")
  end

  def do_request(verb, path, query:, body:, idempotency_key: nil, prefer_text: false)
    with_idempotency(idempotency_key) do
      original_accept = @conn.headers["Accept"]
      effective_prefer_text = prefer_text || @prefer_text_default
      @conn.headers["Accept"] = "text/plain, application/json;q=0.9" if effective_prefer_text
      @conn.run_request(verb, path, body, nil) do |req|
        req.params.update(query) if query.present?
      end
    ensure
      @conn.headers["Accept"] = original_accept if effective_prefer_text
    end
  end

  def service_jwt_for(account, user)
    raise ArgumentError, "InternalApi requires a user to generate JWT" unless user&.id
    JsonWebToken.encode_service_token(account_id: account.id, user_id: user.id)
  end

  def inside_container?
    File.exist?("/.dockerenv") || ENV.key?("KUBERNETES_SERVICE_HOST")
  end
end
