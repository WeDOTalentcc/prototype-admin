class OrganizationalStructureBuilderService
  attr_reader :job, :data, :account, :errors, :changes

  def initialize(job, organizational_data)
    @job = job
    @account = job.account
    @data = organizational_data.present? ? organizational_data.to_h.deep_symbolize_keys : {}
    @errors = []
    @changes = []
  end

  def build
    return failure("Dados organizacionais não fornecidos") if data.empty?
    return failure("Conta não encontrada para o job") unless account

    ActiveRecord::Base.transaction do
      process_department if data[:department].present?
      process_hiring_manager if data[:hiring_manager].present?
      process_team if data[:team].present?
      process_reports_to if data[:reports_to].present?
      process_team_composition if data[:team_composition].present?
    end

    log_changes
    {
      success: errors.empty?,
      errors: errors,
      changes: changes,
      structure: job.reload.organizational_structure,
      job_id: job.id
    }
  rescue StandardError => e
    Rails.logger.error("OrganizationalStructureBuilderService error: #{e.message}")
    failure("Erro ao construir estrutura: #{e.message}")
  end

  private

  def failure(message)
    errors << message
    { success: false, errors: errors.uniq, changes: [] }
  end

  def process_department
    dept_data = data[:department]
    parent = resolve_parent_department(dept_data)
    department = find_or_create_department(
      name: dept_data[:name],
      parent: parent,
      level: parent ? parent.level + 1 : 0
    )

    if job.department_id != department.id
      job.update!(department: department)
      changes << "Departamento definido: #{department.name}"
    end

    department
  end

  def resolve_parent_department(dept_data)
    parent_name = dept_data[:parent]
    return unless parent_name.present?

    find_or_create_department(name: parent_name, level: 0)
  end

  def process_hiring_manager
    manager_data = data[:hiring_manager]
    manager = find_or_create_user(manager_data)

    unless manager
      errors << "Não foi possível criar ou localizar o gestor"
      return
    end

    # Recarrega do banco para garantir que está persistido
    manager = User.find_by(id: manager.id, account_id: account.id)
    unless manager
      errors << "Usuário não encontrado no banco de dados ou não pertence à conta"
      return
    end

    if manager_data[:title].present?
      position = find_or_create_position(
        title: manager_data[:title],
        department: job.department || default_department
      )
      assign_user_to_position(manager, position)
    end

    # Limpa qualquer ID inválido primeiro antes de atualizar
    if job.hiring_manager_id.present? && !User.exists?(id: job.hiring_manager_id, account_id: account.id)
      job.update_column(:hiring_manager_id, nil)
    end

    if job.hiring_manager_id != manager.id
      job.update!(hiring_manager: manager)
      changes << "Gestor definido: #{manager.name}"
    end
  end

  def process_team
    team_data = data[:team]
    team = find_or_create_team(
      name: team_data[:name],
      department: job.department,
      size: team_data[:size],
      lead: job.hiring_manager,
      description: team_data[:description]
    )

    if team_data[:composition].present?
      composition = build_team_composition(team_data[:composition])
      job.update!(team_composition: composition)
      changes << "Composição do time definida: #{composition_size(composition)} pessoas"
    end

    if job.team_id != team.id
      job.update!(team: team)
      changes << "Time definido: #{team.name}"
    end
  end

  def process_reports_to
    reports_data = data[:reports_to]
    position = find_or_create_position(
      title: reports_data[:position],
      department: job.department || default_department
    )

    if reports_data[:name].present?
      user = locate_user(name: reports_data[:name])
      assign_user_to_position(user, position) if user
    end

    if job.reports_to_position_id != position.id
      job.update!(reports_to_position: position)
      changes << "Linha de reporte definida: #{position.title}"
    end
  end

  def process_team_composition
    composition = build_team_composition(data[:team_composition])
    job.update!(team_composition: composition)
    changes << "Composição do time definida: #{composition_size(composition)} pessoas"
  end

  def find_or_create_department(name:, parent: nil, level: 0)
    department = Department.find_or_initialize_by(
      account_id: account.id,
      name: name
    )

    if department.new_record?
      department.level = level
      department.parent_department = parent
      department.is_deleted = false
      department.save!
      changes << "Departamento criado: #{department.name}"
    end

    department
  end

  def find_or_create_team(name:, department:, size:, lead:, description:)
    team = Team.find_or_initialize_by(
      account_id: account.id,
      name: name
    )

    # Limpa qualquer team_lead_id inválido primeiro
    if team.team_lead_id.present? && !User.exists?(id: team.team_lead_id, account_id: account.id)
      team.team_lead_id = nil
    end

    team.department ||= department

    # Valida e atribui o team_lead apenas se for válido
    if lead.present?
      if lead.is_a?(User) && lead.persisted? && lead.account_id == account.id
        team.team_lead = lead
      elsif lead.is_a?(Integer) && User.exists?(id: lead, account_id: account.id)
        team.team_lead_id = lead
      end
    end

    team.description = description if description.present?
    team.member_count = size.to_i if size.present?
    team.save! if team.changed?

    team
  end

  def find_or_create_position(title:, department:)
    position = OrganizationalPosition.find_or_initialize_by(
      account_id: account.id,
      title: title,
      department: department || default_department
    )

    if position.new_record?
      position.save!
      changes << "Posição criada: #{position.title}"
    end

    position
  end

  def assign_user_to_position(user, position)
    return unless user && position

    PositionAssignment.where(
      organizational_position_id: position.id,
      is_current: true
    ).update_all(is_current: false, end_date: Date.current)

    PositionAssignment.create!(
      user: user,
      organizational_position: position,
      account: account,
      start_date: Date.current,
      is_current: true
    )

    changes << "Usuário #{user.name} atribuído à posição #{position.title}"
  end

  def locate_user(data)
    return if data.blank?

    if data[:email].present?
      User.find_by(email: data[:email], account_id: account.id)
    elsif data[:name].present?
      User.where(account_id: account.id)
          .where("LOWER(name) = ?", data[:name].downcase)
          .first
    end
  end

  def find_or_create_user(data)
    return if data.blank?

    user = locate_user(data)
    return user if user

    # Cria o usuário se não existir na conta atual
    if data[:email].present?
      # Verifica se o email já existe em outra conta
      existing_user = User.find_by(email: data[:email])

      if existing_user && existing_user.account_id != account.id
        errors << "Email #{data[:email]} já está em uso em outra conta"
        return nil
      end

      # Cria novo usuário na conta atual
      user = User.new(
        email: data[:email],
        account_id: account.id
      )
      user.name = data[:name] if data[:name].present?
      # Gera uma senha temporária aleatória (o usuário precisará resetar)
      user.password = SecureRandom.hex(16)

      if user.save
        changes << "Usuário criado: #{user.name || user.email}"
        user
      else
        errors << "Não foi possível criar o usuário: #{user.errors.full_messages.join(', ')}"
        nil
      end
    elsif data[:name].present?
      base_email = generate_email_from_name(data[:name], account.name)
      generated_email = ensure_unique_email(base_email)

      user = User.new(
        name: data[:name],
        email: generated_email,
        account_id: account.id
      )
      user.password = SecureRandom.hex(16)

      if user.save
        changes << "Usuário criado: #{user.name} (#{user.email})"
        user
      else
        errors << "Não foi possível criar o usuário: #{user.errors.full_messages.join(', ')}"
        nil
      end
    else
      nil
    end
  end

  def generate_email_from_name(user_name, account_name)
    normalized_user = user_name.to_s
      .unicode_normalize(:nfd)
      .gsub(/[\u0300-\u036f]/, "")
      .downcase
      .gsub(/[^a-z0-9\s]/, "")
      .gsub(/\s+/, ".")
      .gsub(/\.+/, ".")
      .gsub(/^\.|\.$/, "")

    # Normaliza o nome do account da mesma forma
    normalized_account = account_name.to_s
      .unicode_normalize(:nfd)
      .gsub(/[\u0300-\u036f]/, "")
      .downcase
      .gsub(/[^a-z0-9\s]/, "")
      .gsub(/\s+/, ".")
      .gsub(/\.+/, ".")
      .gsub(/^\.|\.$/, "")

    "#{normalized_user}@#{normalized_account}.com"
  end

  def ensure_unique_email(base_email)
    return base_email unless User.exists?(email: base_email)

    counter = 1
    email = base_email

    local_part, domain = base_email.split("@")

    loop do
      email = "#{local_part}#{counter}@#{domain}"
      break unless User.exists?(email: email)
      counter += 1
      raise "Não foi possível gerar email único após 1000 tentativas" if counter > 1000
    end

    email
  end

  def build_team_composition(composition_data)
    Array(composition_data).map do |entry|
      {
        role: entry[:role] || entry["role"],
        count: (entry[:count] || entry["count"]).to_i,
        description: entry[:description] || entry["description"]
      }
    end
  end

  def composition_size(composition)
    composition.sum { |item| item[:count].to_i }
  end

  def default_department
    @default_department ||= Department.find_or_create_by!(
      account_id: account.id,
      name: "Geral"
    ) do |dept|
      dept.level = 0
      dept.is_deleted = false
    end
  end

  def log_changes
    return if changes.empty?

    ActivityLog.create!(
      reference_type: job.class.name,
      reference_id: job.id,
      action: "update_organizational_structure",
      changeset: { changes: changes, timestamp: Time.current },
      user: Current.user || job.user,
      account: account,
      category: "job_structure"
    )
  end
end
