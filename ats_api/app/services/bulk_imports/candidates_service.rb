# app/services/bulk_imports/candidates_service.rb
module BulkImports
  class CandidatesService
    def self.call
      {

        name: { label: "Nome Completo", required: true },
        email: { label: "Email Principal", required: true },
        cpf: { label: "CPF", required: false },
        date_birth: { label: "Data de Nascimento", required: false },

        mobile_phone: { label: "Celular", required: false },
        phone: { label: "Telefone Fixo", required: false },
        secondary_email: { label: "Email Secundário", required: false },

        linkedin: { label: "URL do LinkedIn", required: false },
        github: { label: "URL do GitHub", required: false },
        portfolio: { label: "URL do Portfólio", required: false },

        role_name: { label: "Cargo Atual", required: false },
        current_company: { label: "Empresa Atual", required: false },
        position_level: { label: "Nível do Cargo", required: false },
        curriculum_text: { label: "Texto do Currículo (Resumo)", required: false },

        street: { label: "Rua", required: false },
        number: { label: "Número", required: false },
        complement: { label: "Complemento", required: false },
        district: { label: "Bairro", required: false },
        city: { label: "Cidade", required: false },
        state: { label: "Estado (UF)", required: false },
        zip: { label: "CEP", required: false },
        country: { label: "País", required: false },

        desired_salary: { label: "Salário Desejado", required: false },
        clt_expectation: { label: "Pretensão Salarial (CLT)", required: false },
        pj_expectation: { label: "Pretensão Salarial (PJ)", required: false },
        currency: { label: "Moeda (ex: BRL, USD)", required: false },
        remote_work: { label: "Aceita Remoto?", required: false },
        mobility: { label: "Disponibilidade para Mudança", required: false },

        source: { label: "Origem do Cadastro", required: false },
        comments: { label: "Observações", required: false },
        external_id: { label: "ID Externo do Candidato", required: true }
      }
    end
  end
end
