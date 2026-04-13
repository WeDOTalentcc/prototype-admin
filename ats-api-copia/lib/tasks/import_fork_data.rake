# frozen_string_literal: true

require "json"
require "bcrypt"

namespace :fork do
  desc "Import data exported from the Replit fork (JSON files)"
  task import: :environment do
    data_dir = ENV.fetch("FORK_DATA_DIR") { Rails.root.join("lib/tasks/fork_data/fork_export") }
    data_dir = Pathname.new(data_dir)

    unless data_dir.directory?
      abort "ERROR: Data directory not found: #{data_dir}\n" \
            "  Run the Python export script first and place files in lib/tasks/fork_data/fork_export/"
    end

    puts "=" * 60
    puts "Fork Data Import"
    puts "=" * 60
    puts "Data directory: #{data_dir}"
    puts

    # Ensure we have a base account to attach records to
    account = Account.find_or_create_by!(name: "WeDOTalent") do |a|
      a.tenant = "wedotalent"
    end
    puts "Using account: #{account.name} (id=#{account.id})"
    puts

    import_users(data_dir, account)
    import_candidates(data_dir, account)
    import_jobs(data_dir, account)
    import_applies(data_dir, account)
    import_interviews(data_dir, account)
    import_messages(data_dir, account)
    import_conversations(data_dir, account)

    puts
    puts "=" * 60
    puts "Import complete!"
    puts "=" * 60
  end
end

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read_json(data_dir, filename)
  path = data_dir.join(filename)
  unless path.exist?
    puts "  SKIP: #{filename} not found"
    return nil
  end
  data = JSON.parse(path.read)
  puts "  Reading #{filename}: #{data.size} records"
  data
end

def safe_uuid(value)
  return nil if value.blank?
  value.to_s.strip
end

# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

def import_users(data_dir, account)
  puts "--- Importing users ---"
  records = read_json(data_dir, "users.json")
  return if records.nil?

  imported = 0
  skipped = 0

  records.each do |row|
    fork_uuid = safe_uuid(row["id"])
    next if fork_uuid.blank?

    begin
      User.find_or_create_by!(fork_uuid: fork_uuid) do |u|
        u.email           = row["email"].presence || "fork_user_#{fork_uuid[0..7]}@import.local"
        u.name            = row["name"]
        u.role            = row["role"]
        u.status          = row.fetch("status", "active")
        u.permissions     = row["permissions"] || {}
        u.password        = SecureRandom.hex(16) # random password
        u.account         = account
      end
      imported += 1
    rescue ActiveRecord::RecordInvalid => e
      # Likely duplicate email -- try lookup by email and update fork_uuid
      existing = User.find_by(email: row["email"])
      if existing && existing.fork_uuid.blank?
        existing.update_columns(fork_uuid: fork_uuid)
        imported += 1
      else
        puts "    WARN: user #{row['email']}: #{e.message}"
        skipped += 1
      end
    rescue => e
      puts "    ERROR: user #{row['email']}: #{e.message}"
      skipped += 1
    end
  end

  puts "  Users imported: #{imported}, skipped: #{skipped}"
  puts
end

# ---------------------------------------------------------------------------
# Candidates
# ---------------------------------------------------------------------------

def import_candidates(data_dir, account)
  puts "--- Importing candidates ---"
  records = read_json(data_dir, "candidates.json")
  return if records.nil?

  imported = 0
  skipped = 0

  records.each do |row|
    fork_uuid = safe_uuid(row["id"])
    next if fork_uuid.blank?

    begin
      Candidate.find_or_create_by!(fork_uuid: fork_uuid) do |c|
        c.name                        = row["name"].presence || "Imported Candidate"
        c.email                       = row["email"].presence || "fork_#{fork_uuid[0..7]}@import.local"
        c.mobile_phone                = row["phone"] || row["mobile_phone"]
        c.linkedin                    = row["linkedin_url"] || row["linkedin"]
        c.github                      = row["github_url"] || row["github"]
        c.portfolio                   = row["portfolio_url"] || row["portfolio"]
        c.date_birth                  = row["date_of_birth"] || row["date_birth"]
        c.role_name                   = row["current_title"] || row["role_name"]
        c.current_company             = row["current_company"]
        c.cpf                         = row["cpf"]
        c.city                        = row["location_city"] || row["city"]
        c.state                       = row["location_state"] || row["state"]
        c.country                     = row["location_country"] || row["country"]
        c.source                      = row["source"]
        c.avatar_url                  = row["avatar_url"]
        c.curriculum_pdf_url          = row["curriculum_pdf_url"] || row["resume_url"]
        c.curriculum_text             = row["curriculum_text"] || row["resume_text"]
        c.self_introduction           = row["self_introduction"] || row["bio"]

        # Salary expectations
        c.desired_salary              = row["desired_salary_max"] || row["desired_salary"]
        c.current_salary              = row["current_salary"] || 0
        c.clt_expectation             = row["salary_expectation_clt"] || row["clt_expectation"] || 0
        c.pj_expectation              = row["salary_expectation_pj"] || row["pj_expectation"] || 0
        c.freelance_expectation       = row["salary_expectation_freelance"] || 0
        c.currency                    = row["salary_currency"] || "BRL"

        # Diversity fields
        c.diversity_race_ethnicity    = row["diversity_race_ethnicity"]
        c.diversity_disability        = row["diversity_disability"]
        c.diversity_disability_type   = row["diversity_disability_type"]
        c.diversity_lgbtqia           = row["diversity_lgbtqia"]
        c.diversity_refugee           = row["diversity_refugee"]
        c.diversity_age_50_plus       = row["diversity_age_50_plus"]
        c.diversity_indigenous        = row["diversity_indigenous"]
        c.diversity_documents         = row["diversity_documents"] || {}
        c.diversity_self_declared_at  = row["diversity_self_declared_at"]
        c.diversity_document_deadline = row["diversity_document_deadline"]

        # Professional fields
        c.seniority_level             = row["seniority_level"]
        c.years_of_experience         = row["years_of_experience"]
        c.technical_skills            = Array(row["technical_skills"])
        c.soft_skills                 = Array(row["soft_skills"])
        c.languages                   = Array(row["languages"])
        c.certifications              = Array(row["certifications"])

        c.account                     = account
      end
      imported += 1
    rescue ActiveRecord::RecordInvalid => e
      # Duplicate email -- link existing record
      existing = Candidate.find_by(email: row["email"])
      if existing && existing.fork_uuid.blank?
        existing.update_columns(fork_uuid: fork_uuid)
        imported += 1
      else
        puts "    WARN: candidate #{row['email']}: #{e.message}"
        skipped += 1
      end
    rescue => e
      puts "    ERROR: candidate #{row['email']}: #{e.message}"
      skipped += 1
    end
  end

  puts "  Candidates imported: #{imported}, skipped: #{skipped}"
  puts
end

# ---------------------------------------------------------------------------
# Jobs (from job_vacancies)
# ---------------------------------------------------------------------------

def import_jobs(data_dir, account)
  puts "--- Importing jobs (from job_vacancies) ---"
  records = read_json(data_dir, "job_vacancies.json")
  return if records.nil?

  # Use the first available user as the job owner
  default_user = User.where(account: account).first || User.first
  unless default_user
    puts "  ERROR: No users found -- import users first"
    return
  end

  imported = 0
  skipped = 0

  records.each do |row|
    fork_uuid = safe_uuid(row["id"])
    next if fork_uuid.blank?

    begin
      Job.find_or_create_by!(fork_uuid: fork_uuid) do |j|
        j.title                          = row["title"].presence || "Imported Job"
        j.description                    = row["description"].presence || "Imported from fork"
        j.user                           = default_user
        j.account                        = account
        j.status                         = row.fetch("status", "active")
        j.department                     = row["department"]
        j.employment_type                = row["employment_type"]
        j.seniority_level                = row["seniority_level"]
        j.priority                       = row["priority"]
        j.urgency_level                  = row["urgency_level"]

        # Requirements
        j.technical_requirements         = row["technical_requirements"] || []
        j.behavioral_competencies        = row["behavioral_competencies"] || []
        j.screening_questions            = row["screening_questions"] || []
        j.interview_stages               = row["interview_stages"] || []
        j.languages                      = row["languages"] || []

        # Salary
        j.salary_range                   = row["salary_range"] || {}
        j.bonus_range                    = row["bonus_range"] || {}
        j.benefits                       = Array(row["benefits"])

        # Deadlines
        j.deadline_screening             = row["deadline_screening"]
        j.deadline_shortlist             = row["deadline_shortlist"]
        j.deadline_closing               = row["deadline_closing"]

        # Team
        j.manager                        = row["manager"]
        j.manager_email                  = row["manager_email"]
        j.recruiter                      = row["recruiter"]
        j.recruiter_email                = row["recruiter_email"]

        # Location
        j.city                           = row["city"]
        j.state                          = row["state"]
        j.country                        = row["country"]
        j.is_remote                      = row["is_remote"]

        # Affirmative action
        j.is_affirmative                 = row["is_affirmative"]
        j.affirmative_criteria_primary   = row["affirmative_criteria_primary"]
        j.affirmative_criteria_secondary = row["affirmative_criteria_secondary"]
        j.affirmative_description        = row["affirmative_description"]

        # Tags
        j.tags                           = Array(row["tags"])
      end
      imported += 1
    rescue => e
      puts "    ERROR: job '#{row['title']}' (#{fork_uuid}): #{e.message}"
      skipped += 1
    end
  end

  puts "  Jobs imported: #{imported}, skipped: #{skipped}"
  puts
end

# ---------------------------------------------------------------------------
# Applies (from vacancy_candidates)
# ---------------------------------------------------------------------------

def import_applies(data_dir, account)
  puts "--- Importing applies (from vacancy_candidates) ---"
  records = read_json(data_dir, "vacancy_candidates.json")
  return if records.nil?

  # Build lookup caches: fork_uuid -> Rails id
  candidate_map = Candidate.where.not(fork_uuid: nil).pluck(:fork_uuid, :id).to_h
  job_map       = Job.where.not(fork_uuid: nil).pluck(:fork_uuid, :id).to_h

  imported = 0
  skipped = 0

  records.each do |row|
    fork_uuid = safe_uuid(row["id"])

    candidate_fork_uuid = safe_uuid(row["candidate_id"])
    job_fork_uuid       = safe_uuid(row["vacancy_id"] || row["job_vacancy_id"])

    candidate_id = candidate_map[candidate_fork_uuid]
    job_id       = job_map[job_fork_uuid]

    unless candidate_id
      puts "    WARN: candidate not found for fork_uuid=#{candidate_fork_uuid}"
      skipped += 1
      next
    end

    unless job_id
      puts "    WARN: job not found for fork_uuid=#{job_fork_uuid}"
      skipped += 1
      next
    end

    begin
      # Find the first selective process for this job (web_submission stage)
      selective_process = SelectiveProcess.where(job_id: job_id).order(:position).first
      unless selective_process
        puts "    WARN: no selective process for job_id=#{job_id} -- skipping"
        skipped += 1
        next
      end

      lookup_attrs = if fork_uuid.present?
                       { fork_uuid: fork_uuid }
                     else
                       { candidate_id: candidate_id, job_id: job_id }
                     end

      Apply.find_or_create_by!(lookup_attrs) do |a|
        a.candidate_id        = candidate_id
        a.job_id              = job_id
        a.selective_process   = selective_process
        a.status              = row.fetch("status", "active")
        a.lia_score           = row["lia_score"]
        a.match_percentage    = row["match_percentage"]
        a.source              = row["source"] || row["origin"]
        a.current_stage       = row["stage"]
        a.stage_entered_at    = row["stage_entered_at"]
        a.additional_data     = row["additional_data"] || {}
        a.fork_uuid           = fork_uuid if fork_uuid.present? && !lookup_attrs.key?(:fork_uuid)
      end
      imported += 1
    rescue => e
      puts "    ERROR: apply (candidate=#{candidate_fork_uuid}, job=#{job_fork_uuid}): #{e.message}"
      skipped += 1
    end
  end

  puts "  Applies imported: #{imported}, skipped: #{skipped}"
  puts
end

# ---------------------------------------------------------------------------
# Interviews
# ---------------------------------------------------------------------------

def import_interviews(data_dir, account)
  puts "--- Importing interviews ---"
  records = read_json(data_dir, "interviews.json")
  return if records.nil?

  # Build lookup caches
  candidate_map = Candidate.where.not(fork_uuid: nil).pluck(:fork_uuid, :id).to_h
  job_map       = Job.where.not(fork_uuid: nil).pluck(:fork_uuid, :id).to_h

  imported = 0
  skipped = 0

  records.each do |row|
    fork_id = safe_uuid(row["id"])

    # Resolve candidate -- may be fork UUID or already a Rails id
    candidate_fork_uuid = safe_uuid(row["candidate_id"])
    job_fork_uuid       = safe_uuid(row["job_vacancy_id"])

    candidate_id = candidate_map[candidate_fork_uuid] || candidate_fork_uuid
    job_id       = job_map[job_fork_uuid] || job_fork_uuid

    begin
      Interview.find_or_create_by!(id: fork_id) do |i|
        i.candidate_id              = candidate_id.to_s
        i.candidate_name            = row["candidate_name"]
        i.candidate_email           = row["candidate_email"]
        i.job_vacancy_id            = job_id.to_s
        i.job_title                 = row["job_title"]
        i.title                     = row["title"]
        i.description               = row["description"]
        i.interview_type            = row["interview_type"]
        i.interview_mode            = row.fetch("interview_mode", "video")
        i.interviewer_name          = row["interviewer_name"]
        i.interviewer_email         = row["interviewer_email"]
        i.additional_interviewers   = row["additional_interviewers"] || []
        i.start_time                = row["start_time"]
        i.end_time                  = row["end_time"]
        i.timezone                  = row.fetch("timezone", "America/Sao_Paulo")
        i.duration_minutes          = row["duration_minutes"]
        i.location                  = row["location"]
        i.meeting_url               = row["meeting_url"]
        i.meeting_platform          = row["meeting_platform"]
        i.status                    = row.fetch("status", "scheduled")
        i.confirmation_status       = row.fetch("confirmation_status", "pending")
        i.application_stage         = row["application_stage"]
        i.feedback                  = row["feedback"] || {}
        i.interviewer_notes         = row["interviewer_notes"]
        i.lia_preparation_notes     = row["lia_preparation_notes"] || {}
        i.lia_suggested_questions   = row["lia_suggested_questions"] || []
        i.company_id                = account.id.to_s
        i.created_by                = row["created_by"]
      end
      imported += 1
    rescue => e
      puts "    ERROR: interview #{fork_id}: #{e.message}"
      skipped += 1
    end
  end

  puts "  Interviews imported: #{imported}, skipped: #{skipped}"
  puts
end

# ---------------------------------------------------------------------------
# Messages
# ---------------------------------------------------------------------------

def import_messages(data_dir, account)
  puts "--- Importing messages ---"
  records = read_json(data_dir, "messages.json")
  return if records.nil?

  imported = 0
  skipped = 0

  records.each do |row|
    begin
      # Use the fork id or a combination of fields for idempotency
      fork_id = row["id"]

      # Messages table uses bigint id, so we cannot use the fork UUID as id.
      # Use metadata to store fork reference for idempotency.
      existing = Message.where("metadata->>'fork_id' = ?", fork_id.to_s).first
      next if existing

      Message.create!(
        content:          row["content"],
        entity:           row.fetch("entity", 0),
        status:           row.fetch("status", 0),
        reference_type:   row.fetch("reference_type", "User"),
        reference_id:     row.fetch("reference_id", 1),
        parent_message_id: row["parent_message_id"],
        account:          account,
        metadata:         (row["metadata"] || {}).merge("fork_id" => fork_id.to_s),
        created_at:       row["created_at"],
        updated_at:       row["updated_at"]
      )
      imported += 1
    rescue => e
      puts "    ERROR: message #{row['id']}: #{e.message}"
      skipped += 1
    end
  end

  puts "  Messages imported: #{imported}, skipped: #{skipped}"
  puts
end

# ---------------------------------------------------------------------------
# Conversations (informational -- may not have a direct Rails model)
# ---------------------------------------------------------------------------

def import_conversations(data_dir, account)
  puts "--- Importing conversations ---"
  records = read_json(data_dir, "conversations.json")
  return if records.nil?

  # Conversations from the fork may map to message threads or a separate model.
  # For now, store as messages with a special reference_type if no Conversation
  # model exists.
  if defined?(Conversation)
    imported = 0
    records.each do |row|
      begin
        Conversation.find_or_create_by!(id: row["id"]) do |c|
          c.assign_attributes(row.slice(*Conversation.column_names).compact)
        end
        imported += 1
      rescue => e
        puts "    ERROR: conversation #{row['id']}: #{e.message}"
      end
    end
    puts "  Conversations imported: #{imported}"
  else
    puts "  INFO: No Conversation model found in Rails. Saving conversations.json"
    puts "        for reference. Data can be imported later when the model is created."
    # Copy to a reference location
    dest = Rails.root.join("lib/tasks/fork_data/conversations_reference.json")
    FileUtils.cp(data_dir.join("conversations.json"), dest) if data_dir.join("conversations.json").exist?
    puts "  Saved to: #{dest}"
  end
  puts
end
