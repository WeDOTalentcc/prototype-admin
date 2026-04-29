class EvaluationCandidateSerializer
  include JSONAPI::Serializer

  attributes :candidate_id, :evaluation_id, :apply_id, :job_id, :date_expiration, :date_view, :completed, :is_deleted, :candidate_uid, :uid, :created_at, :updated_at,
             :candidate_name, :candidate_email, :evaluation_name, :evaluation_description, :ai_feedback, :score, :evaluation_summary, :is_screening,
             :wsi_classification, :wsi_level, :wsi_summary, :wsi_big_five_observed, :notification_channels, :f11_report_json,
             :evaluation_type, :phone_call_status, :scheduled_at, :custom_invite_message, :answers_hash, :wsi_decision

  attribute :scheduling_url do |ec|
    ec.scheduling_url
  end
end
