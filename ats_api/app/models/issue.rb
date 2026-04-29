# frozen_string_literal: true

class Issue < ApplicationRecord
  self.inheritance_column = :_type_disabled

  include Searchable

  enum type: {
    nao_informado: 0,
    screening: 1
  }, _prefix: :issue

  enum status: {
    pending: 0,
    received: 1,
    answered: 2
  }

  ISSUE_TYPE_LABELS = {
    nao_informado: "Não informado",
    screening: "Screening"
  }.freeze

  STATUS_LABELS = {
    pending: "Pendente",
    received: "Recebido",
    answered: "Respondido"
  }.freeze

  belongs_to :account
  belongs_to :candidate
  belongs_to :evaluation
  belongs_to :evaluation_candidate
  belongs_to :question, optional: true
  belongs_to :job, optional: true

  validates :text, presence: true
  validates :account_id, :candidate_id, :evaluation_id, :evaluation_candidate_id, presence: true

  after_create :send_screening_notification_email, if: :issue_screening?

  def self.search_fields
    %i[id text issue_type status]
  end

  def search_data
    {
      id: id,
      text: text&.downcase,
      issue_type: type,
      status: status,
      account_id: account_id,
      candidate_id: candidate_id,
      evaluation_id: evaluation_id,
      evaluation_candidate_id: evaluation_candidate_id,
      question_id: question_id,
      job_id: job_id,
      reference_type: reference_type,
      reference_id: reference_id,
      created_at: created_at,
      updated_at: updated_at
    }
  end

  def self.agg_search_array(_params = {})
    {
      issue_type: { field: "issue_type", limit: 5 },
      status: { field: "status", limit: 5 },
      account_id: { field: "account_id", limit: 25 },
      candidate_id: { field: "candidate_id", limit: 25 },
      evaluation_id: { field: "evaluation_id", limit: 25 }
    }
  end

  private

  def send_screening_notification_email
    Issues::ScreeningNotificationJob.perform_later(id, account_id)
  rescue StandardError => e
    Rails.logger.error("[Issue] Falha ao enviar e-mail de screening: #{e.class} - #{e.message}")
    Rails.logger.error(e.backtrace.first(5).join("\n"))
  end
end
