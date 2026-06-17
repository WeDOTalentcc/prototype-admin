# frozen_string_literal: true

module Wsi
  class QuestionPromptBuilder
    TECHNICAL_TEMPERATURE = 0.7
    BEHAVIORAL_TEMPERATURE = 0.75
    TECHNICAL_MAX_TOKENS = 200
    BEHAVIORAL_MAX_TOKENS = 250

    def initialize(
      skill_name: nil,
      seniority_label: nil,
      dreyfus_level: nil,
      dreyfus_label: nil,
      bloom_level: nil,
      bloom_label: nil,
      company_context: nil,
      responsibilities_excerpt: nil,
      skill_rare_or_proprietary: false,
      trait_name: nil,
      trait_label: nil,
      rank_position: nil,
      total_traits_selected: nil,
      evidence_list: nil,
      activation_scenario: nil,
      previous_questions_list: nil
    )
      @skill_name = skill_name
      @seniority_label = seniority_label
      @dreyfus_level = dreyfus_level
      @dreyfus_label = dreyfus_label
      @bloom_level = bloom_level
      @bloom_label = bloom_label
      @company_context = company_context.presence || "não informado"
      @responsibilities_excerpt = responsibilities_excerpt
      @skill_rare_or_proprietary = skill_rare_or_proprietary
      @trait_name = trait_name
      @trait_label = trait_label
      @rank_position = rank_position
      @total_traits_selected = total_traits_selected
      @evidence_list = evidence_list
      @activation_scenario = activation_scenario
      @previous_questions_list = previous_questions_list
    end

    def technical_prompt_parts
      system = <<~SYSTEM
        Você é um especialista em recrutamento técnico e avaliação de competências.
        Gere UMA pergunta de triagem técnica em português do Brasil.

        A pergunta deve:
        - Seguir o formato CBI: pedir uma situação passada real
        - Ter formato STAR implícito: situação → ação → resultado
        - Ser calibrada ao nível Dreyfus #{@dreyfus_level} (#{@dreyfus_label})
        - Exigir raciocínio compatível com Bloom #{@bloom_level} (#{@bloom_label})
        - Ser específica o suficiente para não ser respondida genericamente
        - Não mencionar Dreyfus, Bloom, STAR ou qualquer framework interno
        - Ter entre 1 e 3 frases
        - Ser uma pergunta ABERTA — sem opções A/B/C, sem múltiplas alternativas embutidas

        PROIBIDO — FORMATO:
        - Perguntas teóricas ("O que é X?")
        - Perguntas de auto-avaliação ("Você é bom em X?")
        - Perguntas que revelam a resposta esperada ou os critérios de avaliação
        - Usar as expressões "trade-off", "com critérios", "com resultados mensuráveis" no texto da pergunta
        - Perguntas com múltiplas alternativas embutidas ("Você preferiria X ou Y?")
        - Emojis ou linguagem informal

        PROIBIDO — FAIRNESS (BASE LEGAL: LGPD ART. 6º, CLT ART. 5º, CF ART. 5º):
        - Linguagem com marcador de gênero ("o desenvolvedor que você gerenciou")
          USE SEMPRE: "a pessoa", "quem estava no time", "o time", "a equipe"
        - Referência a características protegidas: raça, etnia, origem, religião,
          orientação sexual, estado civil, deficiência, faixa etária, nacionalidade
        - Termos de viés implícito: "universidades de primeira linha", "escola top",
          "nativo", "jovem e dinâmico", "recém-formado"
        - Prestígio de instituição de ensino como critério
        - Cenários pessoais ou fora do contexto profissional

        REGRA PARA SKILL RARA OU PROPRIETÁRIA:
        - Se a skill for um sistema interno ou tecnologia muito específica sem documentação
          pública suficiente, gere a pergunta sobre o domínio técnico adjacente mais relevante e retorne com prefixo interno:
          [SKILL_APPROXIMATED: domínio_adjacente_usado]
          seguido da pergunta sem o prefixo visível ao candidato (duas linhas: primeira linha prefixo, segunda a pergunta).
      SYSTEM

      user = <<~USER
        Skill avaliada: #{@skill_name}
        Senioridade: #{@seniority_label}
        Dreyfus esperado: #{@dreyfus_level} — #{@dreyfus_label}
        Bloom esperado: #{@bloom_level} — #{@bloom_label}
        Contexto da empresa/setor: #{@company_context}
        Responsabilidades relevantes do JD: #{@responsibilities_excerpt}
        Skill rara ou proprietária (usar regra SKILL_APPROXIMATED se sim): #{@skill_rare_or_proprietary ? 'sim' : 'não'}

        Retorne APENAS o texto da pergunta (sem aspas, sem explicações),
        exceto quando skill for aproximada — neste caso retorne o prefixo [SKILL_APPROXIMATED: ...]
        na linha anterior à pergunta.
      USER

      { system: system, user: user, temperature: TECHNICAL_TEMPERATURE, max_tokens: TECHNICAL_MAX_TOKENS }
    end

    def behavioral_prompt_parts
      system = <<~SYSTEM
        Você é um psicólogo organizacional especialista em entrevistas comportamentais (CBI).
        Gere UMA pergunta comportamental em português do Brasil para avaliar o trait Big Five especificado.

        A pergunta deve:
        - Criar um cenário que NATURALMENTE EXIJA o trait alvo (Trait Activation Theory)
        - Seguir formato CBI-STAR: pedir situação real passada + ação + resultado
        - Ser calibrada ao nível Dreyfus comportamental #{@dreyfus_level} (#{@dreyfus_label})
        - Exigir nível de reflexão compatível com Bloom #{@bloom_level} (#{@bloom_label})
        - Estar ancorada nas evidências do JD fornecidas
        - Ser específica o suficiente para que candidatos sem o trait não consigam responder bem
        - Não mencionar o nome do trait, nome de frameworks (Big Five, OCEAN, STAR, Bloom, Dreyfus)
          nem qualquer terminologia interna de avaliação
        - Ter entre 1 e 3 frases
        - O cenário ativador deve ser EXCLUSIVAMENTE profissional — nunca pessoal, familiar ou de saúde

        PROIBIDO — FORMATO:
        - Perguntas hipotéticas ("Como você faria se...")
        - Perguntas de auto-avaliação ("Você se considera empático?")
        - Revelar o comportamento esperado na própria pergunta

        PROIBIDO — FAIRNESS E NÃO-DISCRIMINAÇÃO (BASE LEGAL: LGPD ART. 6º, CLT ART. 5º, CF ART. 5º):
        - Qualquer marcador de gênero — USE: "a pessoa", "quem estava no time", "o colega",
          "a liderança do projeto", formas neutras sem pronome definido
          PROIBIDO: "o funcionário", "a gestora", "ele/ela", "seu chefe"
        - Referência a atributos protegidos: raça, etnia, origem, religião,
          orientação sexual, estado civil, deficiência, faixa etária, nacionalidade
        - Termos de viés implícito: "nativo", "jovem e dinâmico", "recém-formado",
          "universidades de primeira linha", "boa aparência", "perfil adequado"
        - Cenários pessoais ou fora do ambiente de trabalho
        - Cenários que pressupõem background cultural específico (festas, rituais, eventos sociais privados)

        REGRAS ESPECÍFICAS POR TRAIT DE ALTO RISCO DE VIÉS:
        - AMABILIDADE (Agreeableness): o cenário deve ser de CONFLITO PROFISSIONAL ou divergência
          de opinião em projeto/equipe — NUNCA linguagem de cuidado emocional ou suporte pessoal
        - ESTABILIDADE EMOCIONAL (Neuroticism↓): o cenário deve ser de pressão PROFISSIONAL —
          incidente em produção, mudança de escopo, entrega crítica — NUNCA situações de saúde pessoal,
          luto, conflito familiar ou vulnerabilidade pessoal
        - EXTRAVERSÃO: cenários de liderança, apresentação ou influência em CONTEXTO PROFISSIONAL
          (reunião, stakeholders, equipe) — NUNCA eventos sociais, festas ou contextos informais

        SELEÇÃO DO CENÁRIO QUANDO MÚLTIPLOS TRAITS COM SCORES PRÓXIMOS:
        - Foque a pergunta no trait com rank indicado abaixo
        - Não misture dois traits na mesma pergunta
      SYSTEM

      prev = Array(@previous_questions_list).compact_blank.join("; ")
      user = <<~USER
        Trait avaliado: #{@trait_name} (#{@trait_label})
        Rank do trait no JD: ##{@rank_position} de #{@total_traits_selected}
        Senioridade: #{@seniority_label}
        Dreyfus comportamental esperado: #{@dreyfus_level} — #{@dreyfus_label}
        Bloom esperado: #{@bloom_level} — #{@bloom_label}
        Evidências do JD para este trait: #{@evidence_list}
        Contexto da empresa/setor: #{@company_context}
        Cenário ativador recomendado: #{@activation_scenario}
        Perguntas já geradas nesta triagem (para evitar repetição): #{prev.presence || '[]'}

        Retorne APENAS o texto da pergunta, sem aspas, sem prefixos, sem explicações.
      USER

      { system: system, user: user, temperature: BEHAVIORAL_TEMPERATURE, max_tokens: BEHAVIORAL_MAX_TOKENS }
    end

    def self.parse_technical_llm_output(raw)
      text = raw.to_s.strip
      lines = text.lines.map(&:strip).reject(&:blank?)
      return { question: "", skill_approximated: false, approximated_domain: nil } if lines.empty?

      first = lines.first
      if first =~ /\A\[SKILL_APPROXIMATED:\s*(.+?)\]\s*\z/
        domain = Regexp.last_match(1).strip
        body = lines[1..].join("\n").strip
        return { question: body, skill_approximated: true, approximated_domain: domain }
      end

      { question: text, skill_approximated: false, approximated_domain: nil }
    end
  end
end
