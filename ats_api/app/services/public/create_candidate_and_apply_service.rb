# frozen_string_literal: true

module Public
  class CreateCandidateAndApplyService
    def self.call(job:, name:, email:, mobile_phone:, curriculum_file: nil, curriculum_text: nil, accept_terms:)
      new(job: job, name: name, email: email, mobile_phone: mobile_phone, curriculum_file: curriculum_file, curriculum_text: curriculum_text, accept_terms: accept_terms).call
    end

    def initialize(job:, name:, email:, mobile_phone:, curriculum_file: nil, curriculum_text: nil, accept_terms:)
      @job = job
      @name = name
      @email = email
      @mobile_phone = mobile_phone
      @curriculum_file = curriculum_file
      @curriculum_text = curriculum_text
      @accept_terms = accept_terms
    end

    def call
      return error("accept_terms must be true") unless @accept_terms == true || @accept_terms == "true"
      return error("name is required") if @name.blank?
      return error("email is required") if @email.blank?
      return error("mobile_phone is required") if @mobile_phone.blank?
      return error("curriculum (file or text) is required") if @curriculum_file.blank? && @curriculum_text.blank?

      selective_process = @job.selective_processes.find_by(status: :screening)
      return error("Job has no screening stage configured") unless selective_process

      candidate = find_or_create_candidate
      return error(candidate) if candidate.is_a?(String)

      existing_apply = Apply.find_existing_apply(candidate.id, @job.id)
      return already_applied_error if existing_apply

      apply = Apply.find_or_create_apply(
        candidate_id: candidate.id,
        job_id: @job.id,
        account_id: @job.account_id,
        selective_process_id: selective_process.id,
        selective_process_status: selective_process.name,
        user_id: nil,
        source: "web_response"
      )

      return error("Failed to create application") unless apply&.persisted?

      enqueue_resume_parser(candidate)

      { success: true, apply: apply, candidate: candidate }
    rescue StandardError => e
      Rails.logger.error "[Public::CreateCandidateAndApplyService] #{e.message}"
      error(e.message)
    end

    private

    def find_or_create_candidate
      candidate = Candidate.find_by(email: @email.strip.downcase, account_id: @job.account_id, is_deleted: false)

      if candidate
        update_candidate(candidate)
        candidate
      else
        create_candidate
      end
    end

    def create_candidate
      candidate = Candidate.new(
        account_id: @job.account_id,
        name: @name.strip,
        email: @email.strip.downcase,
        mobile_phone: @mobile_phone.strip,
        curriculum_text: @curriculum_text.presence,
        accept_terms: true,
        source: "public_application"
      )

      unless candidate.save
        return candidate.errors.full_messages.join(", ")
      end

      candidate.curriculum_pdf.attach(@curriculum_file) if @curriculum_file.present?
      candidate
    end

    def update_candidate(candidate)
      attrs = {
        name: @name.strip,
        mobile_phone: @mobile_phone.strip,
        accept_terms: true
      }
      attrs[:curriculum_text] = @curriculum_text if @curriculum_text.present?
      candidate.update(attrs)
      candidate.curriculum_pdf.attach(@curriculum_file) if @curriculum_file.present?
      candidate
    end

    def error(message)
      { success: false, error: message }
    end

    def already_applied_error
      { success: false, already_applied: true, error: "This email has already been registered for this job" }
    end

    def enqueue_resume_parser(candidate)
      return unless @curriculum_file.present? || @curriculum_text.present?

      Candidates::ResumeParserJob.perform_async(
        "candidate_id" => candidate.id,
        "account_id" => @job.account_id,
        "additional_data" => {
          "name" => @name.strip,
          "email" => @email.strip.downcase,
          "phone" => @mobile_phone.strip
        }
      )
    end
  end
end
