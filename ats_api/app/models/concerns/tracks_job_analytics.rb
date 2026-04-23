module TracksJobAnalytics
  extend ActiveSupport::Concern

  included do
    after_commit :enqueue_job_analytics_refresh, on: %i[create update destroy]
  end

  private

  def enqueue_job_analytics_refresh
    jid = resolve_job_id_for_analytics
    return unless jid

    account = resolve_account_for_analytics
    return unless account

    Jobs::RefreshAnalyticsJob.enqueue(jid, account.id)
  end

  def resolve_job_id_for_analytics
    return job_id if respond_to?(:job_id) && job_id.present?
    return apply.job_id if respond_to?(:apply) && apply&.job_id.present?
    return reference_id if respond_to?(:reference_type) && reference_type == "Job"

    nil
  end

  def resolve_account_for_analytics
    return account if respond_to?(:account) && account.present?
    return job.account if respond_to?(:job) && job&.account.present?
    return apply.job.account if respond_to?(:apply) && apply&.job&.account.present?

    nil
  end
end
