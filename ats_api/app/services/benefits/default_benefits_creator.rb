module Benefits
  class DefaultBenefitsCreator
    DEFAULT_BENEFITS = [
      {
        name: "Vale Refeição/Alimentação",
        types: [ "monetary_value" ],
        enable_value_editing: true,
        is_per_day: false,
        days_of_month: 0,
        is_possible_extend_to_dependents: false
      },
      {
        name: "Vale Transporte",
        types: [ "boolean" ],
        enable_value_editing: false,
        is_per_day: false,
        days_of_month: 0,
        is_possible_extend_to_dependents: false
      },
      {
        name: "Plano de Saúde",
        types: [ "boolean", "text" ],
        enable_value_editing: true,
        is_per_day: false,
        days_of_month: 0,
        is_possible_extend_to_dependents: true
      },
      {
        name: "Plano Odontológico",
        types: [ "boolean", "text" ],
        enable_value_editing: true,
        is_per_day: false,
        days_of_month: 0,
        is_possible_extend_to_dependents: true
      },
      {
        name: "Seguro de Vida",
        types: [ "boolean" ],
        enable_value_editing: false,
        is_per_day: false,
        days_of_month: 0,
        is_possible_extend_to_dependents: false
      },
      {
        name: "Auxílio Home Office",
        types: [ "monetary_value" ],
        enable_value_editing: true,
        is_per_day: false,
        days_of_month: 0,
        is_possible_extend_to_dependents: false
      },
      {
        name: "Gympass/Wellhub",
        types: [ "boolean" ],
        enable_value_editing: false,
        is_per_day: false,
        days_of_month: 0,
        is_possible_extend_to_dependents: false
      },
      {
        name: "Day Off de Aniversário",
        types: [ "boolean" ],
        enable_value_editing: false,
        is_per_day: false,
        days_of_month: 0,
        is_possible_extend_to_dependents: false
      },
      {
        name: "Licença Parental Estendida",
        types: [ "boolean", "text" ],
        enable_value_editing: true,
        is_per_day: false,
        days_of_month: 0,
        is_possible_extend_to_dependents: false
      },
      {
        name: "Programa de Desenvolvimento",
        types: [ "boolean", "text" ],
        enable_value_editing: true,
        is_per_day: false,
        days_of_month: 0,
        is_possible_extend_to_dependents: false
      },
      {
        name: "Stock Options/Equity",
        types: [ "boolean", "percentage", "text" ],
        enable_value_editing: true,
        is_per_day: false,
        days_of_month: 0,
        is_possible_extend_to_dependents: false
      },
      {
        name: "Auxílio Educação",
        types: [ "monetary_value", "percentage", "text" ],
        enable_value_editing: true,
        is_per_day: false,
        days_of_month: 0,
        is_possible_extend_to_dependents: false
      },
      {
        name: "Auxílio Creche",
        types: [ "monetary_value" ],
        enable_value_editing: true,
        is_per_day: false,
        days_of_month: 0,
        is_possible_extend_to_dependents: false
      },
      {
        name: "Participação nos Lucros (PLR)",
        types: [ "monetary_value", "percentage", "text" ],
        enable_value_editing: true,
        is_per_day: false,
        days_of_month: 0,
        is_possible_extend_to_dependents: false
      },
      {
        name: "Previdência Privada",
        types: [ "boolean", "percentage", "text" ],
        enable_value_editing: true,
        is_per_day: false,
        days_of_month: 0,
        is_possible_extend_to_dependents: false
      },
      {
        name: "Assistência Psicológica",
        types: [ "boolean" ],
        enable_value_editing: false,
        is_per_day: false,
        days_of_month: 0,
        is_possible_extend_to_dependents: true
      },
      {
        name: "Desconto em Produtos/Serviços",
        types: [ "boolean", "percentage", "text" ],
        enable_value_editing: true,
        is_per_day: false,
        days_of_month: 0,
        is_possible_extend_to_dependents: false
      },
      {
        name: "Horário Flexível",
        types: [ "boolean" ],
        enable_value_editing: false,
        is_per_day: false,
        days_of_month: 0,
        is_possible_extend_to_dependents: false
      },
      {
        name: "Day Off Extra",
        types: [ "text" ],
        enable_value_editing: true,
        is_per_day: true,
        days_of_month: 0,
        is_possible_extend_to_dependents: false
      },
      {
        name: "Auxílio Mudança",
        types: [ "monetary_value", "text" ],
        enable_value_editing: true,
        is_per_day: false,
        days_of_month: 0,
        is_possible_extend_to_dependents: false
      }
    ].freeze

    def self.create_for_account(account)
      new(account).create_defaults
    end

    def self.create_in_public_schema
      # Para benefícios compartilhados entre todos os tenants
      Apartment::Tenant.switch!("public") do
        new(nil).create_defaults
      end
    end

    def initialize(account)
      @account = account
    end

    def create_defaults
      created_count = 0
      skipped_count = 0

      DEFAULT_BENEFITS.each do |benefit_data|
        benefit = Benefit.find_or_initialize_by(name: benefit_data[:name])

        if benefit.new_record?
          benefit.assign_attributes(benefit_data)
          if benefit.save
            created_count += 1
            Rails.logger.info "✓ Benefício criado: #{benefit.name}"
          else
            Rails.logger.error "✗ Erro ao criar benefício #{benefit_data[:name]}: #{benefit.errors.full_messages.join(', ')}"
          end
        else
          skipped_count += 1
          Rails.logger.info "⊙ Benefício já existe: #{benefit.name}"
        end
      end

      {
        created: created_count,
        skipped: skipped_count,
        total: DEFAULT_BENEFITS.count
      }
    end
  end
end
