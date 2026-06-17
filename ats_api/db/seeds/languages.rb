# Seed principal para popular linguagens
# Execute com: rails runner db/seeds/languages.rb ou incluir no seeds.rb

languages = [
  { name: 'English', acronym: 'EN', name_ptbr: 'Inglês' },
  { name: 'Portuguese', acronym: 'PT', name_ptbr: 'Português' },
  { name: 'Spanish', acronym: 'ES', name_ptbr: 'Espanhol' },
  { name: 'French', acronym: 'FR', name_ptbr: 'Francês' },
  { name: 'German', acronym: 'DE', name_ptbr: 'Alemão' },
  { name: 'Italian', acronym: 'IT', name_ptbr: 'Italiano' },
  { name: 'Chinese', acronym: 'ZH', name_ptbr: 'Chinês' },
  { name: 'Japanese', acronym: 'JA', name_ptbr: 'Japonês' },
  { name: 'Korean', acronym: 'KO', name_ptbr: 'Coreano' },
  { name: 'Russian', acronym: 'RU', name_ptbr: 'Russo' },
  { name: 'Arabic', acronym: 'AR', name_ptbr: 'Árabe' },
  { name: 'Hindi', acronym: 'HI', name_ptbr: 'Hindi' }
]

languages.each do |attrs|
  Language.find_or_create_by!(acronym: attrs[:acronym]) do |lang|
    lang.name = attrs[:name]
    lang.name_ptbr = attrs[:name_ptbr]
  end
end

puts "Seed de languages concluído. Total: #{Language.count}" if defined?(Rails::Console)
