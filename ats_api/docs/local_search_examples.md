# Local Search - Exemplos Práticos e Casos de Uso

> **Cookbook de Implementação**  
> Exemplos reais e soluções para problemas comuns  
> **Última atualização:** 2026-02-01

## 📋 Índice

1. [Exemplos de Código](#exemplos-de-código)
2. [Casos de Uso Reais](#casos-de-uso-reais)
3. [Integração com Frontend](#integração-com-frontend)
4. [Otimizações de Performance](#otimizações-de-performance)
5. [Debugging e Troubleshooting](#debugging-e-troubleshooting)
6. [Testes](#testes)

---

## Exemplos de Código

### Exemplo 1: Busca Simples por Palavras-chave

```ruby
# app/controllers/candidates_controller.rb
class CandidatesController < ApplicationController
  def search
    service = Candidates::Search::HybridSearchService.new(
      account_id: current_account.id,
      tenant: current_account.tenant
    )
    
    @result = service.search(
      params[:q],
      user_filters: build_filters,
      limit: params[:limit]&.to_i || 10
    )
    
    respond_to do |format|
      format.html { render :search_results }
      format.json { render json: format_search_response(@result) }
    end
  end
  
  private
  
  def build_filters
    filters = {}
    filters[:city] = params[:city] if params[:city].present?
    filters[:state] = params[:state] if params[:state].present?
    filters[:position_level] = params[:seniority] if params[:seniority].present?
    filters[:has_curriculum] = true if params[:with_cv] == '1'
    filters
  end
  
  def format_search_response(result)
    {
      candidates: result.candidates.map { |c| CandidateSerializer.new(c).as_json },
      metadata: result.metadata,
      search_meta: result.search_meta_by_id,
      total: result.metadata[:count]
    }
  end
end
```

### Exemplo 2: Upload de Currículo

```ruby
# app/controllers/resume_uploads_controller.rb
class ResumeUploadsController < ApplicationController
  def create
    resume_file = params[:resume_file]
    
    unless resume_file
      return render json: { error: 'Resume file required' }, status: :bad_request
    end
    
    # Ler conteúdo do arquivo
    resume_text = extract_text_from_file(resume_file)
    
    if resume_text.blank?
      return render json: { error: 'Could not extract text from file' }, status: :unprocessable_entity
    end
    
    # Log para debug
    Rails.logger.info("[ResumeUpload] Processing resume, length: #{resume_text.length}")
    
    # Buscar candidatos similares
    service = Candidates::Search::HybridSearchService.new(
      account_id: current_account.id,
      tenant: current_account.tenant
    )
    
    @result = service.search(
      resume_text,
      limit: params[:limit]&.to_i || 20
    )
    
    # Verificar qualidade da extração
    if @result.metadata[:extraction_confidence] < 0.5
      Rails.logger.warn("[ResumeUpload] Low extraction confidence: #{@result.metadata[:extraction_confidence]}")
      flash[:warning] = "Algumas informações podem não ter sido extraídas corretamente do CV."
    end
    
    # Salvar upload para histórico
    save_upload_history(resume_file, @result)
    
    render json: {
      candidates: @result.candidates.map { |c| CandidateSerializer.new(c).as_json },
      metadata: @result.metadata,
      extraction_quality: {
        confidence: @result.metadata[:extraction_confidence],
        method: @result.metadata[:extraction_method],
        missing_fields: @result.metadata[:missing_fields],
        queries_generated: @result.metadata[:queries_generated]
      }
    }
  end
  
  private
  
  def extract_text_from_file(file)
    case file.content_type
    when 'application/pdf'
      extract_pdf_text(file)
    when 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
      extract_docx_text(file)
    when 'text/plain'
      file.read
    else
      nil
    end
  end
  
  def extract_pdf_text(file)
    # Usar gem 'pdf-reader'
    reader = PDF::Reader.new(file.path)
    reader.pages.map(&:text).join("\n")
  rescue => e
    Rails.logger.error("[ResumeUpload] PDF extraction failed: #{e.message}")
    nil
  end
  
  def extract_docx_text(file)
    # Usar gem 'docx'
    doc = Docx::Document.open(file.path)
    doc.paragraphs.map(&:text).join("\n")
  rescue => e
    Rails.logger.error("[ResumeUpload] DOCX extraction failed: #{e.message}")
    nil
  end
  
  def save_upload_history(file, result)
    ResumeUploadHistory.create!(
      user_id: current_user.id,
      account_id: current_account.id,
      filename: file.original_filename,
      file_size: file.size,
      extraction_confidence: result.metadata[:extraction_confidence],
      extraction_method: result.metadata[:extraction_method],
      queries_generated: result.metadata[:queries_generated],
      results_count: result.candidates.size
    )
  end
end
```

### Exemplo 3: Busca por Descrição de Vaga

```ruby
# app/controllers/job_matching_controller.rb
class JobMatchingController < ApplicationController
  def match_candidates
    job = Job.find(params[:job_id])
    
    # Usar descrição completa da vaga
    jd_text = build_jd_text(job)
    
    service = Candidates::Search::HybridSearchService.new(
      account_id: current_account.id,
      tenant: current_account.tenant
    )
    
    @result = service.search(
      jd_text,
      limit: params[:limit]&.to_i || 30
    )
    
    # Verificar se foi detectado como JD
    unless @result.metadata[:search_type] == :job_description
      Rails.logger.warn("[JobMatching] JD not detected for job #{job.id}")
      # Forçar indicadores de JD
      jd_text_enhanced = "Requisitos da vaga:\n#{jd_text}\n\nResponsabilidades:\n#{job.responsibilities}"
      @result = service.search(jd_text_enhanced, limit: 30)
    end
    
    # Salvar matching para a vaga
    save_job_matching(job, @result)
    
    render json: {
      job_id: job.id,
      candidates: @result.candidates.map do |c|
        {
          candidate: CandidateSerializer.new(c).as_json,
          match_score: @result.search_meta_by_id[c.id][:final_score],
          boost_breakdown: @result.search_meta_by_id[c.id][:boost_breakdown],
          required_skills_matched: calculate_required_skills_match(c, @result.metadata[:required_skills])
        }
      end,
      job_analysis: {
        required_skills: @result.metadata[:required_skills],
        nice_to_have_skills: @result.metadata[:nice_to_have_skills]
      }
    }
  end
  
  private
  
  def build_jd_text(job)
    <<~JD
      #{job.title}
      
      Descrição: #{job.description}
      
      Requisitos: #{job.requirements}
      
      #{job.nice_to_have.present? ? "Desejável: #{job.nice_to_have}" : ""}
      
      Experiência: #{job.min_experience} a #{job.max_experience} anos
      Nível: #{job.seniority}
    JD
  end
  
  def calculate_required_skills_match(candidate, required_skills)
    return 0 if required_skills.blank?
    
    candidate_text = [
      candidate.curriculum_text,
      candidate.skills&.join(' '),
      candidate.role_name
    ].compact.join(' ').downcase
    
    matched = required_skills.count do |skill|
      candidate_text.include?(skill.downcase)
    end
    
    {
      matched: matched,
      total: required_skills.size,
      percentage: (matched.to_f / required_skills.size * 100).round(2)
    }
  end
  
  def save_job_matching(job, result)
    JobMatching.create!(
      job_id: job.id,
      performed_at: Time.current,
      search_type: result.metadata[:search_type],
      required_skills: result.metadata[:required_skills],
      nice_to_have_skills: result.metadata[:nice_to_have_skills],
      candidates_found: result.candidates.size,
      top_candidate_id: result.candidates.first&.id
    )
  end
end
```

### Exemplo 4: Background Job para Buscas Pesadas

```ruby
# app/jobs/resume_matching_job.rb
class ResumeMatchingJob < ApplicationJob
  queue_as :search
  
  def perform(resume_text, account_id, user_id, options = {})
    account = Account.find(account_id)
    user = User.find(user_id)
    
    service = Candidates::Search::HybridSearchService.new(
      account_id: account.id,
      tenant: account.tenant
    )
    
    # Buscar com limite maior
    result = service.search(
      resume_text,
      limit: options[:limit] || 50
    )
    
    # Salvar resultado no banco
    search_result = SearchResult.create!(
      user_id: user.id,
      account_id: account.id,
      query_type: result.metadata[:search_type],
      query_preview: resume_text[0..200],
      extraction_confidence: result.metadata[:extraction_confidence],
      extraction_method: result.metadata[:extraction_method],
      queries_generated: result.metadata[:queries_generated],
      candidate_ids: result.candidates.map(&:id),
      metadata: result.metadata,
      search_meta: result.search_meta_by_id,
      completed_at: Time.current
    )
    
    # Notificar usuário
    SearchCompleteMailer.notify(user, search_result).deliver_later
    
    # Broadcast via ActionCable (real-time)
    ActionCable.server.broadcast(
      "search_channel_#{user.id}",
      {
        type: 'search_complete',
        search_result_id: search_result.id,
        candidates_count: result.candidates.size
      }
    )
  rescue => e
    Rails.logger.error("[ResumeMatchingJob] Failed: #{e.message}")
    Rails.logger.error(e.backtrace.join("\n"))
    
    # Notificar erro
    SearchFailedMailer.notify(user, e.message).deliver_later
    raise
  end
end

# Uso no controller:
def create_async_search
  ResumeMatchingJob.perform_later(
    params[:resume_text],
    current_account.id,
    current_user.id,
    { limit: 50 }
  )
  
  render json: {
    message: 'Search started in background. You will be notified when complete.',
    status: 'processing'
  }
end
```

---

## Casos de Uso Reais

### Caso 1: Sourcing de Candidatos por Perfil Ideal

**Cenário:** Recrutador tem um perfil ideal em mente e quer encontrar candidatos similares.

```ruby
# app/services/ideal_profile_sourcing.rb
class IdealProfileSourcing
  def initialize(account)
    @account = account
    @search_service = Candidates::Search::HybridSearchService.new(
      account_id: account.id,
      tenant: account.tenant
    )
  end
  
  def find_candidates(ideal_profile_params)
    # Construir "currículo ideal"
    ideal_resume = build_ideal_resume(ideal_profile_params)
    
    # Buscar
    result = @search_service.search(ideal_resume, limit: 50)
    
    # Filtrar por score mínimo
    candidates = result.candidates.select do |c|
      result.search_meta_by_id[c.id][:final_score] >= 0.5
    end
    
    {
      candidates: candidates,
      total_found: candidates.size,
      search_quality: assess_search_quality(result)
    }
  end
  
  private
  
  def build_ideal_resume(params)
    <<~RESUME
      Profissional #{params[:seniority]} com #{params[:years_experience]} anos de experiência.
      
      Atuação como #{params[:role]}.
      
      Tecnologias: #{params[:technologies].join(', ')}.
      
      #{params[:industry].present? ? "Experiência no setor de #{params[:industry]}." : ""}
      
      #{params[:skills].present? ? "Competências: #{params[:skills].join(', ')}." : ""}
    RESUME
  end
  
  def assess_search_quality(result)
    {
      extraction_confidence: result.metadata[:extraction_confidence],
      high_quality: result.metadata[:extraction_confidence] >= 0.75,
      queries_used: result.metadata[:queries_generated],
      recommendation: recommend_adjustment(result)
    }
  end
  
  def recommend_adjustment(result)
    if result.metadata[:extraction_confidence] < 0.5
      "Recomendação: Adicionar mais detalhes ao perfil ideal para melhor extração"
    elsif result.candidates.size < 10
      "Recomendação: Considerar relaxar alguns critérios ou expandir pool de candidatos"
    else
      "Busca com boa qualidade"
    end
  end
end

# Uso:
sourcing = IdealProfileSourcing.new(current_account)
result = sourcing.find_candidates(
  seniority: 'senior',
  years_experience: 8,
  role: 'Desenvolvedor Ruby on Rails',
  technologies: ['Ruby', 'Rails', 'PostgreSQL', 'Redis'],
  industry: 'fintech',
  skills: ['liderança técnica', 'arquitetura de software']
)
```

### Caso 2: Matching Automático de Vagas

**Cenário:** Sistema automaticamente sugere candidatos para cada vaga nova.

```ruby
# app/services/auto_job_matching.rb
class AutoJobMatching
  def self.match_all_open_jobs
    Job.open.find_each do |job|
      AutoJobMatchingJob.perform_later(job.id)
    end
  end
end

# app/jobs/auto_job_matching_job.rb
class AutoJobMatchingJob < ApplicationJob
  queue_as :matching
  
  def perform(job_id)
    job = Job.find(job_id)
    
    service = Candidates::Search::HybridSearchService.new(
      account_id: job.account_id,
      tenant: job.account.tenant
    )
    
    # Construir JD a partir da vaga
    jd_text = build_jd_from_job(job)
    
    # Buscar top 20 candidatos
    result = service.search(jd_text, limit: 20)
    
    # Salvar sugestões
    result.candidates.each_with_index do |candidate, index|
      JobCandidateSuggestion.create!(
        job_id: job.id,
        candidate_id: candidate.id,
        rank: index + 1,
        match_score: result.search_meta_by_id[candidate.id][:final_score],
        boost_breakdown: result.search_meta_by_id[candidate.id][:boost_breakdown],
        suggested_at: Time.current
      )
    end
    
    # Notificar recrutador
    JobMatchingMailer.notify_suggestions(job, result.candidates.size).deliver_later
  end
  
  private
  
  def build_jd_from_job(job)
    parts = []
    parts << "#{job.title}"
    parts << "Descrição: #{job.description}"
    parts << "Requisitos: #{job.requirements}" if job.requirements.present?
    parts << "Desejável: #{job.nice_to_have}" if job.nice_to_have.present?
    parts << "Experiência: #{job.min_experience} a #{job.max_experience} anos"
    parts << "Nível: #{job.seniority}"
    parts.join("\n\n")
  end
end
```

### Caso 3: Busca Incremental com Cache

**Cenário:** Interface de busca com resultados incrementais e cache.

```ruby
# app/controllers/incremental_search_controller.rb
class IncrementalSearchController < ApplicationController
  def search
    cache_key = generate_cache_key
    
    @result = Rails.cache.fetch(cache_key, expires_in: 1.hour) do
      service = Candidates::Search::HybridSearchService.new(
        account_id: current_account.id,
        tenant: current_account.tenant
      )
      
      service.search(
        params[:q],
        user_filters: build_filters,
        limit: current_limit
      )
    end
    
    # Paginar resultados do cache
    page = params[:page]&.to_i || 1
    per_page = params[:per_page]&.to_i || 10
    
    offset = (page - 1) * per_page
    paginated_candidates = @result.candidates[offset, per_page] || []
    
    render json: {
      candidates: paginated_candidates.map { |c| CandidateSerializer.new(c).as_json },
      page: page,
      per_page: per_page,
      total_pages: (@result.candidates.size / per_page.to_f).ceil,
      total_count: @result.candidates.size,
      metadata: @result.metadata
    }
  end
  
  private
  
  def generate_cache_key
    query_hash = Digest::SHA256.hexdigest(params[:q].to_s)
    filters_hash = Digest::SHA256.hexdigest(build_filters.to_json)
    "search/#{current_account.id}/#{query_hash}/#{filters_hash}/#{current_limit}"
  end
  
  def current_limit
    # Sempre buscar um pool maior para cache
    50
  end
end
```

---

## Integração com Frontend

### Exemplo: React Component com Real-time Updates

```typescript
// components/CandidateSearch.tsx
import React, { useState, useEffect } from 'react';
import { searchCandidates, SearchResult } from '../api/search';

export const CandidateSearch: React.FC = () => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SearchResult | null>(null);
  
  const handleSearch = async () => {
    setLoading(true);
    try {
      const result = await searchCandidates(query, { limit: 20 });
      setResult(result);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const renderExtractionQuality = () => {
    if (!result || result.metadata.search_type !== 'resume') return null;
    
    const { extraction_confidence, extraction_method, missing_fields } = result.metadata;
    
    let badgeColor = 'red';
    let badgeText = 'Baixa qualidade';
    
    if (extraction_confidence >= 0.75) {
      badgeColor = 'green';
      badgeText = 'Alta qualidade';
    } else if (extraction_confidence >= 0.50) {
      badgeColor = 'yellow';
      badgeText = 'Qualidade média';
    }
    
    return (
      <div className="extraction-quality">
        <span className={`badge badge-${badgeColor}`}>
          {badgeText} ({Math.round(extraction_confidence * 100)}%)
        </span>
        <small>Método: {extraction_method}</small>
        {missing_fields.length > 0 && (
          <small>Campos faltando: {missing_fields.join(', ')}</small>
        )}
      </div>
    );
  };
  
  const renderCandidate = (candidate: any) => {
    const meta = result?.search_meta_by_id[candidate.id];
    if (!meta) return null;
    
    return (
      <div key={candidate.id} className="candidate-card">
        <h3>{candidate.name}</h3>
        <div className="match-score">
          Score: {Math.round(meta.final_score * 100)}%
        </div>
        
        {meta.multi_query_hits > 1 && (
          <div className="multi-query-badge">
            ⭐ Apareceu em {meta.multi_query_hits} queries
          </div>
        )}
        
        {meta.boost_breakdown && (
          <div className="boosts">
            {Object.entries(meta.boost_breakdown).map(([key, value]) => (
              <span key={key} className="boost-tag">
                {key}: +{Math.round((value as number) * 100)}%
              </span>
            ))}
          </div>
        )}
      </div>
    );
  };
  
  return (
    <div className="candidate-search">
      <div className="search-box">
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Cole o currículo ou descrição da vaga..."
          rows={10}
        />
        <button onClick={handleSearch} disabled={loading}>
          {loading ? 'Buscando...' : 'Buscar Candidatos'}
        </button>
      </div>
      
      {loading && <div className="loader">Processando busca...</div>}
      
      {result && (
        <div className="results">
          <div className="results-header">
            <h2>{result.candidates.length} candidatos encontrados</h2>
            {renderExtractionQuality()}
          </div>
          
          <div className="candidates-list">
            {result.candidates.map(renderCandidate)}
          </div>
        </div>
      )}
    </div>
  );
};
```

---

## Otimizações de Performance

### 1. Parallel Execution

```ruby
# app/services/optimized_search_service.rb
class OptimizedSearchService
  def search_parallel(query, limit: 50)
    service = Candidates::Search::HybridSearchService.new(
      account_id: @account_id,
      tenant: @tenant
    )
    
    # Execute ES e Embedding em paralelo
    threads = []
    es_results = nil
    emb_results = nil
    
    threads << Thread.new do
      es_results = execute_elasticsearch(query)
    end
    
    threads << Thread.new do
      emb_results = execute_embedding(query)
    end
    
    threads.each(&:join)
    
    # Fusão e ranking
    fused = WeightedRankFusion.combine(
      { elasticsearch: es_results, embedding: emb_results },
      weights: { elasticsearch: 0.5, embedding: 0.5 }
    )
    
    Reranker.apply(fused, limit: limit)
  end
end
```

### 2. Batch Embedding Generation

```ruby
# app/services/batch_embedding_service.rb
class BatchEmbeddingService
  def generate_for_queries(queries)
    # Separar queries já em cache
    cached = []
    uncached = []
    
    queries.each do |query|
      if EmbeddingCache.exists?(query, account_id: @account_id)
        cached << query
      else
        uncached << query
      end
    end
    
    # Gerar embeddings em batch para queries não cacheadas
    if uncached.any?
      batch_generate(uncached)
    end
    
    # Retornar todos
    queries.map do |query|
      EmbeddingCache.fetch(query, account_id: @account_id)
    end
  end
  
  private
  
  def batch_generate(queries)
    # API de embedding aceita múltiplas queries
    response = EmbeddingAPI.generate_batch(queries)
    
    # Cachear cada uma
    queries.zip(response.embeddings).each do |query, embedding|
      EmbeddingCache.store(query, embedding, account_id: @account_id)
    end
  end
end
```

---

## Debugging e Troubleshooting

### Debug Helper

```ruby
# app/helpers/search_debug_helper.rb
module SearchDebugHelper
  def debug_search(query, limit: 10)
    service = Candidates::Search::HybridSearchService.new(
      account_id: current_account.id,
      tenant: current_account.tenant
    )
    
    # Ativar modo debug
    result = service.search(query, limit: limit, debug: true)
    
    puts "\n" + "="*80
    puts "SEARCH DEBUG REPORT"
    puts "="*80
    
    puts "\nQuery: #{query[0..100]}..."
    puts "Type detected: #{result.metadata[:search_type]}"
    puts "Results: #{result.candidates.size}"
    
    if result.metadata[:search_type] == :resume
      puts "\nExtraction Quality:"
      puts "  Confidence: #{result.metadata[:extraction_confidence]}"
      puts "  Method: #{result.metadata[:extraction_method]}"
      puts "  Missing fields: #{result.metadata[:missing_fields].join(', ')}"
      puts "  Queries generated: #{result.metadata[:queries_generated]}"
    end
    
    if result.metadata[:search_type] == :job_description
      puts "\nJD Analysis:"
      puts "  Required skills: #{result.metadata[:required_skills].join(', ')}"
      puts "  Nice-to-have: #{result.metadata[:nice_to_have_skills].join(', ')}"
    end
    
    puts "\nFusion Weights:"
    puts "  ES: #{result.metadata[:fusion_weights][:elasticsearch]}"
    puts "  Embedding: #{result.metadata[:fusion_weights][:embedding]}"
    
    if result.explanation
      puts "\nExplanation:"
      puts "  ES query: #{result.explanation[:es_query_used]}"
      puts "  Embedding query: #{result.explanation[:embedding_query_used]}"
      puts "  HyDE used: #{result.explanation[:hyde_used]}"
      puts "  ES count: #{result.explanation[:es_count]}"
      puts "  Embedding count: #{result.explanation[:emb_count]}"
    end
    
    puts "\nTop 5 Results:"
    result.candidates.first(5).each_with_index do |c, i|
      meta = result.search_meta_by_id[c.id]
      puts "  #{i+1}. #{c.name} (score: #{meta[:final_score].round(4)})"
      puts "     Boost: #{meta[:boost].round(4)} #{meta[:boost_breakdown]}"
      puts "     Multi-query hits: #{meta[:multi_query_hits]}" if meta[:multi_query_hits]
    end
    
    puts "\n" + "="*80
    
    result
  end
end
```

### Performance Monitoring

```ruby
# app/services/search_monitor.rb
class SearchMonitor
  def self.log_search(result, duration)
    SearchLog.create!(
      account_id: result.metadata[:account_id],
      search_type: result.metadata[:search_type],
      query_preview: result.metadata[:query_preview],
      duration_ms: duration * 1000,
      results_count: result.candidates.size,
      extraction_confidence: result.metadata[:extraction_confidence],
      queries_generated: result.metadata[:queries_generated],
      cache_hit_rate: calculate_cache_hit_rate,
      performed_at: Time.current
    )
  end
  
  def self.calculate_cache_hit_rate
    stats = EmbeddingCache.stats
    stats[:hits].to_f / (stats[:hits] + stats[:misses]) rescue 0
  end
end

# Uso no controller:
def search
  start_time = Time.current
  
  @result = service.search(params[:q], limit: 10)
  
  duration = Time.current - start_time
  SearchMonitor.log_search(@result, duration)
  
  render json: @result
end
```

---

**Versão:** 2.0  
**Última atualização:** 2026-02-01  
**Próxima revisão:** 2026-03-01
