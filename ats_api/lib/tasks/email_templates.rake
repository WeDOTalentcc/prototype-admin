# frozen_string_literal: true

namespace :email_templates do
  desc "Seed default email templates for a specific tenant"
  task :seed_defaults, [ :tenant ] => :environment do |_t, args|
    tenant = args[:tenant]

    if tenant.blank?
      puts "❌ Tenant is required. Usage: rake email_templates:seed_defaults[tenant_name]"
      exit 1
    end

    account = Account.find_by(tenant: tenant)
    unless account
      puts "❌ Account not found for tenant: #{tenant}"
      exit 1
    end

    puts "🔄 Seeding default email templates for tenant: #{tenant} (Account: #{account.name})"

    Apartment::Tenant.switch(tenant) do
      templates = EmailTemplates::SeedDefaultsService.new(account: account).call

      if templates.nil?
        puts "❌ No users found for account #{account.name}. Cannot create templates without a user."
      elsif templates.empty?
        puts "💡 All default templates already exist for #{account.name}."
      else
        puts "✅ Created #{templates.size} default templates for #{account.name}."
        templates.each { |t| puts "   - #{t.name} (#{EmailTemplate::CATEGORIES.find { |c| c[:id] == t.category_id }&.dig(:name)})" }
      end
    end
  end

  desc "Seed default email templates for ALL tenants"
  task seed_defaults_all: :environment do
    tenants = Account.pluck(:tenant).compact

    puts "🔄 Seeding default email templates for #{tenants.size} tenants..."
    puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    results = { created: 0, skipped: 0, failed: 0 }

    tenants.each do |tenant|
      account = Account.find_by(tenant: tenant)
      next unless account

      Apartment::Tenant.switch(tenant) do
        templates = EmailTemplates::SeedDefaultsService.new(account: account).call

        if templates.nil?
          puts "  ⏭  #{tenant}: No users found, skipping"
          results[:skipped] += 1
        elsif templates.empty?
          results[:skipped] += 1
        else
          puts "  ✅ #{tenant}: Created #{templates.size} templates"
          results[:created] += 1
        end
      rescue StandardError => e
        puts "  ❌ #{tenant}: #{e.message}"
        results[:failed] += 1
      end
    end

    puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    puts "🎯 Done! Created: #{results[:created]} | Skipped: #{results[:skipped]} | Failed: #{results[:failed]}"
  end
end
