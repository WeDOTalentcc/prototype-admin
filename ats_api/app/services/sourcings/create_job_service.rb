module Sourcings
  class CreateJobService
    Result = Struct.new(:success?, :job, :error, :applies_created, keyword_init: true)

    def self.call(sourcing:, job_attributes:, candidate_ids:, user:)
      new(sourcing: sourcing, job_attributes: job_attributes, candidate_ids: candidate_ids, user: user).call
    end

    def initialize(sourcing:, job_attributes:, candidate_ids:, user:)
      @sourcing = sourcing
      @job_attributes = (job_attributes || {}).to_h
      @candidate_ids = Array(candidate_ids)
      @user = user
    end

    def call
      return Result.new(success?: false, error: "sourcing required") unless @sourcing
      return Result.new(success?: false, error: "title é obrigatório") if job_title.blank?

      Job.transaction do
        job = create_job
        return Result.new(success?: false, error: "failed to create job") unless job.persisted?

        return Result.new(success?: true, job: job, applies_created: 0) if @candidate_ids.empty?

        move = MoveToJobService.call(
          sourcing: @sourcing,
          job_id: job.id,
          candidate_ids: @candidate_ids,
          user: @user
        )

        unless move.success?
          raise ActiveRecord::Rollback
        end

        Result.new(success?: true, job: job, applies_created: (move.applies_created || []).size)
      end || Result.new(success?: false, error: "Falha ao adicionar candidatos — nenhuma alteracao foi salva")
    rescue Sourcings::MoveToJobService::BulkApplyError => e
      Result.new(success?: false, error: e.message)
    end

    private

    def job_title
      @job_attributes[:title] || @job_attributes["title"]
    end

    def create_job
      Job.create(
        @job_attributes.merge(
          account_id: @user.account_id,
          user_id: @user.id
        )
      )
    end
  end
end
