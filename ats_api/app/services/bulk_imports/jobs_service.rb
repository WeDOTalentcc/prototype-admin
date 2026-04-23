module BulkImports
  class JobsService
    # Retorna um hash com os campos disponíveis para importação de Vagas.
    # A estrutura é { nome_do_campo: { label: 'Rótulo para o Usuário', required: true/false } }
    def self.call
      {
        # Informações Essenciais
        title: { label: "Título da Vaga", required: true },
        description: { label: "Descrição da Vaga", required: false },

        # Localização
        city: { label: "Cidade", required: false },
        state: { label: "Estado (UF)", required: false },
        country: { label: "País", required: false },

        # Modelo de Trabalho
        workplace_type: { label: "Modelo de Trabalho (remoto, híbrido, presencial)", required: false },
        is_remote: { label: "É 100% Remoto? (true/false)", required: false },

        # Datas
        published_date: { label: "Data de Publicação", required: false },
        application_deadline: { label: "Data Limite para Candidatura", required: false },

        # Informações de Integração e URLs
        job_url: { label: "URL da Vaga Original", required: false },
        provider: { label: "Provedor Externo (ex: Gupy, Catho)", required: false },
        provider_job_id: { label: "ID da Vaga no Provedor", required: false },

        # Flags e Selos
        disabilities: { label: "Vaga Afirmativa para PCD? (true/false)", required: false },
        friendly_badge: { label: 'Possui Selo "Empresa Amiga"? (true/false)', required: false },

        # Informações da Página de Carreiras (se aplicável)
        career_page_name: { label: "Nome da Página de Carreiras", required: false },
        career_page_url: { label: "URL da Página de Carreiras", required: false },
        career_page_logo: { label: "URL do Logo da Página de Carreiras", required: false },

        external_id: { label: "ID Externo da Vaga", required: false }
      }
    end
  end
end
