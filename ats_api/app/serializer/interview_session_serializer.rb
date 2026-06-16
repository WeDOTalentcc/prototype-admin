# frozen_string_literal: true

class InterviewSessionSerializer
  include JSONAPI::Serializer

  attributes :token, :status, :interview_type, :duration_minutes,
             :language, :recommendation

  attribute :score do |session|
    session.score&.round(2)
  end

  attribute :started_at do |session|
    session.started_at&.iso8601
  end

  attribute :completed_at do |session|
    session.completed_at&.iso8601
  end

  attribute :expires_at do |session|
    session.expires_at&.iso8601
  end

  attribute :created_at do |session|
    session.created_at.iso8601
  end

  attribute :public_url do |session|
    session.public_url
  end

  attribute :candidate_id do |session|
    session.candidate_id
  end

  attribute :candidate_name do |session|
    session.candidate_context["name"]
  end

  attribute :job_id do |session|
    session.job_id
  end

  attribute :job_title do |session|
    session.job_context["title"]
  end

  attribute :evaluation_id do |session|
    session.evaluation_id
  end

  attribute :evaluation_candidate_id do |session|
    session.evaluation_candidate_id
  end

  attribute :apply_id do |session|
    session.apply_id
  end

  attribute :questions_count do |session|
    session.questions_snapshot.size
  end

  attribute :created_by_name do |session|
    session.created_by&.name
  end

  attribute :report do |session|
    session.report if session.status.in?(%w[completed scored])
  end

  attribute :transcript do |session|
    session.transcript if session.status.in?(%w[completed scored])
  end
end
