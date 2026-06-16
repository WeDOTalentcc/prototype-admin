module Candidates
  module Search
    class HydeDocumentGenerator
      def generate(profile, context: :resume, verbosity: :standard)
        return "" if profile.blank?

        case context
        when :job_description
          generate_for_jd(profile, verbosity)
        else
          generate_for_resume(profile, verbosity)
        end
      end

      private

      RESUME_HYDE_TEMPLATE = <<~TEMPLATE
        Profissional de tecnologia com perfil %{seniority} e %{years_experience} anos de experiência sólida.

        EXPERIÊNCIA PRINCIPAL:
        Atuo como %{primary_role} com foco em desenvolvimento de soluções %{industry}.
        Possuo experiência hands-on em %{tech_list}, tendo trabalhado em projetos de#{' '}
        alta complexidade envolvendo %{skill_context}.

        STACK TÉCNICA:
        Domínio avançado: %{primary_tech}
        Experiência sólida: %{secondary_tech}

        COMPETÊNCIAS:
        %{transferable_skills_text}

        PERFIL:
        Profissional com forte capacidade %{soft_skills}, experiência em times#{' '}
        %{team_context} e foco em entregas de qualidade no setor de %{industry}.
      TEMPLATE

      RESUME_CONCISE_TEMPLATE = <<~TEMPLATE
        Profissional %{seniority} com %{years_experience} anos de experiência.
        Atuação como %{primary_role}.
        Tecnologias: %{tech_list}.
        Competências: %{transferable_skills_text}.
        Setor: %{industry}.
      TEMPLATE

      JD_HYDE_TEMPLATE = <<~TEMPLATE
        Candidato ideal para vaga de %{role_title}:

        REQUISITOS ATENDIDOS:
        - Experiência de %{experience_range} em %{primary_tech}
        - Conhecimento sólido em %{required_skills}
        - Nível %{seniority} com atuação em %{industry}

        DIFERENCIAIS:
        - Experiência adicional em %{nice_to_have}
        - Capacidade de %{key_responsibilities}

        PERFIL COMPORTAMENTAL:
        Profissional com perfil %{behavioral_traits}, adequado para ambiente %{work_environment}.
      TEMPLATE

      JD_CONCISE_TEMPLATE = <<~TEMPLATE
        Candidato %{seniority} para %{role_title}.
        Experiência: %{primary_tech}.
        Skills: %{required_skills}.
        Setor: %{industry}.
      TEMPLATE

      def generate_for_resume(profile, verbosity)
        template = verbosity == :concise ? RESUME_CONCISE_TEMPLATE : RESUME_HYDE_TEMPLATE

        format(template, {
          seniority: profile["seniority"] || "pleno",
          years_experience: profile["years_experience"] || 5,
          primary_role: profile["primary_role"] || "desenvolvedor",
          industry: profile["industry"] || "tecnologia",
          tech_list: Array(profile["core_technologies"]).join(", "),
          skill_context: derive_skill_context(profile),
          primary_tech: Array(profile["core_technologies"]).first(2).join(" e "),
          secondary_tech: Array(profile["core_technologies"]).drop(2).join(", "),
          transferable_skills_text: format_skills(profile["transferable_skills"]),
          soft_skills: derive_soft_skills(profile["seniority"]),
          team_context: derive_team_context(profile["seniority"])
        })
      end

      def generate_for_jd(profile, verbosity)
        template = verbosity == :concise ? JD_CONCISE_TEMPLATE : JD_HYDE_TEMPLATE

        required = Array(profile["core_technologies"])
        nice_to_have = Array(profile["transferable_skills"])

        format(template, {
          role_title: profile["primary_role"] || "desenvolvedor",
          experience_range: calculate_experience_range(profile["years_experience"]),
          primary_tech: required.first(3).join(", "),
          required_skills: required.join(", "),
          seniority: profile["seniority"] || "pleno",
          industry: profile["industry"] || "tecnologia",
          nice_to_have: nice_to_have.join(", "),
          key_responsibilities: derive_key_responsibilities(profile),
          behavioral_traits: derive_behavioral_traits(profile["seniority"]),
          work_environment: derive_work_environment(profile["industry"])
        })
      end

      def derive_skill_context(profile)
        techs = Array(profile["core_technologies"])
        return "desenvolvimento de software" if techs.empty?

        contexts = []
        contexts << "arquitetura de sistemas distribuídos" if has_distributed_tech?(techs)
        contexts << "desenvolvimento web full-stack" if has_web_tech?(techs)
        contexts << "processamento de dados em larga escala" if has_data_tech?(techs)

        contexts.first || "desenvolvimento de software"
      end

      def has_distributed_tech?(techs)
        distributed = %w[redis elasticsearch kafka rabbitmq microservices]
        techs.any? { |t| distributed.any? { |d| t.downcase.include?(d) } }
      end

      def has_web_tech?(techs)
        web = %w[rails laravel django flask react vue angular next]
        techs.any? { |t| web.any? { |w| t.downcase.include?(w) } }
      end

      def has_data_tech?(techs)
        data = %w[spark hadoop airflow etl pipeline]
        techs.any? { |t| data.any? { |d| t.downcase.include?(d) } }
      end

      def format_skills(skills)
        Array(skills).join(", ").presence || "desenvolvimento de software"
      end

      def derive_soft_skills(seniority)
        case seniority.to_s.downcase
        when "senior", "lead", "principal", "staff"
          "de liderança, mentoria e tomada de decisões técnicas"
        when "pleno"
          "de resolução de problemas e trabalho em equipe"
        else
          "de aprendizado e evolução técnica"
        end
      end

      def derive_team_context(seniority)
        case seniority.to_s.downcase
        when "senior", "lead", "principal", "staff"
          "multidisciplinares e liderança de iniciativas técnicas"
        when "pleno"
          "ágeis e colaborativos"
        else
          "de desenvolvimento e aprendizado contínuo"
        end
      end

      def calculate_experience_range(years)
        return "3 a 5 anos" unless years.present?

        years = years.to_i
        return "1 a 3 anos" if years <= 3
        return "3 a 5 anos" if years <= 5
        return "5 a 8 anos" if years <= 8

        "mais de 8 anos"
      end

      def derive_key_responsibilities(profile)
        seniority = profile["seniority"].to_s.downcase

        case seniority
        when "senior", "lead", "principal", "staff"
          "definir arquitetura, liderar times e tomar decisões técnicas estratégicas"
        when "pleno"
          "desenvolver soluções complexas e colaborar com o time"
        else
          "desenvolver funcionalidades e aprender boas práticas"
        end
      end

      def derive_behavioral_traits(seniority)
        case seniority.to_s.downcase
        when "senior", "lead", "principal", "staff"
          "autônomo, orientado a resultados e com visão estratégica"
        when "pleno"
          "proativo, colaborativo e focado em qualidade"
        else
          "curioso, dedicado e com vontade de aprender"
        end
      end

      def derive_work_environment(industry)
        case industry.to_s.downcase
        when /fintech|banco|financeiro/
          "regulado, com foco em segurança e compliance"
        when /startup|saas/
          "dinâmico, com ritmo acelerado e cultura de inovação"
        when /enterprise|corporativo/
          "estruturado, com processos bem definidos"
        else
          "colaborativo e orientado a resultados"
        end
      end
    end
  end
end
