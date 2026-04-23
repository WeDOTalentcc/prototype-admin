namespace :sectors do
  desc "Remove sectors table from tenant schemas (keep only in public)"
  task fix_schema: :environment do
    puts "Starting sectors schema fix..."
    puts "=" * 80

    # Check if sectors exists in public schema
    puts "\n1. Checking public schema..."
    public_has_sectors = ActiveRecord::Base.connection.table_exists?("sectors")
    puts "   Public schema has sectors table: #{public_has_sectors}"

    if public_has_sectors
      sector_count = Sector.count
      puts "   Public sectors count: #{sector_count}"
    end

    # Get all tenant schemas
    tenant_names = Apartment::Tenant.adapter.list - [ "public", "extensions" ]
    puts "\n2. Found #{tenant_names.count} tenant schemas: #{tenant_names.join(', ')}"

    # Check and remove sectors from each tenant
    puts "\n3. Removing sectors table from tenant schemas..."
    tenant_names.each do |tenant_name|
      Apartment::Tenant.switch(tenant_name) do
        if ActiveRecord::Base.connection.table_exists?("sectors")
          puts "   [#{tenant_name}] Dropping sectors table..."
          ActiveRecord::Base.connection.execute("DROP TABLE IF EXISTS sectors CASCADE")
          puts "   [#{tenant_name}] ✓ Sectors table removed"
        else
          puts "   [#{tenant_name}] ✓ No sectors table found (already clean)"
        end
      end
    end

    # Verify final state
    puts "\n4. Final verification..."
    Apartment::Tenant.switch("public") do
      if ActiveRecord::Base.connection.table_exists?("sectors")
        puts "   ✓ Public schema: sectors table exists"
        puts "   ✓ Sectors count: #{Sector.count}"
      else
        puts "   ✗ WARNING: Public schema does not have sectors table!"
      end
    end

    tenant_names.each do |tenant_name|
      Apartment::Tenant.switch(tenant_name) do
        has_table = ActiveRecord::Base.connection.table_exists?("sectors")
        if has_table
          puts "   ✗ [#{tenant_name}] WARNING: Still has sectors table!"
        else
          puts "   ✓ [#{tenant_name}] Clean (no sectors table)"
        end
      end
    end

    puts "\n" + "=" * 80
    puts "Sectors schema fix completed!"
    puts "\nNext steps:"
    puts "1. If public schema doesn't have sectors, run: bin/rails db:migrate"
    puts "2. If sectors are empty, run: bin/rails runner 'Sector.create_default_sectors'"
    puts "3. Reindex search: bin/rails runner 'Sector.reindex'"
  end
end
