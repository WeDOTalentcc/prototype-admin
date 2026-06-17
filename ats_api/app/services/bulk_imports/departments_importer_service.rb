require "csv"

module BulkImports
  class DepartmentsImporterService
    MANAGER_COLUMNS = %w[manager_email manager_email_2 manager_email_3 manager_email_4].freeze

    def self.call(**args)
      new(**args).call
    end

    attr_reader :data_file, :user, :account, :results

    def initialize(data_file_id:, user_id:)
      @user = User.find(user_id)
      @account = @user.account
      Apartment::Tenant.switch!(@account.tenant)

      @data_file = DataFile.find(data_file_id)
      @results = { created: 0, updated: 0, errors: [] }
      @departments_cache = {}
    end

    def call
      rows = parse_file
      return { error: "Arquivo vazio ou inválido" } if rows.empty?

      ActiveRecord::Base.transaction do
        rows.each_with_index do |row, index|
          process_row(row, index + 2)
        rescue StandardError => e
          @results[:errors] << { row: index + 2, message: e.message }
        end
      end

      @results
    end

    private

    def parse_file
      @data_file.file.open do |file|
        extension = File.extname(@data_file.file.filename.to_s).downcase

        case extension
        when ".csv"
          parse_csv(file)
        when ".xlsx", ".xls"
          parse_excel(file)
        else
          parse_csv(file)
        end
      end
    end

    def parse_csv(file)
      CSV.read(file.path, headers: true, encoding: "bom|utf-8", col_sep: detect_separator(file)).map(&:to_h)
    end

    def detect_separator(file)
      first_line = File.open(file.path, &:readline)
      first_line.count(";") > first_line.count(",") ? ";" : ","
    end

    def parse_excel(file)
      return [] unless defined?(Roo)

      xlsx = Roo::Spreadsheet.open(file.path)
      sheet = xlsx.sheet(0)
      headers = sheet.row(1).map { |h| h.to_s.strip.downcase.gsub(" ", "_") }

      (2..sheet.last_row).map do |i|
        row = sheet.row(i)
        headers.each_with_index.to_h { |header, idx| [ header, row[idx]&.to_s&.strip ] }
      end
    end

    def process_row(row, row_number)
      row = normalize_keys(row)
      name = row["name"]&.strip

      return if name.blank?

      parent = find_or_cache_parent(row["parent_department"])
      department = find_or_create_department(name, row, parent)

      process_managers(department, row)

      @departments_cache[name.downcase] = department
    end

    def normalize_keys(row)
      row.transform_keys { |k| k.to_s.strip.downcase.gsub(" ", "_") }
    end

    def find_or_cache_parent(parent_name)
      return nil if parent_name.blank?

      key = parent_name.strip.downcase
      @departments_cache[key] ||= Department.find_by(account_id: @account.id, name: parent_name.strip, is_deleted: false)
    end

    def find_or_create_department(name, row, parent)
      department = Department.find_by(account_id: @account.id, name: name, is_deleted: false)

      if department
        department.update(
          description: row["description"],
          color: row["color"] || department.color,
          cost_center: row["cost_center"],
          parent_department_id: parent&.id,
          level: parent ? parent.level + 1 : 0
        )
        @results[:updated] += 1
      else
        department = Department.create!(
          account_id: @account.id,
          name: name,
          description: row["description"],
          color: row["color"] || default_color,
          cost_center: row["cost_center"],
          parent_department_id: parent&.id,
          level: parent ? parent.level + 1 : 0
        )
        @results[:created] += 1
      end

      department
    end

    def process_managers(department, row)
      manager_emails = MANAGER_COLUMNS.map { |col| row[col] }.compact.reject(&:blank?)
      return if manager_emails.empty?

      manager_emails.each_with_index do |email, index|
        user = find_or_create_user(email.strip)
        next unless user

        is_primary = index.zero?
        create_manager_relationship(department, user, is_primary)

        next unless is_primary

        department.update(
          manager_id: user.id,
          manager_name: user.name,
          manager_email: user.email
        )
      end
    end

    def find_or_create_user(email)
      return nil if email.blank?

      user = User.find_by(email: email.downcase, account_id: @account.id)
      return user if user

      User.create!(
        email: email.downcase,
        account_id: @account.id,
        name: email.split("@").first.gsub(".", " ").titleize,
        password: SecureRandom.hex(16),
        status: 0,
        is_active: false
      )
    end

    def create_manager_relationship(department, user, is_primary)
      existing = DepartmentRelationship.find_by(
        department_id: department.id,
        user_id: user.id,
        role: "manager"
      )

      return if existing

      DepartmentRelationship.create!(
        department_id: department.id,
        user_id: user.id,
        account_id: @account.id,
        reference_type: "User",
        reference_id: user.id,
        role: "manager",
        is_primary: is_primary
      )
    end

    def default_color
      colors = %w[#60BED1 #4ECDC4 #45B7D1 #96CEB4 #FFEAA7 #DDA0DD #98D8C8 #F7DC6F #BB8FCE #85C1E9 #F8B500 #FF6B6B]
      colors.sample
    end
  end
end
