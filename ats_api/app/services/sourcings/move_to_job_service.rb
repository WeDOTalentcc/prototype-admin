module Sourcings
  class MoveToJobService
    BulkApplyError = Class.new(StandardError)

    Result = Struct.new(:success?, :applies_created, :skipped, :error, keyword_init: true)

    def self.call(sourcing:, job_id:, candidate_ids:, user:)
      new(sourcing: sourcing, job_id: job_id, candidate_ids: candidate_ids, user: user).call
    end

    def initialize(sourcing:, job_id:, candidate_ids:, user:)
      @sourcing = sourcing
      @job_id = job_id
      @candidate_ids = Array(candidate_ids).map(&:to_i).reject(&:zero?)
      @user = user
    end

    def call
      return Result.new(success?: false, error: "sourcing required") unless @sourcing
      return Result.new(success?: false, error: "job_id required") if @job_id.blank?
      return Result.new(success?: false, error: "candidate_ids required") if @candidate_ids.empty?

      job = find_job
      return Result.new(success?: false, error: "job not found") unless job

      created, skipped = build_applies(job)
      Result.new(success?: true, applies_created: created, skipped: skipped)
    rescue BulkApplyError => e
      Result.new(success?: false, error: e.message)
    end

    private

    def find_job
      Job.find_by(id: @job_id, account_id: @user.account_id)
    end

    def build_applies(job)
      created = []
      skipped = []

      ActiveRecord::Base.transaction do
        @candidate_ids.each do |candidate_id|
          existing = Apply.find_by(candidate_id: candidate_id, job_id: job.id, account_id: @user.account_id)
          if existing
            skipped << candidate_id
            next
          end

          apply = Apply.create!(
            candidate_id: candidate_id,
            job_id: job.id,
            account_id: @user.account_id,
            user_id: @user.id,
            source: "talent_pool"
          )

          created << apply.id
        end
      end

      [ created, skipped ]
    rescue ActiveRecord::RecordInvalid => e
      raise BulkApplyError, "Falha ao adicionar candidato #{e.record.candidate_id}: #{e.record.errors.full_messages.join(", ")}"
    end
  end
end
