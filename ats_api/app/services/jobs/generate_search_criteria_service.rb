# frozen_string_literal: true

module Jobs
  class GenerateSearchCriteriaService
    Result = Struct.new(:success?, :criteria, :generated, :error, keyword_init: true)

    def initialize(job:, force: false)
      @job = job
      @force = force
    end

    def call
      return existing_result if @job.agent_search_criteria.present? && !@force
      return insufficient_data_result unless sufficient_data?

      criteria = generate_criteria
      return failure_result unless criteria

      @job.update!(agent_search_criteria: criteria)
      Result.new("success?": true, criteria: criteria, generated: true)
    rescue StandardError => e
      Rails.logger.error "❌ [#{self.class.name}] job=#{@job.id} error=#{e.message}"
      Result.new("success?": false, error: "Internal error generating criteria.")
    end

    private

    def existing_result
      Result.new("success?": true, criteria: @job.agent_search_criteria, generated: false)
    end

    def insufficient_data_result
      Result.new("success?": false, error: "Job needs at least a title and description or skills to generate criteria.")
    end

    def failure_result
      Result.new("success?": false, error: "Failed to generate criteria.")
    end

    def sufficient_data?
      @job.title.present? && (@job.description.present? || @job.skills.any?)
    end

    def generate_criteria
      response = Llm::Gateway.chat(
        messages: [
          { role: "user", content: build_prompt }
        ],
        temperature: 0.2,
        max_tokens: 2048,
        tracking: {
          operation: "jobs.generate_search_criteria",
          job_id: @job.id,
          account_id: @job.account_id,
          user_id: @job.user_id
        }
      )

      extract_text(response)
    end

    def build_prompt
      <<~PROMPT
        Analyze this job and generate search criteria. Respond ONLY with the 5 labeled sections below, no extra text.

        ---
        TITLE: #{@job.title}
        DEPARTMENT: #{@job.department&.name || "N/A"}
        LOCATION: #{[ @job.city, @job.state, @job.country ].compact.join(", ").presence || "N/A"}
        WORK_MODEL: #{@job.workplace_type_text}
        SENIORITY: #{seniority_text}
        EMPLOYMENT_TYPE: #{employment_type_text}
        SKILLS: #{job_skills.join(", ").presence || "N/A"}
        DESCRIPTION: #{(@job.description || "").truncate(3000)}
        ---

        Respond with EXACTLY this format:

        CRITERIOS_PRIMARIOS: [mandatory requirements: role title + seniority level + 3-5 core hard skills. These are non-negotiable dealbreakers.]

        CRITERIOS_SECUNDARIOS: [4-6 complementary skills that increase relevance: tools, methodologies, domain knowledge, leadership ability]

        CRITERIOS_DIFERENCIACAO: [3-5 rare differentiators: niche expertise, industry experience, certifications, languages]

        BUSCA_BOOLEANA: [single LinkedIn boolean string with 4-5 key terms using AND/OR, e.g.: "Ruby on Rails" AND (Senior OR Sênior) AND PostgreSQL AND (Sidekiq OR "background jobs") AND (AWS OR GCP)]

        PERFIL_IDEAL: [2-3 sentences in Brazilian Portuguese describing the ideal candidate. Include: seniority, core skills, preferred sector/industry, location. Do NOT mention salary or benefits.]
      PROMPT
    end

    def seniority_text
      return "Não informada" unless @job.seniority.present?

      Job::SENIORITY[@job.seniority] || "Não informada"
    end

    def employment_type_text
      return "Não informado" unless @job.employment_type.present?

      Job::EMPLOYMENT_TYPES[@job.employment_type] || "Não informado"
    end

    def job_skills
      @job.skills.pluck(:name)
    end

    def extract_text(response)
      text = response&.dig("choices", 0, "message", "content")
      return nil if text.blank?

      text.strip.gsub(/\A["']|["']\z/, "").strip
    end
  end
end
