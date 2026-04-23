namespace :sectors do
  desc "Fix sector names from SCREAMING_SNAKE_CASE to normal capitalized format"
  task fix_names: :environment do
    puts "Starting sector names normalization..."
    puts "=" * 80

    # Mapeamento de nomes antigos para novos
    name_mapping = {
      "TECNOLOGIA_INFORMACAO" => "Tecnologia da informação",
      "SOFTWARE_DESENVOLVIMENTO" => "Software e desenvolvimento",
      "SERVICOS_INTERNET" => "Serviços de internet",
      "SEGURANCA_REDES_COMPUTADORES" => "Segurança de redes e computadores",
      "TELECOMUNICACOES" => "Telecomunicações",
      "HARDWARE_EQUIPAMENTOS" => "Hardware e equipamentos",
      "SEMICONDUTORES" => "Semicondutores",

      "SERVICOS_FINANCEIROS" => "Serviços financeiros",
      "BANCO_INVESTIMENTOS" => "Banco de investimentos",
      "SEGUROS" => "Seguros",
      "CAPITAL_VENTURE" => "Capital de risco",
      "GESTAO_INVESTIMENTOS" => "Gestão de investimentos",
      "FINTECH" => "Fintech",

      "SAUDE_ASSISTENCIA_MEDICA" => "Saúde e assistência médica",
      "FARMACEUTICA" => "Farmacêutica",
      "BIOTECNOLOGIA" => "Biotecnologia",
      "EQUIPAMENTOS_MEDICOS" => "Equipamentos médicos",
      "HOSPITAIS_CLINICAS" => "Hospitais e clínicas",
      "SAUDE_MENTAL_BEM_ESTAR" => "Saúde mental e bem-estar",

      "VAREJO" => "Varejo",
      "ECOMMERCE" => "E-commerce",
      "BENS_CONSUMO" => "Bens de consumo",
      "COSMETICOS_BELEZA" => "Cosméticos e beleza",
      "MODA_ACESSORIOS" => "Moda e acessórios",
      "ALIMENTOS_BEBIDAS" => "Alimentos e bebidas",

      "MANUFATURA" => "Manufatura",
      "AUTOMOTIVO" => "Automotivo",
      "QUIMICOS" => "Químicos",
      "CONSTRUCAO_CIVIL" => "Construção civil",
      "MINERACAO" => "Mineração",
      "PAPEL_CELULOSE" => "Papel e celulose",
      "IMOVEIS_REAL_ESTATE" => "Imóveis e real estate",
      "DESIGN_ARQUITETURA" => "Design e arquitetura",

      "ENERGIA" => "Energia",
      "PETROLEO_GAS" => "Petróleo e gás",
      "ENERGIAS_RENOVAVEIS" => "Energias renováveis",
      "UTILIDADES_PUBLICAS" => "Utilidades públicas",

      "LOGISTICA_SUPPLY_CHAIN" => "Logística e supply chain",
      "AVIACAO" => "Aviação",
      "AEROESPACIAL" => "Aeroespacial",
      "TRANSPORTE_MARITIMO" => "Transporte marítimo",
      "TRANSPORTE_RODOVIARIO" => "Transporte rodoviário",

      "MIDIA_COMUNICACAO" => "Mídia e comunicação",
      "MIDIA_ONLINE" => "Mídia online",
      "ENTRETENIMENTO" => "Entretenimento",
      "PUBLICIDADE_MARKETING" => "Publicidade e marketing",
      "PRODUCAO_AUDIOVISUAL" => "Produção audiovisual",
      "JOGOS_ELETRONICOS" => "Jogos eletrônicos",

      "EDUCACAO" => "Educação",
      "PESQUISA_DESENVOLVIMENTO" => "Pesquisa e desenvolvimento",
      "TREINAMENTO_CAPACITACAO" => "Treinamento e capacitação",

      "CONSULTORIA_ESTRATEGICA" => "Consultoria estratégica",
      "CONSULTORIA_TI" => "Consultoria em TI",
      "RECURSOS_HUMANOS" => "Recursos humanos",
      "RECRUTAMENTO_SELECAO" => "Recrutamento e seleção",
      "SERVICOS_JURIDICOS" => "Serviços jurídicos",
      "CONTABILIDADE_AUDITORIA" => "Contabilidade e auditoria",

      "AGRONEGOCIO" => "Agronegócio",
      "AGRICULTURA" => "Agricultura",
      "PECUARIA" => "Pecuária",
      "PROCESSAMENTO_ALIMENTOS" => "Processamento de alimentos",

      "TURISMO_HOTELARIA" => "Turismo e hotelaria",
      "RESTAURANTES_ALIMENTACAO" => "Restaurantes e alimentação",
      "EVENTOS_ENTRETENIMENTO" => "Eventos e entretenimento",

      "GOVERNO_ADMINISTRACAO_PUBLICA" => "Governo e administração pública",
      "ORGANIZACOES_SEM_FINS_LUCRATIVOS" => "Organizações sem fins lucrativos",
      "THINK_TANKS" => "Think tanks",

      "OUTROS" => "Outros"
    }

    updated_count = 0
    not_found_count = 0

    name_mapping.each do |old_name, new_name|
      sector = Sector.find_by(name: old_name)

      if sector
        puts "  Updating: #{old_name} → #{new_name}"
        sector.update!(name: new_name)
        updated_count += 1
      else
        puts "  ⚠ Not found: #{old_name}"
        not_found_count += 1
      end
    end

    puts "\n" + "=" * 80
    puts "Summary:"
    puts "  ✓ Updated: #{updated_count} sectors"
    puts "  ⚠ Not found: #{not_found_count} sectors"
    puts "\nReindexing search..."

    Sector.reindex

    puts "✓ Reindex completed!"
    puts "\n" + "=" * 80
    puts "Sector names normalization completed!"
  end
end
