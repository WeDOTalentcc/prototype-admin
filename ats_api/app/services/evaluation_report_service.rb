class EvaluationReportService
  Result = Struct.new(:success?, :data, :error)

  def self.call(evaluation_id:, job_id:)
    new(evaluation_id: evaluation_id, job_id: job_id).call
  end

  def initialize(evaluation_id:, job_id:)
    @evaluation_id = evaluation_id
    @job_id = job_id
  end

  def call
    return Result.new(false, nil, "Evaluation ID é obrigatório") if @evaluation_id.blank?
    return Result.new(false, nil, "Job ID é obrigatório") if @job_id.blank?

    evaluation_candidates = find_evaluation_candidates

    answers = Answer.where(evaluation_id: @evaluation_id, candidate_id: evaluation_candidates.pluck(:candidate_id))

    answers_payload = evaluation_candidates.map do |ec|
      candidate_answers = answers.select { |ans| ans.candidate_id == ec.candidate_id }
      if candidate_answers&.count > 0
        payload = {
          candidate_id: ec.candidate_id,
          candidate_name: ec.candidate&.name,
          questions: candidate_answers.map { |ans| { answers: ans.choices, comments: get_response_comments(ans.comments_response) } }
        }
        payload
      end
    end

    job = Job.find_by(id: @job_id)

    job_context = {
      title: job&.title,
      description: job&.description
    }

    prompt = generate_prompt(answers_payload, job_context)

    report = self.generate_report(prompt: prompt)

    return Result.new(false, nil, "Nenhum candidato encontrado") if evaluation_candidates.empty?

    Result.new(true, report, nil)
  end

  private

  def get_response_comments(raw)
    safe_str = raw.gsub(/:([a-zA-Z0-9_]+)=>/, '"\1":')
    safe_str = safe_str.gsub(/\bnil\b/, "null")
    safe_str = safe_str.gsub(/\btrue\b/, "true")
    safe_str = safe_str.gsub(/\bfalse\b/, "false")
    JSON.parse(safe_str)
  end

  def find_evaluation_candidates
    EvaluationCandidate.joins(:evaluation)
                      .where(
                        evaluation: { id: @evaluation_id },
                        job_id: @job_id,
                        is_deleted: false,
                        completed: true
                      )
  end


  def generate_prompt(answers_payload, job_context)
    <<~PROMPT
      Você é um especialista em Recrutamento e Seleção para o mercado de tecnologia no Brasil.
      Sua tarefa é analisar os dados completos das respostas dos candidatos e elaborar um relatório geral, além de trazer até 10 dos candidatos mais bem avaliados, com um feedback breve sobre eles.
      Considere apenas as informações fornecidas sobre a vaga e as respostas.

      ### DADOS DA VAGA ###
      #{job_context}
      ### FIM DOS DADOS ###

      ### RESPOSTAS DOS CANDIDATOS ###
      #{answers_payload.to_json}
      ### FIM DAS RESPOSTAS ###

      Responda APENAS com um objeto JSON contendo uma chave "candidates" que é uma lista de objetos, cada um contendo "name"(nome do candidato) e "description"(feedback sobre o candidato).
    PROMPT
  end

  def generate_report(prompt:)
    headers = {
      "Content-Type" => "application/json",
      "Authorization" => "Bearer #{ENV.fetch('INTERNAL_API_SECRET')}"
    }

    body = { prompt: prompt }.to_json
    path = "/evaluation_reports/generate"
    response = HTTParty.post("#{ENV['RECRUITER_AGENT_API_URL']}#{path}", headers: headers, body: body)

    if response.success?
      response.parsed_response
    else
      Rails.logger.error "Erro em RecruitAgentService#generate_job_suggestion: Status #{response.code}, Body: #{response.body}"
      nil
    end
  rescue StandardError => e
    Rails.logger.error "Exceção em RecruitAgentService#generate_job_suggestion: #{e.message}"
    nil
  end
end
