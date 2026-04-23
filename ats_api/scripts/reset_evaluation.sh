#!/bin/bash

TENANT=${1:-""}
EMAIL=${2:-""}

if [ -z "$TENANT" ] || [ -z "$EMAIL" ]; then
  echo ""
  echo "Uso: ./scripts/reset_evaluation.sh <tenant> <email>"
  echo ""
  echo "Exemplo:"
  echo "  ./scripts/reset_evaluation.sh empresa_teste giovanni@zenlabs.app"
  echo ""
  exit 1
fi

RUBY_SCRIPT=$(cat <<RUBY
candidates = []
Apartment::Tenant.switch("$TENANT") do
  candidates = Candidate.where(email: "$EMAIL").to_a
end

if candidates.empty?
  puts "❌ Candidato não encontrado: $EMAIL"
  exit 1
end

candidates.each do |candidate|
  Apartment::Tenant.switch("$TENANT") do
    puts "Candidato: #{candidate.name} (ID: #{candidate.id})"

    ecs = EvaluationCandidate.where(candidate_id: candidate.id)
    if ecs.empty?
      puts "  ❌ Nenhum EvaluationCandidate"
      puts ""
      next
    end

    ecs.each do |ec|
      puts "  EC ##{ec.id} | Avaliação: #{ec.evaluation&.name} | Job: #{ec.job&.title}"

      answers = Answer.where(evaluation_id: ec.evaluation_id, candidate_id: ec.candidate_id)
      count = answers.count
      answers.destroy_all
      puts "    🗑️  #{count} Answer(s) destruída(s)"

      ec.update_columns(completed: false)
      puts "    ✅ completed: false"
    end
    puts ""
  end
end
RUBY
)

docker compose exec -T web bin/rails runner "$RUBY_SCRIPT"
