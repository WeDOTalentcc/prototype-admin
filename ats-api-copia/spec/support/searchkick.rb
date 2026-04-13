# spec/support/searchkick.rb

RSpec.configure do |config|
  # Garante que todos os índices do Searchkick sejam limpos e reindexados
  # UMA VEZ antes de toda a suíte de testes. Isso é crucial para começar
  # com um estado limpo e ter os dados base disponíveis para todas as specs.
  config.before(:suite) do
    # Rails.application.eager_load!
    # Define o tenant para 'public' antes de qualquer operação Searchkick global.
    # Isso é fundamental para que `tenant_index_name` gere o nome correto do índice.
    # Se você usa um tenant padrão diferente de 'public' nos seus testes, ajuste aqui.
    Apartment::Tenant.switch!('public')

    puts "\nIniciando configuração do Searchkick para a suíte de testes..."

    Searchkick.models.each do |model|
      # Verifica se o modelo tem Searchkick mesmo
      if model.respond_to?(:searchkick_index)
        index_name = model.search_index.name
        puts "  Processando modelo: #{model.name} (Índice: #{index_name})"

        begin
          if model.search_index.exists?
            model.search_index.delete
            puts "    Deletado índice existente: #{index_name}"
          else
            puts "    Índice #{index_name} não existia (não precisa deletar)."
          end
        rescue Elastic::Transport::Transport::Errors::NotFound
          puts "    Índice #{index_name} não encontrado (já limpo)."
        rescue => e
          warn "    ERRO inesperado ao tentar deletar índice #{index_name}: #{e.message}"
        end

        begin
          model.reindex(refresh: true)
          puts "    Reindexado modelo: #{model.name}. Índice #{index_name} está pronto."
        rescue => e
          warn "    ERRO ao reindexar modelo #{model.name}: #{e.message}"
          raise e
        end
      else
        puts "  Modelo #{model.name} não usa Searchkick (ignorando)."
      end
    end

    puts "Configuração de Searchkick concluída."
  end

  # DESABILITA os callbacks do Searchkick para CADA TESTE individualmente.
  # Isso é a chave para a performance! Evita que cada `create(:job)` ou
  # `update` dentro dos testes dispare uma chamada ao Elasticsearch,
  # que é lenta e desnecessária para a maioria dos testes.
  config.before(:each) do
    Searchkick.disable_callbacks
    # Garante que o tenant esteja correto para cada teste,
    # caso algum teste anterior tenha mudado o tenant.
    Apartment::Tenant.switch!('public') # OU Apartment::Tenant.switch!('seu_tenant_padrao_aqui')
  end

  # REATIVA os callbacks do Searchkick para testes ESPECÍFICOS que precisam
  # que os dados sejam indexados (por exemplo, testes de POST/PUT ou que
  # buscam dados recém-criados).
  #
  # A flag `search: true` será usada nos `it` blocks que realmente
  # interagem com o Elasticsearch para busca/indexação imediata.
  config.around(:each, search: true) do |example|
    Searchkick.enable_callbacks do
      example.run
    end
    # Após o teste, force o refresh do índice para garantir que os dados
    # criados/atualizados durante o teste estejam imediatamente visíveis
    # para as asserções de busca.
    # É importante garantir que o tenant esteja correto ANTES de chamar refresh.
    Apartment::Tenant.switch!('public') # Garante que o tenant esteja certo antes do refresh
    Searchkick.client.indices.refresh(index: Job.search_index.name)
  end

  # Garante que os callbacks estejam reativados após CADA TESTE.
  # Isso é um fallback caso algum `around` block não seja executado corretamente,
  # evitando que os próximos testes fiquem com os callbacks desabilitados.
  config.after(:each) do
    Searchkick.enable_callbacks
    # Volta para o tenant público padrão após cada teste para evitar interferência.
    Apartment::Tenant.reset
  end
end