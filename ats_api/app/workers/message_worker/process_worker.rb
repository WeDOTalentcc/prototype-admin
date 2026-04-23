module MessageWorker
  class ProcessWorker
    include Sneakers::Worker
    include HTTParty

    base_uri ENV.fetch("RECRUITER_AGENT_API_URL", "http://host.docker.internal:8081")

    from_queue "messages_processed",
               ack: true,
               durable: true,
               exchange: "",
               routing_key: "messages_processed"

    def work(raw_payload)
      data = JSON.parse(raw_payload)

      if data["user_reference_type"] == "User" && data["user_reference_id"].present?
        account = User.find(data["user_reference_id"]).account
        Apartment::Tenant.switch!(account.tenant)
      end

      message = Message.find(data["original_message_id"])
      @original_message = message

      return ack! if message.entity.to_i == Message::ROLE_USER

      followup_metadata = data["metadata"] || {}
      if followup_metadata["is_audio_followup"]
        handle_audio_followup(message, followup_metadata)
        return ack!
      end

      new_message = handle_standard_response(message, data)
      handle_api_calls(message, new_message, data) if new_message

      ack!
    end

    private

    def handle_audio_followup(message, metadata)
      audio_base64 = metadata["audio_base64"]
      audio_mime = metadata["audio_mime_type"] || "audio/wav"

      last_system_message = Message.where(
        reference_type: message.reference_type,
        reference_id: message.reference_id,
        workspace_id: message.workspace_id,
        entity: Message::ROLE_SYSTEM
      ).order(created_at: :desc).first

      target_message = last_system_message || message

      if audio_base64.present?
        target_message.attach_audio_from_base64(audio_base64, mime_type: audio_mime)
      end

      payload = {
        id: target_message.id,
        type: "audio_followup",
        metadata: {
          audio_base64: audio_base64,
          audio_mime_type: audio_mime,
          is_audio_followup: true
        }
      }

      ActionCable.server.broadcast("messages_user_#{message.reference_id}", payload)
      broadcast_to_domain_channel(message, payload)
    end

    def handle_standard_response(message, data)
      no_reply = extract_no_reply(data)
      original_metadata = message.metadata.is_a?(Hash) ? message.metadata : {}
      teams_context = original_metadata.slice("source", "teams_chat_id", "teams_lia_user_id", "session_id")

      if data["errors"].present? && data["errors"].any?
        data["message"] = data["errors"].join(", ")
      end

      response_metadata = data["response"] || {}
      response_metadata["transcription_info"] = data["transcription_info"] if data["transcription_info"].present?
      response_metadata["audio_transcription"] = data["audio_transcription"] if data["audio_transcription"].present?

      enrich_navigation_with_search_params(response_metadata)

      message.update!(
        status: Message::STATUS_ANSWERED,
        metadata: response_metadata,
        no_reply: no_reply
      )

      content = "<p class='f20'>#{data.dig('response', 'message')}</p>"

      new_message_metadata = response_metadata.merge(teams_context)

      new_message = Message.create!(
        content: content,
        reference_type: "User",
        reference_id: message.reference_id,
        entity: Message::ROLE_SYSTEM,
        status: Message::STATUS_NOT_ANSWERED,
        account_id: message.account_id,
        workspace_id: message.workspace_id,
        domain: message.domain,
        content_format: data.dig("response", "content_format").presence || "plain_text",
        metadata: new_message_metadata
      )

      broadcast_payload = {
        content: new_message.content,
        entity: new_message.entity,
        status: new_message.status,
        metadata: new_message.metadata,
        content_format: new_message.content_format
      }

      audio_data = data.dig("response", "audio_response")
      if audio_data.present?
        audio_base64 = audio_data.is_a?(Hash) ? audio_data["audio_base64"] : audio_data
        audio_mime = audio_data.is_a?(Hash) ? audio_data.fetch("mime_type", "audio/mp3") : "audio/mp3"

        new_message.attach_audio_from_base64(audio_base64, mime_type: audio_mime)

        broadcast_payload[:audio_response] = {
          audio_base64: audio_base64,
          mime_type: audio_mime
        }
      end

      ActionCable.server.broadcast("messages_user_#{message.reference_id}", broadcast_payload)
      broadcast_to_domain_channel(message, broadcast_payload)

      new_message
    end

    def handle_api_calls(message, new_message, data)
      api_calls = Array(data.dig("response", "api_calls"))
      return unless api_calls.any?

      account = Account.find_by(id: message.account_id)
      user = User.find_by(id: message.reference_id)
      client = InternalApi.new(account: account, user: user, prefer_text_default: true)

      handlers = {
        "GET"    => ->(c, path, q, b, k) { c.get(path, query: q, idempotency_key: k, prefer_text: true) },
        "POST"   => ->(c, path, q, b, k) { c.post(path, body: b, query: q, idempotency_key: k, prefer_text: true) },
        "PUT"    => ->(c, path, q, b, k) { c.put(path, body: b, query: q, idempotency_key: k, prefer_text: true) },
        "PATCH"  => ->(c, path, q, b, k) { c.patch(path, body: b, query: q, idempotency_key: k, prefer_text: true) },
        "DELETE" => ->(c, path, q, b, k) { c.delete(path, body: b, query: q, idempotency_key: k, prefer_text: true) }
      }

      api_results = []
      next_suggestions_prompt = nil

      api_calls.each do |call|
        method = call["method"].to_s.upcase.presence || "GET"
        path = call["path"].to_s
        query = call["query"].is_a?(Hash) ? call["query"] : {}
        body = call["body"].is_a?(Hash) ? call["body"] : {}
        key = call["idempotency_key"]

        handler = handlers[method] || ->(*) { raise "Unsupported method: #{method}" }
        result = handler.call(client, path, query, body, key)
        api_results << { method: method, path: path, ok: true, result: result }

        next_suggestions_prompt = call["prompt_instructions"] if call["prompt_instructions"].present?

        api_call_payload = {
          entity: Message::ROLE_SYSTEM,
          status: Message::STATUS_NOT_ANSWERED,
          metadata: { api_call: { path: path, method: method, params: query.merge(body), ok: true } },
          content: "API #{method} #{path} completed",
          created_at: Time.current
        }

        ActionCable.server.broadcast("messages_user_#{message.reference_id}", api_call_payload)
        broadcast_to_domain_channel(message, api_call_payload)
      end

      return unless api_results.any?

      summary_lines = api_results.map do |r|
        payload_text = r[:ok] ? (r[:result].is_a?(String) ? r[:result] : r[:result].to_json) : r[:error].to_s
        status_text = r[:ok] ? "OK" : "FAIL"
        "#{r[:method]} #{r[:path]}: #{status_text}\n\n#{payload_text}\n"
      end.join("\n")

      next_suggestions = generate_suggestions(prompt: next_suggestions_prompt.to_s + summary_lines) if next_suggestions_prompt.present?

      new_message.update!(content: (new_message.content.to_s + "\n\nAPI results:\n\n#{summary_lines}\n"))

      api_result_payload = {
        id: new_message.id,
        entity: new_message.entity,
        status: new_message.status,
        metadata: new_message.metadata.merge(next_suggestions: next_suggestions),
        content: new_message.content,
        created_at: new_message.created_at
      }

      ActionCable.server.broadcast("messages_user_#{message.reference_id}", api_result_payload)
      broadcast_to_domain_channel(message, api_result_payload)
    end

    def extract_no_reply(data)
      return data.dig("errors", "no_reply") if data.dig("errors", "no_reply").present?
      return data.dig("response", "no_reply") if data.dig("response", "no_reply").present?

      data["no_reply"] || false
    end

    def broadcast_to_domain_channel(message, payload)
      return unless message.domain.present? && message.workspace_id.present?

      workspace = message.workspace
      return unless workspace&.domain_reference_id.present?

      DomainMessageChannel.broadcast_message(
        user_id: message.reference_id,
        domain: message.domain,
        domain_reference_id: workspace.domain_reference_id,
        payload: payload.merge(domain_reference_id: workspace.domain_reference_id)
      )
    end

    def generate_suggestions(prompt:)
      headers = {
        "Content-Type" => "application/json",
        "Authorization" => "Bearer #{ENV.fetch('INTERNAL_API_SECRET')}"
      }

      body = { prompt: prompt }.to_json
      path = "/next_suggestions/"
      response = HTTParty.post("#{ENV['RECRUITER_AGENT_API_URL']}#{path}", headers: headers, body: body)

      return response.parsed_response if response.success?

      Rails.logger.error "[ProcessWorker] generate_suggestions failed: Status #{response.code}, Body: #{response.body}"
      nil
    rescue StandardError => e
      Rails.logger.error "[ProcessWorker] generate_suggestions error: #{e.message}"
      nil
    end

    def enrich_navigation_with_search_params(response_metadata)
      navigation_actions = response_metadata["navigation_actions"]
      api_calls = response_metadata["api_calls"]
      return unless navigation_actions.is_a?(Array) && api_calls.is_a?(Array)

      search_params = extract_search_params(api_calls)
      return if search_params.blank?

      navigation_actions.each do |nav|
        next unless nav.is_a?(Hash)
        nav["params"] = (nav["params"] || {}).merge(search_params)
      end

      plan_nav = response_metadata.dig("plan", "navigation_actions")
      return unless plan_nav.is_a?(Array)

      plan_nav.each do |nav|
        next unless nav.is_a?(Hash)
        nav["params"] = (nav["params"] || {}).merge(search_params)
      end
    end

    def extract_search_params(api_calls)
      result = {}

      api_calls.each do |call|
        next unless call.is_a?(Hash)
        params = call["params"] || call["query"] || {}
        next unless params.is_a?(Hash)

        result["term"] = params["term"] if params["term"].present?
        result["where"] = params["where"] if params["where"].present?
        result["filter"] = params["filter"] if params["filter"].present?

        order = params.each_with_object({}) do |(k, v), acc|
          acc[k] = v if k.to_s.start_with?("order[")
        end
        result["order"] = order if order.present?
      end

      result
    end
  end
end
