# frozen_string_literal: true

require 'rails_helper'

# ──────────────────────────────────────────────
# Company Config
# ──────────────────────────────────────────────

RSpec.describe ClientAccount, type: :model do
  subject { build(:client_account) }

  it { should have_many(:client_users) }
  it { should have_one(:company_profile) }
  it { should have_many(:subscriptions) }
  it { should have_many(:invoices) }
  it { should have_many(:payment_methods) }
  it { should validate_presence_of(:name) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe ClientUser, type: :model do
  subject { build(:client_user) }

  it { should belong_to(:client_account) }
  it { should validate_presence_of(:company_id) }
  it { should validate_presence_of(:email) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe CompanyProfile, type: :model do
  subject { build(:company_profile) }

  it { should belong_to(:client_account) }
  it { should have_many(:departments) }
  it { should have_many(:benefits) }
  it { should have_many(:culture_values) }
  it { should have_many(:ideal_profiles) }
  it { should have_many(:compensation_policies) }
  it { should validate_presence_of(:name) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe Department, type: :model do
  subject { build(:department) }

  it { should belong_to(:company_profile) }
  it { should belong_to(:parent).optional }
  it { should have_many(:children) }
  it { should have_many(:ideal_profiles) }
  it { should validate_presence_of(:company_id) }
  it { should validate_presence_of(:name) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe Benefit, type: :model do
  subject { build(:benefit) }

  it { should belong_to(:company_profile) }
  it { should validate_presence_of(:company_id) }
  it { should validate_presence_of(:name) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe CultureValue, type: :model do
  subject { build(:culture_value) }

  it { should belong_to(:company_profile) }
  it { should validate_presence_of(:company_id) }
  it { should validate_presence_of(:name) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe IdealProfile, type: :model do
  subject { build(:ideal_profile) }

  it { should belong_to(:company_profile) }
  it { should belong_to(:department).optional }
  it { should validate_presence_of(:company_id) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe CompanyHiringPolicy, type: :model do
  subject { build(:company_hiring_policy) }

  it { should validate_presence_of(:company_id) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe CompensationPolicy, type: :model do
  subject { build(:compensation_policy) }

  it { should belong_to(:company_profile) }
  it { should validate_presence_of(:company_id) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

# ──────────────────────────────────────────────
# Email & Communication
# ──────────────────────────────────────────────

RSpec.describe EmailTemplate, type: :model do
  subject { build(:email_template) }

  it { should have_many(:email_logs) }
  it { should have_many(:recruitment_email_templates) }
  it { should validate_presence_of(:name) }
  it { should validate_presence_of(:subject) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe EmailLog, type: :model do
  subject { build(:email_log) }

  it { should belong_to(:email_template).optional }
  it { should have_many(:email_tracking_events) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe EmailTrackingEvent, type: :model do
  subject { build(:email_tracking_event) }

  it { should belong_to(:email_log) }
  it { should validate_presence_of(:email_log_id) }
  it { should validate_presence_of(:event_type) }
  it { should validate_presence_of(:event_at) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe RecruitmentEmailTemplate, type: :model do
  subject { build(:recruitment_email_template) }

  it { should belong_to(:email_template).optional }
  it { should validate_presence_of(:company_id) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

# ──────────────────────────────────────────────
# Billing
# ──────────────────────────────────────────────

RSpec.describe Subscription, type: :model do
  subject { build(:subscription) }

  it { should belong_to(:client_account) }
  it { should have_many(:invoices) }
  it { should validate_presence_of(:client_account_id) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe Invoice, type: :model do
  subject { build(:invoice) }

  it { should belong_to(:subscription).optional }
  it { should belong_to(:client_account) }
  it { should validate_presence_of(:client_account_id) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe PaymentMethod, type: :model do
  subject { build(:payment_method) }

  it { should belong_to(:client_account) }
  it { should validate_presence_of(:client_account_id) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe AiConsumption, type: :model do
  subject { build(:ai_consumption) }

  it { should validate_presence_of(:company_id) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe AiCreditsBalance, type: :model do
  subject { build(:ai_credits_balance) }

  it { should validate_presence_of(:company_id) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

# ──────────────────────────────────────────────
# LGPD / Consent
# ──────────────────────────────────────────────

RSpec.describe ConsentRecord, type: :model do
  subject { build(:consent_record) }

  it { should have_many(:consent_events) }
  it { should validate_presence_of(:candidate_id) }
  it { should validate_presence_of(:consent_type) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe ConsentVersion, type: :model do
  subject { build(:consent_version) }

  it { should validate_presence_of(:consent_type) }
  it { should validate_presence_of(:version) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe ConsentEvent, type: :model do
  subject { build(:consent_event) }

  it { should belong_to(:consent_record) }
  it { should validate_presence_of(:consent_id) }
  it { should validate_presence_of(:event_type) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe DataSubjectRequest, type: :model do
  subject { build(:data_subject_request) }

  it { should validate_presence_of(:candidate_id) }
  it { should validate_presence_of(:request_type) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe AutomatedDecisionExplanation, type: :model do
  subject { build(:automated_decision_explanation) }

  it { should validate_presence_of(:candidate_id) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe CompanyRetentionPolicy, type: :model do
  subject { build(:company_retention_policy) }

  it { should validate_presence_of(:company_id) }
  it { should validate_presence_of(:data_type) }
  it { should validate_presence_of(:retention_days) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

# ──────────────────────────────────────────────
# Audit
# ──────────────────────────────────────────────

RSpec.describe AuditLog, type: :model do
  subject { build(:audit_log) }

  it { should validate_presence_of(:created_at) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe AuditRetentionPolicy, type: :model do
  subject { build(:audit_retention_policy) }

  it { should validate_presence_of(:company_id) }
  it { should validate_presence_of(:log_type) }
  it { should validate_presence_of(:retention_days) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe AdminAuditLog, type: :model do
  subject { build(:admin_audit_log) }

  it { should validate_presence_of(:admin_user_id) }
  it { should validate_presence_of(:action) }
  it { should validate_presence_of(:created_at) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

# ──────────────────────────────────────────────
# Notifications
# ──────────────────────────────────────────────

RSpec.describe Notification, type: :model do
  subject { build(:notification) }

  it { should belong_to(:user) }
  it { should validate_presence_of(:user_id) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe ChatNotification, type: :model do
  subject { build(:chat_notification) }

  it { should belong_to(:user) }
  it { should validate_presence_of(:user_id) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe NotificationPolicy, type: :model do
  subject { build(:notification_policy) }

  it { should validate_presence_of(:company_id) }
  it { should validate_presence_of(:channel) }
  it { should validate_presence_of(:event_type) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

# ──────────────────────────────────────────────
# Webhooks
# ──────────────────────────────────────────────

RSpec.describe Webhook, type: :model do
  subject { build(:webhook) }

  it { should have_many(:webhook_logs) }
  it { should have_many(:webhook_delivery_logs) }
  it { should validate_presence_of(:company_id) }
  it { should validate_presence_of(:name) }
  it { should validate_presence_of(:url) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe WebhookLog, type: :model do
  subject { build(:webhook_log) }

  it { should belong_to(:webhook) }
  it { should validate_presence_of(:webhook_id) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe WebhookDeliveryLog, type: :model do
  subject { build(:webhook_delivery_log) }

  it { should belong_to(:webhook) }
  it { should validate_presence_of(:webhook_id) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe WebhookRegistration, type: :model do
  subject { build(:webhook_registration) }

  it { should validate_presence_of(:company_id) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

# ──────────────────────────────────────────────
# Interview Scheduling
# ──────────────────────────────────────────────

RSpec.describe Interview, type: :model do
  subject { build(:interview) }

  it { should belong_to(:candidate) }
  it { should belong_to(:job) }
  it { should have_many(:interview_feedbacks) }
  it { should have_many(:interview_notes) }
  it { should have_many(:interview_reminders) }
  it { should have_one(:self_scheduling_link) }
  it { should have_many(:reschedule_histories) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe InterviewFeedback, type: :model do
  subject { build(:interview_feedback) }

  it { should belong_to(:interview) }
  it { should validate_presence_of(:interview_id) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe InterviewNote, type: :model do
  subject { build(:interview_note) }

  it { should belong_to(:interview) }
  it { should validate_presence_of(:interview_id) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe InterviewReminder, type: :model do
  subject { build(:interview_reminder) }

  it { should belong_to(:interview) }
  it { should validate_presence_of(:interview_id) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe CalendarAvailability, type: :model do
  subject { build(:calendar_availability) }

  it { should belong_to(:user) }
  it { should validate_presence_of(:user_id) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe SelfSchedulingLink, type: :model do
  subject { build(:self_scheduling_link) }

  it { should belong_to(:interview) }
  it { should validate_presence_of(:token) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe RescheduleHistory, type: :model do
  subject { build(:reschedule_history) }

  it { should belong_to(:interview) }
  it { should validate_presence_of(:interview_id) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

# ──────────────────────────────────────────────
# ATS Integrations
# ──────────────────────────────────────────────

RSpec.describe IntegrationProvider, type: :model do
  subject { build(:integration_provider) }

  it { should have_many(:integration_connections) }
  it { should validate_presence_of(:name) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe IntegrationConnection, type: :model do
  subject { build(:integration_connection) }

  it { should belong_to(:integration_provider) }
  it { should have_many(:integration_sync_logs) }
  it { should have_many(:integration_webhooks) }
  it { should validate_presence_of(:company_id) }
  it { should validate_presence_of(:provider_id) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe IntegrationSyncLog, type: :model do
  subject { build(:integration_sync_log) }

  it { should belong_to(:integration_connection) }
  it { should validate_presence_of(:connection_id) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe IntegrationWebhook, type: :model do
  subject { build(:integration_webhook) }

  it { should belong_to(:integration_connection) }
  it { should validate_presence_of(:connection_id) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe AtsConnection, type: :model do
  subject { build(:ats_connection) }

  it { should have_many(:ats_sync_jobs) }
  it { should have_many(:ats_candidates) }
  it { should have_many(:ats_webhook_logs) }
  it { should have_many(:ats_job_mappings) }
  it { should validate_presence_of(:company_id) }
  it { should validate_presence_of(:provider) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe AtsSyncJob, type: :model do
  subject { build(:ats_sync_job) }

  it { should belong_to(:ats_connection) }
  it { should validate_presence_of(:connection_id) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe AtsCandidate, type: :model do
  subject { build(:ats_candidate) }

  it { should belong_to(:ats_connection) }
  it { should validate_presence_of(:connection_id) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe AtsWebhookLog, type: :model do
  subject { build(:ats_webhook_log) }

  it { should belong_to(:ats_connection) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe AtsJobMapping, type: :model do
  subject { build(:ats_job_mapping) }

  it { should belong_to(:ats_connection) }
  it { should validate_presence_of(:connection_id) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

# ──────────────────────────────────────────────
# Automation
# ──────────────────────────────────────────────

RSpec.describe RecruitmentAutomation, type: :model do
  subject { build(:recruitment_automation) }

  it { should validate_presence_of(:company_id) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe RecruitmentSla, type: :model do
  subject { build(:recruitment_sla) }

  it { should have_many(:sla_violations) }
  it { should validate_presence_of(:company_id) }
  it { should validate_presence_of(:max_hours) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe SlaViolation, type: :model do
  subject { build(:sla_violation) }

  it { should belong_to(:recruitment_sla) }
  it { should validate_presence_of(:sla_id) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

# ──────────────────────────────────────────────
# Workforce Planning
# ──────────────────────────────────────────────

RSpec.describe HiringPlan, type: :model do
  subject { build(:hiring_plan) }

  it { should belong_to(:department).optional }
  it { should have_many(:planned_headcounts) }
  it { should validate_presence_of(:company_id) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe PlannedHeadcount, type: :model do
  subject { build(:planned_headcount) }

  it { should belong_to(:hiring_plan) }
  it { should validate_presence_of(:hiring_plan_id) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe WorkforceEntry, type: :model do
  subject { build(:workforce_entry) }

  it { should belong_to(:department).optional }
  it { should validate_presence_of(:company_id) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe ImportJob, type: :model do
  subject { build(:import_job) }

  it { should validate_presence_of(:company_id) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

# ──────────────────────────────────────────────
# Templates
# ──────────────────────────────────────────────

RSpec.describe TemplateCategory, type: :model do
  subject { build(:template_category) }

  it { should belong_to(:parent).optional }
  it { should have_many(:children) }
  it { should validate_presence_of(:name) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe JobTemplate, type: :model do
  subject { build(:job_template) }

  it { should have_many(:template_usage_logs) }
  it { should validate_presence_of(:title) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe PipelineTemplate, type: :model do
  subject { build(:pipeline_template) }

  it { should validate_presence_of(:name) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe TemplateUsageLog, type: :model do
  subject { build(:template_usage_log) }

  it { should belong_to(:job_template) }
  it { should validate_presence_of(:template_id) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

# ──────────────────────────────────────────────
# Approvals
# ──────────────────────────────────────────────

RSpec.describe ApprovalRequest, type: :model do
  subject { build(:approval_request) }

  it { should validate_presence_of(:company_id) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe PendingApproval, type: :model do
  subject { build(:pending_approval) }

  it { should belong_to(:approval_request).optional }
  it { should validate_presence_of(:company_id) }
  it { should validate_presence_of(:approver_id) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

# ──────────────────────────────────────────────
# Goals & Shared Searches
# ──────────────────────────────────────────────

RSpec.describe Goal, type: :model do
  subject { build(:goal) }

  it { should belong_to(:user).optional }
  it { should validate_presence_of(:name) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe GoalTemplate, type: :model do
  subject { build(:goal_template) }

  it { should validate_presence_of(:name) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe SharedSearch, type: :model do
  subject { build(:shared_search) }

  it { should have_many(:shared_search_accesses) }
  it { should have_many(:shared_search_feedbacks) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe SharedSearchAccess, type: :model do
  subject { build(:shared_search_access) }

  it { should belong_to(:shared_search) }
  it { should validate_presence_of(:shared_search_id) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe SharedSearchFeedback, type: :model do
  subject { build(:shared_search_feedback) }

  it { should belong_to(:shared_search) }
  it { should validate_presence_of(:shared_search_id) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

# ──────────────────────────────────────────────
# Assessments
# ──────────────────────────────────────────────

RSpec.describe BigFiveQuestion, type: :model do
  subject { build(:big_five_question) }

  it { should validate_presence_of(:text) }
  it { should validate_presence_of(:trait) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe BigFiveRoleProfile, type: :model do
  subject { build(:big_five_role_profile) }

  it { should validate_presence_of(:name) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe TechnicalQuestion, type: :model do
  subject { build(:technical_question) }

  it { should validate_presence_of(:title) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe TechnicalTestTemplate, type: :model do
  subject { build(:technical_test_template) }

  it { should validate_presence_of(:name) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe BenefitTemplate, type: :model do
  subject { build(:benefit_template) }

  it { should validate_presence_of(:name) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

# ──────────────────────────────────────────────
# Candidate Extensions
# ──────────────────────────────────────────────

RSpec.describe CandidateExperience, type: :model do
  subject { build(:candidate_experience) }

  it { should belong_to(:candidate) }
  it { should validate_presence_of(:company_name) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe CandidateEducation, type: :model do
  subject { build(:candidate_education) }

  it { should belong_to(:candidate) }
  it { should validate_presence_of(:institution) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

RSpec.describe CandidateAttachment, type: :model do
  subject { build(:candidate_attachment) }

  it { should belong_to(:candidate) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end

# ──────────────────────────────────────────────
# Message
# ──────────────────────────────────────────────

RSpec.describe Message, type: :model do
  subject { build(:message) }

  it { should belong_to(:account).optional }
  it { should validate_presence_of(:reference_type) }
  it { should validate_presence_of(:reference_id) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end
end
