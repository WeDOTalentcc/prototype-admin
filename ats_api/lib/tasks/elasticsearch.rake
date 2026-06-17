# frozen_string_literal: true

namespace :elasticsearch do
  desc "Reindex all models with Searchable concern"
  task reindex_all: :environment do
    models = ApplicationRecord.descendants.select do |model|
      model.included_modules.include?(Searchable)
    end

    puts "=== Starting Elasticsearch reindexing ==="
    puts "Found #{models.count} models with Searchable concern"
    puts ""

    successful = []
    skipped = []
    failed = []

    models.each do |model|
      begin
        if model.count.zero?
          skipped << model.name
          puts "⏭ #{model.name} skipped (0 records)"
          next
        end

        puts "Reindexing #{model.name} (#{model.count} records)..."
        model.reindex
        successful << model.name
        puts "✓ #{model.name} reindexed successfully"
      rescue => e
        failed << { model: model.name, error: e.message }
        puts "✗ Failed to reindex #{model.name}: #{e.message}"
        Rails.logger.error("Elasticsearch reindex failed for #{model.name}: #{e.message}")
        Rails.logger.error(e.backtrace.join("\n"))
      end
      puts ""
    end

    puts "=== Reindexing Summary ==="
    puts "Total models: #{models.count}"
    puts "Successful: #{successful.count}"
    puts "Skipped (empty): #{skipped.count}"
    puts "Failed: #{failed.count}"

    if successful.any?
      puts "\nSuccessfully reindexed:"
      successful.each { |name| puts "  ✓ #{name}" }
    end

    if failed.any?
      puts "\nFailed to reindex:"
      failed.each { |info| puts "  ✗ #{info[:model]}: #{info[:error]}" }
    end

    puts "\n=== Reindexing Complete ==="
  end

  desc "Clean up orphaned and direct ES indexes that block aliases"
  task cleanup: :environment do
    client = Searchkick.client
    all_indices = client.cat.indices(format: "json")
    all_aliases = client.cat.aliases(format: "json")

    alias_names = all_aliases.map { |a| a["alias"] }.to_set
    alias_index_names = all_aliases.map { |a| a["index"] }.to_set

    env_suffix = "_#{Rails.env}"
    direct_indexes = []
    orphaned_indexes = []

    all_indices.each do |idx|
      index_name = idx["index"]
      next unless index_name.end_with?(env_suffix)

      has_timestamp = index_name.match?(/\d{20,}$/)

      if has_timestamp
        base_name = index_name.sub(/_\d{20,}$/, "")
        unless alias_index_names.include?(index_name)
          orphaned_indexes << { name: index_name, docs: idx["docs.count"] }
        end
      else
        if alias_names.include?(index_name)
          next
        end
        direct_indexes << { name: index_name, docs: idx["docs.count"] }
      end
    end

    puts "=== Elasticsearch Cleanup ==="
    puts ""

    if direct_indexes.any?
      puts "#{direct_indexes.count} direct indexes found (blocking aliases):"
      direct_indexes.each { |idx| puts "  - #{idx[:name]} (#{idx[:docs]} docs)" }
      puts ""
      puts "Deleting direct indexes..."

      direct_indexes.each do |idx|
        begin
          client.indices.delete(index: idx[:name])
          puts "  ✓ Deleted #{idx[:name]}"
        rescue => e
          puts "  ✗ Failed to delete #{idx[:name]}: #{e.message}"
        end
      end
    else
      puts "No direct indexes found."
    end

    puts ""

    if orphaned_indexes.any?
      puts "#{orphaned_indexes.count} orphaned timestamped indexes found:"
      orphaned_indexes.each { |idx| puts "  - #{idx[:name]} (#{idx[:docs]} docs)" }
      puts ""
      puts "Deleting orphaned indexes..."

      orphaned_indexes.each do |idx|
        begin
          client.indices.delete(index: idx[:name])
          puts "  ✓ Deleted #{idx[:name]}"
        rescue => e
          puts "  ✗ Failed to delete #{idx[:name]}: #{e.message}"
        end
      end
    else
      puts "No orphaned indexes found."
    end

    puts ""
    puts "=== Cleanup Complete ==="
    puts ""
    puts "Run 'rake elasticsearch:reindex_all' to rebuild all indexes properly."
  end

  desc "Full repair: cleanup orphaned indexes then reindex all models"
  task repair: :environment do
    Rake::Task["elasticsearch:cleanup"].invoke
    puts ""
    puts "=" * 60
    puts ""
    Rake::Task["elasticsearch:reindex_all"].invoke
  end
end
