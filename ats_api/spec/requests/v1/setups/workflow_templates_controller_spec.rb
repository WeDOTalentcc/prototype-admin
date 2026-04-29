require 'rails_helper'

RSpec.describe 'V1::Setups::WorkflowTemplates API', type: :request do
  let!(:account) { create(:account, setup_token: SecureRandom.hex(16), setup_token_expires_at: 1.hour.from_now) }
  let!(:main_workflow) { create(:workflow_template, account: account, is_main: true, name: 'Main Process') }
  let!(:other_workflow) { create(:workflow_template, account: account, is_main: false, name: 'Secondary Process') }

  let(:valid_token) { account.setup_token }
  let(:invalid_token) { 'invalid-token' }
  let(:base_url) { "/v1/setups/#{valid_token}/workflow_templates" }
  let(:invalid_url) { "/v1/setups/#{invalid_token}/workflow_templates" }

  describe 'GET /v1/setups/:setup_token/workflow_templates' do
    context 'with a valid setup token' do
      it 'returns the main workflow template' do
        get base_url

        expect(response).to have_http_status(:ok)
        expect(json['data']['attributes']['name']).to eq('Main Process')
        expect(json['data']['id'].to_i).to eq(main_workflow.id)
      end
    end

    context 'with an invalid setup token' do
      it 'returns a not found error' do
        get invalid_url

        expect(response).to have_http_status(:not_found)
      end
    end

    context 'with an expired setup token' do
      before { account.update(setup_token_expires_at: 1.hour.ago) }

      it 'returns a gone error' do
        get base_url

        expect(response).to have_http_status(:gone)
      end
    end
  end

  describe 'PUT /v1/setups/:setup_token/workflow_templates' do
    let(:valid_attributes) { { workflow_template: { name: 'Updated Main Workflow' } }.to_json }
    let(:json_headers) { { 'Content-Type': 'application/json' } }

    context 'with a valid setup token' do
      it 'updates the main workflow template' do
        put base_url, params: valid_attributes, headers: json_headers

        expect(response).to have_http_status(:ok)
        main_workflow.reload
        expect(main_workflow.name).to eq('Updated Main Workflow')
      end
    end

    context 'with an invalid setup token' do
      it 'returns a not found error' do
        put invalid_url, params: valid_attributes, headers: json_headers

        expect(response).to have_http_status(:not_found)
      end
    end
  end
end
