# frozen_string_literal: true

return unless Rails.env.development?

ACCOUNT_ID = 1
USER_ID = 1

account = Account.find(ACCOUNT_ID)
Apartment::Tenant.switch!(account.tenant)

Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Rails.logger.info "🚀 [AgentTestData] Starting L7-L9 agent test data seed"
Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

SAFE_EMAIL = "victhor_root@hotmail.com"
SAFE_PHONE = "18996041211"

seed_jobs = Job.where(
  title: [
    "Desenvolvedor(a) Backend Ruby on Rails",
    "Desenvolvedor(a) Frontend Vue.js",
    "Tech Lead Full Stack",
    "Product Manager",
    "SDR - Sales Development Representative",
    "Desenvolvedor(a) Python Sênior",
    "DevOps Engineer",
    "Data Scientist",
    "Analista de Dados"
  ],
  is_deleted: false
).index_by(&:title)

seed_candidates = Candidate.where(
  name: [
    "João Silva", "Maria Santos", "Pedro Costa", "Ana O.",
    "Lucas Pereira", "Camila dos Santos Rodrigues", "Rafael  Almeida",
    "Juliana Fernandes", "Fernando Calheiros de Lima", "Beatriz Martins"
  ],
  account_id: ACCOUNT_ID,
  is_deleted: false
).index_by(&:name)

abort "❌ Seed jobs not found. Run db:seed first." if seed_jobs.empty?
abort "❌ Seed candidates not found. Run db:seed first." if seed_candidates.empty?

job_backend = seed_jobs["Desenvolvedor(a) Backend Ruby on Rails"]
job_frontend = seed_jobs["Desenvolvedor(a) Frontend Vue.js"]
job_techlead = seed_jobs["Tech Lead Full Stack"]
job_pm = seed_jobs["Product Manager"]
job_sdr = seed_jobs["SDR - Sales Development Representative"]
job_python = seed_jobs["Desenvolvedor(a) Python Sênior"]
job_devops = seed_jobs["DevOps Engineer"]
job_ds = seed_jobs["Data Scientist"]
job_dados = seed_jobs["Analista de Dados"]

cand_joao = seed_candidates["João Silva"]
cand_maria = seed_candidates["Maria Santos"]
cand_pedro = seed_candidates["Pedro Costa"]
cand_ana = seed_candidates["Ana O."]
cand_lucas = seed_candidates["Lucas Pereira"]
cand_camila = seed_candidates["Camila dos Santos Rodrigues"]
cand_rafael = seed_candidates["Rafael  Almeida"]
cand_juliana = seed_candidates["Juliana Fernandes"]
cand_fernando = seed_candidates["Fernando Calheiros de Lima"]
cand_beatriz = seed_candidates["Beatriz Martins"]

all_seed_candidates = [ cand_joao, cand_maria, cand_pedro, cand_ana, cand_lucas,
                       cand_camila, cand_rafael, cand_juliana, cand_fernando, cand_beatriz ].compact

def find_stage(job, stage_name)
  SelectiveProcess.find_by(job_id: job.id, name: stage_name, is_deleted: false)
end

def find_stage_by_status(job, status)
  SelectiveProcess.where(job_id: job.id, status: status, is_deleted: false).order(:position).first
end

aging_candidates_data = [
  { name: "Thiago Nascimento", role_name: "Senior Java Developer", city: "São Paulo", state: "SP" },
  { name: "Carolina Mendes", role_name: "Product Designer", city: "Rio de Janeiro", state: "RJ" },
  { name: "Diego Ferreira", role_name: "Cloud Architect", city: "Curitiba", state: "PR" },
  { name: "Isabela Rocha", role_name: "Data Engineer", city: "Belo Horizonte", state: "MG" },
  { name: "Gustavo Barbosa", role_name: "Mobile Developer", city: "Porto Alegre", state: "RS" },
  { name: "Larissa Tavares", role_name: "DevSecOps Engineer", city: "Florianópolis", state: "SC" },
  { name: "Bruno Cardoso", role_name: "Backend Engineer", city: "Campinas", state: "SP" },
  { name: "Mariana Duarte", role_name: "Full Stack Developer", city: "São Paulo", state: "SP" },
  { name: "Eduardo Neves", role_name: "QA Automation Engineer", city: "Goiânia", state: "GO" },
  { name: "Natalia Pinto", role_name: "Tech Recruiter", city: "São Paulo", state: "SP" },
  { name: "Henrique Lopes", role_name: "SRE Engineer", city: "Recife", state: "PE" },
  { name: "Patricia Souza", role_name: "Business Analyst", city: "Salvador", state: "BA" },
  { name: "Rodrigo Vieira", role_name: "React Developer", city: "São Paulo", state: "SP" },
  { name: "Aline Costa", role_name: "Machine Learning Engineer", city: "Brasília", state: "DF" },
  { name: "Felipe Moreira", role_name: "Golang Developer", city: "Curitiba", state: "PR" }
]

new_candidates = aging_candidates_data.map do |attrs|
  Candidate.find_or_create_by!(name: attrs[:name], account_id: ACCOUNT_ID) do |c|
    c.uid = SecureRandom.uuid
    c.role_name = attrs[:role_name]
    c.city = attrs[:city]
    c.state = attrs[:state]
    c.country = "BR"
    c.source = "manual"
    c.completed_register = true
    c.accept_terms = true
    c.linkedin = "https://linkedin.com/in/#{attrs[:name].parameterize}"
    c.position_level = %w[Senior Pleno].sample
    c.current_salary = rand(10000..25000).round(-2)
    c.clt_expectation = rand(12000..30000).round(-2)
  end.tap { |c| c.update_columns(email: SAFE_EMAIL, mobile_phone: SAFE_PHONE) }
end

puts "✅ Extra candidates OK (#{new_candidates.size})"

aging_jobs = [ job_backend, job_frontend, job_techlead, job_python, job_devops, job_ds, job_dados ].compact

aging_applies_created = 0
aging_jobs.each_with_index do |job, job_idx|
  triagem = find_stage(job, "Triagem") || find_stage_by_status(job, :screening)
  entrevista = find_stage(job, "Entrevista Técnica") || find_stage(job, "Entrevista") || find_stage_by_status(job, :interview)
  inscricao = find_stage(job, "Inscrição") || find_stage_by_status(job, :web_submission)
  next unless triagem || entrevista

  candidates_for_aging = new_candidates.rotate(job_idx * 2).first(rand(3..5))

  candidates_for_aging.each_with_index do |candidate, i|
    stage = i.even? ? triagem : entrevista
    next unless stage

    days_stuck = rand(8..21)

    apply = Apply.find_or_create_by!(
      candidate_id: candidate.id,
      job_id: job.id,
      account_id: ACCOUNT_ID
    ) do |a|
      a.selective_process_id = stage.id
      a.user_id = USER_ID
      a.cv_match = rand(45..88).to_f
      a.total_score = rand(35..85).to_f
    end

    apply.update_columns(
      created_at: (days_stuck + rand(1..5)).days.ago,
      updated_at: days_stuck.days.ago,
      selective_process_id: stage.id
    )

    aging_applies_created += 1
  end
end

puts "✅ Aging applies OK (#{aging_applies_created} stuck >7 days)"

eval_jobs = [ job_backend, job_frontend, job_python, job_devops, job_ds ].compact

evals_created = 0
eval_jobs.each do |job|
  eval_name = "Avaliação Técnica - #{job.title.truncate(30)}"
  sp_interview = find_stage(job, "Entrevista Técnica") || find_stage(job, "Entrevista") || find_stage_by_status(job, :interview)

  evaluation = Evaluation.find_or_create_by!(
    name: eval_name,
    job_id: job.id,
    account_id: ACCOUNT_ID
  ) do |e|
    e.selective_process_id = sp_interview&.id
    e.user_id = USER_ID
    e.status = true
    e.position = 0
    e.description = "Avaliação técnica para #{job.title}"
    e.uid = SecureRandom.uuid
    e.time = 90
    e.is_chatbot = false
    e.ai_enabled = true
    e.is_main = false
  end

  candidates_in_pipeline = Apply.where(job_id: job.id, is_deleted: false)
                                .where.not(selective_process_id: nil)
                                .includes(:candidate)
                                .limit(8)

  answered_count = 0
  candidates_in_pipeline.each_with_index do |apply, idx|
    ec = EvaluationCandidate.find_or_create_by!(
      candidate_id: apply.candidate_id,
      evaluation_id: evaluation.id,
      account_id: ACCOUNT_ID
    ) do |e|
      e.job_id = job.id
      e.user_id = USER_ID
      e.uid = SecureRandom.uuid
      e.candidate_uid = apply.candidate.uid
      e.apply_id = apply.id
    end

    should_answer = idx < (candidates_in_pipeline.size * 0.4).ceil

    if should_answer && !ec.completed
      ec.update_columns(
        completed: true,
        score: rand(55..95).to_f,
        evaluation_summary: "Candidato demonstrou #{%w[bom excelente adequado].sample} domínio técnico.",
        updated_at: rand(1..5).days.ago
      )
      answered_count += 1
    end
  end

  evals_created += 1
end

puts "✅ Evaluations with mixed rates OK (#{evals_created} evaluations)"

paused_jobs_data = [
  {
    title: "Engenheiro de Dados Pleno",
    department: "Tecnologia",
    seniority: 1,
    paused_days_ago: 35,
    skills: %w[Python SQL ETL]
  },
  {
    title: "Analista de BI Sênior",
    department: "Tecnologia",
    seniority: 2,
    paused_days_ago: 45,
    skills: %w[SQL Power\ BI Tableau]
  },
  {
    title: "Scrum Master",
    department: "Product",
    seniority: 1,
    paused_days_ago: 60,
    skills: %w[Scrum Agile Kanban]
  }
]

paused_created = 0
paused_jobs_data.each do |attrs|
  dept = Department.find_by(name: attrs[:department], is_deleted: false)
  next unless dept

  job = Job.find_or_create_by!(title: attrs[:title], account_id: ACCOUNT_ID, is_deleted: false) do |j|
    j.user_id = USER_ID
    j.department_id = dept.id
    j.description = "Vaga para #{attrs[:title]}."
    j.seniority = attrs[:seniority]
    j.employment_type = 0
    j.city = "São Paulo"
    j.state = "SP"
    j.country = "BR"
    j.is_active = false
    j.reason_for_pause = "Headcount congelado - aguardando aprovação orçamentária"
    j.published_date = (attrs[:paused_days_ago] + 15).days.ago
    j.application_deadline = 30.days.from_now
  end

  job.update_columns(
    is_active: false,
    reason_for_pause: "Headcount congelado - aguardando aprovação orçamentária",
    updated_at: attrs[:paused_days_ago].days.ago
  )

  stages = [
    { name: "Inscrição", status: :web_submission, position: 0 },
    { name: "Triagem", status: :screening, position: 1 },
    { name: "Entrevista", status: :interview, position: 2 },
    { name: "Contratado", status: :hired, position: 3 },
    { name: "Reprovado", status: :rejected, position: 4 }
  ]

  stages.each do |stage|
    SelectiveProcess.find_or_create_by!(
      name: stage[:name],
      job_id: job.id,
      is_deleted: false
    ) do |sp|
      sp.status = stage[:status]
      sp.position = stage[:position]
      sp.account_id = ACCOUNT_ID
      sp.uid = SecureRandom.uuid
    end
  end

  paused_created += 1
end

puts "✅ Paused jobs OK (#{paused_created} paused >30 days)"

empty_jobs = [ job_devops, job_ds, job_dados ].compact
empty_jobs.each do |job|
  next if Apply.where(job_id: job.id, is_deleted: false).exists?

  candidates_to_apply = new_candidates.sample(rand(3..6))
  stages = SelectiveProcess.where(job_id: job.id, is_deleted: false).order(:position)
  next if stages.empty?

  candidates_to_apply.each_with_index do |candidate, i|
    stage = stages[i % [ stages.size, 3 ].min]

    days_ago = rand(3..18)
    apply = Apply.find_or_create_by!(
      candidate_id: candidate.id,
      job_id: job.id,
      account_id: ACCOUNT_ID
    ) do |a|
      a.selective_process_id = stage.id
      a.user_id = USER_ID
      a.cv_match = rand(40..90).to_f
      a.total_score = rand(30..85).to_f
    end

    apply.update_columns(
      created_at: days_ago.days.ago,
      updated_at: [ days_ago, rand(1..days_ago) ].max.days.ago
    )
  end
end

puts "✅ Empty jobs populated (DevOps, Data Scientist, Analista de Dados)"

if job_ds && Apply.where(job_id: job_ds.id, is_deleted: false).count < 5
  ds_sps = SelectiveProcess.where(job_id: job_ds.id, is_deleted: false).index_by(&:name)
  ds_candidates_data = [
    { name: "Caio Ribeiro",     sp: "Triagem",            days_ago: 3 },
    { name: "Amanda Farias",    sp: "Triagem",            days_ago: 12 },
    { name: "Marcos Teixeira",  sp: "Entrevista Técnica", days_ago: 6 },
    { name: "Julia Monteiro",   sp: "Entrevista Técnica", days_ago: 15 },
    { name: "Renato Barros",    sp: "Contratado",         days_ago: 2 },
    { name: "Daniela Lima",     sp: "Reprovado",          days_ago: 8 },
    { name: "Otavio Ramos",     sp: "Inscrição",          days_ago: 20 }
  ]
  ds_candidates_data.each do |cd|
    sp = ds_sps[cd[:sp]]
    next unless sp

    candidate = Candidate.find_or_create_by!(name: cd[:name]) do |c|
      c.email = SAFE_EMAIL
      c.mobile_phone = SAFE_PHONE
      c.source = "manual"
      c.account_id = ACCOUNT_ID
    end
    apply = Apply.find_or_create_by!(candidate: candidate, job: job_ds) do |a|
      a.selective_process = sp
      a.is_deleted = false
      a.account_id = ACCOUNT_ID
    end
    apply.update_columns(
      selective_process_id: sp.id,
      created_at: cd[:days_ago].days.ago,
      updated_at: cd[:days_ago].days.ago
    )
  end
  puts "✅ DS job additional applies OK"
end

interview_stage_python = find_stage(job_python, "Entrevista Técnica") || find_stage(job_python, "Entrevista") || find_stage_by_status(job_python, :interview)
interview_stage_backend = find_stage(job_backend, "Entrevista Técnica") || find_stage(job_backend, "Entrevista") || find_stage_by_status(job_backend, :interview)

no_interview_applies = []

[ job_python, job_backend ].compact.each do |job|
  int_stage = job == job_python ? interview_stage_python : interview_stage_backend
  next unless int_stage

  applies_in_interview = Apply.where(job_id: job.id, selective_process_id: int_stage.id, is_deleted: false)

  applies_in_interview.each do |apply|
    existing_interview = InterviewSession.find_by(candidate_id: apply.candidate_id, job_id: job.id)
    no_interview_applies << apply unless existing_interview
  end
end

puts "✅ Candidates in interview without scheduled interview: #{no_interview_applies.size}"

triagem_python = find_stage(job_python, "Triagem") || find_stage_by_status(job_python, :screening)
if triagem_python
  stuck_in_triagem = Apply.where(
    job_id: job_python.id,
    selective_process_id: triagem_python.id,
    is_deleted: false
  ).where("updated_at < ?", 5.days.ago).count

  if stuck_in_triagem < 3
    extra_triagem = new_candidates.last(4)
    extra_triagem.each do |c|
      apply = Apply.find_or_create_by!(
        candidate_id: c.id,
        job_id: job_python.id,
        account_id: ACCOUNT_ID
      ) do |a|
        a.selective_process_id = triagem_python.id
        a.user_id = USER_ID
        a.cv_match = rand(55..85).to_f
        a.total_score = rand(50..80).to_f
      end
      apply.update_columns(
        selective_process_id: triagem_python.id,
        created_at: rand(7..12).days.ago,
        updated_at: rand(6..10).days.ago
      )
    end
  end
end

puts "✅ Python Triagem aging candidates OK"

recent_sourcing = Sourcing.find_or_create_by!(
  query: "desenvolvedor ruby on rails sênior são paulo remoto",
  account_id: ACCOUNT_ID,
  is_deleted: false,
  status: "done"
) do |s|
  s.uid = SecureRandom.uuid
  s.user_id = USER_ID
  s.provider = "hybrid"
  s.results_count = 25
  s.local_results_count = 15
  s.global_results_count = 10
  s.credits_used = 5
  s.searched_at = 15.days.ago
  s.saved = true
  s.parameters = { location: "São Paulo", skills: [ "Ruby", "Rails" ], seniority: "senior" }
end
recent_sourcing.update_columns(created_at: 15.days.ago) if recent_sourcing.created_at > 20.days.ago

sourced_not_applied_data = [
  { name: "Leonardo Martins", role: "Senior Ruby Developer", score: 92 },
  { name: "Priscila Gomes", role: "Rails Backend Engineer", score: 87 },
  { name: "Vinicius Andrade", role: "Full Stack Ruby/Vue", score: 85 },
  { name: "Tatiana Ribeiro", role: "Senior Backend Developer", score: 81 },
  { name: "Ricardo Nascimento", role: "Ruby on Rails Engineer", score: 78 }
]

sourced_imported = 0
sourced_not_applied_data.each do |attrs|
  candidate = Candidate.find_or_create_by!(name: attrs[:name], account_id: ACCOUNT_ID) do |c|
    c.uid = SecureRandom.uuid
    c.role_name = attrs[:role]
    c.city = "São Paulo"
    c.state = "SP"
    c.country = "BR"
    c.source = "sourcing"
    c.completed_register = false
    c.accept_terms = false
    c.position_level = "Senior"
    c.current_salary = rand(12000..25000).round(-2)
    c.clt_expectation = rand(15000..30000).round(-2)
  end
  candidate.update_columns(email: SAFE_EMAIL, mobile_phone: SAFE_PHONE)

  Apply.where(candidate_id: candidate.id, is_deleted: false).delete_all

  profile = SourcedProfile.find_or_create_by!(
    external_id: "seed-agent-#{attrs[:name].parameterize}",
    account_id: ACCOUNT_ID,
    is_deleted: false
  ) do |sp|
    sp.uid = SecureRandom.uuid
    sp.name = attrs[:name]
    sp.provider = "hybrid"
    sp.status = "interested"
    sp.role_name = attrs[:role]
    sp.current_title = attrs[:role]
    sp.city = "São Paulo"
    sp.state = "SP"
    sp.country = "BR"
    sp.total_experience_years = rand(5..12)
    sp.skills_data = %w[Ruby Rails PostgreSQL Docker Redis].map { |s| { name: s } }
    sp.candidate_id = candidate.id
    sp.email = SAFE_EMAIL
    sp.mobile_phone = SAFE_PHONE
  end

  SourcedProfileSourcing.find_or_create_by!(
    sourced_profile_id: profile.id,
    sourcing_id: recent_sourcing.id
  ) do |sps|
    sps.score = attrs[:score]
    sps.search_score = attrs[:score].to_f / 100
    sps.similarity_score = attrs[:score].to_f / 100
    sps.search_source = "hybrid"
    sps.account_id = ACCOUNT_ID
    sps.user_id = USER_ID
  end

  sourced_imported += 1
end

puts "✅ Sourced profiles imported but not applied OK (#{sourced_imported})"

second_sourcing = Sourcing.find_or_create_by!(
  query: "data scientist python machine learning são paulo",
  account_id: ACCOUNT_ID,
  is_deleted: false,
  status: "done"
) do |s|
  s.uid = SecureRandom.uuid
  s.user_id = USER_ID
  s.provider = "local"
  s.results_count = 18
  s.local_results_count = 18
  s.global_results_count = 0
  s.credits_used = 3
  s.searched_at = 20.days.ago
  s.saved = true
  s.parameters = { location: "São Paulo", skills: [ "Python", "Machine Learning", "Data Science" ] }
end
second_sourcing.update_columns(created_at: 20.days.ago) if second_sourcing.created_at > 25.days.ago

third_sourcing = Sourcing.find_or_create_by!(
  query: "frontend developer vue.js react typescript remoto",
  account_id: ACCOUNT_ID,
  is_deleted: false,
  status: "done"
) do |s|
  s.uid = SecureRandom.uuid
  s.user_id = USER_ID
  s.provider = "pearch"
  s.results_count = 30
  s.local_results_count = 10
  s.global_results_count = 20
  s.credits_used = 8
  s.searched_at = 10.days.ago
  s.saved = true
  s.parameters = { skills: [ "Vue.js", "React", "TypeScript" ], remote: true }
end
third_sourcing.update_columns(created_at: 10.days.ago) if third_sourcing.created_at > 15.days.ago

puts "✅ Additional sourcings OK"

rejected_with_interview = 0
[ job_backend, job_sdr ].compact.each do |job|
  rejected_stage = find_stage(job, "Reprovado") || find_stage_by_status(job, :rejected)
  next unless rejected_stage

  rejected_applies = Apply.where(job_id: job.id, selective_process_id: rejected_stage.id, is_deleted: false).limit(2)
  rejected_applies.each do |apply|
    existing = InterviewSession.find_by(candidate_id: apply.candidate_id, job_id: job.id)
    next if existing

    evaluation = Evaluation.find_by(job_id: job.id, account_id: ACCOUNT_ID)
    next unless evaluation

    ec = EvaluationCandidate.find_or_create_by!(
      candidate_id: apply.candidate_id,
      evaluation_id: evaluation.id,
      account_id: ACCOUNT_ID
    ) do |e|
      e.job_id = job.id
      e.user_id = USER_ID
      e.uid = SecureRandom.uuid
      e.candidate_uid = apply.candidate.uid
      e.apply_id = apply.id
    end

    InterviewSession.create!(
      token: SecureRandom.hex(16),
      status: "pending",
      account_id: ACCOUNT_ID,
      evaluation_id: evaluation.id,
      evaluation_candidate_id: ec.id,
      apply_id: apply.id,
      candidate_id: apply.candidate_id,
      job_id: job.id,
      created_by_id: USER_ID,
      interview_type: "voice",
      duration_minutes: 30,
      language: "pt-BR",
      expires_at: 5.days.from_now,
      job_context: { title: job.title, department: job.department&.name },
      candidate_context: { name: apply.candidate.name, role: apply.candidate.role_name },
      questions_snapshot: [
        { question: "Conte sobre sua experiência", type: "open" },
        { question: "Por que tem interesse nesta vaga?", type: "open" }
      ],
      created_at: 2.days.ago
    )
    rejected_with_interview += 1
  end
end

puts "✅ Interviews for rejected candidates OK (#{rejected_with_interview})"

high_conversion_jobs = [ job_backend, job_frontend ].compact
low_conversion_jobs = [ job_devops, job_ds, job_dados ].compact

high_conversion_jobs.each do |job|
  stages = SelectiveProcess.where(job_id: job.id, is_deleted: false).order(:position)
  next if stages.size < 3

  hired_stage = stages.find { |s| s.status == "hired" }
  screening_stage = stages.find { |s| s.status == "screening" }
  next unless hired_stage && screening_stage

  existing_hired = Apply.where(job_id: job.id, selective_process_id: hired_stage.id, is_deleted: false).count
  if existing_hired < 3
    additional = new_candidates.sample(2)
    additional.each do |c|
      apply = Apply.find_or_create_by!(candidate_id: c.id, job_id: job.id, account_id: ACCOUNT_ID) do |a|
        a.selective_process_id = hired_stage.id
        a.user_id = USER_ID
        a.cv_match = rand(80..98).to_f
        a.total_score = rand(75..95).to_f
      end
      apply.update_columns(selective_process_id: hired_stage.id, updated_at: rand(1..5).days.ago)
    end
  end
end

low_conversion_jobs.each do |job|
  stages = SelectiveProcess.where(job_id: job.id, is_deleted: false).order(:position)
  screening = stages.find { |s| s.status == "screening" }
  inscricao = stages.find { |s| s.status == "web_submission" }
  next unless screening && inscricao

  extra = new_candidates.sample(3)
  extra.each do |c|
    apply = Apply.find_or_create_by!(candidate_id: c.id, job_id: job.id, account_id: ACCOUNT_ID) do |a|
      a.selective_process_id = [ screening, inscricao ].sample.id
      a.user_id = USER_ID
      a.cv_match = rand(30..55).to_f
      a.total_score = rand(25..50).to_f
    end
    apply.update_columns(
      created_at: rand(10..25).days.ago,
      updated_at: rand(8..20).days.ago
    )
  end
end

puts "✅ Funnel conversion data OK (high/low)"

feedback_data = [
  { sourcing: recent_sourcing, candidate: cand_joao, type: "like", reason: "Perfil alinhado com a vaga" },
  { sourcing: recent_sourcing, candidate: cand_maria, type: "dislike", reason: "Experiência insuficiente" },
  { sourcing: second_sourcing, candidate: cand_camila, type: "like", reason: "Excelente fit técnico" }
]

feedbacks_created = 0
feedback_data.each do |attrs|
  next unless attrs[:candidate] && attrs[:sourcing]

  CandidateFeedback.find_or_create_by!(
    reference_type: "Sourcing",
    reference_id: attrs[:sourcing].id,
    candidate_id: attrs[:candidate].id,
    account_id: ACCOUNT_ID
  ) do |cf|
    cf.feedback_type = attrs[:type]
    cf.reason = attrs[:reason]
    cf.user_id = USER_ID
  end
  feedbacks_created += 1
end

puts "✅ Candidate feedbacks OK (#{feedbacks_created})"

past_interviews = 0
[ job_backend, job_techlead ].compact.each do |job|
  evaluation = Evaluation.find_by(job_id: job.id, account_id: ACCOUNT_ID)
  next unless evaluation

  completed_evals = EvaluationCandidate.where(evaluation_id: evaluation.id, completed: true)
  completed_evals.each do |ec|
    existing = InterviewSession.find_by(candidate_id: ec.candidate_id, job_id: job.id, status: "completed")
    next if existing

    InterviewSession.find_or_create_by!(
      candidate_id: ec.candidate_id,
      job_id: job.id,
      evaluation_id: evaluation.id,
      status: "completed",
      account_id: ACCOUNT_ID
    ) do |is|
      is.token = SecureRandom.hex(16)
      is.evaluation_candidate_id = ec.id
      is.created_by_id = USER_ID
      is.interview_type = "voice"
      is.duration_minutes = 30
      is.language = "pt-BR"
      is.started_at = rand(3..14).days.ago
      is.completed_at = is.started_at + rand(20..40).minutes
      is.expires_at = is.started_at + 7.days
      is.score = rand(60..92).to_f
      is.recommendation = %w[recommended strongly_recommended].sample
      is.job_context = { title: job.title, department: job.department&.name }
      is.candidate_context = { name: ec.candidate&.name, role: ec.candidate&.role_name }
      is.questions_snapshot = [
        { question: "Conte sobre sua experiência profissional", type: "open" },
        { question: "Descreva um desafio técnico que enfrentou", type: "open" },
        { question: "Por que tem interesse nesta vaga?", type: "open" }
      ]
    end
    past_interviews += 1
  end
end

puts "✅ Completed interviews (no feedback) OK (#{past_interviews})"

week_start = Time.current.beginning_of_week
week_interviews = 0

interview_schedule = [
  { day: 0, hour: 10, candidate: cand_joao, job: job_python },
  { day: 1, hour: 14, candidate: cand_pedro, job: job_backend },
  { day: 2, hour: 11, candidate: cand_lucas, job: job_frontend },
  { day: 3, hour: 15, candidate: cand_rafael, job: job_techlead },
  { day: 4, hour: 10, candidate: cand_maria, job: job_pm }
]

interview_schedule.each do |data|
  next unless data[:candidate] && data[:job]

  scheduled_time = (week_start + data[:day].days).change(hour: data[:hour])
  evaluation = Evaluation.find_by(job_id: data[:job].id, account_id: ACCOUNT_ID)
  next unless evaluation

  apply = Apply.find_by(candidate_id: data[:candidate].id, job_id: data[:job].id, is_deleted: false)

  ec = EvaluationCandidate.find_or_create_by!(
    candidate_id: data[:candidate].id,
    evaluation_id: evaluation.id,
    account_id: ACCOUNT_ID
  ) do |e|
    e.job_id = data[:job].id
    e.user_id = USER_ID
    e.uid = SecureRandom.uuid
    e.candidate_uid = data[:candidate].uid
    e.apply_id = apply&.id
  end

  existing = InterviewSession.find_by(
    candidate_id: data[:candidate].id,
    job_id: data[:job].id,
    evaluation_id: evaluation.id,
    status: "pending",
    account_id: ACCOUNT_ID
  )
  next if existing

  InterviewSession.create!(
    token: SecureRandom.hex(16),
    status: "pending",
    account_id: ACCOUNT_ID,
    evaluation_id: evaluation.id,
    evaluation_candidate_id: ec.id,
    apply_id: apply&.id,
    candidate_id: data[:candidate].id,
    job_id: data[:job].id,
    created_by_id: USER_ID,
    interview_type: "voice",
    duration_minutes: 30,
    language: "pt-BR",
    expires_at: scheduled_time + 7.days,
    job_context: { title: data[:job].title, department: data[:job].department&.name },
    candidate_context: { name: data[:candidate].name, role: data[:candidate].role_name },
    questions_snapshot: [
      { question: "Conte sobre sua experiência profissional", type: "open" },
      { question: "Quais são seus principais pontos fortes?", type: "open" },
      { question: "Por que tem interesse nesta vaga?", type: "open" }
    ],
    created_at: scheduled_time - 2.days
  )
  week_interviews += 1
end

puts "✅ This week's interviews OK (#{week_interviews})"

[ job_backend, job_frontend, job_techlead, job_python, job_pm, job_devops, job_ds, job_dados ].compact.each do |job|
  stages = SelectiveProcess.where(job_id: job.id, is_deleted: false).order(:position)
  applies_count = Apply.where(job_id: job.id, is_deleted: false).count
  rejected_count = Apply.joins(:selective_process).where(job_id: job.id, is_deleted: false, selective_processes: { status: :rejected }).count

  snapshot_data = {
    total_applies: applies_count,
    by_stage: {},
    conversion_rates: {},
    avg_time_per_stage: {},
    rejection_rate: applies_count > 0 ? (rejected_count.to_f / applies_count * 100).round(1) : 0
  }

  prev_count = applies_count
  stages.each do |stage|
    count = Apply.where(job_id: job.id, selective_process_id: stage.id, is_deleted: false).count
    applies_in_stage = Apply.where(job_id: job.id, selective_process_id: stage.id, is_deleted: false)

    avg_days = if applies_in_stage.any?
                 applies_in_stage.average("EXTRACT(EPOCH FROM (COALESCE(updated_at, created_at) - created_at)) / 86400").to_f.round(1)
    else
                 0
    end

    snapshot_data[:by_stage][stage.name] = count
    snapshot_data[:conversion_rates][stage.name] = prev_count > 0 ? (count.to_f / prev_count * 100).round(1) : 0
    snapshot_data[:avg_time_per_stage][stage.name] = avg_days
    prev_count = count if count > 0
  end

  JobAnalyticsSnapshot.find_or_create_by!(job_id: job.id) do |jas|
    jas.snapshot_data = snapshot_data
    jas.computed_at = Time.current
    jas.version = 1
  end
end

puts "✅ Job analytics snapshots OK"

Notification.where(user_id: USER_ID, status: "pending", notification_type: "briefing").update_all(status: "read") rescue nil
AgentNotification.where(user_id: USER_ID, status: "pending", notification_type: "briefing").update_all(status: "read") rescue nil

total_applies = Apply.where(is_deleted: false).count
active_jobs = Job.where(is_deleted: false, is_active: true).count
pending_interviews = InterviewSession.where(status: "pending").count

briefing_key = "agent_briefing_#{Time.current.to_date}"
unless AgentNotification.find_by(alert_key: briefing_key)
  AgentNotification.create!(
    user_id: USER_ID,
    notification_type: "briefing",
    channel: "web",
    status: "pending",
    content: "📋 Briefing #{Time.current.strftime('%d/%m/%Y')} — #{active_jobs} vagas ativas, #{total_applies} candidaturas no pipeline, #{pending_interviews} entrevistas agendadas. #{Apply.where(is_deleted: false).where('updated_at < ?', 7.days.ago).count} candidatos parados há mais de 7 dias precisam de atenção.",
    alert_key: briefing_key,
    metadata: {
      active_jobs: active_jobs,
      total_applies: total_applies,
      pending_interviews: pending_interviews,
      aging_applies: Apply.where(is_deleted: false).where("updated_at < ?", 7.days.ago).count
    },
    created_at: Time.current.beginning_of_day + 8.hours
  )
end

puts "✅ Briefing notification OK"

Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Rails.logger.info "✅ [AgentTestData] L7-L9 agent test data seed completed!"
Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

puts ""
puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
puts "✅ L7-L9 AGENT TEST DATA COMPLETE"
puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
puts ""
puts "Data created:"
puts "  • 15 extra candidates (aging scenarios)"
puts "  • 5 sourced profiles imported but NOT applied"
puts "  • #{aging_applies_created} aging applies (stuck >7 days)"
puts "  • #{evals_created} evaluations with mixed completion rates"
puts "  • #{paused_created} paused jobs (>30 days inactive)"
puts "  • #{rejected_with_interview} interviews for rejected candidates"
puts "  • #{past_interviews} completed interviews (no feedback)"
puts "  • #{week_interviews} interviews scheduled this week"
puts "  • #{feedbacks_created} candidate feedbacks"
puts "  • Job analytics snapshots for all seed jobs"
puts "  • High/low funnel conversion data"
puts "  • Briefing notification"
puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
