# frozen_string_literal: true

# =============================================================================
# Seed script for new endpoints (Notifications, Productivity, Stats)
#
# Usage:
#   docker compose exec web bin/rails runner scripts/seed_new_endpoints.rb
#   -- or in development without Docker: --
#   bin/rails runner scripts/seed_new_endpoints.rb
#
# Idempotent: safe to run multiple times.
# =============================================================================

TODAY = Date.current

module SeedHelpers
  module_function

  def log(emoji, message)
    Rails.logger.info message
    puts "#{emoji} #{message}"
  end

  def find_or_create(klass, find_attrs, create_attrs = {})
    klass.find_or_create_by!(find_attrs) do |record|
      create_attrs.each { |k, v| record.public_send(:"#{k}=", v) }
    end
  end
end

include SeedHelpers

# =============================================================================
# 1. Resolve Account & User (public schema)
# =============================================================================
log "🔍", "Looking up account and user..."

user = User.find_by!(email: "anderson.victhor@wedotalent.cc")
account = user.account

Current.user = user
Current.account = account

log "✅", "Account: #{account.name} (tenant=#{account.tenant}), User: #{user.name} (#{user.email})"

# =============================================================================
# 2. Switch to tenant
# =============================================================================
Apartment::Tenant.switch!(account.tenant)
log "✅", "Switched to tenant: #{account.tenant}"

Searchkick.disable_callbacks

begin

# =============================================================================
# 3. Job Statuses
# =============================================================================
log "🔄", "Seeding job statuses..."
JobStatus.create_default_statuses
active_status   = JobStatus.find_by!(name: "Ativa")
closed_status   = JobStatus.find_by!(name: "Fechada (preenchida)")
paused_status   = JobStatus.find_by!(name: "Paralisada")
draft_status    = JobStatus.find_by!(name: "Rascunho")
log "✅", "Job statuses ready (#{JobStatus.count} total)"

# =============================================================================
# 4. Department
# =============================================================================
log "🔄", "Seeding departments..."

departments = [
  { name: "Engineering", color: "#3B82F6" },
  { name: "Product", color: "#8B5CF6" },
  { name: "People & Culture", color: "#EC4899" },
  { name: "Sales", color: "#F59E0B" },
  { name: "Marketing", color: "#10B981" }
].map do |attrs|
  find_or_create(Department, { name: attrs[:name], account: account }, { color: attrs[:color] })
end

log "✅", "Departments ready (#{departments.size})"

# =============================================================================
# 5. Jobs (8 jobs — varied statuses, dates, seniorities)
# =============================================================================
log "🔄", "Seeding jobs..."

job_definitions = [
  {
    title: "Desenvolvedor(a) Backend Ruby on Rails",
    description: "Buscamos dev Ruby on Rails sênior para atuar no produto principal da empresa. Stack: Rails 7, PostgreSQL, Elasticsearch, Sidekiq.",
    seniority: 2, employment_type: 0, workplace_type: 1, department: departments[0],
    status: active_status, is_active: true, published_date: TODAY - 15.days,
    closing_deadline: TODAY + 30.days, priority: 1, urgency_level: 4, city: "São Paulo", state: "SP"
  },
  {
    title: "Desenvolvedor(a) Frontend Vue.js",
    description: "Vaga para frontend com experiência em Vue 3, Nuxt, TypeScript e design systems.",
    seniority: 1, employment_type: 0, workplace_type: 2, department: departments[0],
    status: active_status, is_active: true, published_date: TODAY - 10.days,
    closing_deadline: TODAY + 45.days, priority: 2, urgency_level: 3, city: "Curitiba", state: "PR"
  },
  {
    title: "Product Manager",
    description: "PM para liderar o roadmap de produto ATS, trabalhando com squads de engenharia e design.",
    seniority: 2, employment_type: 0, workplace_type: 2, department: departments[1],
    status: active_status, is_active: true, published_date: TODAY - 20.days,
    closing_deadline: TODAY + 15.days, priority: 1, urgency_level: 5, city: "São Paulo", state: "SP"
  },
  {
    title: "Tech Lead Full Stack",
    description: "Tech Lead para coordenar time de 6 pessoas. Ruby on Rails + Vue.js, foco em arquitetura e code review.",
    seniority: 5, employment_type: 0, workplace_type: 1, department: departments[0],
    status: active_status, is_active: true, published_date: TODAY - 5.days,
    closing_deadline: TODAY + 60.days, priority: 1, urgency_level: 3, city: "Remote", state: "SP"
  },
  {
    title: "Analista de RH - Business Partner",
    description: "HRBP para suportar áreas de tecnologia e produto. Experiência com ciclos de performance e desenvolvimento.",
    seniority: 2, employment_type: 0, workplace_type: 3, department: departments[2],
    status: paused_status, is_active: false, published_date: TODAY - 30.days,
    closing_deadline: TODAY + 5.days, priority: 3, urgency_level: 2, city: "São Paulo", state: "SP"
  },
  {
    title: "SDR - Sales Development Representative",
    description: "SDR para prospecção outbound de empresas de tecnologia. Experiência com ferramentas de prospecção e CRM.",
    seniority: 0, employment_type: 0, workplace_type: 2, department: departments[3],
    status: active_status, is_active: true, published_date: TODAY - 8.days,
    closing_deadline: TODAY + 40.days, priority: 2, urgency_level: 3, city: "São Paulo", state: "SP"
  },
  {
    title: "Designer UX/UI",
    description: "Designer para criar experiências incríveis no produto ATS. Figma, design system, pesquisa com usuários.",
    seniority: 1, employment_type: 1, workplace_type: 1, department: departments[1],
    status: closed_status, is_active: false, published_date: TODAY - 60.days,
    closing_deadline: TODAY - 10.days, priority: 2, urgency_level: 2, city: "Florianópolis", state: "SC"
  },
  {
    title: "Estagiário(a) de Marketing Digital",
    description: "Estágio em marketing digital com foco em conteúdo, SEO e redes sociais para o mercado HR Tech.",
    seniority: 4, employment_type: 2, workplace_type: 2, department: departments[4],
    status: draft_status, is_active: false, published_date: nil,
    closing_deadline: nil, priority: 3, urgency_level: 1, city: "Curitiba", state: "PR"
  }
]

jobs = job_definitions.map do |defn|
  dept = defn.delete(:department)
  status = defn.delete(:status)

  job = Job.find_or_initialize_by(title: defn[:title], account: account)
  if job.new_record?
    job.assign_attributes(
      defn.merge(
        user: user,
        account: account,
        department: dept,
        job_status: status,
        is_deleted: false,
        is_archived: false,
        is_urgent: defn[:urgency_level].to_i >= 4
      )
    )
    job.save!
  end
  job
end

log "✅", "Jobs ready (#{jobs.size})"

# =============================================================================
# 6. Selective Processes (for each active job)
# =============================================================================
log "🔄", "Seeding selective processes..."

sp_templates = [
  { name: "Inscrição", status: :web_submission, color: "#a8ced5", position: 0 },
  { name: "Triagem", status: :screening, color: "#d5bfa8", position: 1 },
  { name: "Entrevista", status: :interview, color: "#a8d5b7", position: 2 },
  { name: "Contratado", status: :hired, color: "#bfa8d5", position: 3 },
  { name: "Reprovado", status: :rejected, color: "#FCA5A5", position: 4 }
]

selective_processes = {}
jobs.each do |job|
  next if job.selective_processes.where(is_deleted: false).exists?

  selective_processes[job.id] = sp_templates.map do |sp_def|
    SelectiveProcess.create!(
      name: sp_def[:name],
      status: sp_def[:status],
      color: sp_def[:color],
      position: sp_def[:position],
      job: job,
      account: account,
      is_deleted: false
    )
  end
end

jobs.each do |job|
  selective_processes[job.id] ||= job.selective_processes.where(is_deleted: false).order(:position).to_a
end

log "✅", "Selective processes ready"

# =============================================================================
# 7. Candidates (20 candidates — varied profiles)
# =============================================================================
log "🔄", "Seeding candidates..."

candidate_definitions = [
  { name: "João Silva", email: "joao.silva@email.com", role_name: "Backend Developer", source: "LinkedIn", city: "São Paulo", state: "SP", gender: 1 },
  { name: "Maria Santos", email: "maria.santos@email.com", role_name: "Frontend Developer", source: "Indicação", city: "Curitiba", state: "PR", gender: 2 },
  { name: "Lucas Oliveira", email: "lucas.oliveira@email.com", role_name: "Full Stack Developer", source: "LinkedIn", city: "Florianópolis", state: "SC", gender: 1 },
  { name: "Ana Paula Costa", email: "ana.costa@email.com", role_name: "Product Manager", source: "Sourcing", city: "São Paulo", state: "SP", gender: 2 },
  { name: "Carlos Mendes", email: "carlos.mendes@email.com", role_name: "Tech Lead", source: "LinkedIn", city: "Belo Horizonte", state: "MG", gender: 1 },
  { name: "Fernanda Lima", email: "fernanda.lima@email.com", role_name: "UX Designer", source: "Site", city: "Florianópolis", state: "SC", gender: 2 },
  { name: "Pedro Henrique", email: "pedro.henrique@email.com", role_name: "Backend Developer", source: "LinkedIn", city: "Porto Alegre", state: "RS", gender: 1 },
  { name: "Juliana Martins", email: "juliana.martins@email.com", role_name: "Frontend Developer", source: "Indicação", city: "São Paulo", state: "SP", gender: 2 },
  { name: "Rafael Almeida", email: "rafael.almeida@email.com", role_name: "DevOps Engineer", source: "LinkedIn", city: "Campinas", state: "SP", gender: 1 },
  { name: "Isabela Ferreira", email: "isabela.ferreira@email.com", role_name: "Data Analyst", source: "Site", city: "Curitiba", state: "PR", gender: 2 },
  { name: "Thiago Barbosa", email: "thiago.barbosa@email.com", role_name: "Backend Developer", source: "Sourcing", city: "São Paulo", state: "SP", gender: 1 },
  { name: "Camila Rocha", email: "camila.rocha@email.com", role_name: "Product Manager", source: "LinkedIn", city: "Rio de Janeiro", state: "RJ", gender: 2 },
  { name: "Bruno Souza", email: "bruno.souza@email.com", role_name: "Full Stack Developer", source: "LinkedIn", city: "São Paulo", state: "SP", gender: 1 },
  { name: "Letícia Cardoso", email: "leticia.cardoso@email.com", role_name: "HR Business Partner", source: "LinkedIn", city: "São Paulo", state: "SP", gender: 2 },
  { name: "Gustavo Ribeiro", email: "gustavo.ribeiro@email.com", role_name: "SDR", source: "Site", city: "São Paulo", state: "SP", gender: 1 },
  { name: "Mariana Pires", email: "mariana.pires@email.com", role_name: "Marketing Analyst", source: "Indicação", city: "Curitiba", state: "PR", gender: 2 },
  { name: "Diego Nascimento", email: "diego.nascimento@email.com", role_name: "Backend Developer", source: "LinkedIn", city: "Recife", state: "PE", gender: 1 },
  { name: "Patrícia Gomes", email: "patricia.gomes@email.com", role_name: "Frontend Developer", source: "Sourcing", city: "São Paulo", state: "SP", gender: 2 },
  { name: "André Vieira", email: "andre.vieira@email.com", role_name: "Tech Lead", source: "LinkedIn", city: "Curitiba", state: "PR", gender: 1 },
  { name: "Carolina Teixeira", email: "carolina.teixeira@email.com", role_name: "UX Designer", source: "Site", city: "Porto Alegre", state: "RS", gender: 2 }
]

candidates = candidate_definitions.map do |defn|
  Candidate.find_or_create_by!(email: defn[:email], account: account) do |c|
    c.assign_attributes(defn.except(:email).merge(account: account, is_deleted: false))
  end
end

log "✅", "Candidates ready (#{candidates.size})"

# =============================================================================
# 8. Applies (distribute candidates across jobs with varied stages)
# =============================================================================
log "🔄", "Seeding applies..."

apply_map = [
  # job_index, candidate_index, sp_status, cv_match, total_score, days_ago
  [ 0, 0,  :screening,      0.85, 4.2, 14 ],
  [ 0, 6,  :interview,       0.78, 3.8, 12 ],
  [ 0, 10, :web_submission,  0.92, nil, 2 ],
  [ 0, 16, :screening,      0.65, 2.1, 10 ],
  [ 0, 12, :hired,          0.88, 4.5, 30 ],
  [ 0, 2,  :rejected,       0.45, 1.5, 20 ],
  [ 1, 1,  :interview,       0.82, 3.9, 9 ],
  [ 1, 7,  :screening,      0.75, 3.2, 8 ],
  [ 1, 17, :web_submission,  0.70, nil, 3 ],
  [ 1, 5,  :rejected,       0.55, 2.0, 15 ],
  [ 2, 3,  :interview,       0.90, 4.1, 18 ],
  [ 2, 11, :screening,      0.80, 3.5, 16 ],
  [ 2, 4,  :web_submission,  0.88, nil, 5 ],
  [ 3, 4,  :screening,      0.95, 4.8, 4 ],
  [ 3, 18, :web_submission,  0.82, nil, 3 ],
  [ 3, 2,  :interview,       0.87, 4.0, 4 ],
  [ 4, 13, :screening,      0.72, 3.0, 25 ],
  [ 4, 14, :web_submission,  0.60, nil, 28 ],
  [ 5, 14, :screening,      0.78, 3.4, 7 ],
  [ 5, 15, :interview,       0.68, 2.8, 6 ],
  [ 6, 5,  :hired,          0.91, 4.6, 55 ],
  [ 6, 19, :rejected,       0.50, 1.8, 50 ]
]

applies = apply_map.map do |job_idx, cand_idx, sp_status, cv_match, total_score, days_ago|
  job = jobs[job_idx]
  candidate = candidates[cand_idx]
  sps = selective_processes[job.id]
  sp = sps&.find { |s| s.status == sp_status.to_s } || sps&.first

  next unless sp

  existing = Apply.find_by(job: job, candidate: candidate, account: account, is_deleted: false)
  next existing if existing

  apply = Apply.new(
    job: job,
    candidate: candidate,
    selective_process: sp,
    account: account,
    cv_match: cv_match,
    total_score: total_score,
    is_deleted: false,
    created_at: (TODAY - days_ago.days).to_time + rand(1..8).hours,
    updated_at: (TODAY - [ days_ago - rand(0..3), 0 ].max.days).to_time
  )
  apply.save!(validate: false)
  apply
end.compact

log "✅", "Applies ready (#{applies.size})"

# =============================================================================
# 9. Evaluations & EvaluationCandidates
# =============================================================================
log "🔄", "Seeding evaluations..."

eval_definitions = [
  { name: "Avaliação Técnica Backend", job_idx: 0, sp_status: :screening, is_screening: true },
  { name: "Avaliação Cultural", job_idx: 0, sp_status: :interview, is_screening: false },
  { name: "Avaliação Técnica Frontend", job_idx: 1, sp_status: :screening, is_screening: true },
  { name: "Case de Produto", job_idx: 2, sp_status: :interview, is_screening: false },
  { name: "Assessment Técnico Lead", job_idx: 3, sp_status: :screening, is_screening: true }
]

evaluations = eval_definitions.map do |defn|
  job = jobs[defn[:job_idx]]
  sps = selective_processes[job.id]
  sp = sps&.find { |s| s.status == defn[:sp_status].to_s }

  Evaluation.find_or_create_by!(name: defn[:name], job: job, account: account) do |e|
    e.user = user
    e.selective_process = sp
    e.status = true
    e.is_chatbot = true
    e.ai_enabled = true
    e.is_screening = defn[:is_screening]
    e.notification_enabled = false
  end
end

log "✅", "Evaluations ready (#{evaluations.size})"

log "🔄", "Seeding evaluation candidates..."

ec_data = [
  # eval_idx, candidate_idx, completed, score, wsi_classification, days_ago
  [ 0, 0,  true,  4.2, "strong_fit",   10 ],
  [ 0, 6,  true,  3.8, "moderate_fit", 9 ],
  [ 0, 10, false, nil,  nil,            1 ],
  [ 0, 16, true,  2.1, "weak_fit",     8 ],
  [ 0, 12, true,  4.5, "strong_fit",   25 ],
  [ 1, 0,  true,  4.0, "strong_fit",   7 ],
  [ 1, 6,  true,  3.5, "moderate_fit", 6 ],
  [ 2, 1,  true,  3.9, "moderate_fit", 7 ],
  [ 2, 7,  true,  3.2, "moderate_fit", 6 ],
  [ 2, 17, false, nil,  nil,            2 ],
  [ 3, 3,  true,  4.1, "strong_fit",   14 ],
  [ 3, 11, true,  3.5, "moderate_fit", 12 ],
  [ 4, 4,  false, nil,  nil,            3 ],
  [ 4, 18, false, nil,  nil,            2 ]
]

evaluation_candidates = ec_data.map do |eval_idx, cand_idx, completed, score, classification, days_ago|
  evaluation = evaluations[eval_idx]
  candidate = candidates[cand_idx]
  job = evaluation.job

  apply = Apply.find_by(job: job, candidate: candidate, account: account, is_deleted: false)

  existing = EvaluationCandidate.find_by(evaluation: evaluation, candidate: candidate, account: account)
  next existing if existing

  ec = EvaluationCandidate.new(
    evaluation: evaluation,
    candidate: candidate,
    job: job,
    apply: apply,
    user: user,
    account: account,
    completed: completed,
    score: score,
    wsi_classification: classification,
    is_screening: evaluation.is_screening,
    is_deleted: false,
    created_at: (TODAY - days_ago.days).to_time + rand(1..6).hours,
    updated_at: completed ? (TODAY - [ days_ago - rand(1..3), 0 ].max.days).to_time : nil
  )
  ec.save!(validate: false)
  ec
end.compact

log "✅", "Evaluation candidates ready (#{evaluation_candidates.size})"

# =============================================================================
# 10. Meetings (varied statuses)
# =============================================================================
log "🔄", "Seeding meetings..."

meeting_data = [
  { subject: "Entrevista técnica - João Silva (Backend Rails)", candidate_idx: 0, job_idx: 0, sub_status: "completed", days_offset: -5 },
  { subject: "Entrevista técnica - Pedro Henrique (Backend Rails)", candidate_idx: 6, job_idx: 0, sub_status: "completed", days_offset: -3 },
  { subject: "Entrevista cultural - João Silva", candidate_idx: 0, job_idx: 0, sub_status: "scheduled", days_offset: 2 },
  { subject: "Entrevista frontend - Maria Santos (Vue.js)", candidate_idx: 1, job_idx: 1, sub_status: "confirmed", days_offset: 3 },
  { subject: "Case de produto - Ana Paula Costa (PM)", candidate_idx: 3, job_idx: 2, sub_status: "completed", days_offset: -7 },
  { subject: "Entrevista final - Ana Paula Costa", candidate_idx: 3, job_idx: 2, sub_status: "no_show", days_offset: -2 },
  { subject: "Entrevista técnica - Carlos Mendes (Tech Lead)", candidate_idx: 4, job_idx: 3, sub_status: "scheduled", days_offset: 1 },
  { subject: "Entrevista SDR - Gustavo Ribeiro", candidate_idx: 14, job_idx: 5, sub_status: "completed", days_offset: -4 },
  { subject: "Entrevista técnica remota - André Vieira", candidate_idx: 18, job_idx: 3, sub_status: "scheduled", days_offset: 5 },
  { subject: "Entrevista design - Carolina Teixeira", candidate_idx: 19, job_idx: 6, sub_status: "completed", days_offset: -40 }
]

meetings = meeting_data.map do |defn|
  start_time = (TODAY + defn[:days_offset].days).to_time.change(hour: 10 + rand(0..6))
  end_time = start_time + 1.hour

  Meeting.find_or_create_by!(subject: defn[:subject], account: account) do |m|
    m.organizer = user
    m.provider = "microsoft_teams"
    m.start_time = start_time
    m.end_time = end_time
    m.sub_status = defn[:sub_status]
    m.job = jobs[defn[:job_idx]]
    m.is_deleted = false
  end
end

log "✅", "Meetings ready (#{meetings.size})"

# =============================================================================
# 11. Sourcings & Sourced Profiles
# =============================================================================
log "🔄", "Seeding sourcings..."

sourcing_definitions = [
  { query: "Ruby on Rails developer senior São Paulo", provider: "local", status: "done", results_count: 45, credits_used: 30, days_ago: 20 },
  { query: "Vue.js frontend developer", provider: "pearch", status: "done", results_count: 60, credits_used: 40, days_ago: 12 },
  { query: "Product Manager SaaS B2B", provider: "local", status: "done", results_count: 30, credits_used: 20, days_ago: 18 },
  { query: "Tech Lead full stack remote", provider: "hybrid", status: "done", results_count: 25, credits_used: 15, days_ago: 5 }
]

sourcings = sourcing_definitions.map do |defn|
  Sourcing.find_or_create_by!(query: defn[:query], account: account) do |s|
    s.user = user
    s.provider = defn[:provider]
    s.status = defn[:status]
    s.results_count = defn[:results_count]
    s.credits_used = defn[:credits_used]
    s.searched_at = (TODAY - defn[:days_ago].days).to_time
    s.is_deleted = false
    s.parameters = { location: "Brazil", seniority: "senior" }
  end
end

log "✅", "Sourcings ready (#{sourcings.size})"

log "🔄", "Seeding sourced profiles..."

profile_names = [
  { name: "Ricardo Alves", role_name: "Backend Developer", company: "Nubank", experience: 7, status: "interested", provider: "local" },
  { name: "Vanessa Campos", role_name: "Backend Developer", company: "iFood", experience: 4, status: "contacted", provider: "local" },
  { name: "Felipe Moreira", role_name: "Backend Developer", company: "Stone", experience: 8, status: "hired", provider: "local" },
  { name: "Daniela Cruz", role_name: "Frontend Developer", company: "VTEX", experience: 3, status: "new", provider: "pearch" },
  { name: "Roberto Dias", role_name: "Frontend Developer", company: "Resultados Digitais", experience: 5, status: "viewed", provider: "pearch" },
  { name: "Aline Ferreira", role_name: "Frontend Developer", company: "Pipefy", experience: 4, status: "interested", provider: "pearch" },
  { name: "Marcos Teixeira", role_name: "Product Manager", company: "Gupy", experience: 7, status: "contacted", provider: "local" },
  { name: "Renata Sousa", role_name: "Product Manager", company: "Zenvia", experience: 5, status: "rejected", provider: "local" },
  { name: "Eduardo Lima", role_name: "Tech Lead", company: "Creditas", experience: 9, status: "interested", provider: "hybrid" },
  { name: "Priscila Santos", role_name: "Tech Lead", company: "Loft", experience: 8, status: "new", provider: "hybrid" },
  { name: "Gabriel Pereira", role_name: "Backend Developer", company: "PagSeguro", experience: 5, status: "viewed", provider: "local" },
  { name: "Tatiana Machado", role_name: "Full Stack Developer", company: "Loggi", experience: 4, status: "new", provider: "pearch" }
]

sourced_profiles = profile_names.each_with_index.map do |defn, idx|
  sourcing_idx = case defn[:provider]
  when "local" then 0
  when "pearch" then 1
  when "hybrid" then 3
  else 0
  end

  email = "#{defn[:name].downcase.gsub(' ', '.').gsub(/[^a-z.]/, '')}@example.com"
  ext_id = "sp_#{Digest::MD5.hexdigest(defn[:name])[0..7]}"

  imported_candidate = defn[:status] == "hired" ? candidates[12] : nil

  SourcedProfile.find_or_create_by!(external_id: ext_id, account: account) do |sp|
    sp.sourcing = sourcings[sourcing_idx]
    sp.name = defn[:name]
    sp.email = email
    sp.provider = defn[:provider]
    sp.status = defn[:status]
    sp.role_name = defn[:role_name]
    sp.current_company = defn[:company]
    sp.total_experience_years = defn[:experience]
    sp.has_emails = true
    sp.has_phone_numbers = [ true, false ].sample
    sp.candidate_id = imported_candidate&.id
    sp.is_deleted = false
    sp.rating = defn[:status] == "interested" ? rand(3..5) : (defn[:status] == "rejected" ? rand(1..2) : nil)
    sp.city = %w[São\ Paulo Curitiba Florianópolis Belo\ Horizonte Rio\ de\ Janeiro].sample
    sp.state = %w[SP PR SC MG RJ].sample
  end
end

log "✅", "Sourced profiles ready (#{sourced_profiles.size})"

log "🔄", "Seeding sourced profile sourcings (links)..."

sourced_profiles.each_with_index do |sp, idx|
  sourcing_idx = case sp.provider
  when "local" then 0
  when "pearch" then 1
  when "hybrid" then 3
  else 0
  end

  SourcedProfileSourcing.find_or_create_by!(
    sourced_profile: sp,
    sourcing: sourcings[sourcing_idx],
    account: account
  ) do |sps|
    sps.user = user
    sps.score = rand(40..95).to_f
    sps.search_source = sp.provider
    sps.is_deleted = false
  end
end

log "✅", "Sourced profile sourcings ready"

# =============================================================================
# 12. Notification Preferences
# =============================================================================
log "🔄", "Seeding notification preferences..."

NotificationPreference.find_or_create_by!(user: user) do |np|
  np.briefing_enabled = true
  np.briefing_time = "08:30"
  np.briefing_channel = "web"
  np.alert_aging_enabled = true
  np.alert_deadline_enabled = true
  np.alert_no_show_enabled = true
  np.alert_evaluation_enabled = true
  np.alert_strong_fit_enabled = true
  np.alert_stale_job_enabled = true
  np.aging_threshold_days = 3
  np.alert_channels = %w[web]
  np.timezone = "America/Sao_Paulo"
end

log "✅", "Notification preferences ready"

# =============================================================================
# 13. Agent Notifications (varied types, statuses, dates)
# =============================================================================
log "🔄", "Seeding agent notifications..."

notification_data = [
  {
    notification_type: "briefing",
    channel: "web",
    status: "read",
    content: "📋 Briefing 07/03 — 3 novas candidaturas, 2 entrevistas hoje, 1 avaliação completada. Vaga 'Product Manager' com prazo em 15 dias.",
    alert_key: "briefing:#{user.id}:2026-03-07",
    sent_at: (TODAY - 1.day).to_time.change(hour: 8, min: 30),
    read_at: (TODAY - 1.day).to_time.change(hour: 9, min: 15),
    days_ago: 1
  },
  {
    notification_type: "briefing",
    channel: "web",
    status: "sent",
    content: "📋 Briefing 08/03 — 2 novas candidaturas para Backend Rails, entrevista cultural com João Silva amanhã às 10h. Avaliação de Carlos Mendes pendente há 3 dias.",
    alert_key: "briefing:#{user.id}:2026-03-08",
    sent_at: TODAY.to_time.change(hour: 8, min: 30),
    read_at: nil,
    days_ago: 0
  },
  {
    notification_type: "alert_aging",
    channel: "web",
    status: "sent",
    content: "⚠️ João Silva está na etapa Triagem da vaga 'Desenvolvedor(a) Backend Ruby on Rails' há 5 dias sem retorno. Considere avançar ou dar feedback.",
    reference_type: "Apply",
    reference_id: applies[0]&.id,
    alert_key: "aging:apply:#{applies[0]&.id}:2026-03-08",
    sent_at: TODAY.to_time.change(hour: 9),
    read_at: nil,
    days_ago: 0
  },
  {
    notification_type: "alert_aging",
    channel: "web",
    status: "sent",
    content: "⚠️ Diego Nascimento está na etapa Triagem da vaga 'Backend Ruby on Rails' há 10 dias. Este candidato pode estar perdendo interesse.",
    reference_type: "Apply",
    reference_id: applies[3]&.id,
    alert_key: "aging:apply:#{applies[3]&.id}:2026-03-08",
    sent_at: TODAY.to_time.change(hour: 9, min: 5),
    read_at: nil,
    days_ago: 0
  },
  {
    notification_type: "alert_deadline",
    channel: "web",
    status: "sent",
    content: "🔴 A vaga 'Product Manager' tem prazo de fechamento em 15 dias (23/03) e ainda há 3 candidatos na triagem. Considere acelerar o processo.",
    reference_type: "Job",
    reference_id: jobs[2]&.id,
    alert_key: "deadline:job:#{jobs[2]&.id}:2026-03-08",
    sent_at: TODAY.to_time.change(hour: 9, min: 10),
    read_at: nil,
    days_ago: 0
  },
  {
    notification_type: "alert_no_show",
    channel: "web",
    status: "read",
    content: "❌ Ana Paula Costa não compareceu à entrevista final para 'Product Manager' em 06/03. Deseja reagendar ou reprovar?",
    reference_type: "Meeting",
    reference_id: meetings[5]&.id,
    alert_key: "no_show:meeting:#{meetings[5]&.id}:2026-03-06",
    sent_at: (TODAY - 2.days).to_time.change(hour: 11),
    read_at: (TODAY - 2.days).to_time.change(hour: 14),
    days_ago: 2
  },
  {
    notification_type: "alert_evaluation",
    channel: "web",
    status: "sent",
    content: "✅ João Silva completou a Avaliação Técnica Backend com score 4.2/5 (Strong Fit). Classificação WSI: strong_fit.",
    reference_type: "EvaluationCandidate",
    reference_id: evaluation_candidates[0]&.id,
    alert_key: "eval_complete:ec:#{evaluation_candidates[0]&.id}",
    sent_at: (TODAY - 4.days).to_time.change(hour: 14),
    read_at: nil,
    days_ago: 4
  },
  {
    notification_type: "alert_strong_fit",
    channel: "web",
    status: "sent",
    content: "🌟 Bruno Souza recebeu score 4.5 na Avaliação Técnica Backend — Strong Fit! Recomendamos priorizar a entrevista.",
    reference_type: "EvaluationCandidate",
    reference_id: evaluation_candidates[4]&.id,
    alert_key: "strong_fit:ec:#{evaluation_candidates[4]&.id}",
    sent_at: (TODAY - 3.days).to_time.change(hour: 10),
    read_at: nil,
    days_ago: 3
  },
  {
    notification_type: "alert_stale_job",
    channel: "web",
    status: "read",
    content: "⏳ A vaga 'Analista de RH - Business Partner' está paralisada há 30 dias. Deseja reativar, cancelar ou aguardar?",
    reference_type: "Job",
    reference_id: jobs[4]&.id,
    alert_key: "stale:job:#{jobs[4]&.id}:2026-03-07",
    sent_at: (TODAY - 1.day).to_time.change(hour: 8, min: 45),
    read_at: (TODAY - 1.day).to_time.change(hour: 10),
    days_ago: 1
  },
  {
    notification_type: "alert_aging",
    channel: "web",
    status: "read",
    content: "⚠️ Letícia Cardoso está na Triagem da vaga 'Analista de RH' há 8 dias sem atualização.",
    reference_type: "Apply",
    reference_id: applies[16]&.id,
    alert_key: "aging:apply:#{applies[16]&.id}:2026-03-05",
    sent_at: (TODAY - 3.days).to_time.change(hour: 9),
    read_at: (TODAY - 3.days).to_time.change(hour: 11, min: 30),
    days_ago: 3
  },
  {
    notification_type: "alert_evaluation",
    channel: "web",
    status: "sent",
    content: "✅ Maria Santos completou a Avaliação Frontend com score 3.9 (Moderate Fit). Já está na etapa de entrevista.",
    reference_type: "EvaluationCandidate",
    reference_id: evaluation_candidates[7]&.id,
    alert_key: "eval_complete:ec:#{evaluation_candidates[7]&.id}",
    sent_at: (TODAY - 1.day).to_time.change(hour: 16),
    read_at: nil,
    days_ago: 1
  },
  {
    notification_type: "alert_deadline",
    channel: "web",
    status: "sent",
    content: "🟡 A vaga 'Analista de RH - Business Partner' tem prazo em 5 dias (13/03). Está paralisada — considere reativar.",
    reference_type: "Job",
    reference_id: jobs[4]&.id,
    alert_key: "deadline:job:#{jobs[4]&.id}:2026-03-08",
    sent_at: TODAY.to_time.change(hour: 9, min: 15),
    read_at: nil,
    days_ago: 0
  }
]

notification_data.each do |defn|
  AgentNotification.find_or_create_by!(alert_key: defn[:alert_key]) do |n|
    n.user = user
    n.notification_type = defn[:notification_type]
    n.channel = defn[:channel]
    n.status = defn[:status]
    n.content = defn[:content]
    n.reference_type = defn[:reference_type]
    n.reference_id = defn[:reference_id]
    n.metadata = {}
    n.sent_at = defn[:sent_at]
    n.read_at = defn[:read_at]
    n.created_at = defn[:sent_at] || (TODAY - defn[:days_ago].days).to_time
  end
end

log "✅", "Agent notifications ready (#{AgentNotification.where(user: user).count})"

# =============================================================================
# 14. Activity Logs (for productivity avg_days_to_close)
# =============================================================================
log "🔄", "Seeding activity logs for closed jobs..."

closed_job = jobs[6]
if closed_job && !ActivityLog.exists?(reference_type: "Job", reference_id: closed_job.id, action: "update")
  ActivityLog.create!(
    reference_type: "Job",
    reference_id: closed_job.id,
    action: "update",
    changeset: { "job_status_id" => { "from" => active_status.id, "to" => closed_status.id } },
    user: user,
    account: account,
    category: "job_status",
    created_at: (TODAY - 10.days).to_time
  )
end

log "✅", "Activity logs ready"

# =============================================================================
# 15. Calendar Events (today's agenda — briefing reads CalendarEvent, not Meeting)
# =============================================================================
log "🔄", "Seeding calendar events..."

calendar_event_data = [
  {
    title: "Entrevista técnica - João Silva (Backend Rails)",
    event_type: "interview", provider: "microsoft",
    candidate_idx: 0, job_idx: 0, apply_idx: 0,
    hour: 9, minute: 0, duration_minutes: 60,
    sub_status: "confirmed"
  },
  {
    title: "Alinhamento de perfil - Vaga Product Manager",
    event_type: "generic", provider: "microsoft",
    candidate_idx: nil, job_idx: 2, apply_idx: nil,
    hour: 10, minute: 30, duration_minutes: 30,
    sub_status: "confirmed"
  },
  {
    title: "Entrevista frontend - Maria Santos (Vue.js)",
    event_type: "interview", provider: "microsoft",
    candidate_idx: 1, job_idx: 1, apply_idx: 6,
    hour: 11, minute: 0, duration_minutes: 60,
    sub_status: "invite_sent"
  },
  {
    title: "Entrevista cultural - Carlos Mendes (Tech Lead)",
    event_type: "interview", provider: "microsoft",
    candidate_idx: 4, job_idx: 3, apply_idx: 13,
    hour: 14, minute: 0, duration_minutes: 45,
    sub_status: "confirmed"
  },
  {
    title: "Devolutiva candidatos reprovados - Backend Rails",
    event_type: "feedback", provider: "microsoft",
    candidate_idx: nil, job_idx: 0, apply_idx: nil,
    hour: 16, minute: 0, duration_minutes: 30,
    sub_status: "confirmed"
  },
  {
    title: "Entrevista final - Ana Paula Costa (PM)",
    event_type: "interview", provider: "microsoft",
    candidate_idx: 3, job_idx: 2, apply_idx: 10,
    hour: 17, minute: 0, duration_minutes: 60,
    sub_status: "invite_sent"
  }
]

calendar_events = calendar_event_data.map do |defn|
  start_time = TODAY.to_time.in_time_zone("America/Sao_Paulo").change(hour: defn[:hour], min: defn[:minute])
  end_time = start_time + defn[:duration_minutes].minutes

  job = jobs[defn[:job_idx]]
  apply = defn[:apply_idx] ? applies[defn[:apply_idx]] : nil

  CalendarEvent.find_or_create_by!(title: defn[:title], start_time: start_time, account: account) do |ce|
    ce.organizer = user
    ce.event_type = defn[:event_type]
    ce.provider = defn[:provider]
    ce.start_time = start_time
    ce.end_time = end_time
    ce.timezone = "America/Sao_Paulo"
    ce.sub_status = defn[:sub_status]
    ce.job = job
    ce.apply = apply
    ce.is_deleted = false
    ce.is_cancelled = false
    ce.is_all_day = false
    ce.importance = "normal"
  end
end

log "✅", "Calendar events ready (#{calendar_events.size})"

# =============================================================================
# 16. Recent Applies (last 24h — so briefing shows new_applies > 0)
# =============================================================================
log "🔄", "Seeding recent applies (last 24h)..."

recent_candidate_defs = [
  { name: "Luiza Fernandes", email: "luiza.fernandes@email.com", role_name: "Backend Developer", source: "LinkedIn", city: "São Paulo", state: "SP", gender: 2 },
  { name: "Matheus Correia", email: "matheus.correia@email.com", role_name: "Full Stack Developer", source: "Site", city: "Campinas", state: "SP", gender: 1 },
  { name: "Bianca Moura", email: "bianca.moura@email.com", role_name: "Frontend Developer", source: "Indicação", city: "Curitiba", state: "PR", gender: 2 },
  { name: "Henrique Lopes", email: "henrique.lopes@email.com", role_name: "Product Manager", source: "LinkedIn", city: "São Paulo", state: "SP", gender: 1 },
  { name: "Amanda Rezende", email: "amanda.rezende@email.com", role_name: "SDR", source: "Site", city: "Belo Horizonte", state: "MG", gender: 2 }
]

recent_candidates = recent_candidate_defs.map do |defn|
  Candidate.find_or_create_by!(email: defn[:email], account: account) do |c|
    c.assign_attributes(defn.except(:email).merge(account: account, is_deleted: false))
  end
end

recent_apply_map = [
  { cand_idx: 0, job_idx: 0, cv_match: 0.91, hours_ago: 2 },
  { cand_idx: 1, job_idx: 3, cv_match: 0.84, hours_ago: 5 },
  { cand_idx: 2, job_idx: 1, cv_match: 0.77, hours_ago: 8 },
  { cand_idx: 3, job_idx: 2, cv_match: 0.88, hours_ago: 12 },
  { cand_idx: 4, job_idx: 5, cv_match: 0.72, hours_ago: 18 }
]

recent_applies = recent_apply_map.map do |defn|
  candidate = recent_candidates[defn[:cand_idx]]
  job = jobs[defn[:job_idx]]
  sps = selective_processes[job.id]
  sp = sps&.find { |s| s.status == "web_submission" } || sps&.first
  next unless sp

  existing = Apply.find_by(job: job, candidate: candidate, account: account, is_deleted: false)
  next existing if existing

  apply = Apply.new(
    job: job,
    candidate: candidate,
    selective_process: sp,
    account: account,
    cv_match: defn[:cv_match],
    is_deleted: false,
    created_at: Time.current - defn[:hours_ago].hours,
    updated_at: Time.current - defn[:hours_ago].hours
  )
  apply.save!(validate: false)
  apply
end.compact

log "✅", "Recent applies ready (#{recent_applies.size})"

# =============================================================================
# 17. Recent Evaluation Completions (last 24h — briefing counts these)
# =============================================================================
log "🔄", "Seeding recent evaluation completions..."

recent_eval_data = [
  { eval_idx: 0, candidate: candidates[10], score: 3.6, wsi: "moderate_fit", hours_ago: 3 },
  { eval_idx: 2, candidate: candidates[17], score: 4.3, wsi: "strong_fit", hours_ago: 6 },
  { eval_idx: 4, candidate: candidates[4],  score: 4.7, wsi: "strong_fit", hours_ago: 10 }
]

recent_eval_data.each do |defn|
  evaluation = evaluations[defn[:eval_idx]]
  job = evaluation.job
  apply = Apply.find_by(job: job, candidate: defn[:candidate], account: account, is_deleted: false)

  ec = EvaluationCandidate.find_or_initialize_by(evaluation: evaluation, candidate: defn[:candidate], account: account)
  ec.assign_attributes(
    job: job,
    apply: apply,
    user: user,
    completed: true,
    score: defn[:score],
    wsi_classification: defn[:wsi],
    is_screening: evaluation.is_screening,
    is_deleted: false,
    updated_at: Time.current - defn[:hours_ago].hours
  )
  ec.save!(validate: false)
end

log "✅", "Recent evaluation completions ready"

# =============================================================================
# 18. Apply Statuses (pipeline movements — briefing counts recent movements)
# =============================================================================
log "🔄", "Seeding apply statuses (pipeline movements)..."

apply_status_data = [
  { apply: applies[0], sp_status: :screening, hours_ago: 20, comment: "" },
  { apply: applies[1], sp_status: :interview, hours_ago: 16, comment: "Bom desempenho na triagem técnica" },
  { apply: applies[6], sp_status: :interview, hours_ago: 14, comment: "" },
  { apply: applies[7], sp_status: :screening, hours_ago: 10, comment: "" },
  { apply: applies[13], sp_status: :screening, hours_ago: 4, comment: "Perfil excelente, priorizar entrevista" },
  { apply: applies[18], sp_status: :screening, hours_ago: 8, comment: "" }
]

apply_status_data.each do |defn|
  next unless defn[:apply]

  sp = selective_processes[defn[:apply].job_id]&.find { |s| s.status == defn[:sp_status].to_s }
  next unless sp

  existing = ApplyStatus.find_by(apply: defn[:apply], selective_process: sp)
  next if existing

  as = ApplyStatus.new(
    apply: defn[:apply],
    selective_process: sp,
    status_name: sp.name,
    user: user,
    account_id: account.id,
    comment: defn[:comment],
    is_deleted: false,
    created_at: Time.current - defn[:hours_ago].hours,
    updated_at: Time.current - defn[:hours_ago].hours
  )
  as.save!(validate: false)
end

log "✅", "Apply statuses ready"

# =============================================================================
# Summary
# =============================================================================
puts ""
puts "=" * 60
log "🚀", "SEED COMPLETE — Summary:"
puts "=" * 60
puts "  Jobs:                    #{Job.where(is_deleted: false).count}"
puts "  Candidates:              #{Candidate.where(is_deleted: false).count}"
puts "  Applies:                 #{Apply.where(is_deleted: false).count}"
puts "  Selective Processes:     #{SelectiveProcess.count}"
puts "  Evaluations:             #{Evaluation.count}"
puts "  Evaluation Candidates:   #{EvaluationCandidate.where(is_deleted: false).count}"
puts "  Meetings:                #{Meeting.where(is_deleted: false).count}"
puts "  Calendar Events:         #{CalendarEvent.where(is_deleted: false).count}"
puts "  Apply Statuses (24h):    #{ApplyStatus.where('apply_statuses.created_at >= ?', 24.hours.ago).count}"
puts "  Sourcings:               #{Sourcing.where(is_deleted: false).count}"
puts "  Sourced Profiles:        #{SourcedProfile.active.count}"
puts "  Departments:             #{Department.active.count}"
puts "  Job Statuses:            #{JobStatus.count}"
puts "  Notification Prefs:      #{NotificationPreference.count}"
puts "  Agent Notifications:     #{AgentNotification.count}"
puts "    - Unread:              #{AgentNotification.unread.count}"
puts "    - Read:                #{AgentNotification.where.not(read_at: nil).count}"
puts "=" * 60
puts ""
log "✅", "Ready to test endpoints!"
puts ""
puts "  GET  /v1/users/notification_preferences"
puts "  PUT  /v1/users/notification_preferences"
puts "  GET  /v1/users/notifications"
puts "  GET  /v1/users/notifications/:id"
puts "  PUT  /v1/users/notifications/:id/read"
puts "  POST /v1/users/notifications/mark_all_read"
puts "  GET  /v1/users/notifications/unread_count"
puts "  POST /v1/users/notifications/send_push  (service token)"
puts "  GET  /v1/users/sourced_profiles/stats"
puts "  GET  /v1/users/evaluation_candidates/stats"
puts "  GET  /v1/users/me/productivity"
puts ""

ensure
  Searchkick.enable_callbacks
end
