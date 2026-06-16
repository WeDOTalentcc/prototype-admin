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
# 10. Demo WSI Screening (fully populated for screenshot/demo)
# ---------------------------------------------------------------------------
#
# The recruiter "modal de triagem" (TriagemDetailsModal in plataforma-lia)
# reads completed screenings from the wsi_* tables that the Python
# lia-agent-system owns (wsi_sessions, wsi_questions, wsi_response_analyses,
# wsi_results, wsi_reports, wsi_feedbacks). The candidate-side
# conversation lives in `triagem_sessions` / `triagem_messages`. The live
# schema for both groups is owned by lia-agent-system (see
# `lia-agent-system/libs/models/lia_models/triagem.py`,
# `lia-agent-system/database/wsi_schema_corrected.sql` and
# `lia-agent-system/database/TRIAGEM_OWNERSHIP.md`). Rails must not
# create or alter these tables.
#
# Because these tables are owned by the Python app:
#   * we don't touch them through ActiveRecord models (none exist here);
#   * we gate every block on `table_exists?` so `db:seed` stays safe
#     against a Rails-only DB where the Python app hasn't created its
#     tables yet, and it just no-ops with an informational message;
#   * we use deterministic UUIDs + ON CONFLICT DO NOTHING everywhere so
#     re-runs (and resumes after a partial failure) don't duplicate rows;
#   * we set `app.company_id` GUC because `job_vacancies` and
#     `triagem_sessions` have FORCED row-level security on company_id.

demo_company_id     = "00000000-0000-4000-a000-000000000001"  # matches existing "Demo Company"
demo_candidate_id   = "11111111-1111-4111-8111-111111111111"
demo_job_vacancy_id = "22222222-2222-4222-8222-222222222222"
demo_session_id     = "33333333-3333-4333-8333-333333333333"
demo_result_id      = "44444444-4444-4444-8444-444444444441"
demo_report_id      = "44444444-4444-4444-8444-444444444442"
demo_feedback_id    = "44444444-4444-4444-8444-444444444443"
demo_triagem_id     = "55555555-5555-4555-8555-555555555555"

demo_candidate_name  = "Maria Silva"
demo_candidate_email = "maria@example.com"
demo_job_title       = "Senior Backend Engineer"

conn = ActiveRecord::Base.connection
q    = ->(v) { conn.quote(v) }

# This block depends on the Python lia-agent-system schema being live
# (wsi_*, candidate_jobs, Python-shape candidates/job_vacancies with
# `company_id`). On a Rails-only DB those tables/columns won't exist, so
# we gate the entire block and just log a skip, leaving `db:seed` happy.
demo_schema_ok =
  conn.table_exists?("wsi_sessions") &&
  conn.table_exists?("candidates") &&
  conn.table_exists?("job_vacancies") &&
  conn.table_exists?("candidate_jobs") &&
  conn.column_exists?("candidates", "company_id") &&
  conn.column_exists?("job_vacancies", "company_id")

if demo_schema_ok

  # Honour RLS for the tenant-scoped tables we touch below.
  conn.execute("SELECT set_config('app.company_id', #{q.call(demo_company_id)}, false)")

  # If the existing Rails AR seed already created Maria via `Candidate`,
  # reuse her real UUID instead of forcing a parallel candidate row, so
  # the Kanban and modal show the same candidate.
  existing_maria_id = conn.select_value(
    "SELECT id::text FROM candidates WHERE email = #{q.call(demo_candidate_email)} LIMIT 1"
  )
  demo_candidate_id = existing_maria_id if existing_maria_id

  # 1) Candidate (shared `candidates` table is UUID-keyed; insert only if missing).
  conn.execute(<<~SQL)
    INSERT INTO candidates (id, name, email, mobile_phone, current_title,
                            seniority_level, source, company_id)
    VALUES (#{q.call(demo_candidate_id)}, #{q.call(demo_candidate_name)},
            #{q.call(demo_candidate_email)}, '+5511999990001',
            'Backend Engineer', 'senior', 'seed', #{q.call(demo_company_id)})
    ON CONFLICT (id) DO NOTHING
  SQL

  # 2) Matching job_vacancy (RLS-scoped on company_id).
  conn.execute(<<~SQL)
    INSERT INTO job_vacancies (id, company_id, title, status, department,
                               seniority_level, employment_type,
                               created_at, updated_at)
    VALUES (#{q.call(demo_job_vacancy_id)}, #{q.call(demo_company_id)},
            #{q.call(demo_job_title)}, 'Ativa', 'Engineering',
            'senior', 'clt', NOW(), NOW())
    ON CONFLICT (id) DO NOTHING
  SQL

  # 3) Application link so the candidate appears on the Kanban for the vaga.
  demo_candidate_job_id = "77777777-7777-4777-8777-777777777777"
  conn.execute(<<~SQL)
    INSERT INTO candidate_jobs (id, candidate_id, job_vacancy_id,
                                status, source, applied_at, created_at, updated_at)
    VALUES (#{q.call(demo_candidate_job_id)}, #{q.call(demo_candidate_id)},
            #{q.call(demo_job_vacancy_id)}, 'screening', 'seed',
            NOW(), NOW(), NOW())
    ON CONFLICT (id) DO NOTHING
  SQL

# 4) WSI session + 5 questions + 5 response analyses + result + report + feedback.
#    Owned by lia-agent-system; gate on table existence so a Rails-only DB
#    just no-ops gracefully.
if conn.table_exists?("wsi_sessions") &&
   conn.table_exists?("wsi_questions") &&
   conn.table_exists?("wsi_response_analyses") &&
   conn.table_exists?("wsi_results") &&
   conn.table_exists?("wsi_reports") &&
   conn.table_exists?("wsi_feedbacks")
  conn.execute(<<~SQL)
    INSERT INTO wsi_sessions (id, candidate_id, job_vacancy_id, screening_type,
                              mode, status, question_set_version, question_set_id,
                              started_at, completed_at, created_at, updated_at)
    VALUES (#{q.call(demo_session_id)}, #{q.call(demo_candidate_id)},
            #{q.call(demo_job_vacancy_id)}, 'chat', 'compact', 'completed',
            1, 'seed-backend-v1',
            NOW() - INTERVAL '20 minutes', NOW() - INTERVAL '5 minutes',
            NOW() - INTERVAL '20 minutes', NOW())
    ON CONFLICT (id) DO NOTHING
  SQL

  questions = [
    { id: "66666666-6666-4666-8666-000000000001",
      competency: "Ruby on Rails",
      framework: "Bloom",
      qtype: "contextual",
      text: "Conte sobre uma API que voce projetou no Rails. Quais decisoes de modelagem voce tomou e por que?",
      weight: 1.0,
      seq: 1,
      response: "No ultimo projeto desenhei uma API REST para gestao de pedidos. Separei agregados de Order e LineItem, usei service objects para regras de negocio e Sidekiq para o pos-processamento. Optei por chaves UUID para evitar leak de cardinalidade.",
      auto: 4.5, ctx: 4.7, bloom: 5, dreyfus: 4, score: 4.6,
      evidences: ["Cita service objects", "Justifica uso de UUID", "Mencao a Sidekiq"],
      red_flags: [],
      justification: "Resposta estruturada, com tradeoffs explicitos e exemplos concretos." },
    { id: "66666666-6666-4666-8666-000000000002",
      competency: "PostgreSQL",
      framework: "Dreyfus",
      qtype: "microcase",
      text: "Uma query de relatorio passou de 200ms para 8s apos uma migration. Como voce investigaria?",
      weight: 1.0,
      seq: 2,
      response: "Comecaria comparando EXPLAIN ANALYZE antes e depois. Verificaria se algum indice ficou invalido, se o plano mudou para seq scan e se a migration introduziu colunas calculadas. Se preciso, recriaria o indice CONCURRENTLY e revisaria estatisticas com ANALYZE.",
      auto: 4.2, ctx: 4.4, bloom: 4, dreyfus: 4, score: 4.3,
      evidences: ["Usa EXPLAIN ANALYZE", "Cita CREATE INDEX CONCURRENTLY", "Revisa estatisticas"],
      red_flags: [],
      justification: "Diagnostico metodico, demonstra experiencia em performance tuning." },
    { id: "66666666-6666-4666-8666-000000000003",
      competency: "Sistemas Distribuidos",
      framework: "Bloom",
      qtype: "situational",
      text: "Como voce garantiria idempotencia em um endpoint de pagamento?",
      weight: 1.0,
      seq: 3,
      response: "Receberia um Idempotency-Key do cliente, persistiria a chave junto com o hash do payload e o resultado. Em retentativas, retornaria a resposta original sem reprocessar. Adicionaria expiracao da chave depois de algumas horas.",
      auto: 4.0, ctx: 4.3, bloom: 5, dreyfus: 4, score: 4.2,
      evidences: ["Idempotency-Key", "Hash do payload", "Expiracao"],
      red_flags: [],
      justification: "Padrao reconhecido, aplicado corretamente ao contexto." },
    { id: "66666666-6666-4666-8666-000000000004",
      competency: "Colaboracao",
      framework: "BigFive",
      qtype: "autodeclaration",
      text: "Conte uma situacao em que voce discordou de um colega senior. Como conduziu?",
      weight: 0.8,
      seq: 4,
      response: "Discordamos da escolha entre filas SQS vs Kafka. Pedi um espaco para alinhar criterios (volume, ordering, custo) e escrevi um RFC curto. Apos a revisao do time fechamos no SQS por simplicidade operacional, e propus reavaliar em 6 meses.",
      auto: 4.1, ctx: 4.2, bloom: 4, dreyfus: 4, score: 4.1,
      evidences: ["Escreveu RFC", "Definiu criterios objetivos", "Acordo com revisao futura"],
      red_flags: [],
      justification: "Postura colaborativa, escuta ativa e foco em criterio tecnico." },
    { id: "66666666-6666-4666-8666-000000000005",
      competency: "Ownership",
      framework: "CBI",
      qtype: "contextual",
      text: "Conte um incidente em producao que voce liderou. O que aprendeu?",
      weight: 0.9,
      seq: 5,
      response: "Lideramos a resposta a um vazamento de memoria no worker de imports. Coordenei rollback, abri war room e produzi o postmortem com action items. Implementamos limites de memoria por job e alertas no Datadog. A falha nao reincidiu nos meses seguintes.",
      auto: 4.4, ctx: 4.6, bloom: 5, dreyfus: 5, score: 4.5,
      evidences: ["Liderou war room", "Postmortem com action items", "Acompanhamento posterior"],
      red_flags: [],
      justification: "Demonstra ownership end-to-end e cultura de aprendizado." }
  ]

  questions.each do |qq|
    conn.execute(<<~SQL)
      INSERT INTO wsi_questions (id, session_id, competency, framework,
                                 question_type, question_text, weight,
                                 expected_signals, scoring_criteria,
                                 sequence_order, created_at)
      VALUES (#{q.call(qq[:id])}, #{q.call(demo_session_id)},
              #{q.call(qq[:competency])}, #{q.call(qq[:framework])},
              #{q.call(qq[:qtype])}, #{q.call(qq[:text])},
              #{qq[:weight]}, '[]'::jsonb, '{}'::jsonb,
              #{qq[:seq]}, NOW())
      ON CONFLICT (id) DO NOTHING
    SQL

    response_analysis_id = qq[:id].sub("66666666-6666-4666-8666",
                                       "66666666-6666-4666-8667")
    conn.execute(<<~SQL)
      INSERT INTO wsi_response_analyses (id, session_id, question_id,
                                         candidate_id, job_vacancy_id,
                                         competency, response_text,
                                         autodeclaration_score, context_score,
                                         bloom_level, dreyfus_level,
                                         evidences, red_flags,
                                         consistency_penalty, final_score,
                                         justification, created_at)
      VALUES (#{q.call(response_analysis_id)}, #{q.call(demo_session_id)},
              #{q.call(qq[:id])},
              #{q.call(demo_candidate_id)}, #{q.call(demo_job_vacancy_id)},
              #{q.call(qq[:competency])}, #{q.call(qq[:response])},
              #{qq[:auto]}, #{qq[:ctx]}, #{qq[:bloom]}, #{qq[:dreyfus]},
              #{q.call(qq[:evidences].to_json)}::jsonb,
              #{q.call(qq[:red_flags].to_json)}::jsonb,
              0, #{qq[:score]}, #{q.call(qq[:justification])}, NOW())
      ON CONFLICT (id) DO NOTHING
    SQL
  end

  conn.execute(<<~SQL)
    INSERT INTO wsi_results (id, session_id, candidate_id, job_vacancy_id,
                             technical_wsi, behavioral_wsi, overall_wsi,
                             classification, percentile, created_at)
    VALUES (#{q.call(demo_result_id)}, #{q.call(demo_session_id)},
            #{q.call(demo_candidate_id)}, #{q.call(demo_job_vacancy_id)},
            4.4, 4.3, 4.35, 'alto', 88, NOW())
    ON CONFLICT (id) DO NOTHING
  SQL

  technical_analysis = {
    pontos_fortes: ["Domina Rails e PostgreSQL", "Diagnostico de performance",
                    "Padroes de resiliencia (idempotencia)"],
    gaps: ["Pouca exposicao a Kafka em producao"]
  }
  behavioral_analysis = {
    colaboracao: 4.2,
    ownership: 4.5,
    comunicacao: 4.3,
    destaques: ["Estrutura RFCs antes de decisoes", "Lidera incidentes com calma"]
  }
  cultural_fit = {
    score: 4.4,
    valores_alinhados: ["Ownership", "Aprendizado continuo"]
  }
  recommendation = {
    decisao: "avancar",
    nivel_recomendado: "senior",
    proximos_passos: "Avancar para entrevista tecnica com o tech lead."
  }

  conn.execute(<<~SQL)
    INSERT INTO wsi_reports (id, wsi_result_id, candidate_id, executive_summary,
                             technical_analysis, behavioral_analysis,
                             cultural_fit, recommendation, created_at)
    VALUES (#{q.call(demo_report_id)}, #{q.call(demo_result_id)},
            #{q.call(demo_candidate_id)},
            'Maria apresenta forte fit tecnico e comportamental para a vaga de Senior Backend Engineer. Demonstrou solidez em Rails, PostgreSQL e padroes de resiliencia, alem de ownership claro em incidentes. Recomendamos avancar para a etapa tecnica.',
            #{q.call(technical_analysis.to_json)}::jsonb,
            #{q.call(behavioral_analysis.to_json)}::jsonb,
            #{q.call(cultural_fit.to_json)}::jsonb,
            #{q.call(recommendation.to_json)}::jsonb,
            NOW())
    ON CONFLICT (id) DO NOTHING
  SQL

  development_plan = {
    foco_30_dias: ["Estudo dirigido em Kafka"],
    foco_90_dias: ["POC de event-streaming no time"]
  }
  recommended_resources = [
    { title: "Designing Data-Intensive Applications", type: "livro" },
    { title: "Kafka: The Definitive Guide", type: "livro" }
  ]

  conn.execute(<<~SQL)
    INSERT INTO wsi_feedbacks (id, wsi_result_id, candidate_id, decision,
                               main_message, technical_strengths,
                               development_opportunities, behavioral_strengths,
                               next_steps, personalized_tip,
                               development_plan, recommended_resources,
                               created_at)
    VALUES (#{q.call(demo_feedback_id)}, #{q.call(demo_result_id)},
            #{q.call(demo_candidate_id)}, 'aprovado',
            'Parabens, Maria! Sua triagem demonstrou solidez tecnica e comportamental para a vaga.',
            #{q.call(["Rails avancado", "Tuning em PostgreSQL", "Padroes de resiliencia"].to_json)}::jsonb,
            #{q.call(["Aprofundar event-streaming com Kafka"].to_json)}::jsonb,
            #{q.call(["Comunicacao estruturada", "Lideranca em incidentes"].to_json)}::jsonb,
            'Convidaremos voce para a entrevista tecnica com o tech lead nos proximos dias.',
            'Compartilhe um RFC curto sobre uma decisao recente — voce ja faz isso muito bem!',
            #{q.call(development_plan.to_json)}::jsonb,
            #{q.call(recommended_resources.to_json)}::jsonb,
            NOW())
    ON CONFLICT (id) DO NOTHING
  SQL
else
  puts "  [skip] wsi_* tables not present in this DB; skipping WSI demo block."
end

# 5) Triagem session + dialogue (candidate-side conversation, RLS-scoped).
#    These tables are owned by the Python lia-agent-system; the live shape
#    matches the SQLAlchemy models in
#    `lia-agent-system/libs/models/lia_models/triagem.py` (columns: `token`,
#    `current_block`, `wsi_final_score`, `metadata_json`,
#    `triagem_messages.session_id`, `triagem_messages.wsi_block`, ...).
#    We still gate on `table_exists?` + a representative column probe so the
#    seed safely no-ops on a Rails-only DB where the Python app has not yet
#    created its tables. See `lia-agent-system/database/TRIAGEM_OWNERSHIP.md`.

dialogue = [
  { sender: "lia",       block: 0, content: "Oi, Maria! Eu sou a LIA. Vou te fazer algumas perguntas rapidas sobre a vaga de Senior Backend Engineer. Tudo bem comecar?" },
  { sender: "candidate", block: 0, content: "Tudo otimo, podemos comecar." },
  { sender: "lia",       block: 1, content: "Conte sobre uma API que voce projetou no Rails. Quais decisoes de modelagem voce tomou e por que?" },
  { sender: "candidate", block: 1, content: "No ultimo projeto desenhei uma API REST para gestao de pedidos, separando Order e LineItem em agregados, usei service objects e Sidekiq para o pos-processamento. Optei por UUID nas chaves." },
  { sender: "lia",       block: 2, content: "Otima resposta! Agora um caso pratico: uma query de relatorio passou de 200ms para 8s apos uma migration. Como voce investigaria?" },
  { sender: "candidate", block: 2, content: "Comparo EXPLAIN ANALYZE antes e depois, verifico indices invalidos, refaco com CREATE INDEX CONCURRENTLY se preciso e revisito ANALYZE." },
  { sender: "lia",       block: 7, content: "Maravilha, Maria! Triagem concluida. Sua nota foi 4.35 (alto). Vamos te chamar para a entrevista tecnica em breve." }
]

if conn.table_exists?("triagem_sessions") &&
   conn.table_exists?("triagem_messages") &&
   conn.column_exists?("triagem_sessions", "token") &&
   conn.column_exists?("triagem_messages", "wsi_block")
  # (a) Python live shape
  conn.execute(<<~SQL)
    INSERT INTO triagem_sessions (id, token, candidate_id, candidate_name,
                                  candidate_email, job_id, job_title,
                                  company_id, company_name, status,
                                  current_block, total_blocks, wsi_final_score,
                                  recommendation, invite_channel, voice_mode,
                                  expires_at, started_at, completed_at,
                                  created_at, updated_at, metadata_json)
    VALUES (#{q.call(demo_triagem_id)},
            'seed-triagem-maria-silva',
            #{q.call(demo_candidate_id)}, #{q.call(demo_candidate_name)},
            #{q.call(demo_candidate_email)},
            #{q.call(demo_job_vacancy_id)}, #{q.call(demo_job_title)},
            #{q.call(demo_company_id)}, 'WeDOTalent', 'completed',
            7, 7, 4.35, 'avancar', 'email', false,
            NOW() + INTERVAL '7 days',
            NOW() - INTERVAL '20 minutes',
            NOW() - INTERVAL '5 minutes',
            NOW() - INTERVAL '20 minutes', NOW(),
            #{q.call({ wsi_session_id: demo_session_id, wsi_result_id: demo_result_id, source: "seed" }.to_json)}::json)
    ON CONFLICT (id) DO NOTHING
  SQL

  dialogue.each_with_index do |msg, idx|
    msg_id = "55555555-5555-4555-8556-#{idx.to_s.rjust(12, '0')}"
    conn.execute(<<~SQL)
      INSERT INTO triagem_messages (id, session_id, sender, content,
                                    message_type, wsi_block, score,
                                    metadata_json, created_at)
      VALUES (#{q.call(msg_id)}, #{q.call(demo_triagem_id)},
              #{q.call(msg[:sender])}, #{q.call(msg[:content])},
              'text', #{msg[:block]}, NULL, '{}'::json,
              NOW() - INTERVAL '20 minutes' + (#{idx} * INTERVAL '90 seconds'))
      ON CONFLICT (id) DO NOTHING
    SQL
  end
else
  puts "  [skip] triagem_sessions/triagem_messages tables not present in the expected Python shape; skipping triagem demo block."
end

  puts "Demo WSI screening seeded for #{demo_candidate_name} on #{demo_job_title}"
  puts "  candidate_id   = #{demo_candidate_id}"
  puts "  job_vacancy_id = #{demo_job_vacancy_id}"
  puts "  wsi_result_id  = #{demo_result_id}"
  puts "  triagem token  = seed-triagem-maria-silva"

  # -------------------------------------------------------------------------
  # 10b. Additional demo screenings (varied scores for Kanban demo)
  # -------------------------------------------------------------------------
  # Adds two more (candidate, vaga) screenings so the Kanban shows variation
  # in WSI score, classification and recommendation: one "medio" (Joao,
  # frontend) and one "baixo" (Ana, full stack). Uses the same idempotent
  # ON CONFLICT DO NOTHING pattern as Maria's block.
  additional_screenings = [
    {
      candidate_id:        "11111111-1111-4111-8111-111111111112",
      candidate_name:      "Joao Santos",
      candidate_email:     "joao@example.com",
      candidate_phone:     "+5511999990002",
      candidate_title:     "Frontend Developer",
      candidate_seniority: "mid",
      job_vacancy_id:      "22222222-2222-4222-8222-222222222223",
      job_title:           "Senior Frontend Engineer",
      job_department:      "Product",
      job_seniority:       "senior",
      candidate_job_id:    "77777777-7777-4777-8777-777777777778",
      session_id:          "33333333-3333-4333-8333-333333333334",
      result_id:           "44444444-4444-4444-8444-444444444451",
      report_id:           "44444444-4444-4444-8444-444444444452",
      feedback_id:         "44444444-4444-4444-8444-444444444453",
      triagem_id:          "55555555-5555-4555-8555-555555555556",
      triagem_token:       "seed-triagem-joao-santos",
      question_prefix:     "66666666-6666-4666-8676",
      analysis_prefix:     "66666666-6666-4666-8677",
      message_prefix:      "55555555-5555-4555-8557",
      question_set_id:     "seed-frontend-v1",
      technical_wsi:       3.2,
      behavioral_wsi:      3.4,
      overall_wsi:         3.3,
      classification:      "medio",
      percentile:          55,
      recommendation: {
        decisao:          "considerar",
        nivel_recomendado: "pleno",
        proximos_passos:  "Marcar entrevista comportamental para validar pontos de atencao em arquitetura."
      },
      executive_summary: "Joao apresenta perfil pleno aderente, com bom dominio de React e comunicacao, mas com gaps em TypeScript avancado e arquitetura de frontend. Recomendamos uma etapa adicional de avaliacao antes de avancar.",
      technical_analysis: {
        pontos_fortes: ["React solido", "Boas praticas de CSS", "Comunicacao tecnica clara"],
        gaps:          ["Pouca exposicao a TypeScript avancado", "Arquitetura de componentes complexos"]
      },
      behavioral_analysis: {
        colaboracao: 3.6, ownership: 3.2, comunicacao: 3.8,
        destaques: ["Curiosidade tecnica", "Gosta de pareamento"]
      },
      cultural_fit: {
        score: 3.5,
        valores_alinhados: ["Aprendizado continuo"]
      },
      feedback_decision: "em_avaliacao",
      feedback_main:     "Joao, sua triagem mostra um bom perfil intermediario. Vamos aprofundar em proximos passos.",
      feedback_strengths:    ["React solido", "Boa comunicacao tecnica"],
      feedback_dev:          ["Aprofundar TypeScript avancado", "Estudar arquitetura de frontend"],
      feedback_behavioral:   ["Curiosidade", "Trabalho em time"],
      feedback_next:         "Marcaremos uma conversa rapida com a tech lead de frontend.",
      feedback_tip:          "Estude padroes de composicao no React e tipagens avancadas — voce vai se destacar.",
      development_plan: {
        foco_30_dias: ["Curso de TypeScript avancado"],
        foco_90_dias: ["Refatorar um modulo do dia a dia aplicando padroes"]
      },
      recommended_resources: [
        { title: "Effective TypeScript", type: "livro" },
        { title: "Patterns.dev",        type: "site"  }
      ],
      questions: [
        { competency: "React",        framework: "Bloom",   qtype: "contextual",
          text: "Conte sobre um componente complexo que voce projetou. Como organizou estado e composicao?",
          response: "Construi um wizard multi-step com contexto local e algumas chamadas a API. Separei em componentes pequenos e usei hooks customizados, embora algumas partes tenham acabado bem acopladas.",
          auto: 3.5, ctx: 3.4, bloom: 3, dreyfus: 3, score: 3.4,
          evidences: ["Hooks customizados", "Componentizacao"], red_flags: ["Acoplamento residual mencionado"],
          justification: "Boa nocao de composicao, mas reconhece acoplamento que poderia evitar." },
        { competency: "TypeScript",   framework: "Dreyfus", qtype: "microcase",
          text: "Como voce tiparia uma funcao que recebe um payload variavel a partir de um discriminator?",
          response: "Usaria union types com um campo 'kind' e narrowing por if/switch. Nunca usei mapped/conditional types em producao.",
          auto: 3.0, ctx: 3.1, bloom: 3, dreyfus: 2, score: 3.0,
          evidences: ["Cita union types", "Narrowing"], red_flags: ["Sem experiencia com tipos avancados"],
          justification: "Conhecimento basico solido, mas sem profundidade em recursos avancados." },
        { competency: "Acessibilidade", framework: "Bloom", qtype: "situational",
          text: "Como voce garantiria que um modal seja acessivel?",
          response: "Bloquearia o foco dentro do modal com um trap, fecharia no Escape e usaria role='dialog' com aria-labelledby.",
          auto: 3.6, ctx: 3.5, bloom: 4, dreyfus: 3, score: 3.5,
          evidences: ["Focus trap", "ARIA roles"], red_flags: [],
          justification: "Resposta correta e direta para um caso classico." },
        { competency: "Colaboracao",   framework: "BigFive", qtype: "autodeclaration",
          text: "Conte uma situacao em que voce recebeu um code review duro. Como reagiu?",
          response: "No comeco fiquei desconfortavel, mas pedi um pareamento e refiz a PR aceitando a maioria dos pontos.",
          auto: 3.4, ctx: 3.5, bloom: 3, dreyfus: 3, score: 3.4,
          evidences: ["Pareamento", "Abertura para revisao"], red_flags: [],
          justification: "Postura saudavel, demonstra capacidade de absorver feedback." },
        { competency: "Ownership",     framework: "CBI",     qtype: "contextual",
          text: "Conte um bug em producao que voce ajudou a resolver. Qual foi seu papel?",
          response: "Participei da investigacao mas quem coordenou foi outro dev. Ajudei a reproduzir o bug e abri o PR de correcao.",
          auto: 3.0, ctx: 3.2, bloom: 3, dreyfus: 3, score: 3.1,
          evidences: ["Reproducao do bug", "PR de correcao"], red_flags: ["Nao liderou o esforco"],
          justification: "Contribuicao tecnica relevante, mas ainda nao lidera respostas a incidentes." }
      ],
      dialogue: [
        { sender: "lia",       block: 0, content: "Oi, Joao! Eu sou a LIA. Vou te fazer algumas perguntas sobre a vaga de Senior Frontend Engineer. Tudo bem comecar?" },
        { sender: "candidate", block: 0, content: "Tudo bem, pode mandar." },
        { sender: "lia",       block: 1, content: "Conte sobre um componente complexo que voce projetou. Como organizou estado e composicao?" },
        { sender: "candidate", block: 1, content: "Construi um wizard multi-step com contexto local e hooks, mas algumas partes ficaram acopladas." },
        { sender: "lia",       block: 2, content: "Como voce tiparia uma funcao que recebe um payload variavel a partir de um discriminator em TypeScript?" },
        { sender: "candidate", block: 2, content: "Union types com um campo 'kind' e narrowing por if/switch. Nunca usei mapped/conditional em producao." },
        { sender: "lia",       block: 7, content: "Obrigada, Joao! Triagem concluida. Sua nota foi 3.3 (medio). Vamos te dar um retorno em breve." }
      ]
    },
    {
      candidate_id:        "11111111-1111-4111-8111-111111111113",
      candidate_name:      "Ana Oliveira",
      candidate_email:     "ana@example.com",
      candidate_phone:     "+5511999990003",
      candidate_title:     "Full Stack Developer",
      candidate_seniority: "junior",
      job_vacancy_id:      "22222222-2222-4222-8222-222222222224",
      job_title:           "Senior Full Stack Engineer",
      job_department:      "Engineering",
      job_seniority:       "senior",
      candidate_job_id:    "77777777-7777-4777-8777-777777777779",
      session_id:          "33333333-3333-4333-8333-333333333335",
      result_id:           "44444444-4444-4444-8444-444444444461",
      report_id:           "44444444-4444-4444-8444-444444444462",
      feedback_id:         "44444444-4444-4444-8444-444444444463",
      triagem_id:          "55555555-5555-4555-8555-555555555557",
      triagem_token:       "seed-triagem-ana-oliveira",
      question_prefix:     "66666666-6666-4666-8686",
      analysis_prefix:     "66666666-6666-4666-8687",
      message_prefix:      "55555555-5555-4555-8558",
      question_set_id:     "seed-fullstack-v1",
      technical_wsi:       2.1,
      behavioral_wsi:      2.4,
      overall_wsi:         2.2,
      classification:      "baixo",
      percentile:          18,
      recommendation: {
        decisao:           "nao_avancar",
        nivel_recomendado: "junior",
        proximos_passos:   "Nao avancar para esta vaga senior. Manter no banco para oportunidades juniores."
      },
      executive_summary: "Ana demonstra perfil aderente a vagas juniores, mas com gaps tecnicos relevantes para uma posicao senior full stack (arquitetura, persistencia e ownership). Recomendamos nao avancar nesta vaga.",
      technical_analysis: {
        pontos_fortes: ["Vontade de aprender", "Conhece o basico de Rails e React"],
        gaps:          ["Modelagem de dados", "Performance de queries", "Padroes de resiliencia"]
      },
      behavioral_analysis: {
        colaboracao: 2.8, ownership: 2.0, comunicacao: 2.6,
        destaques: ["Disposta a estudar"]
      },
      cultural_fit: {
        score: 2.5,
        valores_alinhados: ["Aprendizado continuo"]
      },
      feedback_decision: "reprovado",
      feedback_main:     "Ana, agradecemos sua participacao. Para esta vaga senior, identificamos gaps importantes — mas seu perfil pode encaixar em oportunidades juniores futuras.",
      feedback_strengths:    ["Energia para aprender", "Familiaridade basica com a stack"],
      feedback_dev:          ["Modelagem relacional", "Performance de queries", "Padroes de arquitetura"],
      feedback_behavioral:   ["Abertura para feedback"],
      feedback_next:         "Vamos manter seu perfil em nosso banco para vagas juniores compativeis.",
      feedback_tip:          "Aprofunde-se em SQL e padroes de design — vai abrir muitas portas.",
      development_plan: {
        foco_30_dias: ["Curso intensivo de SQL e modelagem"],
        foco_90_dias: ["Construir um projeto completo aplicando padroes basicos"]
      },
      recommended_resources: [
        { title: "SQL Antipatterns",            type: "livro" },
        { title: "The Pragmatic Programmer",    type: "livro" }
      ],
      questions: [
        { competency: "Ruby on Rails", framework: "Bloom",   qtype: "contextual",
          text: "Conte sobre uma feature que voce desenvolveu em Rails. Como modelou os dados?",
          response: "Fiz um CRUD de tarefas com scaffold. Usei o que o Rails gerou e nao mexi muito na modelagem.",
          auto: 2.0, ctx: 2.1, bloom: 2, dreyfus: 1, score: 2.1,
          evidences: ["Mencao a scaffold"], red_flags: ["Sem decisoes proprias de modelagem"],
          justification: "Resposta superficial, indica pouca autonomia tecnica." },
        { competency: "PostgreSQL",    framework: "Dreyfus", qtype: "microcase",
          text: "Uma query simples ficou lenta. O que voce faria?",
          response: "Talvez adicionar um indice. Sinceramente nunca precisei investigar performance ainda.",
          auto: 1.8, ctx: 2.0, bloom: 2, dreyfus: 1, score: 1.9,
          evidences: ["Cita indice"], red_flags: ["Nunca investigou performance"],
          justification: "Conhecimento incipiente; ainda nao teve a experiencia esperada para o nivel." },
        { competency: "Sistemas Distribuidos", framework: "Bloom", qtype: "situational",
          text: "Como voce garantiria que um endpoint nao processe a mesma requisicao duas vezes?",
          response: "Acho que daria pra checar antes se ja foi processado, mas nunca implementei algo assim.",
          auto: 1.9, ctx: 2.0, bloom: 2, dreyfus: 1, score: 1.9,
          evidences: [], red_flags: ["Sem familiaridade com idempotencia"],
          justification: "Nao demonstra conhecimento de padroes basicos esperados." },
        { competency: "Colaboracao",   framework: "BigFive", qtype: "autodeclaration",
          text: "Conte uma situacao em que voce precisou pedir ajuda. Como agiu?",
          response: "Travei numa task e demorei a pedir ajuda. Quando pedi, resolveram comigo em meia hora.",
          auto: 2.7, ctx: 2.6, bloom: 3, dreyfus: 2, score: 2.6,
          evidences: ["Reconhece atraso", "Pede ajuda"], red_flags: ["Demora em sinalizar bloqueio"],
          justification: "Reconhece o ponto, mas ainda demora a sinalizar bloqueios." },
        { competency: "Ownership",     framework: "CBI",     qtype: "contextual",
          text: "Conte uma situacao em que voce assumiu a responsabilidade por algo que deu errado.",
          response: "Quebrei a build uma vez e o senior corrigiu pra mim. Aprendi a rodar os testes localmente depois disso.",
          auto: 2.0, ctx: 2.2, bloom: 2, dreyfus: 2, score: 2.1,
          evidences: ["Aprendizado pos-erro"], red_flags: ["Nao corrigiu o proprio erro"],
          justification: "Aprendizado positivo, mas ainda nao demonstra ownership ativo." }
      ],
      dialogue: [
        { sender: "lia",       block: 0, content: "Oi, Ana! Eu sou a LIA. Vou te fazer algumas perguntas sobre a vaga de Senior Full Stack Engineer. Tudo bem comecar?" },
        { sender: "candidate", block: 0, content: "Oi, sim, podemos comecar." },
        { sender: "lia",       block: 1, content: "Conte sobre uma feature que voce desenvolveu em Rails. Como modelou os dados?" },
        { sender: "candidate", block: 1, content: "Fiz um CRUD de tarefas com scaffold; nao mexi muito na modelagem." },
        { sender: "lia",       block: 2, content: "Uma query simples ficou lenta. O que voce faria para investigar?" },
        { sender: "candidate", block: 2, content: "Talvez adicionar um indice. Nunca precisei investigar performance ainda." },
        { sender: "lia",       block: 7, content: "Obrigada, Ana! Triagem concluida. Sua nota foi 2.2. Daremos um retorno em breve." }
      ]
    }
  ]

  wsi_tables_ok =
    conn.table_exists?("wsi_sessions") &&
    conn.table_exists?("wsi_questions") &&
    conn.table_exists?("wsi_response_analyses") &&
    conn.table_exists?("wsi_results") &&
    conn.table_exists?("wsi_reports") &&
    conn.table_exists?("wsi_feedbacks")

  triagem_tables_ok =
    conn.table_exists?("triagem_sessions") &&
    conn.table_exists?("triagem_messages") &&
    conn.column_exists?("triagem_sessions", "token") &&
    conn.column_exists?("triagem_messages", "wsi_block")

  additional_screenings.each do |p|
    # Reuse the Rails-side candidate UUID if it already exists for this email
    existing_id = conn.select_value(
      "SELECT id::text FROM candidates WHERE email = #{q.call(p[:candidate_email])} LIMIT 1"
    )
    cand_id = existing_id || p[:candidate_id]

    conn.execute(<<~SQL)
      INSERT INTO candidates (id, name, email, mobile_phone, current_title,
                              seniority_level, source, company_id)
      VALUES (#{q.call(cand_id)}, #{q.call(p[:candidate_name])},
              #{q.call(p[:candidate_email])}, #{q.call(p[:candidate_phone])},
              #{q.call(p[:candidate_title])}, #{q.call(p[:candidate_seniority])},
              'seed', #{q.call(demo_company_id)})
      ON CONFLICT (id) DO NOTHING
    SQL

    conn.execute(<<~SQL)
      INSERT INTO job_vacancies (id, company_id, title, status, department,
                                 seniority_level, employment_type,
                                 created_at, updated_at)
      VALUES (#{q.call(p[:job_vacancy_id])}, #{q.call(demo_company_id)},
              #{q.call(p[:job_title])}, 'Ativa', #{q.call(p[:job_department])},
              #{q.call(p[:job_seniority])}, 'clt', NOW(), NOW())
      ON CONFLICT (id) DO NOTHING
    SQL

    conn.execute(<<~SQL)
      INSERT INTO candidate_jobs (id, candidate_id, job_vacancy_id,
                                  status, source, applied_at, created_at, updated_at)
      VALUES (#{q.call(p[:candidate_job_id])}, #{q.call(cand_id)},
              #{q.call(p[:job_vacancy_id])}, 'screening', 'seed',
              NOW(), NOW(), NOW())
      ON CONFLICT (id) DO NOTHING
    SQL

    if wsi_tables_ok
      conn.execute(<<~SQL)
        INSERT INTO wsi_sessions (id, candidate_id, job_vacancy_id, screening_type,
                                  mode, status, question_set_version, question_set_id,
                                  started_at, completed_at, created_at, updated_at)
        VALUES (#{q.call(p[:session_id])}, #{q.call(cand_id)},
                #{q.call(p[:job_vacancy_id])}, 'chat', 'compact', 'completed',
                1, #{q.call(p[:question_set_id])},
                NOW() - INTERVAL '25 minutes', NOW() - INTERVAL '8 minutes',
                NOW() - INTERVAL '25 minutes', NOW())
        ON CONFLICT (id) DO NOTHING
      SQL

      p[:questions].each_with_index do |qq, idx|
        seq         = idx + 1
        suffix      = (idx + 1).to_s.rjust(12, "0")
        question_id = "#{p[:question_prefix]}-#{suffix}"
        analysis_id = "#{p[:analysis_prefix]}-#{suffix}"

        conn.execute(<<~SQL)
          INSERT INTO wsi_questions (id, session_id, competency, framework,
                                     question_type, question_text, weight,
                                     expected_signals, scoring_criteria,
                                     sequence_order, created_at)
          VALUES (#{q.call(question_id)}, #{q.call(p[:session_id])},
                  #{q.call(qq[:competency])}, #{q.call(qq[:framework])},
                  #{q.call(qq[:qtype])}, #{q.call(qq[:text])},
                  1.0, '[]'::jsonb, '{}'::jsonb,
                  #{seq}, NOW())
          ON CONFLICT (id) DO NOTHING
        SQL

        conn.execute(<<~SQL)
          INSERT INTO wsi_response_analyses (id, session_id, question_id,
                                             candidate_id, job_vacancy_id,
                                             competency, response_text,
                                             autodeclaration_score, context_score,
                                             bloom_level, dreyfus_level,
                                             evidences, red_flags,
                                             consistency_penalty, final_score,
                                             justification, created_at)
          VALUES (#{q.call(analysis_id)}, #{q.call(p[:session_id])},
                  #{q.call(question_id)},
                  #{q.call(cand_id)}, #{q.call(p[:job_vacancy_id])},
                  #{q.call(qq[:competency])}, #{q.call(qq[:response])},
                  #{qq[:auto]}, #{qq[:ctx]}, #{qq[:bloom]}, #{qq[:dreyfus]},
                  #{q.call(qq[:evidences].to_json)}::jsonb,
                  #{q.call(qq[:red_flags].to_json)}::jsonb,
                  0, #{qq[:score]}, #{q.call(qq[:justification])}, NOW())
          ON CONFLICT (id) DO NOTHING
        SQL
      end

      conn.execute(<<~SQL)
        INSERT INTO wsi_results (id, session_id, candidate_id, job_vacancy_id,
                                 technical_wsi, behavioral_wsi, overall_wsi,
                                 classification, percentile, created_at)
        VALUES (#{q.call(p[:result_id])}, #{q.call(p[:session_id])},
                #{q.call(cand_id)}, #{q.call(p[:job_vacancy_id])},
                #{p[:technical_wsi]}, #{p[:behavioral_wsi]}, #{p[:overall_wsi]},
                #{q.call(p[:classification])}, #{p[:percentile]}, NOW())
        ON CONFLICT (id) DO NOTHING
      SQL

      conn.execute(<<~SQL)
        INSERT INTO wsi_reports (id, wsi_result_id, candidate_id, executive_summary,
                                 technical_analysis, behavioral_analysis,
                                 cultural_fit, recommendation, created_at)
        VALUES (#{q.call(p[:report_id])}, #{q.call(p[:result_id])},
                #{q.call(cand_id)},
                #{q.call(p[:executive_summary])},
                #{q.call(p[:technical_analysis].to_json)}::jsonb,
                #{q.call(p[:behavioral_analysis].to_json)}::jsonb,
                #{q.call(p[:cultural_fit].to_json)}::jsonb,
                #{q.call(p[:recommendation].to_json)}::jsonb,
                NOW())
        ON CONFLICT (id) DO NOTHING
      SQL

      conn.execute(<<~SQL)
        INSERT INTO wsi_feedbacks (id, wsi_result_id, candidate_id, decision,
                                   main_message, technical_strengths,
                                   development_opportunities, behavioral_strengths,
                                   next_steps, personalized_tip,
                                   development_plan, recommended_resources,
                                   created_at)
        VALUES (#{q.call(p[:feedback_id])}, #{q.call(p[:result_id])},
                #{q.call(cand_id)}, #{q.call(p[:feedback_decision])},
                #{q.call(p[:feedback_main])},
                #{q.call(p[:feedback_strengths].to_json)}::jsonb,
                #{q.call(p[:feedback_dev].to_json)}::jsonb,
                #{q.call(p[:feedback_behavioral].to_json)}::jsonb,
                #{q.call(p[:feedback_next])},
                #{q.call(p[:feedback_tip])},
                #{q.call(p[:development_plan].to_json)}::jsonb,
                #{q.call(p[:recommended_resources].to_json)}::jsonb,
                NOW())
        ON CONFLICT (id) DO NOTHING
      SQL
    end

    if triagem_tables_ok
      conn.execute(<<~SQL)
        INSERT INTO triagem_sessions (id, token, candidate_id, candidate_name,
                                      candidate_email, job_id, job_title,
                                      company_id, company_name, status,
                                      current_block, total_blocks, wsi_final_score,
                                      recommendation, invite_channel, voice_mode,
                                      expires_at, started_at, completed_at,
                                      created_at, updated_at, metadata_json)
        VALUES (#{q.call(p[:triagem_id])},
                #{q.call(p[:triagem_token])},
                #{q.call(cand_id)}, #{q.call(p[:candidate_name])},
                #{q.call(p[:candidate_email])},
                #{q.call(p[:job_vacancy_id])}, #{q.call(p[:job_title])},
                #{q.call(demo_company_id)}, 'WeDOTalent', 'completed',
                7, 7, #{p[:overall_wsi]},
                #{q.call(p[:recommendation][:decisao])}, 'email', false,
                NOW() + INTERVAL '7 days',
                NOW() - INTERVAL '25 minutes',
                NOW() - INTERVAL '8 minutes',
                NOW() - INTERVAL '25 minutes', NOW(),
                #{q.call({ wsi_session_id: p[:session_id], wsi_result_id: p[:result_id], source: "seed" }.to_json)}::json)
        ON CONFLICT (id) DO NOTHING
      SQL

      p[:dialogue].each_with_index do |msg, idx|
        msg_id = "#{p[:message_prefix]}-#{idx.to_s.rjust(12, '0')}"
        conn.execute(<<~SQL)
          INSERT INTO triagem_messages (id, session_id, sender, content,
                                        message_type, wsi_block, score,
                                        metadata_json, created_at)
          VALUES (#{q.call(msg_id)}, #{q.call(p[:triagem_id])},
                  #{q.call(msg[:sender])}, #{q.call(msg[:content])},
                  'text', #{msg[:block]}, NULL, '{}'::json,
                  NOW() - INTERVAL '25 minutes' + (#{idx} * INTERVAL '90 seconds'))
          ON CONFLICT (id) DO NOTHING
        SQL
      end
    end

    puts "Demo WSI screening seeded for #{p[:candidate_name]} on #{p[:job_title]} (#{p[:classification]})"
  end
else
  puts "Demo WSI screening: required Python lia-agent-system tables/columns " \
       "are not present in this database; skipping the demo block. " \
       "(seeds.rb section 10 — open follow-up to align schemas)"
end

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------

puts
puts "Seeds created successfully!"
puts "  Admin login: admin@wedotalent.com / password123"
