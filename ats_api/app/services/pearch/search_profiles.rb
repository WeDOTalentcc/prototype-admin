module Pearch
  class SearchProfiles
    PROFILES = [
      {
        id: "fast",
        name: "Rápido",
        description: "Busca rápida sem insights detalhados. Ideal para exploração inicial.",
        estimated_time_seconds: 5,
        cost_per_result: 1,
        default_limit: 10,
        features: {
          type: "fast",
          insights: false,
          profile_scoring: false,
          high_freshness: false
        }
      },
      {
        id: "balanced",
        name: "Balanceado",
        description: "Melhor custo-benefício. Boa qualidade com velocidade aceitável.",
        estimated_time_seconds: 15,
        cost_per_result: 3,
        default_limit: 30,
        features: {
          type: "fast",
          insights: true,
          profile_scoring: true,
          high_freshness: false
        },
        recommended: true
      },
      {
        id: "premium",
        name: "Premium",
        description: "Máxima qualidade e insights detalhados. Para buscas críticas.",
        estimated_time_seconds: 45,
        cost_per_result: 7,
        default_limit: 10,
        features: {
          type: "pro",
          insights: true,
          profile_scoring: true,
          high_freshness: false
        }
      }
    ].freeze

    COST_NOTES = [
      "Custos adicionais: show_emails (+2/resultado), show_phone_numbers (+14/resultado)",
      "high_freshness adiciona +2 créditos/resultado e ~30 segundos ao tempo",
      "Use thread_id para paginação sem custo adicional pelos mesmos resultados"
    ].freeze

    def self.all
      PROFILES
    end

    def self.find(id)
      PROFILES.find { |p| p[:id] == id.to_s }
    end

    def self.default
      find("balanced")
    end

    def self.cost_notes
      COST_NOTES
    end

    def self.estimate_cost(profile_id, options = {})
      profile = find(profile_id) || default
      base_cost = profile[:cost_per_result] * (options[:limit] || profile[:default_limit])

      base_cost += options[:limit] * 2 if options[:show_emails]
      base_cost += options[:limit] * 14 if options[:show_phone_numbers]
      base_cost += options[:limit] * 2 if options[:high_freshness]

      base_cost
    end
  end
end
