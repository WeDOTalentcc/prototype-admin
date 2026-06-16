# syntax=docker/dockerfile:1

# -------------------------------------------------------------------------------------
# CONFIGURAÇÃO UNIVERSAL
# -------------------------------------------------------------------------------------
ARG RUBY_VERSION=3.4.4
ARG BUNDLER_VERSION=2.6.5

# -------------------------------------------------------------------------------------
# Estágio BASE: Mínimo necessário para EXECUTAR a aplicação.
# -------------------------------------------------------------------------------------
FROM ruby:${RUBY_VERSION}-slim AS base

RUN apt-get update -qq && \
    apt-get install --no-install-recommends -y \
    curl git imagemagick libjemalloc2 libpq5 libvips42 libyaml-0-2 postgresql-client \
    openjdk-17-jre-headless && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

WORKDIR /rails

# IMPORTANTE: Não criar usuário rails aqui para dev - causa problemas de permissão
# com volumes montados. Vamos lidar com isso de forma diferente.

ENV BUNDLE_PATH="/usr/local/bundle"
ENV PATH="/usr/local/bundle/bin:$PATH"

# -------------------------------------------------------------------------------------
# Estágio BUILD: Compila gems e prepara o código.
# -------------------------------------------------------------------------------------
FROM base AS build
ARG APP_ENV=production
ARG BUNDLER_VERSION

ENV RAILS_ENV=${APP_ENV}

# Instala dependências de BUILD
RUN apt-get update -qq && \
    apt-get install --no-install-recommends -y \
    build-essential libpq-dev libvips-dev libyaml-dev libssh2-1-dev cmake pkg-config libgit2-dev && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

# Instala a versão exata do Bundler
RUN gem install bundler -v "${BUNDLER_VERSION}"

WORKDIR /rails

# Cache de gems
COPY Gemfile Gemfile.lock ./

# Configura grupos de gems dependendo do ambiente
RUN if [ "${APP_ENV}" = "production" ]; then \
        bundle config set without 'development test'; \
    else \
        bundle config unset without || true; \
    fi && \
    bundle config set jobs $(nproc) && \
    bundle install && \
    rm -rf ~/.bundle/ "${BUNDLE_PATH}"/ruby/*/cache "${BUNDLE_PATH}"/ruby/*/bundler/gems/*/.git

# Copia o resto do código
COPY . .

# Precompila bootsnap (se não for desenvolvimento com volume montado)
RUN if [ "${APP_ENV}" = "production" ]; then \
        bundle exec bootsnap precompile --gemfile && \
        bundle exec bootsnap precompile app/ lib/; \
    fi

# -------------------------------------------------------------------------------------
# Estágio FINAL
# -------------------------------------------------------------------------------------
FROM base AS final
ARG APP_ENV=production
ARG BUNDLER_VERSION

ENV RAILS_ENV=${APP_ENV}

# Reinstala bundler na versão correta (importante!)
RUN gem install bundler -v "${BUNDLER_VERSION}"

# Instala dependências de build TAMBÉM no final para desenvolvimento
# (necessário para gems nativas quando bundle install roda no entrypoint)
RUN if [ "${APP_ENV}" != "production" ]; then \
        apt-get update -qq && \
        apt-get install --no-install-recommends -y \
        build-essential libpq-dev libvips-dev libyaml-dev libssh2-1-dev cmake pkg-config libgit2-dev && \
        rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*; \
    fi

# Copia gems e código do estágio de build
COPY --from=build "${BUNDLE_PATH}" "${BUNDLE_PATH}"
COPY --from=build /rails /rails

# Copia e configura o entrypoint
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

WORKDIR /rails

# Usa o entrypoint inteligente
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Comando padrão (bundle exec garante que puma seja encontrado no Cloud Run)
CMD ["bundle", "exec", "puma", "-C", "config/puma.rb"]
EXPOSE 8080
