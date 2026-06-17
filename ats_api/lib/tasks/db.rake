namespace :db do
  desc "Runs migrations from db/migrate_public on the public schema"
  task migrate_public: :environment do
    migrations_path = "db/migrate_public"

    puts "[MIGRATE PUBLIC] Checking for pending migrations in #{migrations_path}..."
    puts "[DEBUG] Files in dir: #{Dir.entries(migrations_path).select { |f| f.ends_with?('.rb') }}"

    Apartment::Tenant.switch!("public") do
      context = ActiveRecord::MigrationContext.new(migrations_path, ActiveRecord::SchemaMigration)
      puts "[DEBUG] Migration versions: #{context.get_all_versions.inspect}"

      pending_migrations = context.open.pending_migrations

      if pending_migrations.empty?
        puts "[MIGRATE PUBLIC] No pending migrations found. Schema is up to date."
      else
        puts "[MIGRATE PUBLIC] Found #{pending_migrations.count} pending migration(s):"
        pending_migrations.each { |m| puts "  -> #{m.name}" }

        puts "[MIGRATE PUBLIC] Running migrations..."
        context.up
        puts "[MIGRATE PUBLIC] Done."
      end
    end
  end
end
