# frozen_string_literal: true

class AgingApplySerializer
  include JSONAPI::Serializer

  set_type :aging_apply

  attributes :cv_match, :total_score

  attribute :apply_id, &:id

  attribute :candidate_name do |record|
    record.try(:candidate_name)
  end

  attribute :candidate_email do |record|
    record.try(:candidate_email)
  end

  attribute :job_id do |record|
    record.job_id
  end

  attribute :job_title do |record|
    record.try(:job_title)
  end

  attribute :current_stage do |record|
    record.try(:stage_name)
  end

  attribute :current_stage_status do |record|
    SelectiveProcess.statuses.key(record.try(:stage_status).to_i) rescue record.try(:stage_status)
  end

  attribute :days_in_stage do |record|
    record.try(:days_in_stage).to_i
  end

  attribute :last_activity_at do |record|
    record.try(:last_activity_at)
  end

  attribute :severity do |record|
    days = record.try(:days_in_stage).to_i
    if days >= 5
      "critical"
    elsif days >= 3
      "warning"
    else
      "attention"
    end
  end
end
