namespace :selective_processes do
  desc "Update existing selective processes with default colors based on status"
  task update_colors: :environment do
    puts "Starting to update selective process colors..."

    # Get all tenants
    tenants = Account.pluck(:tenant).compact.uniq
    total_updated = 0

    tenants.each do |tenant|
      begin
        Apartment::Tenant.switch!(tenant)
        puts "\n🏢 Processing tenant: #{tenant}"

        SelectiveProcess.find_each do |process|
          # Get the default color based on status
          default_color = SelectiveProcess::STATUS_COLORS[process.status.to_sym]

          if default_color && process.color.blank?
            process.update_column(:color, default_color)
            total_updated += 1
            puts "  ✅ Updated: #{process.name} (#{process.status}) -> #{default_color}"
          elsif process.color.present?
            puts "  ⏭️  Skipped: #{process.name} (already has color: #{process.color})"
          else
            puts "  ⚠️  Warning: #{process.name} has unknown status: #{process.status}"
          end
        end

      rescue => e
        puts "  ❌ Error processing tenant #{tenant}: #{e.message}"
      ensure
        Apartment::Tenant.reset
      end
    end

    puts "\n✨ Done! Total processes updated: #{total_updated}"
  end

  desc "Preview color changes without updating"
  task preview_colors: :environment do
    puts "Previewing selective process color changes..."
    puts "\n📋 Status Colors Map:"
    SelectiveProcess::STATUS_COLORS.each do |status, color|
      puts "  #{status.to_s.ljust(20)} -> #{color}"
    end

    tenants = Account.pluck(:tenant).compact.uniq
    total_to_update = 0

    tenants.each do |tenant|
      begin
        Apartment::Tenant.switch!(tenant)
        puts "\n🏢 Tenant: #{tenant}"

        SelectiveProcess.find_each do |process|
          if process.color.blank?
            default_color = SelectiveProcess::STATUS_COLORS[process.status.to_sym]
            if default_color
              total_to_update += 1
              puts "  🔄 Would update: #{process.name} (#{process.status}) -> #{default_color}"
            end
          end
        end

      rescue => e
        puts "  ❌ Error: #{e.message}"
      ensure
        Apartment::Tenant.reset
      end
    end

    puts "\n📊 Total processes to be updated: #{total_to_update}"
    puts "\n💡 Run 'ats selective_processes:update_colors' to apply changes"
  end
end
