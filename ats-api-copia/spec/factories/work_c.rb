# frozen_string_literal: true

FactoryBot.define do
  # ──────────────────────────────────────────────
  # Company Config
  # ──────────────────────────────────────────────

  factory :client_account do
    name { Faker::Company.name }
    cnpj { Faker::Number.number(digits: 14).to_s }
    status { "active" }
    primary_email { Faker::Internet.email }
  end

  factory :client_user do
    association :client_account, factory: :client_account
    company_id { client_account.id }
    email { Faker::Internet.unique.email }
    name { Faker::Name.name }
    role { "admin" }
    status { "active" }
  end

  factory :company_profile do
    association :client_account
    name { Faker::Company.name }
  end

  factory :department do
    association :company_profile, factory: :company_profile
    company_id { company_profile.id }
    name { Faker::Commerce.department }
  end

  factory :benefit do
    association :company_profile, factory: :company_profile
    company_id { company_profile.id }
    name { Faker::Lorem.word.capitalize }
    category { "health" }
  end

  factory :culture_value do
    association :company_profile, factory: :company_profile
    company_id { company_profile.id }
    name { Faker::Company.buzzword.capitalize }
  end

  factory :ideal_profile do
    association :company_profile, factory: :company_profile
    company_id { company_profile.id }
    name { Faker::Job.title }
  end

  factory :company_hiring_policy do
    company_id { "test_company" }
  end

  factory :compensation_policy do
    association :company_profile, factory: :company_profile
    company_id { company_profile.id }
    name { Faker::Lorem.sentence(word_count: 3) }
    currency { "BRL" }
  end

  # ──────────────────────────────────────────────
  # Email & Communication
  # ──────────────────────────────────────────────

  factory :email_template do
    name { Faker::Lorem.sentence(word_count: 3) }
    subject { Faker::Lorem.sentence(word_count: 5) }
    body_html { "<p>#{Faker::Lorem.paragraph}</p>" }
    company_id { "test_company" }
  end

  factory :email_log do
    recipient_email { Faker::Internet.email }
    subject { Faker::Lorem.sentence(word_count: 5) }
    status { "sent" }
  end

  factory :email_tracking_event do
    association :email_log
    event_type { "open" }
    event_at { Time.current }
  end

  factory :recruitment_email_template do
    company_id { "test_company" }
    stage_name { "screening" }
    action_type { "auto_reply" }
  end

  # ──────────────────────────────────────────────
  # Billing
  # ──────────────────────────────────────────────

  factory :subscription do
    association :client_account
    plan_name { "Pro" }
    status { "active" }
    amount { 299.90 }
    currency { "BRL" }
    billing_cycle { "monthly" }
  end

  factory :invoice do
    association :client_account
    invoice_number { Faker::Number.unique.number(digits: 8).to_s }
    status { "pending" }
    total { Faker::Commerce.price(range: 100..5000.0) }
    currency { "BRL" }
    issue_date { Time.current }
    due_date { 30.days.from_now }
  end

  factory :payment_method do
    association :client_account
    method_type { "credit_card" }
    provider { "stripe" }
    last4 { Faker::Number.number(digits: 4).to_s }
    brand { "visa" }
    holder_name { Faker::Name.name }
    is_default { true }
  end

  factory :ai_consumption do
    company_id { "test_company" }
    tokens_used { Faker::Number.between(from: 100, to: 10_000) }
    cost { Faker::Commerce.price(range: 0.01..5.0) }
    provider { "openai" }
    model { "gpt-4" }
    operation { "screening" }
    usage_date { Date.current }
  end

  factory :ai_credits_balance do
    company_id { "test_company" }
    credits_remaining { 1000 }
    credits_monthly { 5000 }
    credits_used_this_period { 4000 }
  end

  # ──────────────────────────────────────────────
  # LGPD / Consent
  # ──────────────────────────────────────────────

  factory :consent_record do
    candidate_id { SecureRandom.uuid }
    consent_type { "data_processing" }
    status { "given" }
    given_at { Time.current }
  end

  factory :consent_version do
    consent_type { "data_processing" }
    version { Faker::Number.between(from: 1, to: 10) }
    text_pt { Faker::Lorem.paragraph }
    is_active { true }
  end

  factory :consent_event do
    association :consent_record
    consent_id { consent_record.id }
    event_type { "given" }
  end

  factory :data_subject_request do
    candidate_id { SecureRandom.uuid }
    request_type { "access" }
    status { "pending" }
  end

  factory :automated_decision_explanation do
    candidate_id { SecureRandom.uuid }
    decision_type { "screening" }
    decision { "approved" }
    explanation { Faker::Lorem.paragraph }
    score { Faker::Number.between(from: 0.0, to: 1.0).round(2) }
    confidence { Faker::Number.between(from: 0.5, to: 1.0).round(2) }
  end

  factory :company_retention_policy do
    company_id { "test_company" }
    data_type { "candidate_data" }
    retention_days { 365 }
    action { "anonymize" }
  end

  # ──────────────────────────────────────────────
  # Audit
  # ──────────────────────────────────────────────

  factory :audit_log do
    company_id { "test_company" }
    agent_name { "lia" }
    action { "screening" }
    created_at { Time.current }
  end

  factory :audit_retention_policy do
    company_id { "test_company" }
    log_type { "ai_decision" }
    retention_days { 730 }
  end

  factory :admin_audit_log do
    admin_user_id { SecureRandom.uuid }
    action { "update_settings" }
    created_at { Time.current }
  end

  # ──────────────────────────────────────────────
  # Notifications
  # ──────────────────────────────────────────────

  factory :notification do
    association :user
    user_id { user.id.to_s }
    notification_type { "info" }
    title { Faker::Lorem.sentence(word_count: 4) }
    message { Faker::Lorem.paragraph }
    status { "unread" }
  end

  factory :chat_notification do
    association :user
    user_id { user.id.to_s }
    conversation_id { SecureRandom.uuid }
    unread_count { Faker::Number.between(from: 0, to: 50) }
  end

  factory :notification_policy do
    company_id { "test_company" }
    channel { "email" }
    event_type { "new_application" }
    is_enabled { true }
  end

  # ──────────────────────────────────────────────
  # Webhooks
  # ──────────────────────────────────────────────

  factory :webhook do
    company_id { "test_company" }
    name { Faker::Lorem.sentence(word_count: 3) }
    url { Faker::Internet.url }
    is_active { true }
  end

  factory :webhook_log do
    association :webhook
    event { "candidate.created" }
    status { "success" }
    response_code { 200 }
    created_at { Time.current }
  end

  factory :webhook_delivery_log do
    association :webhook
    attempt { 1 }
    status { "success" }
    response_code { 200 }
    created_at { Time.current }
  end

  factory :webhook_registration do
    company_id { "test_company" }
    provider { "zapier" }
    is_active { true }
  end

  # ──────────────────────────────────────────────
  # Interview Scheduling
  # ──────────────────────────────────────────────

  factory :interview do
    association :candidate
    association :job
    job_vacancy_id { job.id }
    title { "Interview - #{Faker::Job.title}" }
    interview_type { "technical" }
    interview_mode { "video" }
    start_time { 1.day.from_now }
    end_time { 1.day.from_now + 1.hour }
    status { "scheduled" }
  end

  factory :interview_feedback do
    association :interview
    interviewer_name { Faker::Name.name }
    recommendation { "strong_yes" }
    overall_score { Faker::Number.between(from: 1.0, to: 5.0).round(1) }
  end

  factory :interview_note do
    association :interview
    author_name { Faker::Name.name }
    content { Faker::Lorem.paragraph }
  end

  factory :interview_reminder do
    association :interview
    reminder_type { "24h_before" }
    channel { "email" }
    send_at { 23.hours.from_now }
    status { "pending" }
  end

  factory :calendar_availability do
    association :user
    user_id { user.id.to_s }
    day_of_week { Faker::Number.between(from: 0, to: 6) }
    start_time { "09:00" }
    end_time { "18:00" }
    timezone { "America/Sao_Paulo" }
  end

  factory :self_scheduling_link do
    association :interview
    token { SecureRandom.urlsafe_base64(32) }
    expires_at { 7.days.from_now }
    status { "active" }
  end

  factory :reschedule_history do
    association :interview
    old_start_time { 1.day.from_now }
    new_start_time { 2.days.from_now }
    reason { Faker::Lorem.sentence }
  end

  # ──────────────────────────────────────────────
  # ATS Integrations
  # ──────────────────────────────────────────────

  factory :integration_provider do
    name { Faker::App.unique.name }
    provider_type { "ats" }
    display_name { Faker::App.name }
    is_active { true }
  end

  factory :integration_connection do
    company_id { "test_company" }
    association :integration_provider, factory: :integration_provider
    provider_id { integration_provider.id }
    status { "active" }
  end

  factory :integration_sync_log do
    association :integration_connection, factory: :integration_connection
    connection_id { integration_connection.id }
    direction { "inbound" }
    entity_type { "candidate" }
    records_synced { 10 }
  end

  factory :integration_webhook do
    association :integration_connection, factory: :integration_connection
    connection_id { integration_connection.id }
    url { Faker::Internet.url }
    is_active { true }
  end

  factory :ats_connection do
    company_id { "test_company" }
    provider { Faker::App.unique.name }
    status { "active" }
  end

  factory :ats_sync_job do
    association :ats_connection
    connection_id { ats_connection.id }
    direction { "inbound" }
    entity_type { "candidate" }
    status { "pending" }
  end

  factory :ats_candidate do
    association :ats_connection
    connection_id { ats_connection.id }
    external_id { SecureRandom.uuid }
    sync_status { "synced" }
  end

  factory :ats_webhook_log do
    association :ats_connection
    connection_id { ats_connection.id }
    event { "candidate.created" }
    processed { false }
    created_at { Time.current }
  end

  factory :ats_job_mapping do
    association :ats_connection
    connection_id { ats_connection.id }
    external_job_id { SecureRandom.uuid }
    local_job_id { SecureRandom.uuid }
    sync_status { "synced" }
  end

  # ──────────────────────────────────────────────
  # Automation
  # ──────────────────────────────────────────────

  factory :recruitment_automation do
    company_id { "test_company" }
    name { Faker::Lorem.sentence(word_count: 3) }
    trigger_event { "application_received" }
    action_type { "send_email" }
    is_active { true }
  end

  factory :recruitment_sla do
    company_id { "test_company" }
    stage_name { "screening" }
    max_hours { 48 }
    is_active { true }
  end

  factory :sla_violation do
    association :recruitment_sla
    sla_id { recruitment_sla.id }
    candidate_id { SecureRandom.uuid }
    violation_date { Time.current }
    hours_exceeded { 12 }
    resolved { false }
  end

  # ──────────────────────────────────────────────
  # Workforce Planning
  # ──────────────────────────────────────────────

  factory :hiring_plan do
    company_id { "test_company" }
    name { "Hiring Plan #{Faker::Date.forward(days: 90).year}" }
    year { Date.current.year }
    status { "draft" }
  end

  factory :planned_headcount do
    association :hiring_plan
    role_title { Faker::Job.title }
    seniority { "senior" }
    quantity { Faker::Number.between(from: 1, to: 5) }
    priority { "high" }
    status { "planned" }
  end

  factory :workforce_entry do
    company_id { "test_company" }
    current_headcount { 50 }
    target_headcount { 60 }
    gap { 10 }
    period { "Q1" }
    year { Date.current.year }
  end

  factory :import_job do
    company_id { "test_company" }
    source { "csv" }
    status { "pending" }
  end

  # ──────────────────────────────────────────────
  # Templates
  # ──────────────────────────────────────────────

  factory :template_category do
    name { Faker::Job.field.capitalize }
  end

  factory :job_template do
    title { Faker::Job.title }
    category { "engineering" }
    is_active { true }
  end

  factory :pipeline_template do
    name { "Pipeline #{Faker::Lorem.word.capitalize}" }
    stages { [{ name: "Screening", order: 1 }, { name: "Interview", order: 2 }] }
    is_active { true }
  end

  factory :template_usage_log do
    association :job_template, factory: :job_template
    template_id { job_template.id }
    template_type { "job" }
    company_id { "test_company" }
    created_at { Time.current }
  end

  # ──────────────────────────────────────────────
  # Approvals
  # ──────────────────────────────────────────────

  factory :approval_request do
    company_id { SecureRandom.uuid }
    request_type { "vacancy_approval" }
    status { "pending" }
    priority { "normal" }
  end

  factory :pending_approval do
    company_id { SecureRandom.uuid }
    association :approval_request
    approver_id { SecureRandom.uuid }
    status { "pending" }
  end

  # ──────────────────────────────────────────────
  # Goals & Shared Searches
  # ──────────────────────────────────────────────

  factory :goal do
    name { Faker::Lorem.sentence(word_count: 3) }
    target { 100.0 }
    current { 0.0 }
    unit { "hires" }
    status { "pending" }
  end

  factory :goal_template do
    name { Faker::Lorem.sentence(word_count: 3) }
    category { "recruitment" }
    default_target { 50.0 }
    unit { "hires" }
    period { "monthly" }
  end

  factory :shared_search do
    share_type { "candidate_list" }
    title { Faker::Lorem.sentence(word_count: 4) }
    status { "active" }
  end

  factory :shared_search_access do
    association :shared_search
    recipient_email { Faker::Internet.email }
    access_token { SecureRandom.urlsafe_base64(32) }
    expires_at { 30.days.from_now }
  end

  factory :shared_search_feedback do
    association :shared_search
    candidate_id { SecureRandom.uuid }
    given_by_email { Faker::Internet.email }
    decision { "approved" }
    rating { Faker::Number.between(from: 1, to: 5) }
    comment { Faker::Lorem.sentence }
  end

  # ──────────────────────────────────────────────
  # Assessments
  # ──────────────────────────────────────────────

  factory :big_five_question do
    text { Faker::Lorem.sentence }
    trait { %w[openness conscientiousness extroversion agreeableness neuroticism].sample }
    polarity { "positive" }
    is_active { true }
  end

  factory :big_five_role_profile do
    name { Faker::Job.title }
    role_category { "engineering" }
    seniority_level { "senior" }
    is_active { true }
  end

  factory :technical_question do
    title { Faker::Lorem.sentence(word_count: 5) }
    question_type { "multiple_choice" }
    difficulty { "medium" }
    area { "backend" }
    is_active { true }
  end

  factory :technical_test_template do
    name { "Test - #{Faker::Job.title}" }
    area { "backend" }
    total_time { 60 }
    passing_score { 70.0 }
    is_active { true }
  end

  factory :benefit_template do
    name { Faker::Lorem.word.capitalize }
    category { "health" }
    is_active { true }
  end

  # ──────────────────────────────────────────────
  # Candidate Extensions
  # ──────────────────────────────────────────────

  factory :candidate_experience do
    association :candidate
    company_name { Faker::Company.name }
    title { Faker::Job.title }
    start_date { "2020-01" }
    end_date { "2023-06" }
  end

  factory :candidate_education do
    association :candidate
    institution { Faker::University.name }
    degree { "bachelor" }
    field_of_study { Faker::Educator.subject }
  end

  factory :candidate_attachment do
    association :candidate
    file_name { "resume.pdf" }
    file_url { Faker::Internet.url }
    file_type { "application/pdf" }
  end

  # ──────────────────────────────────────────────
  # Message (not previously factoryed)
  # ──────────────────────────────────────────────

  factory :message do
    reference_type { "User" }
    reference_id { SecureRandom.uuid }
    content { Faker::Lorem.paragraph }
    status { 0 }
    role { 1 }
    entity { "chat" }
  end
end
