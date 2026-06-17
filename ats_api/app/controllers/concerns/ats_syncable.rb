# frozen_string_literal: true

module AtsSyncable
  extend ActiveSupport::Concern

  private

  def sync_candidate_to_ats(candidate)
    return unless should_sync_to_ats?(candidate.account)

    AtsSync::CandidateJob.perform_in(2.seconds, candidate.id, candidate.account_id)
  end

  def sync_apply_to_ats(apply)
    return unless should_sync_to_ats?(apply.account)

    AtsSync::ProcessApplyWithEnrichmentJob.perform_in(2.seconds, apply.id, apply.account_id)
  end

  def should_sync_to_ats?(account)
    return false unless AtsSync.config.enabled?
    return false unless account&.ats_provider.present?

    true
  end
end
