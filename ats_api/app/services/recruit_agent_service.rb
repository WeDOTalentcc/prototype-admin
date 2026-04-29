# app/services/recruit_agent_service.rb
require "httparty"

class RecruitAgentService
  include HTTParty

  base_uri ENV.fetch("RECRUITER_AGENT_API_URL", "http://host.docker.internal:8081")

  def self.generate_job_suggestion(type:, prompt:)
    api_url = ENV.fetch("RECRUITER_AGENT_API_URL", "http://host.docker.internal:8081")
    endpoint = "#{api_url}/jobs/suggestions/#{type}"

    headers = {
      "Content-Type" => "application/json",
      "Authorization" => "Bearer #{ENV.fetch('INTERNAL_API_SECRET')}"
    }

    body = { prompt: prompt }.to_json
    response = HTTParty.post(endpoint, headers: headers, body: body, timeout: 30)

    if response.success?
      parsed = response.parsed_response
      parsed
    else
      error_msg = "Erro em RecruitAgentService#generate_job_suggestion: Status #{response.code}, Body: #{response.body}"
      nil
    end
  rescue HTTParty::Error => e
    error_msg = "Erro HTTP em RecruitAgentService#generate_job_suggestion: #{e.message}"
    nil
  rescue StandardError => e
    error_msg = "Exceção em RecruitAgentService#generate_job_suggestion: #{e.message}"
    nil
  end

  def self.map_csv_headers(csv_headers:, target_fields:, entity_name:)
    headers = {
      "Content-Type" => "application/json",
      "Authorization" => "Bearer #{ENV.fetch('INTERNAL_API_SECRET')}"
    }

    body = {
      csv_headers: csv_headers,
      target_fields: target_fields,
      entity_name: entity_name
    }.to_json

    response = post("/map-headers", body: body, headers: headers)

    if response.success?
      response.parsed_response
    else
      Rails.logger.error "Erro ao chamar RecruitAgentService#map_csv_headers: Status #{response.code}, Body: #{response.body}"
      {}
    end
  rescue StandardError => e
    Rails.logger.error "Exceção ao chamar RecruitAgentService#map_csv_headers: #{e.message}"
    {}
  end

  def self.extract_candidate_data(text)
    secret_token = ENV.fetch("INTERNAL_API_SECRET")

    headers = {
      "Content-Type" => "application/json",
      "Authorization" => "Bearer #{secret_token}"
    }

    body = { text: text }.to_json

    response = post("/extract-candidate-data", body: body, headers: headers)

    if response.success?
      response.parsed_response.deep_symbolize_keys
    else
      Rails.logger.error "Erro ao chamar RecruitAgentService: Status #{response.code}, Body: #{response.body}"
      nil
    end
  rescue StandardError => e
    Rails.logger.error "Exceção ao chamar RecruitAgentService: #{e.message}"
    nil
  end

  def self.generate_workspace_name(message)
    headers = {
      "Content-Type" => "application/json",
      "Authorization" => "Bearer #{ENV.fetch('INTERNAL_API_SECRET')}"
    }

    body = { message: message }.to_json

    response = post("/workspaces/generate-name", body: body, headers: headers)

    if response.success?
      response.parsed_response["name"]
    else
      Rails.logger.error "Erro ao chamar RecruitAgentService#generate_workspace_name: Status #{response.code}, Body: #{response.body}"
      nil
    end
  rescue StandardError => e
    Rails.logger.error "Exceção ao chamar RecruitAgentService#generate_workspace_name: #{e.message}"
    nil
  end
end
