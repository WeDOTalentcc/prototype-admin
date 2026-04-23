class OrganizationalStructureValidator
  def initialize(job)
    @job = job
    @warnings = []
    @suggestions = []
  end

  def validate
    check_department
    check_manager
    check_team
    check_reports_to

    {
      valid: @warnings.empty?,
      complete: @warnings.empty?,
      suggestions: @suggestions,
      warnings: @warnings,
      completion_percentage: completion_percentage
    }
  end

  private

  def check_department
    return if @job.department.present?

    @warnings << "Departamento não definido"
    @suggestions << "Pergunte qual é a área ou departamento da vaga"
  end

  def check_manager
    return if @job.hiring_manager.present?

    @warnings << "Gestor não definido"
    @suggestions << "Pergunte quem será o gestor direto"
  end

  def check_team
    if @job.team.blank?
      @warnings << "Time não definido"
      @suggestions << "Pergunte como é o time atual e quantas pessoas existem"
      return
    end

    return if @job.team_composition.present?

    @warnings << "Composição do time não informada"
    @suggestions << "Pergunte quantas pessoas de cada papel existem no time"
  end

  def check_reports_to
    return if @job.reports_to_position.present?

    @warnings << "Linha de reporte não definida"
    @suggestions << "Confirme para quem a posição irá se reportar"
  end

  def completion_percentage
    total = 4
    completed = 0
    completed += 1 if @job.department.present?
    completed += 1 if @job.hiring_manager.present?
    completed += 1 if @job.team.present? && @job.team_composition.present?
    completed += 1 if @job.reports_to_position.present?
    ((completed.to_f / total) * 100).round
  end
end
