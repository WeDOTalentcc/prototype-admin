# app/services/job_suggestion_service.rb
class JobSuggestionService
  Result = Struct.new(:success?, :suggestion, :error)

  PROMPT_BUILDERS = {
    "title"                => :prompt_for_title,
    "description"          => :prompt_for_description,
    "skills"               => :prompt_for_skills,
    "behavioral_skills"    => :prompt_for_behavioral_skills,
    "responsibilities"     => :prompt_for_responsibilities,
    "questions"            => :prompt_for_questions,
    "evaluation_questions" => :prompt_for_evaluation_questions
  }.freeze

  def self.call(job_data:, type:)
    new(job_data: job_data, type: type).call
  end

  def initialize(job_data:, type:, wsi_type: "wsi_compact", query: nil, job: nil)
    @data = job_data
    @type = type
    @wsi_type = wsi_type
    @query = query.presence
    @job = job
  end

  def call
    prompt = build_prompt
    return Result.new(false, nil, "Tipo de sugestão inválido.") unless prompt

    generate_with_gemini(prompt)
  end

  private

  def generate_with_gemini(prompt)
    return Result.new(false, nil, "Ambiente de teste não suporta chamadas à API.") if Rails.env.test?

    begin
      response = Llm::Gateway.chat(
        messages: [
          {
            role: "system",
            content: "Você é um especialista em Recrutamento e Seleção no Brasil, utilizando a metodologia WSI (WeDoTalent Skill Index). Você deve retornar APENAS um objeto JSON válido, sem texto adicional."
          },
          {
            role: "user",
            content: prompt
          }
        ],
        temperature: 0.3,
        max_tokens: 3000,
        tracking: { operation: "jobs.suggestion" }
      )

      content = response.dig("choices", 0, "message", "content")

      if content.nil?
        return Result.new(false, nil, "Falha ao gerar perguntas: resposta vazia do Gemini")
      end

      json_content = extract_json_from_response(content)

      if json_content.nil?
        return Result.new(false, nil, "Falha ao processar resposta do Gemini: formato inválido")
      end

      parsed_response = JSON.parse(json_content, symbolize_names: true)
      parsed_response = apply_evaluation_questions_jd_anchoring(parsed_response)
      Result.new(true, parsed_response, nil)
    rescue JSON::ParserError => e
      error_msg = "Erro ao fazer parse do JSON retornado pelo Gemini: #{e.message}"
      Result.new(false, nil, error_msg)
    rescue StandardError => e
      if gemini_rate_limited?(e)
        return Result.new(
          false,
          nil,
          "AI API rate limit or quota exceeded. Wait a few minutes, reduce request frequency, or increase quota in Google AI Studio / Cloud billing."
        )
      end

      error_msg = "Erro ao gerar perguntas com Gemini: #{e.message}"
      Result.new(false, nil, error_msg)
    end
  end

  def gemini_rate_limited?(error)
    msg = error.message.to_s
    msg.include?("429") || /resource exhausted|too many requests/i.match?(msg)
  end

  def apply_evaluation_questions_jd_anchoring(parsed_response)
    return parsed_response unless @type == "evaluation_questions"
    return parsed_response if @job.blank?

    Wsi::EvaluationQuestionsJdAnchoring.apply!(parsed_response, job: @job)
  end

  def extract_json_from_response(text)
    return nil if text.blank?

    cleaned_text = text.gsub(/```(?:json)?\s*/, "").gsub(/```\s*/, "").strip

    json_match = cleaned_text.match(/\{[\s\S]*\}/)

    if json_match
      json_text = json_match[0]
      JSON.parse(json_text)
      return json_text
    end

    JSON.parse(cleaned_text)
    cleaned_text
  rescue JSON::ParserError => e
    Rails.logger.warn "JobSuggestionService: Erro ao extrair JSON: #{e.message}"
    nil
  end

  def build_job_context
    context_str = ""

    if @type == "evaluation_questions"
      context_str += build_detailed_job_context
    else
      relevant_fields = [
        :title, :description, :contract_type, :seniority_level,
        :workplace_type, :city, :state, :country
      ]
      relevant_fields.each do |field|
        value = @data[field]
        if value.present?
          label = field.to_s.humanize
          context_str += "- #{label}: #{value}\n"
        end
      end
      if @data[:is_remote]
        context_str += "- Localização: Remoto\n"
      end
      if @data[:responsibilities].present? && @data[:responsibilities].is_a?(Array) && @data[:responsibilities].any?
        responsibilities_text = @data[:responsibilities].join("\n- ")
        context_str += "- Responsabilidades:\n- #{responsibilities_text}\n"
      end

      context_str += wizard_skills_context_lines
    end

    context_str.strip
  end

  def wizard_skills_context_lines
    lines = +""
    skills = @data[:skills] || @data["skills"]
    if skills.present? && skills.is_a?(Array) && skills.any?
      lines << "- Skills técnicas (wizard): #{skills.join(', ')}\n"
    end
    behavioral = @data[:behavioral_skills] || @data["behavioral_skills"]
    if behavioral.present? && behavioral.is_a?(Array) && behavioral.any?
      lines << "- Competências comportamentais (wizard): #{behavioral.join(', ')}\n"
    end
    lines
  end

  def build_detailed_job_context
    context_str = ""

    context_str += "- Título: #{@data[:title]}\n" if @data[:title].present?
    context_str += "- Descrição: #{@data[:description]}\n" if @data[:description].present?
    context_str += "- Cidade: #{@data[:city]}\n" if @data[:city].present?
    context_str += "- Estado: #{@data[:state]}\n" if @data[:state].present?
    context_str += "- País: #{@data[:country]}\n" if @data[:country].present?
    context_str += "- Nível de Senioridade: #{@data[:seniority]}\n" if @data[:seniority].present?
    if @data[:wsi_calibration_line].present?
      context_str += "- WSI seniority calibration (methodology §4.1): #{@data[:wsi_calibration_line]}\n"
    end
    context_str += "- Tipo de Contrato: #{@data[:employment_type]}\n" if @data[:employment_type].present?

    if @data[:skills].present? && @data[:skills].is_a?(Array) && @data[:skills].any?
      skills_text = @data[:skills].join(", ")
      context_str += "- Habilidades Técnicas: #{skills_text}\n"
    end

    if @data[:languages].present? && @data[:languages].is_a?(Array) && @data[:languages].any?
      languages_text = @data[:languages].join(", ")
      context_str += "- Idiomas: #{languages_text}\n"
    end

    context_str
  end

  def build_prompt
    builder_method = PROMPT_BUILDERS[@type]

    return nil unless builder_method

    job_context = build_job_context

    send(builder_method, job_context)
  end

  def prompt_for_title(context)
    <<~PROMPT
      Você é um especialista em Recrutamento e Seleção no Brasil.
      Sua tarefa é analisar os dados completos de uma vaga e sugerir 3 títulos de cargo precisos, profissionais e atrativos para o mercado brasileiro. Considere todos os detalhes fornecidos.

      ### DADOS DA VAGA ###
      #{context}
      ### FIM DOS DADOS ###

      Responda APENAS com um objeto JSON contendo uma chave "title" que é uma lista de strings.
    PROMPT
  end

  def prompt_for_description(context)
    <<~PROMPT
      Você é um Redator especialista em Job Descriptions, focado no mercado brasileiro e na metodologia WSI (WeDoTalent Skill Index).
      Sua tarefa é criar UMA descrição de vaga completa, profissional e atrativa, e extrair as competências técnicas e comportamentais seguindo rigorosamente o WSI.

      ### METODOLOGIA WSI - DIRETRIZES OBRIGATÓRIAS ###

      **Competências (Boas Práticas WSI - Seção 10):**
      - Até 7 competências totais: exatamente 5 técnicas + 2 comportamentais
      - Distribuição de pesos: 70% técnicas / 30% comportamentais (Seção 5.4)
      - Competências técnicas: ferramentas, tecnologias, domínios específicos (validáveis por autodeclaração + contexto - Seção 4)
      - Competências comportamentais: alinhadas ao Big Five/OCEAN (Seção 2.4):
        - O (Abertura): Curiosidade, inovação, aprendizado
        - C (Conscienciosidade): Organização, foco em resultado, rigor técnico
        - E (Extroversão): Comunicação, liderança, assertividade
        - A (Amabilidade): Empatia, colaboração, trabalho em equipe
        - N (Estabilidade Emocional): Controle sob pressão, tomada de decisão, resiliência

      **Estrutura para Triagem WSI (Seção 3.1):**
      - Skills técnicas: mensuráveis em escala 1-5 (Modelo Dreyfus - Seção 2.3)
      - Skills comportamentais: validáveis por perguntas situacionais STAR (CBI - Seção 2.1)
      - Responsabilidades que evidenciem níveis cognitivos (Taxonomia de Bloom - Seção 2.2)

      ### DADOS DA VAGA PARA USAR COMO BASE ###
      #{context}
      ### FIM DOS DADOS ###

      **FORMATO DE RESPOSTA - Objeto JSON com exatamente 3 chaves:**

      1. "description" (string): Uma única descrição em markdown com as seções:
         - ## Descrição da Posição
         - ## Responsabilidades
         - ## Qualificações Obrigatórias
         - ## Qualificações Desejáveis
         Linguagem inclusiva e convidativa.

      2. "skills" (array de strings): Exatamente 5 competências técnicas mais relevantes para a vaga.
         Exemplo: ["SAP ECC", "Módulos Financeiro e Contábil", "Oracle EPM", "Pacote Office", "Análise de Sistemas"]

      3. "behavioral_skills" (array de strings): Exatamente 2 competências comportamentais alinhadas ao Big Five.
         Exemplo: ["Trabalho em Equipe", "Comunicação com Stakeholders"]

      Responda APENAS com o objeto JSON, sem texto adicional.
    PROMPT
  end

  def prompt_for_skills(context)
    exclusion_section = existing_skills_exclusion_section

    <<~PROMPT
      Você é um sistema de IA especialista em extrair competências TÉCNICAS de descrições de vagas, seguindo a metodologia WSI (WeDoTalent Skill Index).

      ### METODOLOGIA WSI - SKILLS TÉCNICAS (F1 / P3) ###

      **Mínimo obrigatório:** pelo menos 9 competências técnicas específicas por vaga (não genéricas: evite só "cloud", "dados", "programação" sem decompor).
      Se o texto da vaga trouxer menos de 9, decomponha skills genéricas em sub-skills específicas (ex.: "Cloud" → "AWS EC2", "S3", "IAM", "CloudFormation").
      **Distribuição (Seção 5.4):** Competências técnicas representam 70% do peso na triagem WSI.
      **Tipos de Validação (Seção 4):** Skills técnicas são validáveis por autodeclaração + contexto (escala 1-5, Modelo Dreyfus - Seção 2.3).

      **O que incluir:**
      - Ferramentas e tecnologias específicas (ex: SAP ECC, Ruby on Rails, Figma)
      - Domínios técnicos e metodologias (ex: Testes Automatizados, Análise de Sistemas)
      - Competências mensuráveis em escala 1-5 (Novice a Expert)
      - NÃO inclua soft skills ou competências comportamentais
      #{exclusion_section}

      ### DADOS DA VAGA ###
      #{context}
      ### FIM DOS DADOS ###

      Responda APENAS com um objeto JSON com a chave "skills", contendo pelo menos 9 strings (competências técnicas), preferencialmente exatamente 9 ou mais se o JD justificar.
      Exemplo: {"skills": ["Ruby on Rails", "PostgreSQL", "Redis", "RSpec", "Sidekiq", "Docker", "AWS EC2", "REST APIs", "Git"]}
    PROMPT
  end

  def prompt_for_behavioral_skills(context)
    exclusion_section = existing_behavioral_skills_exclusion_section

    <<~PROMPT
      Você é um sistema de IA especialista em extrair competências COMPORTAMENTAIS de descrições de vagas, seguindo a metodologia WSI (WeDoTalent Skill Index).

      ### METODOLOGIA WSI - SKILLS COMPORTAMENTAIS (F1 / P5) ###

      **Mínimo obrigatório:** pelo menos 5 competências comportamentais, cada uma contextualizável ao papel (não apenas adjetivos soltos).
      **Cobertura desejável:** inclua competências que reflitam os cinco eixos Big Five (OCEAN) quando o JD permitir inferência justificada.
      **Distribuição (Seção 5.4):** Competências comportamentais representam 30% do peso na triagem WSI.
      **Validação (Seção 3.1):** Fit comportamental via perguntas situacionais (CBI/STAR - Seção 2.1).

      **Big Five (OCEAN) - Seção 2.4 - Use como referência:**
      - O (Abertura): Curiosidade, inovação, aprendizado contínuo
      - C (Conscienciosidade): Organização, foco em resultado, rigor técnico
      - E (Extroversão): Comunicação, liderança, assertividade
      - A (Amabilidade): Empatia, colaboração, trabalho em equipe
      - N (Estabilidade Emocional): Controle sob pressão, tomada de decisão, resiliência

      **O que incluir:**
      - Competências validáveis por perguntas situacionais STAR (Situation, Task, Action, Result)
      - Soft skills alinhadas ao Big Five, com redação profissional
      - NÃO inclua skills técnicas ou ferramentas
      #{exclusion_section}

      ### DADOS DA VAGA ###
      #{context}
      ### FIM DOS DADOS ###

      Responda APENAS com um objeto JSON com a chave "behavioral_skills", contendo pelo menos 5 strings com menos de 7 palavras (competências comportamentais), preferencialmente exatamente 5 ou mais se o JD justificar.
      Exemplo: {"behavioral_skills": ["Comunicação com stakeholders", "Colaboração cross-funcional", "Organização e priorização", "Resiliência sob prazos", "Pensamento crítico"]}
    PROMPT
  end

  def prompt_for_responsibilities(context)
    existing_section = existing_responsibilities_context_section

    <<~PROMPT
      Você é um especialista em recrutamento no Brasil. Sugira responsabilidades para a vaga como **tópicos curtos de lista**, no estilo de bullet de JD (uma linha por item).

      ### FORMATO OBRIGATÓRIO ###
      - Cada item: **no máximo 5 palavras** (contar palavras separadas por espaço); **uma única linha**; **sem vírgulas**; nada de frases longas.
      - Estrutura: **verbo de ação + objeto** o mais enxuto possível dentro do limite.
      - Linguagem **neutra em gênero**; sem “candidato ideal”, “ele/ela”, nem marcadores discriminatórios.
      - Pareça item de lista em vaga de emprego, não parágrafo de relatório.

      ### REGRAS DE CONTEÚDO ###
      - Baseie-se nos dados da vaga (título, descrição, senioridade, skills); não invente áreas inteiras ausentes do contexto.
      - Compatível com a senioridade informada.
      - Não cite frameworks internos (WSI, Big Five, Bloom, Dreyfus, STAR).
      #{existing_section}

      ### DADOS DA VAGA (JD + COMPLEMENTOS) ###
      #{context}
      ### FIM DOS DADOS ###

      Responda APENAS com JSON: chave "responsibilities" = array de strings, **pelo menos 3** itens e no máximo 6 itens, cada string curta conforme acima.
      Exemplo: {"responsibilities": ["Priorizar backlog com produto", "Desenvolver APIs em Rails", "Revisar código do time", "Participar ritos do squad"]}
    PROMPT
  end

  def existing_responsibilities_context_section
    raw = @data[:responsibilities] || @data["responsibilities"]
    return "" if raw.blank?

    items = Array(raw).map(&:to_s).map(&:strip).reject(&:blank?)
    return "" if items.empty?

    <<~SECTION

      **Responsabilidades já informadas pelo recrutador (preserve o que for correto; complemente lacunas ou substitua trechos genéricos — não duplique o mesmo sentido):**
      #{items.map { |line| "- #{line}" }.join("\n")}
    SECTION
  end

  def prompt_for_questions(context)
    <<~PROMPT
      Você é um especialista em Recrutamento e Seleção no Brasil.
      Sua tarefa é analisar os dados completos de uma vaga e sugerir 5 perguntas de entrevista que ajudem a avaliar as habilidades técnicas e comportamentais dos candidatos.
      Considere apenas as informações fornecidas sobre a vaga.

      ### DADOS DA VAGA ###
      #{context}
      ### FIM DOS DADOS ###

      Responda APENAS com um objeto JSON contendo uma chave "questions" que é uma lista de objetos, cada um contendo "title"(título da pergunta) e "description"(pergunta).
    PROMPT
  end

  def self.trait_ranking_mode_for_wsi_type(wsi_type)
    wsi_type.to_s == "wsi_compact_plus" ? :full : :compact
  end

  def self.ensure_wsi_jd_trait_ranking!(job, wsi_type:)
    return { success: false, error: "job missing" } if job.blank?

    mode = trait_ranking_mode_for_wsi_type(wsi_type)
    result = Wsi::TraitRankingService.call(job: job, mode: mode)
    unless result[:success]
      Rails.logger.warn "[JobSuggestionService] wsi_jd_trait_ranking not persisted for job #{job.id} (#{result[:code]}): #{result[:error]}"
    end
    result
  end

  def self.generate_evaluation_questions(job, wsi_type: "wsi_compact", query: nil)
    job = job.reload if job.respond_to?(:reload) && job.persisted?
    ensure_wsi_jd_trait_ranking!(job, wsi_type: wsi_type)
    new(
      job_data: build_job_data_for_evaluation(job, wsi_type: wsi_type),
      type: "evaluation_questions",
      wsi_type: wsi_type,
      query: query,
      job: job
    ).call
  end

  def self.top_ocean_traits_for_job(job)
    data = job&.wsi_jd_trait_ranking
    return [] unless data.is_a?(Hash)

    rows = Array(data["big_five_ranking"]).select do |r|
      r.is_a?(Hash) && r["in_top_n"]
    end
    rows.sort_by { |r| r["rank"].to_i }.map { |r| r["trait"] }.compact
  end

  def self.build_job_data_for_evaluation(job, wsi_type: "wsi_compact")
    skills = job.skill_relationships
                 .includes(:skill)
                 .where(is_deleted: false)
                 .order(priority: :desc)
                 .map { |sr| sr.skill&.name }
                 .compact

    languages = job.language_relationships
                   .includes(:language)
                   .map { |lr| lr.language&.name }
                   .compact

    seniority_text = job.seniority.present? ? Job::SENIORITY[job.seniority] : nil
    employment_type_text = job.employment_type.present? ? Job::EMPLOYMENT_TYPES[job.employment_type] : nil
    wsi_calibration_line = wsi_calibration_line_for_job(job)

    mode = trait_ranking_mode_for_wsi_type(wsi_type)
    seniority_key = Wsi::Constants.seniority_key(job)
    distribution_plan = Wsi::QuestionDistributionService.call(seniority_key: seniority_key, mode: mode)
    framework_allocation = Wsi::QuestionDistributionService.framework_allocation(
      technical: distribution_plan[:technical],
      behavioral: distribution_plan[:behavioral],
      mode: mode
    )
    macro_weights = Wsi::Constants::SENIORITY_WEIGHTS.fetch(seniority_key, Wsi::Constants::SENIORITY_WEIGHTS["pleno"])
    total_questions = distribution_plan[:technical] + distribution_plan[:behavioral]

    {
      title: job.title,
      description: job.description,
      city: job.city,
      state: job.state,
      country: job.country,
      seniority: seniority_text,
      employment_type: employment_type_text,
      skills: skills,
      languages: languages,
      wsi_calibration_line: wsi_calibration_line,
      wsi_distribution_plan: distribution_plan,
      wsi_framework_allocation: framework_allocation,
      wsi_macro_weights: macro_weights,
      wsi_total_questions: total_questions,
      wsi_top_ocean_traits: top_ocean_traits_for_job(job),
      wsi_mode: mode.to_s
    }
  end

  def self.wsi_calibration_line_for_job(job)
    key = Wsi::Constants.seniority_key(job)
    cal = Wsi::Constants.seniority_calibration(key)
    [
      "canonical_key=#{key}",
      "experience_years=#{cal[:experience_years]}",
      "dreyfus_technical=#{cal[:dreyfus_technical_level]} (#{cal[:dreyfus_technical_label]})",
      "bloom_expected=#{cal[:bloom_expected]}",
      "dreyfus_behavioral=#{cal[:dreyfus_behavioral_level]}"
    ].join("; ")
  end

  def existing_skills_exclusion_section
    skills = extract_existing_skills
    return "" if skills.empty?

    <<~SECTION

      **IMPORTANTE - Skills já selecionadas na vaga (NÃO sugerir novamente):**
      #{skills.join(", ")}
      Sugira APENAS competências técnicas DIFERENTES das listadas acima. Evite sinônimos ou variações (ex: "Ruby" vs "Ruby on Rails").
    SECTION
  end

  def existing_behavioral_skills_exclusion_section
    skills = extract_existing_behavioral_skills
    return "" if skills.empty?

    <<~SECTION

      **IMPORTANTE - Competências comportamentais já selecionadas na vaga (NÃO sugerir novamente):**
      #{skills.join(", ")}
      Sugira APENAS competências comportamentais DIFERENTES das listadas acima. Evite sinônimos ou variações (ex: "Trabalho em Equipe" vs "Colaboração").
    SECTION
  end

  def extract_existing_skills
    raw = @data[:skills] || @data["skills"]
    return [] if raw.blank?

    Array(raw).map { |s| s.is_a?(Hash) ? (s[:name] || s["name"]) : s.to_s }.compact.reject(&:blank?)
  end

  def extract_existing_behavioral_skills
    raw = @data[:behavioral_skills] || @data["behavioral_skills"]
    return [] if raw.blank?

    Array(raw).map { |s| s.is_a?(Hash) ? (s[:name] || s["name"]) : s.to_s }.compact.reject(&:blank?)
  end

  def query_section
    return "" if @query.blank?
    <<~SECTION

      ### QUERY / FOCO ADICIONAL DO USUÁRIO ###
      Use esta query como foco complementar ao gerar as perguntas. As perguntas devem considerar tanto os dados da vaga quanto este foco.
      #{@query}
      ### FIM DA QUERY ###
    SECTION
  end

  def prompt_for_evaluation_questions(context)
    wsi_config = get_wsi_config

    <<~PROMPT
      Você é um especialista em Recrutamento e Seleção no Brasil, utilizando a metodologia WSI (WeDoTalent Skill Index).
      Sua tarefa é analisar os dados completos de uma vaga e gerar perguntas de avaliação que sigam os frameworks científicos consolidados: CBI (Competency-Based Interviewing), Taxonomia de Bloom, Modelo Dreyfus e Big Five (OCEAN).

      ### METODOLOGIA WSI - DIRETRIZES ###

      **Modelo WSI Selecionado: #{wsi_config[:name]}**
      - Total de perguntas: #{wsi_config[:min_questions]}-#{wsi_config[:max_questions]} perguntas
      - Tempo médio: #{wsi_config[:time_range]}
      - Uso ideal: #{wsi_config[:ideal_use]}
      - Precisão esperada: #{wsi_config[:precision]}

      #{wsi_evaluation_distribution_section}

      **Tipos de Pergunta a Incluir:**
      1. **Autodeclaração + Contexto** (60% do peso): Perguntas que quantificam domínio (escala 1-5) e validam aplicação real com evidências STAR (Situation, Task, Action, Result)
      2. **Microcase Prático** (20% do peso): Testes de lógica técnica, adequados para vagas seniores e especializadas
      3. **Situação Contextual** (15% do peso): Avalia profundidade, clareza e postura comportamental
      4. **Pergunta Teórica Leve** (5% do peso): Valida clareza conceitual e consistência

      **Níveis Cognitivos (Taxonomia de Bloom):**
      - Lembrar: Autodeclaração simples
      - Compreender: Perguntas teóricas
      - Aplicar: Microcases práticos
      - Analisar: Contexto real e situações complexas
      - Criar: Respostas de inovação/liderança (para níveis sênior)

      **Modelo Dreyfus (Scores 1-5):**
      - 1 (Novice): Conhecimento básico, teórico
      - 2 (Advanced Beginner): Aplicação parcial e guiada
      - 3 (Competent): Execução estável e consistente
      - 4 (Proficient): Aplicação autônoma e adaptativa
      - 5 (Expert): Domínio intuitivo e contextual

      **Big Five (OCEAN) para Soft Skills:**
      - O (Abertura): Curiosidade, inovação, aprendizado
      - C (Conscienciosidade): Organização, foco em resultado, rigor técnico
      - E (Extroversão): Energia, assertividade, comunicação, liderança
      - A (Amabilidade): Empatia, colaboração, trabalho em equipe
      - N (Estabilidade Emocional): Controle sob pressão, tomada de decisão, resiliência

      **Boas Práticas:**
      - #{wsi_competencies_practice_line}
      - Perguntas curtas e diretas (respostas de até 40 segundos em áudio)
      - Priorize evidências concretas (projetos, métricas, resultados)
      - Inclua perguntas que permitam detectar inflação de score (autodeclara alto, contexto pobre)
      - Considere o nível de senioridade da vaga para ajustar complexidade

      ### DADOS DA VAGA ###
      #{context}
      ### FIM DOS DADOS ###
      #{query_section}

      **INSTRUÇÕES:**
      Gere perguntas que:
      1. Validem competências técnicas específicas mencionadas na vaga (skills, tecnologias)
      2. Avaliem fit comportamental usando situações STAR
      3. Considerem o nível de senioridade informado
      4. Incluam microcases práticos para vagas sênior/lead
      5. Testem diferentes níveis cognitivos (aplicar, analisar, criar)
      6. Sejam adequadas para avaliação via conversação (respostas curtas e objetivas)
      #{single_question_instruction}

      Responda APENAS com um objeto JSON contendo uma chave "questions" que é uma lista de objetos. **OBRIGATÓRIO**: TODAS as perguntas DEVEM incluir TODOS os campos abaixo, sem exceção.

      Campos de cada pergunta:
      - "title": título/tema da pergunta (nome da competência avaliada)
      - "description": a pergunta completa e clara
      - "response_type": ("autodeclaration", "contextual", "microcase", "situational", "theoretical")
      - "competence_type": ("technical" ou "behavioral")
      - "bloom_level": ("remember", "understand", "apply", "analyze", "create")
      - "dreyfus_target": 1-5 baseado na senioridade da vaga
      - "ocean_trait": ("openness", "conscientiousness", "extraversion", "agreeableness", "stability") ou null — use "stability" (estabilidade emocional); o sistema persiste como neuroticism internamente
      - "framework": **OBRIGATÓRIO** - um de: "cbi", "bloom", "dreyfus", "big_five". Framework PRINCIPAL da pergunta (WSI Seção 2):
        • "cbi": CBI/STAR (Seção 2.1) - perguntas situacionais, fit comportamental, cenários STAR
        • "bloom": Taxonomia de Bloom (Seção 2.2) - microcases, teóricas, autodeclaração com foco cognitivo
        • "dreyfus": Modelo Dreyfus (Seção 2.3) - validação técnica de maturidade (escala 1-5), padrão para skills técnicas
        • "big_five": Big Five/OCEAN (Seção 2.4) - soft skills quando ocean_trait é o foco
      - "framework_weights": **OBRIGATÓRIO** - objeto com bloom, dreyfus, big_five, cbi_star (valores decimais que somam 1.0). Técnico: {"bloom": 0.25, "dreyfus": 0.35, "big_five": 0.1, "cbi_star": 0.3}. Comportamental: {"bloom": 0.15, "dreyfus": 0.25, "big_five": 0.3, "cbi_star": 0.3}
      - "validation_type_weight": **OBRIGATÓRIO** - número 0-1 conforme response_type: autodeclaration=0.60, contextual=0.60, microcase=0.20, situational=0.15, theoretical=0.05
      - "time": tempo em minutos (1, 1.5 ou 2). Autodeclaração/microcase/teórica: 1. Contextual/situacional: 1.5 ou 2.
      #{category_section}

      Regra para "framework": deve ser o framework com MAIOR peso em framework_weights para aquela pergunta. Ex: se dreyfus=0.35 é o maior → framework="dreyfus".

      Exemplo de framework_weights por competence_type:
      • technical: {"bloom": 0.25, "dreyfus": 0.35, "big_five": 0.1, "cbi_star": 0.3}
      • behavioral: {"bloom": 0.15, "dreyfus": 0.25, "big_five": 0.3, "cbi_star": 0.3}

      Exemplo de validation_type_weight por response_type:
      • autodeclaration: 0.60 | contextual: 0.60 | microcase: 0.20 | situational: 0.15 | theoretical: 0.05

      Gere exatamente entre #{wsi_config[:min_questions]} e #{wsi_config[:max_questions]} perguntas. NUNCA retorne framework_weights vazio {}, validation_type_weight null nem framework vazio.
    PROMPT
  end

  def get_wsi_config
    case @wsi_type
    when "query"
      {
        name: "WSI Query",
        min_questions: 1,
        max_questions: 1,
        time_range: "40s-1:30 min",
        ideal_use: "Foco pontual guiado por query do usuário",
        precision: "~90%"
      }
    when "wsi_compact_plus"
      wsi_config_from_distribution(
        name: "WSI Compact+",
        fallback_min: 8,
        fallback_max: 10,
        fallback_time: "6:30-9 min",
        ideal_use: "Triagem aprofundada, posições críticas, Senior+",
        precision: "~95%"
      )
    else
      wsi_config_from_distribution(
        name: "WSI Compact",
        fallback_min: 6,
        fallback_max: 8,
        fallback_time: "5-7 min",
        ideal_use: "Triagens rápidas, alto volume, vagas operacionais/júnior",
        precision: "~90%"
      )
    end
  end

  def wsi_config_from_distribution(name:, fallback_min:, fallback_max:, fallback_time:, ideal_use:, precision:)
    raw = @data[:wsi_distribution_plan] || @data["wsi_distribution_plan"]
    plan = raw.is_a?(Hash) ? raw.to_h.symbolize_keys : {}
    total = plan[:technical].to_i + plan[:behavioral].to_i

    if total.positive?
      {
        name: name,
        min_questions: total,
        max_questions: total,
        time_range: wsi_time_range_for_total(total),
        ideal_use: ideal_use,
        precision: precision
      }
    else
      {
        name: name,
        min_questions: fallback_min,
        max_questions: fallback_max,
        time_range: fallback_time,
        ideal_use: ideal_use,
        precision: precision
      }
    end
  end

  def wsi_time_range_for_total(total)
    case total
    when 1..7 then "5-7 min"
    when 8..10 then "6:30-10 min"
    else "10-15 min"
    end
  end

  def wsi_evaluation_distribution_section
    raw_plan = @data[:wsi_distribution_plan] || @data["wsi_distribution_plan"]
    return wsi_evaluation_distribution_fallback if raw_plan.blank? || !raw_plan.is_a?(Hash)

    plan = raw_plan.to_h.symbolize_keys
    return wsi_evaluation_distribution_fallback if plan[:technical].nil?

    fw = (@data[:wsi_framework_allocation] || @data["wsi_framework_allocation"] || {}).to_h.symbolize_keys
    weights = (@data[:wsi_macro_weights] || @data["wsi_macro_weights"] || {}).to_h.symbolize_keys
    weights = Wsi::Constants::SENIORITY_WEIGHTS["pleno"] if weights.blank?
    fw = Wsi::QuestionDistributionService.framework_allocation(
      technical: plan[:technical],
      behavioral: plan[:behavioral],
      mode: (@data[:wsi_mode] || @data["wsi_mode"] || "compact").to_sym
    ) if fw.blank?
    traits = @data[:wsi_top_ocean_traits] || @data["wsi_top_ocean_traits"] || []
    t_count = plan[:technical].to_i + plan[:behavioral].to_i
    pct_t = t_count.positive? ? (100.0 * plan[:technical].to_f / t_count).round(1) : 0.0
    pct_b = t_count.positive? ? (100.0 * plan[:behavioral].to_f / t_count).round(1) : 0.0
    traits_line = traits.any? ? traits.join(", ") : "(priorize traits do ranking Big Five da vaga quando disponível)"

    <<~SECTION.strip
      **Estrutura da Avaliação:**
      - Distribuição por senioridade: #{plan[:technical]} perguntas técnicas (#{pct_t}%) e #{plan[:behavioral]} comportamentais (#{pct_b}%) — total #{t_count} perguntas
      - Traits OCEAN prioritários (Top-#{plan[:top_n_traits]}): #{traits_line}
      - Pesos no score WSI (técnico / comportamental): #{weights[:technical]} / #{weights[:behavioral]}
      - Alocação por framework (slots): Dreyfus #{fw[:dreyfus]}, Bloom #{fw[:bloom]}, CBI técnico #{fw[:cbi_technical]}, CBI comportamental #{fw[:cbi_behavioral]}, Big Five #{fw[:big_five]}
      - Duração estimada: alinhe ao tempo do modelo WSI acima
    SECTION
  end

  def wsi_evaluation_distribution_fallback
    wsi_config = get_wsi_config
    <<~SECTION.strip
      **Estrutura da Avaliação:**
      - Distribuição: proporcional à senioridade (use calibração WSI da vaga)
      - Duração estimada: #{wsi_config[:time_range]}
    SECTION
  end

  def wsi_competencies_practice_line
    raw = @data[:wsi_distribution_plan] || @data["wsi_distribution_plan"]
    plan = raw.is_a?(Hash) ? raw.to_h.symbolize_keys : {}
    if plan[:technical].present?
      total = plan[:technical].to_i + plan[:behavioral].to_i
      "Defina exatamente #{plan[:technical]} competências cobertas por perguntas técnicas e #{plan[:behavioral]} por perguntas comportamentais (#{total} perguntas no total, sem misturar a contagem)"
    else
      "Defina competências alinhadas à senioridade e ao modelo WSI selecionado"
    end
  end

  def single_question_instruction
    return "" unless @wsi_type == "query"

    <<~TEXT
      7. Como o tipo selecionado é "query", gere exatamente 1 pergunta de maior impacto, mantendo os princípios WSI (CBI, Bloom, Dreyfus e OCEAN quando aplicável).
    TEXT
  end

  def category_section
    return "" unless %w[wsi_compact wsi_compact_plus].include?(@wsi_type)

    <<~TEXT
      - "category": **OBRIGATÓRIO** - uma de: "padrao" (Perguntas Padrão da Empresa), "avaliacao" (Avaliação Técnica), "situacional" (Análise Situacional e Fit). Use "padrao" para perguntas genéricas/abertura, "avaliacao" para competências técnicas, "situacional" para fit comportamental e cenários STAR.
    TEXT
  end
end
