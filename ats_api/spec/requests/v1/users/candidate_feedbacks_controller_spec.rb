# frozen_string_literal: true

require 'rails_helper'

RSpec.describe 'V1::Users::CandidateFeedbacks API', type: :request do
  let!(:account) { create(:account) }
  let!(:user) do
    Apartment::Tenant.switch!(account.tenant)
    create(:user, account: account)
  end
  let!(:sourcing) do
    Apartment::Tenant.switch!(account.tenant)
    create(:sourcing, account: account, user: user)
  end
  let!(:candidate) do
    Apartment::Tenant.switch!(account.tenant)
    create(:candidate, account: account)
  end
  let!(:job) do
    Apartment::Tenant.switch!(account.tenant)
    create(:job, account: account, user: user)
  end

  let(:invalid_auth_headers) { { 'Authorization' => 'Bearer invalid_token', 'Content-Type' => 'application/json' } }
  let(:no_auth_headers) { { 'Content-Type' => 'application/json' } }

  describe 'GET /v1/users/candidate_feedbacks', skip: "Elasticsearch multi-tenant config needed" do
    before do
      Apartment::Tenant.switch!(account.tenant)

      3.times do
        c = create(:candidate, account: account)
        create(:candidate_feedback, sourcing: sourcing, user: user, account: account, candidate: c)
      end

      CandidateFeedback.reindex
      sleep 1
    end

    after do
      Apartment::Tenant.reset
    end

    context 'when authenticated' do
      it 'returns all feedbacks' do
        get '/v1/users/candidate_feedbacks', headers: auth_headers(user)
        expect(response).to have_http_status(:ok)
        expect(json['data'].size).to eq(3)
      end

      it 'returns feedbacks with correct structure' do
        get '/v1/users/candidate_feedbacks', headers: auth_headers(user)

        feedback_data = json['data'].first
        expect(feedback_data['type']).to eq('candidate_feedback')
        expect(feedback_data['attributes']).to have_key('feedback_type')
        expect(feedback_data['attributes']).to have_key('sourcing_id')
        expect(feedback_data['attributes']).to have_key('candidate_id')
      end

      context 'with filters' do
        before do
          Apartment::Tenant.switch!(account.tenant)

          other_sourcing = create(:sourcing, account: account, user: user)
          candidate1 = create(:candidate, account: account)
          candidate2 = create(:candidate, account: account)
          candidate3 = create(:candidate, account: account)

          @like_feedback = create(:candidate_feedback, sourcing: sourcing, user: user, account: account, candidate: candidate1, feedback_type: 'like')
          @dislike_feedback = create(:candidate_feedback, sourcing: sourcing, user: user, account: account, candidate: candidate2, feedback_type: 'dislike')
          @other_sourcing_feedback = create(:candidate_feedback, sourcing: other_sourcing, user: user, account: account, candidate: candidate3)
          @other_sourcing = other_sourcing

          CandidateFeedback.reindex
          sleep 1
        end

        it 'filters by feedback_type' do
          get '/v1/users/candidate_feedbacks',
              params: { where: { feedback_type: 'like' }.to_json },
              headers: auth_headers(user)

          expect(response).to have_http_status(:ok)
          feedback_types = json['data'].map { |f| f['attributes']['feedback_type'] }.uniq
          expect(feedback_types).to eq([ 'like' ])
        end

        it 'filters by sourcing_id' do
          get '/v1/users/candidate_feedbacks',
              params: { where: { sourcing_id: sourcing.id }.to_json },
              headers: auth_headers(user)

          expect(response).to have_http_status(:ok)
          sourcing_ids = json['data'].map { |f| f['attributes']['sourcing_id'] }.uniq
          expect(sourcing_ids).to eq([ sourcing.id ])
        end
      end

      it 'returns meta with total' do
        get '/v1/users/candidate_feedbacks', headers: auth_headers(user)

        expect(json['meta']).to have_key('total')
        expect(json['meta']['total']).to be >= 3
      end
    end

    context 'when unauthenticated' do
      it 'returns unauthorized' do
        get '/v1/users/candidate_feedbacks', headers: no_auth_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end

    context 'with invalid token' do
      it 'returns unauthorized' do
        get '/v1/users/candidate_feedbacks', headers: invalid_auth_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'POST /v1/users/candidate_feedbacks' do
    let(:valid_params) do
      {
        sourcing_id: sourcing.id,
        candidate_id: candidate.id,
        feedback_type: 'like',
        job_id: job.id
      }
    end

    let(:invalid_params) do
      {
        feedback_type: 'invalid_type'
      }
    end

    context 'when authenticated with valid params' do
      it 'creates a new feedback' do
        expect {
          post '/v1/users/candidate_feedbacks',
               params: valid_params.to_json,
               headers: auth_headers(user)
        }.to change(CandidateFeedback, :count).by(1)

        expect(response).to have_http_status(:created)
      end

      it 'returns created feedback with correct attributes' do
        post '/v1/users/candidate_feedbacks',
             params: valid_params.to_json,
             headers: auth_headers(user)

        expect(response).to have_http_status(:created)
        expect(json['data']['attributes']['feedback_type']).to eq('like')
        expect(json['data']['attributes']['sourcing_id']).to eq(sourcing.id)
        expect(json['data']['attributes']['candidate_id']).to eq(candidate.id)
        expect(json['data']['attributes']['job_id']).to eq(job.id)
      end

      it 'returns meta with action :created' do
        post '/v1/users/candidate_feedbacks',
             params: valid_params.to_json,
             headers: auth_headers(user)

        expect(json['meta']['action']).to eq('created')
        expect(json['meta']['message']).to include('sucesso')
      end
    end

    context 'when feedback already exists with same type (toggle OFF)' do
      let!(:existing_feedback) do
        create(:candidate_feedback,
          sourcing: sourcing,
          candidate: candidate,
          user: user,
          account: account,
          feedback_type: 'like',
          is_deleted: false
        )
      end

      it 'does not create new feedback' do
        expect {
          post '/v1/users/candidate_feedbacks',
               params: valid_params.to_json,
               headers: auth_headers(user)
        }.not_to change(CandidateFeedback, :count)
      end

      it 'soft deletes existing feedback' do
        post '/v1/users/candidate_feedbacks',
             params: valid_params.to_json,
             headers: auth_headers(user)

        expect(response).to have_http_status(:ok)
        existing_feedback.reload
        expect(existing_feedback.is_deleted).to be true
      end

      it 'returns meta with action :removed' do
        post '/v1/users/candidate_feedbacks',
             params: valid_params.to_json,
             headers: auth_headers(user)

        expect(json['meta']['action']).to eq('removed')
      end
    end

    context 'when feedback exists with different type (toggle)' do
      let!(:existing_feedback) do
        create(:candidate_feedback,
          sourcing: sourcing,
          candidate: candidate,
          user: user,
          account: account,
          feedback_type: 'like',
          is_deleted: false
        )
      end

      let(:toggle_params) do
        {
          sourcing_id: sourcing.id,
          candidate_id: candidate.id,
          feedback_type: 'dislike'
        }
      end

      it 'does not create new feedback' do
        expect {
          post '/v1/users/candidate_feedbacks',
               params: toggle_params.to_json,
               headers: auth_headers(user)
        }.not_to change(CandidateFeedback, :count)
      end

      it 'updates feedback type' do
        post '/v1/users/candidate_feedbacks',
             params: toggle_params.to_json,
             headers: auth_headers(user)

        expect(response).to have_http_status(:ok)
        existing_feedback.reload
        expect(existing_feedback.feedback_type).to eq('dislike')
        expect(existing_feedback.is_deleted).to be false
      end

      it 'returns meta with action :updated' do
        post '/v1/users/candidate_feedbacks',
             params: toggle_params.to_json,
             headers: auth_headers(user)

        expect(json['meta']['action']).to eq('updated')
      end
    end

    context 'with sourced_profile_sourcing_id' do
      let(:sourced_profile) { create(:sourced_profile, account: account, candidate: candidate) }
      let(:sourced_profile_sourcing) { create(:sourced_profile_sourcing, sourced_profile: sourced_profile, sourcing: sourcing, account: account, user: user) }

      let(:sps_params) do
        {
          sourced_profile_sourcing_id: sourced_profile_sourcing.id,
          feedback_type: 'like'
        }
      end

      it 'creates feedback with sourced_profile_sourcing_id' do
        expect {
          post '/v1/users/candidate_feedbacks',
               params: sps_params.to_json,
               headers: auth_headers(user)
        }.to change(CandidateFeedback, :count).by(1)

        expect(response).to have_http_status(:created)

        feedback = CandidateFeedback.last
        expect(feedback.sourced_profile_sourcing_id).to eq(sourced_profile_sourcing.id)
        expect(feedback.sourcing_id).to eq(sourcing.id)
        expect(feedback.candidate_id).to eq(candidate.id)
      end
    end

    context 'with invalid params' do
      it 'returns unprocessable entity' do
        post '/v1/users/candidate_feedbacks',
             params: invalid_params.to_json,
             headers: auth_headers(user)

        expect(response).to have_http_status(:unprocessable_entity)
        expect(json['errors']).to be_present
      end
    end

    context 'when unauthenticated' do
      it 'returns unauthorized' do
        post '/v1/users/candidate_feedbacks',
             params: valid_params.to_json,
             headers: no_auth_headers

        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'DELETE /v1/users/candidate_feedbacks/:id' do
    let!(:feedback) do
      create(:candidate_feedback,
        sourcing: sourcing,
        candidate: candidate,
        user: user,
        account: account,
        is_deleted: false
      )
    end

    context 'when authenticated' do
      it 'soft deletes the feedback' do
        delete "/v1/users/candidate_feedbacks/#{feedback.id}",
               headers: auth_headers(user)

        expect(response).to have_http_status(:ok)
        feedback.reload
        expect(feedback.is_deleted).to be true
      end

      it 'returns the deleted feedback' do
        delete "/v1/users/candidate_feedbacks/#{feedback.id}",
               headers: auth_headers(user)

        expect(json['data']['id']).to eq(feedback.id.to_s)
        expect(json['meta']['message']).to include('removido com sucesso')
      end

      it 'does not physically delete the record' do
        expect {
          delete "/v1/users/candidate_feedbacks/#{feedback.id}",
                 headers: auth_headers(user)
        }.not_to change(CandidateFeedback, :count)
      end
    end

    context 'when feedback does not exist' do
      it 'returns not found' do
        delete '/v1/users/candidate_feedbacks/99999',
               headers: auth_headers(user)

        expect(response).to have_http_status(:not_found)
        expect(json['errors']).to include('CandidateFeedback não encontrado')
      end
    end

    context 'when feedback already deleted' do
      before { feedback.update!(is_deleted: true) }

      it 'returns not found' do
        delete "/v1/users/candidate_feedbacks/#{feedback.id}",
               headers: auth_headers(user)

        expect(response).to have_http_status(:not_found)
      end
    end

    context 'when unauthenticated' do
      it 'returns unauthorized' do
        delete "/v1/users/candidate_feedbacks/#{feedback.id}",
               headers: no_auth_headers

        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'DELETE /v1/users/candidate_feedbacks with where filter' do
    let!(:candidate1) { create(:candidate, account: account) }
    let!(:candidate2) { create(:candidate, account: account) }
    let!(:sourced_profile) { create(:sourced_profile, account: account, candidate: candidate1) }
    let!(:sourced_profile_sourcing) { create(:sourced_profile_sourcing, sourced_profile: sourced_profile, sourcing: sourcing, account: account, user: user) }

    let!(:feedback1) do
      create(:candidate_feedback,
        sourced_profile_sourcing: sourced_profile_sourcing,
        sourcing: sourcing,
        candidate: candidate1,
        user: user,
        account: account,
        feedback_type: 'like',
        is_deleted: false
      )
    end

    let!(:feedback2) do
      create(:candidate_feedback,
        sourcing: sourcing,
        candidate: candidate2,
        user: user,
        account: account,
        feedback_type: 'like',
        is_deleted: false
      )
    end

    context 'when authenticated with where filter by sourced_profile_sourcing_id' do
      it 'soft deletes the last feedback matching the filter' do
        where_params = { sourced_profile_sourcing_id: sourced_profile_sourcing.id }

        delete "/v1/users/candidate_feedbacks?where=#{CGI.escape(where_params.to_json)}",
               headers: auth_headers(user)

        expect(response).to have_http_status(:ok)
        feedback1.reload
        expect(feedback1.is_deleted).to be true
        expect(feedback2.reload.is_deleted).to be false
      end
    end

    context 'when authenticated with where filter by candidate_id' do
      it 'soft deletes the last feedback for the candidate' do
        where_params = { candidate_id: candidate2.id }

        delete "/v1/users/candidate_feedbacks?where=#{CGI.escape(where_params.to_json)}",
               headers: auth_headers(user)

        expect(response).to have_http_status(:ok)
        feedback2.reload
        expect(feedback2.is_deleted).to be true
        expect(feedback1.reload.is_deleted).to be false
      end
    end

    context 'when multiple feedbacks match the filter' do
      let!(:candidate3) { create(:candidate, account: account) }
      let!(:sourcing2) { create(:sourcing, account: account, user: user) }

      let!(:feedback3) do
        create(:candidate_feedback,
          sourcing: sourcing2,
          candidate: candidate3,
          user: user,
          account: account,
          feedback_type: 'like',
          is_deleted: false,
          created_at: 1.hour.ago
        )
      end

      it 'deletes only the most recent one (last)' do
        where_params = { feedback_type: 'like' }

        delete "/v1/users/candidate_feedbacks?where=#{CGI.escape(where_params.to_json)}",
               headers: auth_headers(user)

        expect(response).to have_http_status(:ok)

        last_like = [ feedback1, feedback2, feedback3 ].select { |f| f.feedback_type == 'like' && !f.is_deleted }.max_by(&:created_at)

        deleted_feedback = CandidateFeedback.find(last_like.id)
        expect(deleted_feedback.is_deleted).to be true

        feedback3.reload
        expect([ feedback1, feedback2, feedback3 ].any? { |f| f.reload.is_deleted && f != deleted_feedback }).to be false
      end
    end

    context 'when no feedback matches the filter' do
      it 'returns not found' do
        where_params = { candidate_id: 99999 }

        delete "/v1/users/candidate_feedbacks?where=#{CGI.escape(where_params.to_json)}",
               headers: auth_headers(user)

        expect(response).to have_http_status(:not_found)
        expect(json['errors']).to include('CandidateFeedback não encontrado')
      end
    end

    context 'when unauthenticated' do
      it 'returns unauthorized' do
        where_params = { candidate_id: candidate1.id }

        delete "/v1/users/candidate_feedbacks?where=#{CGI.escape(where_params.to_json)}",
               headers: no_auth_headers

        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'multi-tenant scoping', skip: "Elasticsearch multi-tenant config needed" do
    before do
      @other_account = create(:account)
      Apartment::Tenant.switch!(@other_account.tenant)

      @other_user = create(:user, account: @other_account)
      @other_sourcing = create(:sourcing, account: @other_account, user: @other_user)
      @other_candidate = create(:candidate, account: @other_account)
      @other_feedback = create(:candidate_feedback,
        sourcing: @other_sourcing,
        candidate: @other_candidate,
        user: @other_user,
        account: @other_account
      )

      CandidateFeedback.reindex
      sleep 1

      Apartment::Tenant.switch!(account.tenant)
      CandidateFeedback.reindex
      sleep 1
    end

    after do
      Apartment::Tenant.reset
    end

    it 'does not return feedbacks from other accounts in index' do
      get '/v1/users/candidate_feedbacks', headers: auth_headers(user)

      feedback_ids = json['data'].map { |f| f['id'].to_i }
      expect(feedback_ids).not_to include(@other_feedback.id)
    end

    it 'cannot delete feedback from other account' do
      delete "/v1/users/candidate_feedbacks/#{@other_feedback.id}",
             headers: auth_headers(user)

      expect(response).to have_http_status(:not_found)
    end

    it 'cannot create feedback for sourcing from other account' do
      post '/v1/users/candidate_feedbacks',
           params: {
             sourcing_id: @other_sourcing.id,
             candidate_id: candidate.id,
             feedback_type: 'like'
           }.to_json,
           headers: auth_headers(user)

      expect(response).to have_http_status(:unprocessable_entity)
    end
  end

  describe 'different contexts' do
    context 'with apply_id context' do
      let(:selective_process) { create(:selective_process, account: account) }
      let(:apply) { create(:apply, candidate: candidate, job: job, selective_process: selective_process, account: account) }

      it 'creates feedback with apply context' do
        post '/v1/users/candidate_feedbacks',
             params: {
               apply_id: apply.id,
               feedback_type: 'like'
             }.to_json,
             headers: auth_headers(user)

        expect(response).to have_http_status(:created)
        expect(json['data']['attributes']['apply_id']).to eq(apply.id)
        expect(json['data']['attributes']['candidate_id']).to eq(candidate.id)
        expect(json['data']['attributes']['job_id']).to eq(job.id)
      end
    end

    context 'with only candidate_id context' do
      it 'creates feedback with only candidate' do
        post '/v1/users/candidate_feedbacks',
             params: {
               candidate_id: candidate.id,
               feedback_type: 'like'
             }.to_json,
             headers: auth_headers(user)

        expect(response).to have_http_status(:created)
        expect(json['data']['attributes']['candidate_id']).to eq(candidate.id)
        expect(json['data']['attributes']['sourcing_id']).to be_nil
        expect(json['data']['attributes']['apply_id']).to be_nil
      end
    end
  end
end
