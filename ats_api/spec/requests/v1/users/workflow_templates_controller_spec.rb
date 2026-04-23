require 'rails_helper'

RSpec.describe 'V1::Users::WorkflowTemplates API', type: :request do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }
  let!(:other_user) { create(:user, account: account) }
  let!(:workflow_template) { create(:workflow_template, user: user, account: account) }
  let!(:other_workflow_template) { create(:workflow_template, user: other_user, account: account) }

  let(:invalid_auth_headers) { { 'Authorization' => 'Bearer invalid_token' } }
  let(:no_auth_headers) { {} }
  let(:headers) { auth_headers(user) }

  describe 'GET /v1/users/workflow_templates' do
    before do
      create(:workflow_template, is_deleted: true, user: user, account: account)
    end

    context 'when unauthenticated' do
      it 'returns unauthorized' do
        get '/v1/users/workflow_templates', headers: no_auth_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end

    context 'with invalid token' do
      it 'returns unauthorized' do
        get '/v1/users/workflow_templates', headers: invalid_auth_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'GET /v1/users/workflow_templates/:id' do
    context 'when authenticated' do
      it 'returns the workflow template' do
        get "/v1/users/workflow_templates/#{workflow_template.id}", headers: headers

        expect(response).to have_http_status(:ok)
        expect(json['data']['id'].to_i).to eq(workflow_template.id)
      end
    end

    context 'when unauthenticated' do
      it 'returns unauthorized' do
        get "/v1/users/workflow_templates/#{workflow_template.id}", headers: no_auth_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'POST /v1/users/workflow_templates' do
    let(:valid_attributes) do
      {
        workflow_template: {
          name: 'New Candidate Workflow',
          user_id: user.id,
          account_id: account.id
        }
      }.to_json
    end

    let(:invalid_attributes) do
      { workflow_template: { name: '' } }.to_json
    end

    context 'when authenticated with valid attributes' do
      it 'creates a new workflow template' do
        expect { post '/v1/users/workflow_templates', params: valid_attributes, headers: headers }
          .to change(WorkflowTemplate, :count).by(1)

        expect(response).to have_http_status(:created)
        expect(json['data']['attributes']['name']).to eq('New Candidate Workflow')
      end
    end

    context 'when unauthenticated' do
      it 'returns unauthorized' do
        post '/v1/users/workflow_templates', params: valid_attributes, headers: no_auth_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'PUT /v1/users/workflow_templates/:id' do
    let(:new_attributes) { { workflow_template: { name: 'Updated Workflow Name' } }.to_json }

    context 'when authenticated' do
      it 'updates the workflow template' do
        put "/v1/users/workflow_templates/#{workflow_template.id}", params: new_attributes, headers: headers

        expect(response).to have_http_status(:ok)
        workflow_template.reload
        expect(workflow_template.name).to eq('Updated Workflow Name')
      end
    end

    context 'when unauthenticated' do
      it 'returns unauthorized' do
        put "/v1/users/workflow_templates/#{workflow_template.id}", params: new_attributes, headers: no_auth_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'DELETE /v1/users/workflow_templates/:id' do
    context 'when authenticated' do
      it 'soft deletes the workflow template' do
        expect { delete "/v1/users/workflow_templates/#{workflow_template.id}", headers: headers }
          .not_to change(WorkflowTemplate, :count)

        expect(response).to have_http_status(:ok)
        workflow_template.reload
        expect(workflow_template.is_deleted).to be true
      end
    end

    context 'when unauthenticated' do
      it 'returns unauthorized' do
        delete "/v1/users/workflow_templates/#{workflow_template.id}", headers: no_auth_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end
end
