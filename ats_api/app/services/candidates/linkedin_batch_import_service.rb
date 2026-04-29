# frozen_string_literal: true

module Candidates
  class LinkedinBatchImportService
    def initialize(job:, selective_process:, linkedin_urls:, account:, user:)
      @job = job
      @selective_process = selective_process
      @linkedin_urls = Array(linkedin_urls)
      @account = account
      @user = user
    end

    def call
      return error("No LinkedIn URLs provided") if linkedin_urls.empty?

      results = []

      linkedin_urls.each_with_index do |url, index|
        result = process_url(url, index)
        results << result
      end

      succeeded = results.count { |r| r[:success] }
      failed = results.count { |r| !r[:success] }

      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.info "✅ [LinkedinBatchImportService] Import finished"
      Rails.logger.info "   Total: #{results.size} | Succeeded: #{succeeded} | Failed: #{failed}"
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

      { success: true, results: results, total: results.size, succeeded: succeeded, failed: failed }
    end

    private

    attr_reader :job, :selective_process, :linkedin_urls, :account, :user

    def process_url(url, index)
      Rails.logger.info "🔄 [LinkedinBatchImportService] Processing #{index + 1}/#{linkedin_urls.size}: #{url}"

      profile_data = parse_linkedin_profile(url)
      return { success: false, url: url, error: "Failed to parse LinkedIn profile" } unless profile_data

      candidate = find_or_create_candidate(profile_data, url)
      return { success: false, url: url, error: "Failed to create candidate" } unless candidate

      LinkedinDataProcessor.new(candidate, profile_data).process_all

      apply = Apply.find_or_create_apply(
        candidate_id: candidate.id,
        job_id: job.id,
        account_id: account.id,
        selective_process_id: selective_process.id,
        selective_process_status: selective_process.status,
        user_id: user.id
      )

      Rails.logger.info "✅ [LinkedinBatchImportService] Candidate##{candidate.id} → Apply##{apply&.id}"

      { success: true, url: url, candidate_id: candidate.id, apply_id: apply&.id }
    rescue Apify::LinkedinProfileParserService::RateLimitError => e
      Rails.logger.error "❌ [LinkedinBatchImportService] Rate limited on #{url}: #{e.message}"
      { success: false, url: url, error: "Rate limited" }
    rescue StandardError => e
      Rails.logger.error "❌ [LinkedinBatchImportService] Error processing #{url}: #{e.message}"
      { success: false, url: url, error: e.message }
    end

    def parse_linkedin_profile(url)
      results = Apify::LinkedinProfileParserService.parse(
        linkedin_profile_urls: [ url ],
        include_email: true
      )

      result = results&.first
      return nil if result.blank? || (result.is_a?(Hash) && result[:error])

      result
    end

    def find_or_create_candidate(profile_data, url)
      basic_info = profile_data[:basic_info] || profile_data["basic_info"] || {}
      linkedin_slug = extract_linkedin_slug(url)

      candidate = find_existing_candidate(basic_info, linkedin_slug)
      return candidate if candidate

      name = basic_info[:fullname] || basic_info["fullname"] || linkedin_slug
      email = basic_info[:email] || basic_info["email"]
      profile_url = basic_info[:profile_url] || basic_info["profile_url"] || url

      Candidate.create!(
        name: name,
        email: email,
        linkedin: profile_url,
        account_id: account.id,
        source: "linkedin_import"
      )
    rescue ActiveRecord::RecordInvalid => e
      Rails.logger.error "❌ [LinkedinBatchImportService] Failed to create candidate: #{e.message}"
      nil
    end

    def find_existing_candidate(basic_info, linkedin_slug)
      email = basic_info[:email] || basic_info["email"]

      conditions = []
      values = {}

      if email.present?
        conditions << "email = :email"
        values[:email] = email
      end

      if linkedin_slug.present?
        conditions << "linkedin ILIKE :linkedin"
        values[:linkedin] = "%#{linkedin_slug}%"
      end

      return nil if conditions.empty?

      Candidate.where(account_id: account.id)
               .where(conditions.join(" OR "), values)
               .first
    end

    def extract_linkedin_slug(url)
      return url unless url.include?("/")

      url.split("/in/").last&.split("/")&.first&.split("?")&.first
    end

    def error(message)
      { success: false, error: message }
    end
  end
end
