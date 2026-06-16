# lib/tasks/seed_public.rake

namespace :db do
  desc "Seed countries directly in public schema"
  task seed_countries: :environment do
    Apartment::Tenant.switch!("public")
    country_names = %w[
      Afeganistão África\ do\ Sul Albânia Alemanha Andorra Angola Antígua\ e\ Barbuda Arábia\ Saudita
      Argélia Argentina Armênia Austrália Áustria Azerbaijão Bahamas Bahrein Bangladesh Barbados
      Bélgica Belize Benin Bielorrússia Bolívia Bósnia\ e\ Herzegovina Botsuana Brasil Brunei
      Bulgária Burkina\ Faso Burundi Butão Cabo\ Verde Camarões Camboja Canadá Catar Cazaquistão
      Chade Chile China Chipre Colômbia Comores Congo Coreia\ do\ Norte Coreia\ do\ Sul Costa\ do\ Marfim
      Costa\ Rica Croácia Cuba Dinamarca Djibuti Dominica Egito El\ Salvador Emirados\ Árabes\ Unidos
      Equador Eritreia Eslováquia Eslovênia Espanha Estados\ Unidos Estônia Etiópia Fiji Filipinas
      Finlândia França Gabão Gâmbia Gana Geórgia Grécia Granada Guatemala Guiana Guiné Guiné-Bissau
      Guiné\ Equatorial Haiti Holanda Honduras Hungria Iêmen Ilhas\ Marshall Ilhas\ Salomão Índia
      Indonésia Irã Iraque Irlanda Islândia Israel Itália Jamaica Japão Jordânia Kiribati Kuwait
      Laos Lesoto Letônia Líbano Libéria Líbia Liechtenstein Lituânia Luxemburgo Macedônia Madagascar
      Malásia Malaui Maldivas Mali Malta Marrocos Maurício Mauritânia México Micronésia Moçambique
      Mônaco Mongólia Montenegro Mianmar Namíbia Nauru Nepal Nicarágua Níger Nigéria Noruega Nova\ Zelândia
      Omã Uganda Uzbequistão Paquistão Palau Panamá Papua-Nova\ Guiné Paraguai Peru Polônia Portugal Quênia
      Quirguistão Reino\ Unido República\ Centro-Africana República\ Dominicana República\ Tcheca Romênia
      Ruanda Rússia Samoa San\ Marino Santa\ Lúcia São\ Cristóvão\ e\ Névis São\ Tomé\ e\ Príncipe São\ Vicente\ e\ Granadinas
      Senegal Serra\ Leoa Seychelles Singapura Síria Somália Sri\ Lanka Suazilândia Sudão Sudão\ do\ Sul Suécia
      Suíça Suriname Tailândia Taiwan Tanzânia Timor-Leste Togo Tonga Trinidad\ e\ Tobago Tunísia Turcomenistão
      Turquia Tuvalu Ucrânia Uganda Uruguai Uzbequistão Vanuatu Vaticano Venezuela Vietnã Zâmbia Zimbábue
    ]

    country_names.each do |name|
      Country.find_or_create_by(name: name.gsub("\\", ""))
    end

    puts "✅ Países seedados no schema public."
  end
end
