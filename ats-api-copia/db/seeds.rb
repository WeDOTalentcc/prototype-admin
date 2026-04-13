# frozen_string_literal: true

# Seeds for WeDOTalent ATS
#
# Idempotent: safe to run multiple times (uses find_or_create_by!).
# Usage: bin/rails db:seed

puts "Seeding database..."

# ---------------------------------------------------------------------------
# 1. Base Account
# ---------------------------------------------------------------------------

account = Account.find_or_create_by!(name: "WeDOTalent Demo") do |a|
  a.tenant = "wedotalent-demo"
end
puts "Account: #{account.name} (id=#{account.id})"

# ---------------------------------------------------------------------------
# 2. Client Account
# ---------------------------------------------------------------------------

client = ClientAccount.find_or_create_by!(name: "WeDOTalent Demo") do |c|
  c.cnpj   = "12.345.678/0001-90" if c.respond_to?(:cnpj=)
  c.status = "active" if c.respond_to?(:status=)
end
puts "Client account: #{client.name} (id=#{client.id})"

# ---------------------------------------------------------------------------
# 3. Admin User
# ---------------------------------------------------------------------------

admin = User.find_or_create_by!(email: "admin@wedotalent.com") do |u|
  u.password = "password123"
  u.account  = account
  u.name     = "Admin WeDO"
  u.role     = "admin"
  u.status   = "active"
end
puts "Admin user: #{admin.email} (id=#{admin.id})"

# ---------------------------------------------------------------------------
# 4. Company Profile
# ---------------------------------------------------------------------------

company_profile = CompanyProfile.find_or_create_by!(client_account_id: client.id) do |cp|
  cp.name          = "WeDOTalent"
  cp.industry      = "Technology" if cp.respond_to?(:industry=)
  cp.description   = "Plataforma de recrutamento inteligente com IA" if cp.respond_to?(:description=)
  cp.website       = "https://wedotalent.com" if cp.respond_to?(:website=)
  cp.employee_count = 50 if cp.respond_to?(:employee_count=)
  cp.founded_year  = 2023 if cp.respond_to?(:founded_year=)
end
puts "Company profile: #{company_profile.name} (id=#{company_profile.id})"

# ---------------------------------------------------------------------------
# 5. Departments
# ---------------------------------------------------------------------------

departments = %w[Engineering Product Design Marketing Sales]
departments.each do |dept_name|
  Department.find_or_create_by!(company_id: company_profile.id, name: dept_name)
end
puts "Departments: #{departments.join(', ')}"

# ---------------------------------------------------------------------------
# 6. Sample Jobs (3)
# ---------------------------------------------------------------------------

job_definitions = [
  {
    title: "Senior Backend Engineer",
    description: "We are looking for an experienced Backend Engineer to design and build scalable APIs and microservices. You will work with Ruby on Rails, PostgreSQL, and Redis in a collaborative agile environment.",
    department: "Engineering",
    seniority_level: "senior",
    employment_type: "clt",
    status: "active"
  },
  {
    title: "Senior Frontend Engineer",
    description: "We are looking for a Frontend Engineer passionate about building beautiful, performant user interfaces. You will work with React, TypeScript, and modern CSS to deliver an exceptional candidate experience.",
    department: "Product",
    seniority_level: "senior",
    employment_type: "clt",
    status: "active"
  },
  {
    title: "Senior Full Stack Engineer",
    description: "We are looking for a Full Stack Engineer who thrives across the entire stack. You will build features end-to-end using Rails, React, and PostgreSQL, collaborating closely with Product and Design.",
    department: "Design",
    seniority_level: "senior",
    employment_type: "clt",
    status: "active"
  }
]

job_definitions.each do |attrs|
  Job.find_or_create_by!(title: attrs[:title]) do |j|
    j.description     = attrs[:description]
    j.user            = admin
    j.account         = account
    j.status          = attrs[:status]
    j.department      = attrs[:department]
    j.seniority_level = attrs[:seniority_level]
    j.employment_type = attrs[:employment_type]
  end
end
puts "Jobs: #{job_definitions.map { |j| j[:title] }.join(', ')}"

# ---------------------------------------------------------------------------
# 7. Sample Candidates (5)
# ---------------------------------------------------------------------------

candidate_definitions = [
  {
    name: "Maria Silva",
    email: "maria@example.com",
    seniority_level: "senior",
    role_name: "Backend Engineer",
    technical_skills: %w[Ruby Python PostgreSQL],
    mobile_phone: "+5511999990001"
  },
  {
    name: "Joao Santos",
    email: "joao@example.com",
    seniority_level: "mid",
    role_name: "Frontend Developer",
    technical_skills: %w[React TypeScript CSS],
    mobile_phone: "+5511999990002"
  },
  {
    name: "Ana Oliveira",
    email: "ana@example.com",
    seniority_level: "junior",
    role_name: "Full Stack Developer",
    technical_skills: %w[JavaScript Rails Node.js],
    mobile_phone: "+5511999990003"
  },
  {
    name: "Pedro Costa",
    email: "pedro@example.com",
    seniority_level: "senior",
    role_name: "DevOps Engineer",
    technical_skills: %w[Docker Kubernetes AWS],
    mobile_phone: "+5511999990004"
  },
  {
    name: "Lucia Ferreira",
    email: "lucia@example.com",
    seniority_level: "mid",
    role_name: "Data Engineer",
    technical_skills: %w[Python SQL Spark],
    mobile_phone: "+5511999990005"
  }
]

candidate_definitions.each do |attrs|
  Candidate.find_or_create_by!(email: attrs[:email]) do |c|
    c.name             = attrs[:name]
    c.account          = account
    c.seniority_level  = attrs[:seniority_level]
    c.role_name        = attrs[:role_name]
    c.technical_skills = attrs[:technical_skills]
    c.mobile_phone     = attrs[:mobile_phone]
  end
end
puts "Candidates: #{candidate_definitions.map { |c| c[:name] }.join(', ')}"

# ---------------------------------------------------------------------------
# 8. Email Templates
# ---------------------------------------------------------------------------

email_templates = [
  {
    name: "Candidatura Recebida",
    subject: "Recebemos sua candidatura!",
    body_html: "<p>Ola {{candidate_name}},</p><p>Recebemos sua candidatura para a vaga de <strong>{{job_title}}</strong>. Nossa equipe esta analisando seu perfil e entraremos em contato em breve.</p><p>Atenciosamente,<br/>Equipe WeDOTalent</p>"
  },
  {
    name: "Entrevista Agendada",
    subject: "Entrevista agendada - {{job_title}}",
    body_html: "<p>Ola {{candidate_name}},</p><p>Sua entrevista para a vaga de <strong>{{job_title}}</strong> foi agendada para {{interview_date}} as {{interview_time}}.</p><p>Link: {{meeting_url}}</p><p>Atenciosamente,<br/>Equipe WeDOTalent</p>"
  },
  {
    name: "Feedback Negativo",
    subject: "Atualizacao sobre sua candidatura - {{job_title}}",
    body_html: "<p>Ola {{candidate_name}},</p><p>Agradecemos seu interesse na vaga de <strong>{{job_title}}</strong>. Apos analise cuidadosa, decidimos seguir com outros candidatos neste momento.</p><p>Desejamos sucesso em sua jornada profissional.</p><p>Atenciosamente,<br/>Equipe WeDOTalent</p>"
  },
  {
    name: "Proposta",
    subject: "Proposta de trabalho - {{job_title}}",
    body_html: "<p>Ola {{candidate_name}},</p><p>Temos o prazer de informar que voce foi selecionado(a) para a vaga de <strong>{{job_title}}</strong>! Em anexo, segue nossa proposta formal.</p><p>Atenciosamente,<br/>Equipe WeDOTalent</p>"
  }
]

email_templates.each do |attrs|
  EmailTemplate.find_or_create_by!(name: attrs[:name], company_id: client.id.to_s) do |et|
    et.subject   = attrs[:subject]
    et.body_html = attrs[:body_html] if et.respond_to?(:body_html=)
    et.category  = "recruitment" if et.respond_to?(:category=)
    et.is_active = true if et.respond_to?(:is_active=)
  end
end
puts "Email templates: #{email_templates.map { |t| t[:name] }.join(', ')}"

# ---------------------------------------------------------------------------
# 9. Sample Applies (connect candidates to jobs)
# ---------------------------------------------------------------------------

jobs = Job.where(account: account).limit(3).to_a
candidates = Candidate.where(account: account).limit(5).to_a

if jobs.any? && candidates.any?
  applies_created = 0
  candidates.each_with_index do |candidate, idx|
    job = jobs[idx % jobs.size]
    sp = SelectiveProcess.where(job_id: job.id).order(:position).first
    next unless sp

    Apply.find_or_create_by!(candidate: candidate, job: job) do |a|
      a.selective_process = sp
      a.status = "active"
    end
    applies_created += 1
  end
  puts "Applies created: #{applies_created}"
end

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------

puts
puts "Seeds created successfully!"
puts "  Admin login: admin@wedotalent.com / password123"
