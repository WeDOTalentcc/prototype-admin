module Skills
  class DefaultCategoriesCreator
    DEFAULT_CATEGORIES = [
      { name: "Linguagens de Programação", description: "Linguagens de programação e scripting", icon: "💻", color: "#3B82F6" },
      { name: "Frameworks Backend", description: "Frameworks e bibliotecas para desenvolvimento backend", icon: "⚙️", color: "#10B981" },
      { name: "Frameworks Frontend", description: "Frameworks e bibliotecas para desenvolvimento frontend", icon: "🎨", color: "#8B5CF6" },
      { name: "Bancos de Dados", description: "Sistemas de gerenciamento de banco de dados", icon: "🗄️", color: "#F59E0B" },
      { name: "DevOps & Cloud", description: "Ferramentas de infraestrutura, cloud e DevOps", icon: "☁️", color: "#06B6D4" },
      { name: "Mobile", description: "Desenvolvimento mobile nativo e híbrido", icon: "📱", color: "#EC4899" },
      { name: "Testes & QA", description: "Ferramentas e frameworks de testes", icon: "🧪", color: "#14B8A6" },
      { name: "Design & UX/UI", description: "Ferramentas de design e prototipação", icon: "🎭", color: "#F97316" },
      { name: "Data Science & IA", description: "Machine Learning, Data Science e Inteligência Artificial", icon: "🤖", color: "#6366F1" },
      { name: "Metodologias Ágeis", description: "Metodologias e frameworks ágeis", icon: "🔄", color: "#84CC16" },
      { name: "Segurança", description: "Segurança da informação e cybersecurity", icon: "🔒", color: "#EF4444" },
      { name: "Soft Skills", description: "Habilidades comportamentais e interpessoais", icon: "🤝", color: "#A855F7" },
      { name: "Gestão de Projetos", description: "Ferramentas e metodologias de gestão", icon: "📊", color: "#0EA5E9" },
      { name: "Ferramentas de Colaboração", description: "Ferramentas de comunicação e trabalho em equipe", icon: "💬", color: "#22C55E" },
      { name: "Versionamento", description: "Controle de versão e gestão de código", icon: "🔀", color: "#F43F5E" },
      { name: "CMS & E-commerce", description: "Plataformas de conteúdo e e-commerce", icon: "🛒", color: "#14B8A6" },
      { name: "APIs & Integrações", description: "Desenvolvimento e integração de APIs", icon: "🔌", color: "#8B5CF6" },
      { name: "Business Intelligence", description: "Ferramentas de BI e análise de dados", icon: "📈", color: "#F59E0B" },
      { name: "Automação", description: "RPA e ferramentas de automação", icon: "🔁", color: "#06B6D4" },
      { name: "Blockchain & Web3", description: "Blockchain, criptomoedas e Web3", icon: "⛓️", color: "#FBBF24" },
      { name: "Marketing Digital", description: "SEO, SEM, Redes Sociais, Marketing de Conteúdo", icon: "📣", color: "#EF4444" },
      { name: "Vendas & CRM", description: "Técnicas de vendas, CRM, prospecção", icon: "💰", color: "#10B981" },
      { name: "Financeiro & Contábil", description: "Contabilidade, finanças, controladoria", icon: "💵", color: "#F59E0B" },
      { name: "Recursos Humanos", description: "Recrutamento, treinamento, cultura organizacional", icon: "👥", color: "#8B5CF6" },
      { name: "Jurídico", description: "Direito, compliance, contratos", icon: "⚖️", color: "#6366F1" },
      { name: "Logística & Supply Chain", description: "Gestão de estoque, transporte, distribuição", icon: "🚚", color: "#06B6D4" },
      { name: "Atendimento ao Cliente", description: "SAC, suporte, experiência do cliente", icon: "🎧", color: "#EC4899" },
      { name: "Idiomas", description: "Inglês, Espanhol, Mandarim e outros idiomas", icon: "🌐", color: "#14B8A6" },
      { name: "Liderança", description: "Gestão de pessoas, coaching, mentoria", icon: "👔", color: "#A855F7" },
      { name: "Comunicação", description: "Oratória, apresentações, redação", icon: "🗣️", color: "#F97316" },
      { name: "Criatividade & Inovação", description: "Design Thinking, brainstorming, inovação", icon: "💡", color: "#FBBF24" },
      { name: "Análise de Negócios", description: "Business analysis, requisitos, processos", icon: "🔍", color: "#3B82F6" },
      { name: "Produto & UX Research", description: "Product management, pesquisa de usuário", icon: "🎯", color: "#EC4899" },
      { name: "Compliance & Governança", description: "Auditoria, LGPD, políticas corporativas", icon: "📋", color: "#EF4444" },
      { name: "Qualidade & Processos", description: "Six Sigma, Lean, melhoria contínua", icon: "✅", color: "#10B981" },
      { name: "Educação & Treinamento", description: "Didática, metodologias de ensino, e-learning", icon: "📚", color: "#6366F1" },
      { name: "Saúde & Bem-estar", description: "Medicina, enfermagem, nutrição, psicologia", icon: "🏥", color: "#EF4444" },
      { name: "Engenharia & Manufatura", description: "Engenharia civil, mecânica, industrial", icon: "🏗️", color: "#F59E0B" },
      { name: "Sustentabilidade & ESG", description: "Meio ambiente, responsabilidade social, ESG", icon: "🌱", color: "#10B981" },
      { name: "Audiovisual & Produção", description: "Edição de vídeo, fotografia, produção", icon: "🎬", color: "#8B5CF6" }
    ].freeze

    def self.create_for_account(account)
      new(account).create_defaults
    end

    def initialize(account)
      @account = account
    end

    def create_defaults
      created_count = 0
      skipped_count = 0

      DEFAULT_CATEGORIES.each do |category_data|
        category = SkillCategory.find_or_initialize_by(name: category_data[:name])

        if category.persisted?
          skipped_count += 1
          log_skipped(category)
          next
        end

        category.assign_attributes(category_data)

        if category.save
          created_count += 1
          log_created(category)
        else
          log_error(category_data, category)
        end
      end

      build_result(created_count, skipped_count)
    end

    private

    def log_created(category)
      Rails.logger.info "✓ Categoria criada: #{category.name}"
    end

    def log_skipped(category)
      Rails.logger.info "⊙ Categoria já existe: #{category.name}"
    end

    def log_error(category_data, category)
      Rails.logger.error "✗ Erro ao criar categoria #{category_data[:name]}: #{category.errors.full_messages.join(', ')}"
    end

    def build_result(created, skipped)
      {
        created: created,
        skipped: skipped,
        total: DEFAULT_CATEGORIES.count
      }
    end
  end
end
