class SelectiveProcess < ApplicationRecord
  include Searchable

  enable_autocomplete :name

  belongs_to :job, optional: true
  belongs_to :account
  belongs_to :workflow_template, optional: true
  has_many :applies, dependent: :nullify

  validates :name, presence: true
  validates :status, presence: true
  validates :external_id, uniqueness: { allow_nil: true, scope: :account_id }

  scope :active, -> { where(is_deleted: false) }

  enum status: {
    web_submission: 0,
    screening: 1,
    interview: 2,
    rejected: 3,
    hired: 4
  }

  STATUS_COLORS = {
    web_submission: "#a8ced5",
    screening: "#d5bfa8",
    interview: "#a8d5b7",
    hired: "#bfa8d5",
    rejected: "#FCA5A5"
  }.freeze

  INTERVIEW_SUB_STATUSES = [
    { code: "invite_sent",  display_name: "Convite Enviado" },
    { code: "scheduled",    display_name: "Agendada" },
    { code: "confirmed",    display_name: "Confirmada" },
    { code: "completed",    display_name: "Realizada" },
    { code: "no_show",      display_name: "No-show" }
  ].freeze

  REJECTED_SUB_STATUSES = [
    { code: "profile_mismatch",        display_name: "Perfil fora do esperado" },
    { code: "salary_expectation",      display_name: "Expectativa salarial incompatível" },
    { code: "no_show_interview",       display_name: "Faltou na entrevista" },
    { code: "better_candidate",        display_name: "Outro candidato selecionado" },
    { code: "lack_technical_skills",   display_name: "Falta de habilidades técnicas" },
    { code: "culture_fit",             display_name: "Fit cultural incompatível" },
    { code: "location_mobility",       display_name: "Disponibilidade de localização/mobilidade" },
    { code: "lack_experience",         display_name: "Experiência insuficiente" },
    { code: "overqualified",           display_name: "Perfil acima do esperado" },
    { code: "communication_skills",    display_name: "Habilidades de comunicação insatisfatórias" },
    { code: "candidate_withdrew",      display_name: "Candidato desistiu do processo" },
    { code: "no_response",             display_name: "Candidato não retornou contato" },
    { code: "position_cancelled",      display_name: "Vaga cancelada" },
    { code: "lack_education",          display_name: "Requisitos de formação não atendidos" },
    { code: "behavioral_issues",       display_name: "Questões comportamentais identificadas" },
    { code: "background_check_failed", display_name: "Verificação de antecedentes reprovado" },
    { code: "reference_check_failed",  display_name: "Verificação de referências reprovada" },
    { code: "internal_candidate",      display_name: "Candidato interno selecionado" },
    { code: "wrong_position",          display_name: "Candidato aplicou para vaga errada" },
    { code: "other",                   display_name: "Outro motivo" }
  ].freeze

  DEFAULT_SUB_STATUSES_BY_STATUS = {
    interview: INTERVIEW_SUB_STATUSES,
    rejected:  REJECTED_SUB_STATUSES
  }.freeze

  NAME_STATUS_INFERENCE = [
    [ /interview/i, :interview ]
  ].freeze

  before_create :infer_status_from_name

  private

  def infer_status_from_name
    inferred = NAME_STATUS_INFERENCE.find { |pattern, _| name.to_s.match?(pattern) }&.last
    self.status = inferred if inferred && web_submission?
  end

  public

  def self.default_process
    [
      { name: "Funil",      position: 0, status: statuses[:web_submission], color: STATUS_COLORS[:web_submission], sub_status: [] },
      { name: "Triagem",    position: 1, status: statuses[:screening],      color: STATUS_COLORS[:screening],      sub_status: [] },
      { name: "Entrevista", position: 2, status: statuses[:interview],      color: STATUS_COLORS[:interview],      sub_status: INTERVIEW_SUB_STATUSES },
      { name: "Reprovados", position: 3, status: statuses[:rejected],       color: STATUS_COLORS[:rejected],       sub_status: REJECTED_SUB_STATUSES }
    ]
  end

  # def self.make_sub_status(status)
  #   sub_statuses = []
  #   SelectiveProcess.sub_status(status).each do |sub_status|
  #     sub_statuses.push({
  #                         name: sub_status,
  #                         color: SelectiveProcess.general_sub_status_colors.dig(sub_status)
  #                       })
  #   end

  #   sub_statuses
  # end

  # def self.sub_status_insert(selective_process, item)
  #   unless selective_process.sub_status.empty?
  #     status_to_include = selective_process.sub_status
  #     make_sub_status(item[:status]).each do |sub_status_to_make|
  #       next if selective_process.sub_status.nil? || selective_process.sub_status.empty?

  #       sub_status_map = selective_process.sub_status.map { |val| val["name"].downcase }
  #       next if sub_status_map.include?(sub_status_to_make[:name].downcase)

  #       status_to_include.push({
  #         "name"=> sub_status_to_make[:name],
  #         "color"=> sub_status_to_make[:color]
  #       })
  #     end
  #     return status_to_include
  #   end

  #   make_sub_status(item[:status])
  # end

  def self.make_a_copy_from_job(job_id, to_job_id)
    selective_processes = SelectiveProcess.where(job_id:)

    selective_processes.each do |selective_process|
      selective_process_new = SelectiveProcess.find_or_create_by(
        name: selective_process[:name],
        position: selective_process[:position],
        status: selective_process[:status],
        job_id: to_job_id,
        duration: selective_process[:duration],
      )

      next unless selective_process_new
    end
  end

  ACTION_BEHAVIOR_MAP = {
    "web_submission" => "intake",
    "screening"      => "screening",
    "interview"      => "scheduling",
    "rejected"       => "conclusion_rejected",
    "hired"          => "conclusion_hired"
  }.freeze

  def action_behavior
    ACTION_BEHAVIOR_MAP[status.to_s] || "passive"
  end

  def sub_status_options
    Array(sub_status).map do |item|
      case item
      when Hash then { code: item["code"] || item[:code], display_name: item["display_name"] || item[:display_name] }
      when String then { code: item, display_name: item }
      end
    end.compact
  end

  def display_name
    name.presence || status.humanize
  end

  def default_color
    STATUS_COLORS[status.to_sym] || "#E5E7EB"
  end

  def color_with_fallback
    color.presence || default_color
  end

  def self.find_by_external_id(external_id)
    find_by(external_id: external_id)
  end

  def self.find_or_create_by_external_id(external_id, attributes = {})
    process = find_by_external_id(external_id)
    return process if process

    create(attributes.merge(external_id: external_id))
  end

  # Soft delete: marca como deletado em vez de remover do banco
  def destroy
    update_column(:is_deleted, true)
  end

  def deleted?
    is_deleted?
  end

  def search_data
    {
      id: id,
      name: name,
      position: position,
      status: status,
      color: color,
      sub_status: Array(sub_status).map { |s| s.is_a?(Hash) ? s["code"] || s[:code] : s }.compact,
      job_id: job_id,
      account_id: account_id,
      workflow_template_id: workflow_template_id,
      created_at: created_at,
      updated_at: updated_at
    }
  end
end
