# frozen_string_literal: true

return unless Rails.env.development?

ACCOUNT_ID = 1
USER_ID = 1
TENANT = "public"

account = Account.find(ACCOUNT_ID)
user = User.find(USER_ID)

Apartment::Tenant.switch!(TENANT)

Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Rails.logger.info "🚀 [SampleData] Starting development sample data seed"
Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

tech_dept = Department.find_or_create_by!(name: "Tecnologia", account_id: ACCOUNT_ID) do |d|
  d.level = 0
  d.description = "Departamento de Tecnologia e Inovação"
  d.color = "#3B82F6"
  d.headcount = 30
end

eng_dept = Department.find_or_create_by!(name: "Engineering", account_id: ACCOUNT_ID) do |d|
  d.parent_department_id = tech_dept.id
  d.level = 1
  d.description = "Software Engineering"
  d.color = "#6366F1"
  d.headcount = 20
end

product_dept = Department.find_or_create_by!(name: "Product", account_id: ACCOUNT_ID) do |d|
  d.level = 0
  d.description = "Product Management"
  d.color = "#8B5CF6"
  d.headcount = 8
end

sales_dept = Department.find_or_create_by!(name: "Sales", account_id: ACCOUNT_ID) do |d|
  d.level = 0
  d.description = "Sales & Business Development"
  d.color = "#10B981"
  d.headcount = 15
end

people_dept = Department.find_or_create_by!(name: "People & Culture", account_id: ACCOUNT_ID) do |d|
  d.level = 0
  d.description = "People, HR & Culture"
  d.color = "#F59E0B"
  d.headcount = 10
end

puts "✅ Departments OK"

CATEGORY_MAP = {
  "Aprovação" => 1,
  "Rejeição" => 2,
  "Agendamento" => 3,
  "Follow-up" => 4,
  "Feedback" => 5,
  "Contato Inicial" => 6,
  "Pós-Entrevista" => 7
}.freeze

email_templates_data = [
  {
    name: "Boas-vindas ao Processo Seletivo",
    subject: "Bem-vindo(a) ao processo seletivo — {{job_title}}",
    category_id: CATEGORY_MAP["Contato Inicial"],
    content: "Olá {{candidate_name}},\n\nAgradecemos seu interesse na vaga de {{job_title}}.\n\nEm breve entraremos em contato com os próximos passos.\n\nAtenciosamente,\n{{user_name}}"
  },
  {
    name: "Agendamento de Entrevista",
    subject: "Entrevista agendada — {{job_title}}",
    category_id: CATEGORY_MAP["Agendamento"],
    content: "Olá {{candidate_name}},\n\nSua entrevista para a vaga de {{job_title}} foi agendada.\n\nPor favor, confirme sua disponibilidade.\n\nAtenciosamente,\n{{user_name}}"
  },
  {
    name: "Aprovação — Próxima Etapa",
    subject: "Parabéns! Você avançou no processo seletivo",
    category_id: CATEGORY_MAP["Aprovação"],
    content: "Olá {{candidate_name}},\n\nTemos o prazer de informar que você avançou para a próxima etapa do processo seletivo para {{job_title}}.\n\nEntraremos em contato em breve.\n\nAtenciosamente,\n{{user_name}}"
  },
  {
    name: "Feedback — Não Aprovado",
    subject: "Atualização sobre o processo seletivo",
    category_id: CATEGORY_MAP["Rejeição"],
    content: "Olá {{candidate_name}},\n\nAgradecemos sua participação no processo seletivo para {{job_title}}. Infelizmente, não seguiremos com sua candidatura neste momento.\n\nDesejamos sucesso.\n\nAtenciosamente,\n{{user_name}}"
  },
  {
    name: "Proposta de Trabalho",
    subject: "Proposta de trabalho — {{job_title}}",
    category_id: CATEGORY_MAP["Aprovação"],
    content: "Olá {{candidate_name}},\n\nTemos o prazer de lhe apresentar uma proposta para a posição de {{job_title}}.\n\nAguardamos seu retorno.\n\nAtenciosamente,\n{{user_name}}"
  },
  {
    name: "Follow-up Avaliação",
    subject: "Lembrete: avaliação pendente — {{job_title}}",
    category_id: CATEGORY_MAP["Follow-up"],
    content: "Olá {{candidate_name}},\n\nNotamos que sua avaliação para a vaga de {{job_title}} ainda está pendente. Caso precise de ajuda, estamos à disposição.\n\nAtenciosamente,\n{{user_name}}",
    is_automated: true,
    trigger_event: "evaluation_pending",
    delay_hours: 48
  },
  {
    name: "Pós-Entrevista — Agradecimento",
    subject: "Obrigado pela entrevista — {{job_title}}",
    category_id: CATEGORY_MAP["Pós-Entrevista"],
    content: "Olá {{candidate_name}},\n\nAgradecemos por participar da entrevista para {{job_title}}. Foi um prazer conhecê-lo(a).\n\nRetornaremos em breve com os próximos passos.\n\nAtenciosamente,\n{{user_name}}"
  },
  {
    name: "Feedback Pós-Entrevista",
    subject: "Feedback da sua entrevista — {{job_title}}",
    category_id: CATEGORY_MAP["Feedback"],
    content: "Olá {{candidate_name}},\n\nGostaríamos de compartilhar o feedback da sua entrevista para {{job_title}}.\n\nEstamos à disposição para esclarecer qualquer dúvida.\n\nAtenciosamente,\n{{user_name}}"
  }
]

email_templates_data.each do |attrs|
  EmailTemplate.find_or_create_by!(name: attrs[:name], account_id: ACCOUNT_ID) do |t|
    t.subject = attrs[:subject]
    t.category_id = attrs[:category_id]
    t.content = attrs[:content]
    t.user_id = USER_ID
    t.is_automated = attrs[:is_automated] || false
    t.trigger_event = attrs[:trigger_event]
    t.delay_hours = attrs[:delay_hours]
  end
end

puts "✅ Email Templates OK"

skill_names = %w[
  Ruby Rails Python Django JavaScript TypeScript React Vue.js Angular Node.js
  PostgreSQL MySQL MongoDB Redis Elasticsearch Docker Kubernetes AWS GCP Azure
  Java Spring Kotlin Swift Go Rust C++ C# .NET PHP Laravel
  GraphQL REST API Git CI/CD Terraform Ansible Figma Sketch
  Scrum Kanban Agile SAFe Product\ Management Data\ Science Machine\ Learning
  Deep\ Learning NLP Computer\ Vision TensorFlow PyTorch Pandas NumPy
  SQL NoSQL ETL Data\ Engineering Power\ BI Tableau Excel
  Leadership Communication Teamwork Problem\ Solving Critical\ Thinking
]

skill_names.each do |name|
  Skill.find_or_create_by!(name: name, account_id: ACCOUNT_ID)
end

puts "✅ Skills OK"

SAFE_EMAIL = "victhor_root@hotmail.com"
SAFE_PHONE = "18996041211"

candidate_data = [
  { name: "João Silva", role_name: "Senior Software Engineer", current_company: "Tech Corp", city: "São Paulo", state: "SP" },
  { name: "Maria Santos", role_name: "Product Manager", current_company: "Startup XYZ", city: "São Paulo", state: "SP" },
  { name: "Pedro Costa", role_name: "DevOps Engineer", current_company: "Cloud Solutions", city: "Rio de Janeiro", state: "RJ" },
  { name: "Ana Oliveira", role_name: "Frontend Developer", current_company: "Digital Agency", city: "Curitiba", state: "PR" },
  { name: "Lucas Pereira", role_name: "Backend Developer", current_company: "FinTech Corp", city: "Belo Horizonte", state: "MG" },
  { name: "Camila Rodrigues", role_name: "Data Scientist", current_company: "DataCo", city: "São Paulo", state: "SP" },
  { name: "Rafael Almeida", role_name: "Tech Lead", current_company: "Enterprise Tech", city: "Florianópolis", state: "SC" },
  { name: "Juliana Fernandes", role_name: "UX Designer", current_company: "Design Studio", city: "Porto Alegre", state: "RS" },
  { name: "Fernando Lima", role_name: "QA Engineer", current_company: "Quality First", city: "Campinas", state: "SP" },
  { name: "Beatriz Martins", role_name: "Scrum Master", current_company: "Agile Corp", city: "São Paulo", state: "SP" }
]

sample_candidates = candidate_data.map do |attrs|
  Candidate.find_or_create_by!(name: attrs[:name], account_id: ACCOUNT_ID) do |c|
    c.uid = SecureRandom.uuid
    c.role_name = attrs[:role_name]
    c.current_company = attrs[:current_company]
    c.city = attrs[:city]
    c.state = attrs[:state]
    c.country = "BR"
    c.source = "manual"
    c.completed_register = true
    c.accept_terms = true
    c.linkedin = "https://linkedin.com/in/#{attrs[:name].parameterize}"
    c.position_level = %w[Senior Pleno Junior].sample
    c.current_salary = rand(8000..25000).round(-2)
    c.clt_expectation = rand(10000..30000).round(-2)
  end.tap do |c|
    c.update_columns(email: SAFE_EMAIL, mobile_phone: SAFE_PHONE)
  end
end

puts "✅ Candidates OK (#{sample_candidates.size})"

job_data = [
  { title: "Desenvolvedor(a) Backend Ruby on Rails", department: eng_dept, seniority: 2, employment_type: 0, city: "São Paulo", state: "SP", skills: %w[Ruby Rails PostgreSQL Redis Docker] },
  { title: "Desenvolvedor(a) Frontend Vue.js", department: eng_dept, seniority: 2, employment_type: 0, city: "São Paulo", state: "SP", skills: %w[JavaScript Vue.js TypeScript CSS HTML] },
  { title: "Tech Lead Full Stack", department: eng_dept, seniority: 5, employment_type: 0, city: "São Paulo", state: "SP", skills: %w[Ruby Rails Vue.js PostgreSQL Docker Kubernetes] },
  { title: "Product Manager", department: product_dept, seniority: 2, employment_type: 0, city: "São Paulo", state: "SP", skills: %w[Product\ Management Scrum Agile] },
  { title: "SDR - Sales Development Representative", department: sales_dept, seniority: 0, employment_type: 0, city: "São Paulo", state: "SP", skills: %w[Communication Leadership] },
  { title: "Desenvolvedor(a) Python Sênior", department: eng_dept, seniority: 2, employment_type: 0, city: "Rio de Janeiro", state: "RJ", skills: %w[Python Django PostgreSQL Docker AWS] },
  { title: "DevOps Engineer", department: eng_dept, seniority: 2, employment_type: 1, city: "Remote", state: "SP", skills: %w[Docker Kubernetes AWS Terraform CI/CD] },
  { title: "Data Scientist", department: tech_dept, seniority: 1, employment_type: 0, city: "São Paulo", state: "SP", skills: %w[Python Machine\ Learning SQL Data\ Science] },
  { title: "Analista de RH - Business Partner", department: people_dept, seniority: 1, employment_type: 0, city: "São Paulo", state: "SP", skills: %w[Communication Leadership] },
  { title: "Analista de Dados", department: tech_dept, seniority: 1, employment_type: 0, city: "Belo Horizonte", state: "MG", skills: %w[SQL Python Power\ BI Excel] }
]

sample_jobs = job_data.map do |attrs|
  job = Job.find_or_initialize_by(title: attrs[:title], account_id: ACCOUNT_ID, user_id: USER_ID, is_deleted: false)

  if job.new_record?
    job.assign_attributes(
      description: "Vaga para #{attrs[:title]}. Buscamos profissionais qualificados e motivados para integrar nosso time.",
      department_id: attrs[:department].id,
      seniority: attrs[:seniority],
      employment_type: attrs[:employment_type],
      city: attrs[:city],
      state: attrs[:state],
      country: "BR",
      is_active: true,
      is_remote: attrs[:city] == "Remote",
      workplace_type: attrs[:city] == "Remote" ? "remote" : "hybrid",
      published_date: rand(1..30).days.ago,
      application_deadline: rand(15..60).days.from_now,
      responsibilities: [
        "Desenvolver e manter soluções de alta qualidade",
        "Colaborar com times multidisciplinares",
        "Participar de code reviews e discussões técnicas",
        "Contribuir para melhoria contínua dos processos"
      ]
    )
    job.save!

    stages = [
      { name: "Inscrição", status: :web_submission, position: 0 },
      { name: "Triagem", status: :screening, position: 1 },
      { name: "Entrevista Técnica", status: :interview, position: 2 },
      { name: "Entrevista Final", status: :interview, position: 3 },
      { name: "Contratado", status: :hired, position: 4 },
      { name: "Reprovado", status: :rejected, position: 5 }
    ]

    sps = stages.map do |stage|
      SelectiveProcess.create!(
        name: stage[:name],
        status: stage[:status],
        position: stage[:position],
        job_id: job.id,
        account_id: ACCOUNT_ID,
        uid: SecureRandom.uuid
      )
    end

    attrs[:skills]&.each do |skill_name|
      skill = Skill.find_or_create_by!(name: skill_name, account_id: ACCOUNT_ID)
      SkillRelationship.find_or_create_by!(
        skill_id: skill.id,
        reference_type: "Job",
        reference_id: job.id,
        account_id: ACCOUNT_ID
      )
    end
  end

  job
end

puts "✅ Jobs OK (#{sample_jobs.size})"

recent_jobs = sample_jobs.first(6)
applies_created = 0

recent_jobs.each_with_index do |job, job_idx|
  stages = SelectiveProcess.where(job_id: job.id, is_deleted: false).order(:position)
  next if stages.empty?

  candidates_for_job = sample_candidates.rotate(job_idx).first(rand(3..6))

  candidates_for_job.each_with_index do |candidate, i|
    stage = stages[i % stages.size]

    apply = Apply.find_or_create_by!(
      candidate_id: candidate.id,
      job_id: job.id,
      account_id: ACCOUNT_ID
    ) do |a|
      a.selective_process_id = stage.id
      a.user_id = USER_ID
      a.cv_match = rand(50..98).to_f
      a.total_score = rand(40..95).to_f
      a.created_at = rand(1..72).hours.ago
    end

    applies_created += 1 if apply.previously_new_record?
  end
end

puts "✅ Applies OK (#{applies_created} new)"

now = Time.current

interview_data = [
  { offset_days: 1, hour: 10, status: "pending", candidate: sample_candidates[0], job: recent_jobs[0] },
  { offset_days: 1, hour: 14, status: "pending", candidate: sample_candidates[1], job: recent_jobs[1] },
  { offset_days: 2, hour: 11, status: "pending", candidate: sample_candidates[2], job: recent_jobs[2] },
  { offset_days: 3, hour: 15, status: "pending", candidate: sample_candidates[3], job: recent_jobs[3] },
  { offset_days: 0, hour: 16, status: "pending", candidate: sample_candidates[4], job: recent_jobs[0] },
  { offset_days: -1, hour: 10, status: "completed", candidate: sample_candidates[5], job: recent_jobs[1] }
]

interviews_created = 0
interview_data.each do |data|
  interview_time = (now.beginning_of_day + data[:offset_days].days).change(hour: data[:hour])
  job = data[:job]
  candidate = data[:candidate]

  evaluation = Evaluation.find_or_create_by!(
    job_id: job.id,
    name: "Entrevista - #{job.title}",
    account_id: ACCOUNT_ID
  ) do |e|
    sp = SelectiveProcess.find_by(job_id: job.id, status: :interview, is_deleted: false)
    e.selective_process_id = sp&.id
    e.user_id = USER_ID
    e.status = true
    e.position = 0
    e.description = "Entrevista para #{job.title}"
    e.is_main = true
    e.time = 60
    e.uid = SecureRandom.uuid
    e.is_chatbot = false
    e.ai_enabled = true
  end

  apply = Apply.find_by(candidate_id: candidate.id, job_id: job.id)

  eval_candidate = EvaluationCandidate.find_or_create_by!(
    candidate_id: candidate.id,
    evaluation_id: evaluation.id,
    account_id: ACCOUNT_ID
  ) do |ec|
    ec.apply_id = apply&.id
    ec.job_id = job.id
    ec.user_id = USER_ID
    ec.uid = SecureRandom.uuid
    ec.candidate_uid = candidate.uid
    ec.completed = data[:status] == "completed"
    ec.score = data[:status] == "completed" ? rand(60..95).to_f : nil
  end

  existing = InterviewSession.find_by(
    candidate_id: candidate.id,
    job_id: job.id,
    evaluation_id: evaluation.id,
    account_id: ACCOUNT_ID
  )

  next if existing

  InterviewSession.create!(
    token: SecureRandom.hex(16),
    status: data[:status],
    account_id: ACCOUNT_ID,
    evaluation_id: evaluation.id,
    evaluation_candidate_id: eval_candidate.id,
    apply_id: apply&.id,
    candidate_id: candidate.id,
    job_id: job.id,
    created_by_id: USER_ID,
    interview_type: "voice",
    duration_minutes: 30,
    language: "pt-BR",
    started_at: data[:status] == "completed" ? interview_time : nil,
    completed_at: data[:status] == "completed" ? interview_time + 35.minutes : nil,
    expires_at: interview_time + 7.days,
    job_context: { title: job.title, department: job.department&.name, seniority: job.seniority },
    candidate_context: { name: candidate.name, role: candidate.role_name, company: candidate.current_company },
    questions_snapshot: [
      { question: "Conte sobre sua experiência profissional", type: "open" },
      { question: "Quais são seus principais pontos fortes?", type: "open" },
      { question: "Por que tem interesse nesta vaga?", type: "open" }
    ],
    score: data[:status] == "completed" ? rand(65..92).to_f : nil,
    recommendation: data[:status] == "completed" ? "recommended" : nil,
    created_at: interview_time - 2.days
  )
  interviews_created += 1
end

puts "✅ Interviews OK (#{interviews_created} new)"

completed_evals = 0
sample_candidates.first(5).each_with_index do |candidate, i|
  job = recent_jobs[i % recent_jobs.size]
  evaluation = Evaluation.find_by(job_id: job.id, account_id: ACCOUNT_ID)
  next unless evaluation

  apply = Apply.find_by(candidate_id: candidate.id, job_id: job.id)

  ec = EvaluationCandidate.find_or_create_by!(
    candidate_id: candidate.id,
    evaluation_id: evaluation.id,
    account_id: ACCOUNT_ID
  ) do |e|
    e.apply_id = apply&.id
    e.job_id = job.id
    e.user_id = USER_ID
    e.uid = SecureRandom.uuid
    e.candidate_uid = candidate.uid
  end

  if !ec.completed
    ec.update!(
      completed: true,
      score: rand(55..95).to_f,
      evaluation_summary: "Candidato demonstrou bom domínio técnico e habilidades interpessoais adequadas.",
      updated_at: rand(1..20).hours.ago
    )
    completed_evals += 1
  end
end

puts "✅ Evaluation Candidates OK (#{completed_evals} completed)"

notification_data = [
  {
    notification_type: "briefing",
    status: "pending",
    content: "📋 Briefing #{now.strftime('%d/%m')} — #{applies_created} novas candidaturas para suas vagas. 3 entrevistas agendadas hoje.",
    metadata: { jobs_count: sample_jobs.size, new_applies: applies_created },
    created_at: now.beginning_of_day + 8.hours
  },
  {
    notification_type: "alert_deadline",
    status: "pending",
    content: "🟡 A vaga '#{recent_jobs[0]&.title}' tem prazo de fechamento em 5 dias. #{rand(3..8)} candidatos em triagem.",
    reference_type: "Job",
    reference_id: recent_jobs[0]&.id,
    created_at: 2.hours.ago
  },
  {
    notification_type: "alert_strong_fit",
    status: "pending",
    content: "🟢 #{sample_candidates[0].name} tem match de 92% com a vaga '#{recent_jobs[0]&.title}'. Recomendamos avançar para entrevista.",
    reference_type: "Candidate",
    reference_id: sample_candidates[0].id,
    created_at: 3.hours.ago
  },
  {
    notification_type: "alert_aging",
    status: "pending",
    content: "⚠️ #{sample_candidates[1].name} está na etapa Triagem da vaga '#{recent_jobs[1]&.title}' há 7 dias sem movimentação.",
    reference_type: "Apply",
    reference_id: Apply.find_by(candidate_id: sample_candidates[1].id, job_id: recent_jobs[1]&.id)&.id,
    created_at: 4.hours.ago
  },
  {
    notification_type: "alert_evaluation",
    status: "pending",
    content: "📝 #{sample_candidates[2].name} completou a avaliação para '#{recent_jobs[2]&.title}' com nota 87/100.",
    reference_type: "Candidate",
    reference_id: sample_candidates[2].id,
    created_at: 5.hours.ago
  },
  {
    notification_type: "alert_no_show",
    status: "pending",
    content: "🔴 #{sample_candidates[3].name} não compareceu à entrevista para '#{recent_jobs[3]&.title}' agendada para hoje.",
    reference_type: "Candidate",
    reference_id: sample_candidates[3].id,
    created_at: 6.hours.ago
  },
  {
    notification_type: "alert_stale_job",
    status: "pending",
    content: "📊 A vaga '#{recent_jobs[4]&.title}' está aberta há 30 dias sem novas candidaturas na última semana.",
    reference_type: "Job",
    reference_id: recent_jobs[4]&.id,
    created_at: 8.hours.ago
  },
  {
    notification_type: "alert_strong_fit",
    status: "pending",
    content: "🟢 #{sample_candidates[6].name} tem match de 88% com a vaga '#{recent_jobs[2]&.title}'. Perfil altamente qualificado.",
    reference_type: "Candidate",
    reference_id: sample_candidates[6].id,
    created_at: 10.hours.ago
  }
]

AgentNotification.where(user_id: USER_ID, status: "pending").update_all(status: "read", read_at: 1.day.ago)

notifications_created = 0
notification_data.each do |attrs|
  key = "sample_#{attrs[:notification_type]}_#{attrs[:reference_id]}_#{now.to_date}"
  existing = AgentNotification.find_by(alert_key: key)
  next if existing

  AgentNotification.create!(
    user_id: USER_ID,
    notification_type: attrs[:notification_type],
    channel: "web",
    status: attrs[:status],
    content: attrs[:content],
    reference_type: attrs[:reference_type],
    reference_id: attrs[:reference_id],
    alert_key: key,
    metadata: attrs[:metadata] || {},
    created_at: attrs[:created_at]
  )
  notifications_created += 1
end

puts "✅ Notifications OK (#{notifications_created} new, 8 unread)"

approval_data = [
  {
    reference_type: "Job",
    reference_id: recent_jobs[0]&.id,
    comments: "Solicitação de aprovação para publicação da vaga #{recent_jobs[0]&.title}",
    approval_level: 1
  },
  {
    reference_type: "Job",
    reference_id: recent_jobs[2]&.id,
    comments: "Aprovação necessária para abrir vaga de #{recent_jobs[2]&.title} — headcount adicional",
    approval_level: 1
  },
  {
    reference_type: "Job",
    reference_id: recent_jobs[5]&.id,
    comments: "Aprovação de orçamento para contratação — #{recent_jobs[5]&.title}",
    approval_level: 2
  }
]

approvals_created = 0
approval_data.each do |attrs|
  next unless attrs[:reference_id]

  existing = ApprovalRequest.find_by(
    reference_type: attrs[:reference_type],
    reference_id: attrs[:reference_id],
    approver_id: USER_ID,
    status: 0
  )
  next if existing

  ApprovalRequest.create!(
    account_id: ACCOUNT_ID,
    approver_id: USER_ID,
    requested_by_id: USER_ID,
    reference_type: attrs[:reference_type],
    reference_id: attrs[:reference_id],
    approval_level: attrs[:approval_level],
    status: 0,
    comments: attrs[:comments],
    expires_at: 7.days.from_now
  )
  approvals_created += 1
end

puts "✅ Approval Requests OK (#{approvals_created} pending)"

recent_jobs.each do |job|
  next if job.department_id.blank?

  dept = Department.find_by(id: job.department_id)
  next unless dept

  applies_count = Apply.where(job_id: job.id, is_deleted: false).count

  ActivityLog.create!(
    reference_type: "Job",
    reference_id: job.id,
    action: "update",
    changeset: { "is_active" => [ false, true ] },
    user_id: USER_ID,
    account_id: ACCOUNT_ID,
    category: "others",
    created_at: rand(1..48).hours.ago
  )
end

sample_candidates.first(5).each do |candidate|
  ActivityLog.create!(
    reference_type: "Candidate",
    reference_id: candidate.id,
    action: "create",
    changeset: { "name" => [ nil, candidate.name ] },
    user_id: USER_ID,
    account_id: ACCOUNT_ID,
    category: "others",
    created_at: rand(1..72).hours.ago
  )
end

Apply.where(job_id: recent_jobs.map(&:id), is_deleted: false)
     .where("created_at > ?", 48.hours.ago)
     .find_each do |apply|
  existing_log = ActivityLog.find_by(reference_type: "Apply", reference_id: apply.id, action: "create")
  next if existing_log

  ActivityLog.create!(
    reference_type: "Apply",
    reference_id: apply.id,
    action: "create",
    changeset: { "candidate_id" => [ nil, apply.candidate_id ], "job_id" => [ nil, apply.job_id ] },
    user_id: USER_ID,
    account_id: ACCOUNT_ID,
    category: "others",
    created_at: apply.created_at
  )
end

puts "✅ Activity Logs OK"

Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Rails.logger.info "✅ [SampleData] Development sample data seed completed!"
Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

puts ""
puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
puts "✅ SAMPLE DATA SEED COMPLETE"
puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
