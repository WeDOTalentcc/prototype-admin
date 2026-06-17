require 'rails_helper'

RSpec.describe 'V1::Users::Jobs::MatchesController', type: :request do
  let(:user) { create(:user) }
  let(:account) { user.account }
  let!(:job) { create(:job, user: user, account: account, title: 'Ruby Dev', description: 'Rails API position') }
  let!(:candidates) do
    create_list(:candidate, 3, account: account).each(&:reload)
  end

  before do
    allow(Embeddings::Encoder).to receive(:new).and_return(double(call: Array.new(PINECONE_DIM, 0.01)))
    allow(VectorStores::PineconeStore).to receive(:new).and_return(double(query: pinecone_response))
    allow(Candidate).to receive(:search_default).and_call_original
  end

  let(:pinecone_response) do
    {
      'matches' => candidates.map.with_index do |c, idx|
        {
          'score' => (0.9 - idx * 0.1),
          'metadata' => { 'candidate_id' => c.id }
        }
      end
    }
  end

  describe 'GET /v1/users/jobs/:job_id/matches/candidates' do
    it 'returns matched candidates with scores' do
      get "/v1/users/jobs/#{job.id}/matches/candidates", headers: auth_headers(user)
      expect(response).to have_http_status(:ok)
      body = JSON.parse(response.body)
      expect(body['data']).to be_present
      first = body['data'].first
      expect(first['attributes']['match_score']).to be >= body['data'].last['attributes']['match_score']
      expect(body['meta']['total_count']).to be >= 0
    end

    it 'applies where filter narrowing results' do
      target_id = candidates.first.id
      where_param = { id: [ target_id ] }.to_json
      get "/v1/users/jobs/#{job.id}/matches/candidates", params: { where: where_param }, headers: auth_headers(user)
      body = JSON.parse(response.body)
      ids = body['data'].map { |r| r['attributes']['id'] }
      expect(ids).to eq([ target_id ])
    end

    it 'returns 403 for different account' do
      other_job = create(:job)
      get "/v1/users/jobs/#{other_job.id}/matches/candidates", headers: auth_headers(user)
      expect(response.status).to eq(403).or eq(404)
    end
  end
end
