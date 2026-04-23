# spec/support/searchkick.rb

RSpec.configure do |config|
  config.before(:suite) do
    Apartment::Tenant.switch!('public')

    puts "\nSearchkick test setup: creating indexes..."

    Searchkick.models.each do |model|
      next unless model.respond_to?(:searchkick_index)

      index_name = model.search_index.name

      begin
        if model.search_index.exists?
          model.search_index.delete
        end
      rescue Elastic::Transport::Transport::Errors::NotFound
      rescue => e
        warn "    WARN: #{index_name}: #{e.message}"
      end

      begin
        model.reindex
      rescue => e
        warn "    WARN reindex #{model.name}: #{e.message}"
      end
    end

    puts "Searchkick test setup complete."
  end

  config.before(:each) do
    Searchkick.disable_callbacks
    Apartment::Tenant.switch!('public')
  end

  config.around(:each, search: true) do |example|
    Searchkick.enable_callbacks do
      example.run
    end
    Apartment::Tenant.switch!('public')
    Searchkick.client.indices.refresh(index: '_all') rescue nil
  end

  config.after(:each) do
    Searchkick.enable_callbacks
    Apartment::Tenant.reset
  end
end
