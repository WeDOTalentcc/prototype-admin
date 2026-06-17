#!/bin/bash

# Script para reembedar TODOS os candidatos e jobs em produção
# IMPORTANTE: Rode este script na VM ats-infra-server

set -e

echo "=========================================="
echo "🚀 REEMBEDDING COMPLETO EM PRODUÇÃO"
echo "=========================================="
echo ""
echo "Este script vai reembedar:"
echo "  - Todos os candidatos"
echo "  - Todos os jobs"
echo ""
echo "⚠️  ATENÇÃO: Este processo pode demorar MUITO tempo!"
echo "⚠️  Use a versão PARALLEL para ir mais rápido (recomendado)"
echo ""

# Verificar se está na VM correta
if [ ! -d "/home/rails/ats_api" ]; then
  echo "❌ ERRO: Este script deve ser executado na VM ats-infra-server"
  echo "Execute: gcloud compute ssh ats-infra-server --zone=us-central1-a"
  exit 1
fi

# Ir para o diretório da aplicação
cd /home/rails/ats_api

# Verificar dimensões atuais
echo "📊 Verificando dimensões atuais dos embeddings..."
echo ""
RAILS_ENV=production bundle exec rails embeddings:check_dimensions
echo ""

# Perguntar ao usuário qual modo usar
echo "Escolha o modo de execução:"
echo "  1) PARALLEL (RÁPIDO - 20 workers simultâneos) - RECOMENDADO"
echo "  2) SEQUENTIAL (LENTO - 1 por vez, mais seguro)"
echo ""
read -p "Digite 1 ou 2: " mode

case $mode in
  1)
    echo ""
    echo "🚀 Modo PARALLEL selecionado (20 workers)"
    echo ""
    
    # Perguntar número de workers
    read -p "Quantos workers usar? (padrão: 20): " workers
    workers=${workers:-20}
    
    echo ""
    echo "=========================================="
    echo "🔄 REEMBEDDING CANDIDATOS (PARALLEL)"
    echo "Workers: $workers"
    echo "=========================================="
    echo ""
    
    RAILS_ENV=production WORKERS=$workers bundle exec rails embeddings:sync_all_candidates_parallel
    
    echo ""
    echo "=========================================="
    echo "🔄 REEMBEDDING JOBS (PARALLEL)"
    echo "Workers: $workers"
    echo "=========================================="
    echo ""
    
    RAILS_ENV=production WORKERS=$workers bundle exec rails embeddings:sync_all_jobs_parallel
    ;;
    
  2)
    echo ""
    echo "🐌 Modo SEQUENTIAL selecionado"
    echo ""
    
    echo "=========================================="
    echo "🔄 REEMBEDDING CANDIDATOS (SEQUENTIAL)"
    echo "=========================================="
    echo ""
    
    RAILS_ENV=production bundle exec rails embeddings:sync_all_candidates
    
    echo ""
    echo "=========================================="
    echo "🔄 REEMBEDDING JOBS (SEQUENTIAL)"
    echo "=========================================="
    echo ""
    
    RAILS_ENV=production bundle exec rails embeddings:sync_all_jobs
    ;;
    
  *)
    echo "❌ Opção inválida. Abortando."
    exit 1
    ;;
esac

echo ""
echo "=========================================="
echo "📊 VERIFICAÇÃO FINAL"
echo "=========================================="
echo ""

RAILS_ENV=production bundle exec rails embeddings:check_dimensions

echo ""
echo "=========================================="
echo "✅ REEMBEDDING COMPLETO FINALIZADO!"
echo "=========================================="
echo ""
echo "Próximos passos:"
echo "  1. Verificar os logs acima para confirmar que tudo rodou sem erros"
echo "  2. Testar as buscas na aplicação"
echo "  3. Se houver problemas, rodar novamente para os registros com erro"
echo ""
