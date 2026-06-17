# app/services/schema_clone_service.rb

class SchemaCloneService
  class CloneError < StandardError; end

  DUMP_DIR = "/var/backups/tenants"

  def initialize(account:, source_schema: nil, target_schema: nil, allow_destroy: false, keep_days: 7)
    @account = account
    @source_schema = source_schema || account.tenant
    @target_schema = target_schema || account.staging_tenant
    @allow_destroy = allow_destroy
    @keep_days = keep_days
  end

  def call
    validate_safety

    ensure_dump_dir
    dump_schema
    cleanup_old_backups
    recreate_target_schema
    restore_dump

    Rails.logger.info("✅ Clone concluído: #{@source_schema} -> #{@target_schema}")
  end

  private

  attr_reader :account, :source_schema, :target_schema, :allow_destroy, :keep_days

  def validate_safety
    raise CloneError, "Target schema must end with '_staging'" unless target_schema.end_with?("_staging")

    unless schema_exists?(source_schema)
      raise CloneError, "Source schema '#{source_schema}' does not exist"
    end

    if schema_exists?(target_schema) && !allow_destroy
      raise CloneError, "Target schema '#{target_schema}' already exists. Set allow_destroy: true to drop it."
    end
  end

  def schema_exists?(schema_name)
    query = <<~SQL
      SELECT 1
      FROM information_schema.schemata
      WHERE schema_name = #{ActiveRecord::Base.connection.quote(schema_name)}
    SQL

    ActiveRecord::Base.connection.select_value(query).present?
  end

  def ensure_dump_dir
    FileUtils.mkdir_p(dump_dir)
  end

  def dump_schema
    timestamp = Time.now.strftime("%Y%m%d%H%M%S")
    @dump_file = File.join(dump_dir, "#{timestamp}.dump")

    cmd = [
      "pg_dump",
      "--schema=#{source_schema}",
      "--format=custom",
      "--no-owner",
      "--file=#{@dump_file}",
      db_name
    ].join(" ")

    run!(cmd, "Erro ao criar dump do schema #{source_schema}")
  end

  def cleanup_old_backups
    Dir.glob(File.join(dump_dir, "*.dump")).each do |file|
      if File.mtime(file) < (Time.now - keep_days * 24 * 60 * 60)
        File.delete(file)
      end
    end
  end

  def recreate_target_schema
    drop_cmd = "DROP SCHEMA IF EXISTS \"#{target_schema}\" CASCADE;"
    create_cmd = "CREATE SCHEMA \"#{target_schema}\";"

    ActiveRecord::Base.connection.execute(drop_cmd)
    ActiveRecord::Base.connection.execute(create_cmd)
  end

  def restore_dump
    cmd = [
      "pg_restore",
      "--schema=#{target_schema}",
      "--no-owner",
      "--dbname=#{db_name}",
      @dump_file
    ].join(" ")

    run!(cmd, "Erro ao restaurar dump no schema #{target_schema}")
  end

  def dump_dir
    File.join(DUMP_DIR, source_schema)
  end

  def db_name
    ActiveRecord::Base.connection_db_config.database
  end

  def run!(command, error_message)
    Rails.logger.info("Executando: #{command}")
    success = system(command)
    raise CloneError, error_message unless success
  end
end
