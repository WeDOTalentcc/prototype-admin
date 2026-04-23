# Script para importar dados do data_raw dos candidatos
# Uso: rails runner scripts/import_candidate_data_from_raw.rb [account_id] [--dry-run]
#
# ============================================================================
# COMO USAR NO RAILS CONSOLE:
# ============================================================================
#
# 1. Carregar o script:
#    load 'scripts/import_candidate_data_from_raw.rb'
#
# 2. Processar todos os candidatos de uma conta:
#    importer = CandidateDataRawImporter.new(1)  # account_id = 1
#    importer.run
#
# 3. Modo DRY RUN (não salva, só mostra o que faria):
#    importer = CandidateDataRawImporter.new(1, dry_run: true)
#    importer.run
#
# 4. Processar UM candidato específico:
#    importer = CandidateDataRawImporter.new(1)
#    importer.process_single_candidate(123)  # candidate_id = 123
#
# 5. Processar uma lista de candidatos:
#    importer = CandidateDataRawImporter.new(1)
#    importer.process_candidate_ids([123, 456, 789])
#
# 6. Ver estatísticas a qualquer momento:
#    importer.stats
#    importer.print_summary
#
# ============================================================================

class CandidateDataRawImporter
  attr_reader :account, :dry_run, :stats

  def initialize(account_id, dry_run: false)
    @account = Account.find(account_id)
    @dry_run = dry_run
    @stats = {
      processed: 0,
      updated: 0,
      errors: 0,
      skipped: 0,
      experiences_created: 0,
      educations_created: 0,
      skills_created: 0,
      languages_created: 0,
      curriculum_updated: 0
    }
  end

  # Processa um único candidato pelo ID
  def process_single_candidate(candidate_id)
    Apartment::Tenant.switch!(@account.tenant)

    candidate = Candidate.find_by(id: candidate_id)
    unless candidate
      puts "❌ Candidato ##{candidate_id} não encontrado"
      return nil
    end

    puts "📊 Modo: #{@dry_run ? 'DRY RUN' : 'PRODUÇÃO'}"
    process_candidate(candidate, 1, 1)
    print_summary
    @stats
  end

  # Processa uma lista de IDs de candidatos
  def process_candidate_ids(candidate_ids)
    Apartment::Tenant.switch!(@account.tenant)

    total = candidate_ids.size
    puts "📊 Modo: #{@dry_run ? 'DRY RUN' : 'PRODUÇÃO'}"
    puts "📋 Processando #{total} candidatos...\n\n"

    candidate_ids.each_with_index do |candidate_id, index|
      candidate = Candidate.find_by(id: candidate_id)
      unless candidate
        puts "❌ Candidato ##{candidate_id} não encontrado, pulando..."
        @stats[:skipped] += 1
        next
      end

      process_candidate(candidate, index + 1, total)
    rescue => e
      @stats[:errors] += 1
      puts "❌ Erro ao processar candidato #{candidate_id}: #{e.message}"
      puts "   #{e.backtrace.first(3).join("\n   ")}"
    end

    print_summary
    @stats
  end

  def run
    Apartment::Tenant.switch!(@account.tenant)

    puts "🔍 Buscando candidatos com data_raw do provider questt..."
    puts "📊 Modo: #{@dry_run ? 'DRY RUN (não salvará dados)' : 'PRODUÇÃO'}"
    puts ""

    candidates = Candidate.where.not(data_raw: nil)
                          .where("data_raw LIKE ?", "%provider%questt%")
                          .where(is_deleted: false)

    total = candidates.count
    puts "📋 Encontrados #{total} candidatos para processar\n\n"

    candidates.find_each.with_index do |candidate, index|
      process_candidate(candidate, index + 1, total)
    rescue => e
      @stats[:errors] += 1
      puts "❌ Erro ao processar candidato #{candidate.id}: #{e.message}"
      puts "   #{e.backtrace.first(3).join("\n   ")}"
    end

    print_summary
  end

  # Método público para processar um candidato (útil no console)
  def process_candidate(candidate, current, total)
    @stats[:processed] += 1

    data = parse_data_raw(candidate.data_raw)
    return unless data && data['provider'] == 'questt'

    puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    puts "📦 [#{current}/#{total}] Processando: #{candidate.name} (ID: #{candidate.id})"

    changes_made = false

    # 1. Criar curriculum_text se não existir
    if candidate.curriculum_text.blank? && data['experiences_a'].present?
      curriculum = build_curriculum_text(data, candidate)
      if curriculum.present?
        puts "   📝 Criando curriculum_text (#{curriculum.length} chars)"
        unless @dry_run
          candidate.update_column(:curriculum_text, curriculum)
          @stats[:curriculum_updated] += 1
        end
        changes_made = true
      end
    end

    # 2. Criar experiências
    exp_count = create_experiences(candidate, data['experiences_a'])
    if exp_count > 0
      puts "   💼 #{exp_count} experiências criadas"
      @stats[:experiences_created] += exp_count
      changes_made = true
    end

    # 3. Criar educações
    edu_count = create_educations(candidate, data['educations_a'])
    if edu_count > 0
      puts "   🎓 #{edu_count} educações criadas"
      @stats[:educations_created] += edu_count
      changes_made = true
    end

    # 4. Criar skills
    skills_count = create_skills(candidate, data['skills'])
    if skills_count > 0
      puts "   🔧 #{skills_count} skills associadas"
      @stats[:skills_created] += skills_count
      changes_made = true
    end

    # 5. Criar idiomas
    lang_count = create_languages(candidate, data['languages'])
    if lang_count > 0
      puts "   🌐 #{lang_count} idiomas criados"
      @stats[:languages_created] += lang_count
      changes_made = true
    end

    if changes_made
      @stats[:updated] += 1
      puts "   ✅ Candidato atualizado com sucesso"
    else
      puts "   ⏭️  Nenhuma mudança necessária"
    end
  end

  # Método para visualizar o data_raw de um candidato (debug)
  def inspect_candidate(candidate_id)
    Apartment::Tenant.switch!(@account.tenant)
    candidate = Candidate.find(candidate_id)
    data = parse_data_raw(candidate.data_raw)

    puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    puts "📦 Candidato: #{candidate.name} (ID: #{candidate.id})"
    puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if data.nil?
      puts "❌ data_raw inválido ou nulo"
      return nil
    end

    puts "\n📋 Provider: #{data['provider']}"
    puts "\n💼 Experiências (#{data['experiences_a']&.size || 0}):"
    data['experiences_a']&.each_with_index do |exp, i|
      puts "   #{i+1}. #{exp['occupation_name']} @ #{exp['company_name']}"
    end

    puts "\n🎓 Educações (#{data['educations_a']&.size || 0}):"
    data['educations_a']&.each_with_index do |edu, i|
      puts "   #{i+1}. #{edu['study_area_name']} - #{edu['institution_name']}"
    end

    puts "\n🔧 Skills (#{data['skills']&.size || 0}):"
    puts "   #{data['skills']&.map { |s| s['skill_name'] }&.compact&.join(', ')}"

    puts "\n🌐 Idiomas (#{data['languages']&.size || 0}):"
    data['languages']&.each do |lang|
      puts "   - #{lang.dig('language', 'name')}: #{lang.dig('level', 'name')}"
    end

    data
  end

  private

  def parse_data_raw(data_raw)
    return nil if data_raw.blank?
    JSON.parse(data_raw)
  rescue JSON::ParserError => e
    puts "   ⚠️  Erro ao parsear data_raw: #{e.message}"
    nil
  end

  def build_curriculum_text(data, candidate)
    parts = []

    # Nome e título
    parts << "#{data['name'] || candidate.name}"
    parts << data['role_name'] if data['role_name'].present?

    # Informações básicas
    location = [ data['city_name'], data['state_uf'], data['country'] ].compact.join(", ")
    parts << "Localização: #{location}" if location.present?

    parts << "Email: #{data['email']}" if data['email'].present?
    parts << "Telefone: #{data['mobile_phone']}" if data['mobile_phone'].present?
    parts << "LinkedIn: #{data['linkedin']}" if data['linkedin'].present?
    parts << "Empresa Atual: #{data['current_company']}" if data['current_company'].present?

    # Experiências
    if data['experiences_a'].present?
      parts << "\n═══════════════════════════════════════"
      parts << "EXPERIÊNCIAS PROFISSIONAIS"
      parts << "═══════════════════════════════════════\n"

      data['experiences_a'].each do |exp|
        parts << "\n#{exp['occupation_name']&.upcase}"
        parts << "#{exp['company_name']&.titleize}" if exp['company_name'].present?

        start_date = parse_date_simple(exp['start_date'])
        end_date = exp['end_date'] ? parse_date_simple(exp['end_date']) : 'Atual'
        parts << "Período: #{start_date} - #{end_date}"
        parts << ""
      end
    end

    # Educação
    if data['educations_a'].present?
      parts << "\n═══════════════════════════════════════"
      parts << "FORMAÇÃO ACADÊMICA"
      parts << "═══════════════════════════════════════\n"

      data['educations_a'].each do |edu|
        parts << "\n#{edu['study_area_name']&.titleize}" if edu['study_area_name'].present?
        parts << "#{edu['institution_name']&.titleize}"

        if edu['start_date'] || edu['end_date']
          start_date = parse_date_simple(edu['start_date'])
          end_date = parse_date_simple(edu['end_date'])
          parts << "Período: #{[ start_date, end_date ].compact.join(' - ')}"
        end
        parts << ""
      end
    end

    # Skills
    if data['skills'].present? && data['skills'].any?
      parts << "\n═══════════════════════════════════════"
      parts << "HABILIDADES"
      parts << "═══════════════════════════════════════"
      skill_names = data['skills'].map { |s| s['skill_name'] }.compact.join(", ")
      parts << skill_names if skill_names.present?
    end

    # Idiomas
    if data['languages'].present? && data['languages'].any?
      parts << "\n═══════════════════════════════════════"
      parts << "IDIOMAS"
      parts << "═══════════════════════════════════════"
      data['languages'].each do |lang|
        level = lang.dig('level', 'name') || ''
        name = lang.dig('language', 'name') || ''
        parts << "#{name}: #{level}" if name.present?
      end
    end

    parts.compact.join("\n")
  end

  def create_experiences(candidate, experiences_data)
    return 0 if experiences_data.blank? || @dry_run

    count = 0
    experiences_data.each do |exp_data|
      company_name = exp_data['company_name']&.strip
      occupation_name = exp_data['occupation_name']&.strip
      start_date = parse_date(exp_data['start_date'])

      # Busca existente pelo company_id e occupation_id (mais confiável)
      company = Company.find_by("LOWER(name) = ? AND account_id = ? AND is_deleted = ?",
                                 company_name&.downcase, @account.id, false)
      occupation = Occupation.find_by("LOWER(name) = ? AND account_id = ?",
                                       occupation_name&.downcase, @account.id)

      existing = Experience.where(candidate_id: candidate.id, is_deleted: false)
                           .where(start_date: start_date)

      if company && occupation
        existing = existing.where(company_id: company.id, occupation_id: occupation.id)
      end

      next if existing.exists?

      Experience.create!(
        candidate: candidate,
        account: @account,
        company_name: company_name,
        occupation_name: occupation_name,
        start_date: start_date,
        end_date: parse_date(exp_data['end_date']),
        work_here: exp_data['end_date'].nil?,
        description: exp_data['description']&.strip
      )
      count += 1
    rescue => e
      puts "      ⚠️  Erro ao criar experiência '#{company_name}': #{e.message}"
    end

    count
  end

  def create_educations(candidate, educations_data)
    return 0 if educations_data.blank? || @dry_run

    count = 0
    educations_data.each do |edu_data|
      institution_name = edu_data['institution_name']&.strip
      study_area_name = edu_data['study_area_name']&.strip

      # Busca existente por institution_id e study_area_id
      institution = Institution.find_by("LOWER(name) = ?", institution_name&.downcase)
      study_area = StudyArea.find_by("LOWER(name) = ?", study_area_name&.downcase)

      existing = Education.where(candidate_id: candidate.id)

      if institution && study_area
        existing = existing.where(institution_id: institution.id, study_area_id: study_area.id)
        next if existing.exists?
      elsif institution_name.present? && study_area_name.present?
        # Se não encontrou por ID, verifica se já existe pelo nome (para evitar duplicatas)
        similar = Education.joins(:institution, :study_area)
                           .where(candidate_id: candidate.id)
                           .where("LOWER(institutions.name) = ?", institution_name&.downcase)
                           .where("LOWER(study_areas.name) = ?", study_area_name&.downcase)
        next if similar.exists?
      end

      Education.create!(
        candidate: candidate,
        account: @account,
        institution_name: institution_name,
        study_area_name: study_area_name,
        formation_type: map_formation_type(edu_data['formation_type']),
        start_date: parse_date(edu_data['start_date']),
        end_date: parse_date(edu_data['end_date']),
        study_here: edu_data['end_date'].nil?
      )
      count += 1
    rescue => e
      puts "      ⚠️  Erro ao criar educação '#{institution_name}': #{e.message}"
    end

    count
  end

  def map_formation_type(formation_string)
    return 8 if formation_string.blank? # Outros (default)

    formation_map = {
      'ensino médio' => 0,
      'curso técnico' => 1,
      'curso online' => 2,
      'graduação' => 3,
      'pós-graduação' => 4,
      'mestrado' => 5,
      'doutorado' => 6,
      'phd' => 7,
      'outros' => 8
    }

    formation_map[formation_string.downcase.strip] || 8
  end

  def create_skills(candidate, skills_data)
    return 0 if skills_data.blank? || @dry_run

    count = 0
    skills_data.each do |skill_data|
      skill_name = skill_data['skill_name']&.strip
      next if skill_name.blank?

      skill = Skill.find_or_create_by!(name: skill_name, account: @account)

      unless SkillRelationship.exists?(
        reference_type: 'Candidate',
        reference_id: candidate.id,
        skill_id: skill.id
      )
        SkillRelationship.create!(
          reference: candidate,
          skill: skill,
          is_main: skill_data['main'] || false
        )
        count += 1
      end
    rescue => e
      puts "      ⚠️  Erro ao criar skill #{skill_name}: #{e.message}"
    end

    count
  end

  def create_languages(candidate, languages_data)
    return 0 if languages_data.blank? || @dry_run

    count = 0
    languages_data.each do |lang_data|
      language_name = lang_data.dig('language', 'name')&.strip
      next if language_name.blank?

      # Language é global (não tem account_id), precisa de acronym e name_ptbr
      acronym = lang_data.dig('language', 'acronym')&.strip || generate_acronym(language_name)
      name_ptbr = lang_data.dig('language', 'name_ptbr')&.strip || language_name

      language = Language.find_by("LOWER(name) = ?", language_name.downcase)

      unless language
        language = Language.create!(
          name: language_name,
          acronym: acronym,
          name_ptbr: name_ptbr
        )
      end

      level_name = lang_data.dig('level', 'name')
      level_id = map_language_level(level_name)

      unless LanguageRelationship.exists?(
        reference_type: 'Candidate',
        reference_id: candidate.id,
        language_id: language.id
      )
        LanguageRelationship.create!(
          reference: candidate,
          language: language,
          level_id: level_id
        )
        count += 1
      end
    rescue => e
      puts "      ⚠️  Erro ao criar idioma '#{language_name}': #{e.message}"
    end

    count
  end

  def generate_acronym(language_name)
    # Mapa de idiomas comuns para acrônimos
    acronyms = {
      'português' => 'PT', 'portuguese' => 'PT',
      'inglês' => 'EN', 'english' => 'EN',
      'espanhol' => 'ES', 'spanish' => 'ES',
      'francês' => 'FR', 'french' => 'FR',
      'alemão' => 'DE', 'german' => 'DE',
      'italiano' => 'IT', 'italian' => 'IT',
      'japonês' => 'JA', 'japanese' => 'JA',
      'chinês' => 'ZH', 'chinese' => 'ZH',
      'coreano' => 'KO', 'korean' => 'KO',
      'russo' => 'RU', 'russian' => 'RU',
      'árabe' => 'AR', 'arabic' => 'AR',
      'holandês' => 'NL', 'dutch' => 'NL',
      'mandarim' => 'ZH', 'mandarin' => 'ZH'
    }

    acronyms[language_name.downcase] || language_name[0..1].upcase
  end

  def parse_date(date_string)
    return nil if date_string.blank?
    Date.parse(date_string)
  rescue ArgumentError, TypeError
    nil
  end

  def parse_date_simple(date_string)
    date = parse_date(date_string)
    return nil unless date
    date.strftime("%m/%Y")
  rescue
    nil
  end

  def map_language_level(level_name)
    return nil if level_name.blank?

    case level_name.downcase
    when /básico|basic|elementary/
      1
    when /intermediário|intermediate/
      2
    when /avançado|advanced|fluente|fluent/
      3
    when /nativo|native/
      4
    else
      2 # Default intermediário
    end
  end

  def print_summary
    puts "\n\n"
    puts "═══════════════════════════════════════════════════════════"
    puts "📊 RESUMO DA IMPORTAÇÃO"
    puts "═══════════════════════════════════════════════════════════"
    puts "Modo: #{@dry_run ? '🔍 DRY RUN' : '✅ PRODUÇÃO'}"
    puts "Conta: #{@account.name}"
    puts ""
    puts "Candidatos processados:    #{@stats[:processed]}"
    puts "Candidatos atualizados:    #{@stats[:updated]}"
    puts "Candidatos pulados:        #{@stats[:skipped]}"
    puts "Erros:                     #{@stats[:errors]}"
    puts ""
    puts "Currículos criados:        #{@stats[:curriculum_updated]}"
    puts "Experiências criadas:      #{@stats[:experiences_created]}"
    puts "Educações criadas:         #{@stats[:educations_created]}"
    puts "Skills associadas:         #{@stats[:skills_created]}"
    puts "Idiomas criados:           #{@stats[:languages_created]}"
    puts "═══════════════════════════════════════════════════════════"
  end
end

# Execução do script
if __FILE__ == $PROGRAM_NAME || caller.any? { |c| c.include?('rails/commands/runner') }
  account_id = ARGV[0]
  dry_run = ARGV.include?('--dry-run')

  unless account_id
    puts "❌ Uso: rails runner scripts/import_candidate_data_from_raw.rb <account_id> [--dry-run]"
    puts ""
    puts "Exemplos:"
    puts "  rails runner scripts/import_candidate_data_from_raw.rb 1 --dry-run"
    puts "  rails runner scripts/import_candidate_data_from_raw.rb 1"
    exit 1
  end

  begin
    importer = CandidateDataRawImporter.new(account_id, dry_run: dry_run)
    importer.run
  rescue ActiveRecord::RecordNotFound
    puts "❌ Account com ID #{account_id} não encontrado!"
    exit 1
  rescue => e
    puts "❌ Erro fatal: #{e.message}"
    puts e.backtrace.first(10).join("\n")
    exit 1
  end
end
