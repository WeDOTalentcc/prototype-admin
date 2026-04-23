# frozen_string_literal: true

# Uso: docker compose exec web bin/rails runner scripts/count_pending_screening_sends.rb
#
# Conta quantos candidatos receberiam EvaluationCandidate pelo cron de screening.
# Requer que a coluna is_screening_active exista nos tenants (rode db:migrate se necessário).

total = 0
skipped_tenants = []

Account.where.not(tenant: nil).find_each do |account|
  Apartment::Tenant.switch(account.tenant) do
    unless ActiveRecord::Base.connection.column_exists?(:jobs, :is_screening_active)
      skipped_tenants << "#{account.name} (tenant: #{account.tenant})"
      next
    end

    Job.where(is_screening_active: true, is_deleted: false).find_each do |job|
      sp = job.selective_processes.unscoped
        .where(is_deleted: false, status: SelectiveProcess.statuses[:screening])
        .order(:position).first
      next unless sp

      eval_obj = Evaluation.screening.find_by(
        job_id: job.id,
        selective_process_id: sp.id,
        is_deleted: false
      )
      next unless eval_obj

      count = Apply.where(
        job_id: job.id,
        selective_process_id: sp.id,
        is_deleted: false
      ).where(
        "NOT EXISTS (
          SELECT 1 FROM evaluation_candidates ec
          WHERE ec.apply_id = applies.id
            AND ec.evaluation_id = ?
            AND ec.is_deleted = false
        )",
        eval_obj.id
      ).count

      total += count
      puts "  Job #{job.id} (#{job.title}): #{count} applies" if count > 0
    end
  end
end

puts "\nTotal: #{total} candidatos elegíveis"
if skipped_tenants.any?
  puts "\nTenants ignorados (schema desatualizado - rode db:migrate):"
  skipped_tenants.each { |t| puts "  - #{t}" }
end
