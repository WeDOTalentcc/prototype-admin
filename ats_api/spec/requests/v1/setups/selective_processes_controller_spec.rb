require 'rails_helper'

RSpec.describe 'V1::Setups::WorkflowTemplates::SelectiveProcesses API', type: :request do
  let!(:account) { create(:account, setup_token: SecureRandom.hex(16), setup_token_expires_at: 1.hour.from_now) }
  let!(:workflow) { create(:workflow_template, account: account, is_main: true) }
  let!(:user) { create(:user) }
  let!(:step1) { create(:selective_process, workflow_template: workflow, account: account, name: 'Triagem', position: 1) }
  let!(:step2) { create(:selective_process, workflow_template: workflow, account: account, name: 'Entrevista RH', position: 2) }

  let(:valid_token) { account.setup_token }
  let(:base_url) { "/v1/setups/#{valid_token}/workflow_templates/selective_processes" }
  let(:json_headers) { { 'Content-Type': 'application/json' } }

  describe 'GET /index' do
    it 'returns all selective processes for the main workflow' do
      get base_url

      expect(response).to have_http_status(:ok)
      expect(json['data'].size).to eq(2)
      expect(json['data'][0]['attributes']['name']).to eq('Triagem')
    end
  end

  describe 'GET /show' do
    it 'returns a single selective process' do
      get "#{base_url}/#{step1.id}"

      expect(response).to have_http_status(:ok)
      expect(json['data']['attributes']['name']).to eq('Triagem')
    end
  end

 describe 'POST /create' do
    let(:valid_attributes) do
      { selective_process: { name: 'Entrevista Gestor', position: 3, status: 1, account_id: user.account_id } }.to_json
    end

    it 'creates a new selective process' do
      expect { post base_url, params: valid_attributes, headers: json_headers }
        .to change(SelectiveProcess, :count).by(1)
     expect(response).to have_http_status(:created)
      expect(json['data']['attributes']['name']).to eq('Entrevista Gestor')
    end
  end

  describe 'PUT /update' do
    let(:new_attributes) { { selective_process: { name: 'Triagem de Currículos' } }.to_json }

    it 'updates the selective process' do
      put "#{base_url}/#{step1.id}", params: new_attributes, headers: json_headers

      expect(response).to have_http_status(:ok)
      step1.reload
      expect(step1.name).to eq('Triagem de Currículos')
    end
  end

  describe 'DELETE /destroy' do
    it 'deletes the selective process' do
      expect { delete "#{base_url}/#{step2.id}" }
        .to change(SelectiveProcess, :count).by(-1)

      expect(response).to have_http_status(:no_content)
    end
  end
end
