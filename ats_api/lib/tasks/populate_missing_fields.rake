namespace :jobs do
  desc "Populate missing_fields for all existing jobs"
  task populate_missing_fields: :environment do
    puts "Starting to populate missing_fields for all jobs..."

    total = Job.count
    updated = 0

    Job.find_each.with_index do |job, index|
      begin
        # Calcula os campos faltantes
        fields = job.make_missing_fields

        # Atualiza direto no banco sem disparar callbacks
        job.update_column(:missing_fields, fields)

        updated += 1

        # Log de progresso a cada 100 registros
        if (index + 1) % 100 == 0
          puts "Processed #{index + 1}/#{total} jobs..."
        end
      rescue => e
        puts "Error updating job #{job.id}: #{e.message}"
      end
    end

    puts "✅ Finished! Updated #{updated}/#{total} jobs"
  end
end
