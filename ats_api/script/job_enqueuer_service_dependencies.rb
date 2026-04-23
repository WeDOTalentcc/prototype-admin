#!/usr/bin/env ruby
# frozen_string_literal: true

# Script que coleta todos os arquivos usados por Sourcings::JobEnqueuerService
# (direta ou indiretamente). Rode: ruby script/job_enqueuer_service_dependencies.rb
# ou: rails runner script/job_enqueuer_service_dependencies.rb
# Saída: job_enqueuer_service_dependencies.txt na raiz do projeto.

ROOT_FILE = "app/services/sourcings/job_enqueuer_service.rb"
BASE_DIRS = %w[app/services app/jobs app/serializer app/channels app/models].freeze
SKIP_NAMESPACES = %w[Rails Sidekiq Apartment JSON Time Date SecureRandom ActiveRecord].freeze

def project_root
  File.expand_path("..", __dir__)  # script/ está dentro da raiz do projeto
end

def constant_to_path(constant_name)
  constant_name.to_s.gsub(/::/, "/").gsub(/([A-Z]+)([A-Z][a-z])/, '\1_\2').gsub(/([a-z\d])([A-Z])/, '\1_\2').downcase + ".rb"
end

def resolve_file(constant_name)
  path_suffix = constant_to_path(constant_name)
  BASE_DIRS.each do |base|
    candidate = File.join(project_root, base, path_suffix)
    return candidate if File.file?(candidate)
  end
  nil
end

def extract_constants(content, current_namespace = nil)
  constants = []
  # Fully qualified: Sourcings::*, Candidates::*, Pearch::*, SourcedProfiles::*
  content.scan(/\b(Sourcings::[A-Za-z0-9_:]+|Candidates::[A-Za-z0-9_:]+|Pearch::[A-Za-z0-9_:]+|SourcedProfiles::[A-Za-z0-9_:]+|Embeddings::[A-Za-z0-9_:]+|CandidateService::[A-Za-z0-9_:]+)\b/) do
    constants << $1
  end
  # Top-level app classes often used
  %w[
    ProcessSourcingJob SourcingSerializer SourcingChannel
    Account User Sourcing Candidate SourcedProfile SourcedProfileSourcing
    GeminiClient Embedding
  ].each do |name|
    constants << name if content.include?(name) && content =~ /\b#{Regexp.escape(name)}\b/
  end
  # Em contexto Candidates (arquivo em candidates/ ou search/) Search::X -> Candidates::Search::X
  if content.include?("Search::") && (content.include?("module Candidates") || content.include?("Candidates::") || content.include?("class HybridSearchService") || content.include?("class LocalSearchJob"))
    content.scan(/\bSearch::([A-Za-z0-9_]+)\b/) do
      constants << "Candidates::Search::#{$1}"
    end
  end
  # Em contexto Pearch, TalentSearchExecutorService
  constants << "Pearch::TalentSearchExecutorService" if content.include?("TalentSearchExecutorService")
  constants.uniq.reject { |c| SKIP_NAMESPACES.any? { |s| c.start_with?(s) } }
end

def extract_constants_from_file(file_path, content)
  constants = extract_constants(content)
  # Em arquivos em candidates/search/, constantes nuas (ElasticsearchStrategy, etc.) são Candidates::Search::*
  if file_path.include?("/candidates/search/")
    content.scan(/\b(ElasticsearchStrategy|EmbeddingStrategy|EmbeddingCache|QueryAnalyzer|SearchTelemetry|WeightedRankFusion|Reranker|AdaptivePool|Configuration|BaseFilters|FilterMerger)\b/) do
      constants << "Candidates::Search::#{$1}"
    end
  end
  constants.uniq
end

def collect_all_files
  collected = {}
  queue = [ File.join(project_root, ROOT_FILE) ]
  while queue.any?
    path = queue.shift
    next unless path && path.start_with?(project_root) && path.end_with?(".rb")
    next if collected[path]

    # guardar path absoluto para ler; depois escrever relativos no .txt
    collected[path] = true
    next unless File.file?(path)

    content = File.read(path) rescue ""
    extract_constants_from_file(path, content).each do |const_name|
      resolved = resolve_file(const_name)
      queue << resolved if resolved && !collected[resolved]
    end
  end
  collected.keys.sort
end

SEPARATOR = "\n\n#{'=' * 80}\n\n"

def run
  files = collect_all_files
  relative_files = files.map { |p| p.start_with?(project_root + "/") ? p.sub(project_root + "/", "") : p }.sort
  out_path = File.join(project_root, "job_enqueuer_service_dependencies.txt")

  lines = relative_files.map do |rel_path|
    full_path = File.join(project_root, rel_path)
    content = File.file?(full_path) ? File.read(full_path) : ""
    "path: #{rel_path}\n\n#{content}"
  end
  File.write(out_path, lines.join(SEPARATOR) + "\n")
  puts "Escritos #{relative_files.size} arquivos (path + conteúdo) em #{out_path}"
end

run
