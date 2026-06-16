# frozen_string_literal: true

# GAP-10-004: LGPD data retention for Rails-managed candidates.
#
# Candidates whose lgpd_expires_at has passed are anonymized:
# PII fields are nullified; the record itself is kept for referential
# integrity (evaluation_candidates, interviews, etc.).
#
# Mirrors lia-agent-system app/domains/lgpd/services/lgpd_cleanup_service.py.
# LGPD Art. 16, Art. 18 — minimização + right to erasure.
#
# Run via schedule.yml (daily at 02:00 UTC) or manually:
#   LgpdCandidateCleanupJob.perform_later
class LgpdCandidateCleanupJob < ApplicationJob
  queue_as :low_priority

  # PII columns to nullify when a candidate's retention period has expired.
  # Never delete the row — referential integrity must be preserved.
  PII_COLUMNS = %w[
    name
    surname
    email
    secondary_email
    mobile_phone
    phone
    secondary_phone
    cpf
    data_raw
  ].freeze

  # Sentinel value written to `name` so the record is identifiable as anonymized.
  ANONYMIZED_SENTINEL = "[LGPD-ANONYMIZED]"

  def perform(dry_run: false)
    expired = Candidate.where("lgpd_expires_at IS NOT NULL AND lgpd_expires_at < ?", Time.current)

    count = expired.count
    Rails.logger.info("[LgpdCandidateCleanupJob] #{dry_run ? '[DRY-RUN] ' : ''}Found #{count} candidates with expired LGPD retention")
    return if count.zero?

    expired.find_each do |candidate|
      if dry_run
        Rails.logger.info("[LgpdCandidateCleanupJob] [DRY-RUN] Would anonymize candidate id=#{candidate.id}")
      else
        anonymize!(candidate)
      end
    end

    Rails.logger.info("[LgpdCandidateCleanupJob] #{dry_run ? '[DRY-RUN] ' : ''}Processed #{count} candidates")
  end

  private

  def anonymize!(candidate)
    updates = PII_COLUMNS.each_with_object({}) do |col, h|
      h[col] = nil if candidate.class.column_names.include?(col)
    end
    # Keep a non-null sentinel in `name` for queries that require presence
    updates["name"] = ANONYMIZED_SENTINEL if updates.key?("name")
    # Clear lgpd_expires_at to prevent re-processing
    updates["lgpd_expires_at"] = nil

    candidate.update_columns(updates)
    Rails.logger.info("[LgpdCandidateCleanupJob] Anonymized candidate id=#{candidate.id}")
  rescue => e
    Rails.logger.error("[LgpdCandidateCleanupJob] Failed to anonymize candidate id=#{candidate.id}: #{e.message}")
    # Continue — do not abort the batch on a single failure
  end
end
