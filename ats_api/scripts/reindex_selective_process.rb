# frozen_string_literal: true

puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
puts "🔄 [ReindexSelectiveProcess] Starting reindex for all tenants"
puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

Apartment::Tenant.switch('public') do
  tenants = Apartment.tenant_names

  puts "   Found #{tenants.length} tenants to process"
  puts ""

  tenants.each_with_index do |tenant, index|
    begin
      puts "   [#{index + 1}/#{tenants.length}] Processing tenant: #{tenant}"

      Apartment::Tenant.switch(tenant) do
        puts "      ↳ Deleting old index..."
        begin
          SelectiveProcess.searchkick_index.delete
        rescue => e
          puts "      ↳ Index doesn't exist or error: #{e.message}"
        end

        puts "      ↳ Reindexing..."
        SelectiveProcess.reindex

        count = SelectiveProcess.count
        puts "      ✅ Success! Reindexed #{count} records"
      end
    rescue => e
      puts "      ❌ Error: #{e.message}"
      puts "         #{e.backtrace.first(3).join("\n         ")}"
    end

    puts ""
  end
end

puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
puts "✅ [ReindexSelectiveProcess] Completed!"
puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
