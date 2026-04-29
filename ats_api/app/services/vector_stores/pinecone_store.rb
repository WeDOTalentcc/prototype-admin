# app/services/vector_stores/pinecone_store.rb
class VectorStores::PineconeStore
  # def initialize
  #   @client = Pinecone::Client.new
  #   @index  = @client.index(ENV.fetch("PINECONE_INDEX"))
  # end

  # def index
  #   @index
  # end

  # def upsert(namespace:, id:, values:, metadata: {})
  #   index.upsert(
  #     vectors: [{ id: id.to_s, values: values, metadata: metadata }],
  #     namespace: namespace
  #   )
  # end

  # def delete(namespace:, ids:)
  #   index.delete(ids: Array(ids).map(&:to_s), namespace: namespace)
  # end

  # def query(namespace:, vector:, top_k: 10, filter: nil)
  #   payload = {
  #     vector: vector,
  #     namespace: namespace,
  #     top_k: top_k,
  #     include_values: false,
  #     include_metadata: true
  #   }
  #   payload[:filter] = filter if filter.is_a?(Hash) && !filter.empty?
  #   index.query(**payload)
  # end
end
