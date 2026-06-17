# syntax=docker/dockerfile:1

ARG RUBY_VERSION=3.3.0
FROM ruby:$RUBY_VERSION-slim AS base

# Diretório da app
WORKDIR /rails

# Instala pacotes base
RUN apt-get update -qq && \
    apt-get install --no-install-recommends -y \
    curl \
    libjemalloc2 \
    git \
    build-essential \
    libpq-dev \
    libyaml-dev \
    libvips \
    libssh-dev \
    cmake \
    postgresql-client \
    netcat-traditional && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/* # <-- Removi os comentários e coloquei o rm na sequência direta
# do comando anterior, usando "&& \" para encadear.

ENV RAILS_ENV="development" \
    BUNDLE_PATH="/usr/local/bundle"

# Fase de build (Esta seção está boa, o netcat-traditional já foi instalado na fase "base")
FROM base AS build

# Reinstala pacotes de build essenciais e remove cache.
RUN apt-get update -qq && \
    apt-get install --no-install-recommends -y \
    build-essential \
    git \
    libpq-dev \
    pkg-config \
    libssh-dev \
    cmake && \
    rm -rf /var/lib/apt/lists /var/cache/apt/archives

# Instala gems
COPY Gemfile Gemfile.lock ./
RUN bundle install && \
    rm -rf ~/.bundle/ "${BUNDLE_PATH}"/ruby/*/cache "${BUNDLE_PATH}"/ruby/*/bundler/gems/*/.git && \
    bundle exec bootsnap precompile --gemfile

# Copia código da aplicação
COPY . .

RUN rm -rf tmp/db

# Precompile bootsnap do app
RUN bundle exec bootsnap precompile app/ lib/

# Imagem final
FROM base

# Copia gems e código
COPY --from=build "${BUNDLE_PATH}" "${BUNDLE_PATH}"
COPY --from=build /rails /rails

# Cria usuário não-root
RUN groupadd --system --gid 1000 rails && \
    useradd rails --uid 1000 --gid 1000 --create-home --shell /bin/bash && \
    chown -R rails:rails db log storage tmp

USER 1000:1000

# ENTRYPOINT prepara o banco
ENTRYPOINT ["/rails/bin/docker-entrypoint"]

# Porta padrão
EXPOSE 3000

# Comando default
CMD ["./bin/rails", "server"]
