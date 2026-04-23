# app/services/vector_stores/namespaces.rb
module VectorStores
  module Namespaces
    extend self

    TENANT_PREFIX  = ENV.fetch("PINECONE_TENANT_PREFIX", "acct")
    NAMESPACE_BASE = {
      jobs:       ENV.fetch("PINECONE_NAMESPACE_JOBS", "jobs"),
      candidates: ENV.fetch("PINECONE_NAMESPACE_CANDIDATES", "candidates")
    }.freeze

    def for_account(account_id, type)
      base = NAMESPACE_BASE.fetch(type.to_sym) { raise ArgumentError, "invalid type: #{type.inspect}" }
      "#{TENANT_PREFIX}:#{account_id}:#{base}"
    end
  end
end
