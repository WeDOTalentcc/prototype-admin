# frozen_string_literal: true

require 'rails_helper'

RSpec.describe 'V1::Users::EmailTemplates API', type: :request do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }
  let!(:other_user) { create(:user) }

  let(:authentication_headers) { auth_headers(user) }
  let(:invalid_authentication_headers) { { 'Authorization' => 'Bearer invalid_token' } }
  let(:no_authentication_headers) { {} }

  describe 'GET /v1/users/email_templates' do
    let!(:user_templates) { create_list(:email_template, 3, user: user, account: user.account) }
    let!(:other_templates) { create_list(:email_template, 2, user: other_user, account: other_user.account) }
    let!(:deleted_template) { create(:email_template, :deleted, user: user, account: user.account) }

    before do
      EmailTemplate.reindex
    end

    context 'when authenticated' do
      it 'returns only user templates' do
        get '/v1/users/email_templates', headers: authentication_headers

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json['data'].size).to eq(3)
      end

      it 'excludes deleted templates by default' do
        get '/v1/users/email_templates', headers: authentication_headers

        json = JSON.parse(response.body)
        template_ids = json['data'].map { |t| t['id'].to_i }
        expect(template_ids).not_to include(deleted_template.id)
      end
    end

    context 'when not authenticated' do
      it 'returns unauthorized' do
        get '/v1/users/email_templates', headers: no_authentication_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'GET /v1/users/email_templates/:id' do
    let!(:email_template) { create(:email_template, user: user, account: user.account) }

    context 'when authenticated' do
      it 'returns the email template' do
        get "/v1/users/email_templates/#{email_template.id}", headers: authentication_headers

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)

        expect(json['data']['id']).to eq(email_template.id.to_s)
        expect(json['data']['attributes']['name']).to eq(email_template.name)
        expect(json['data']['attributes']['subject']).to eq(email_template.subject)
        expect(json['data']['attributes']['content']).to eq(email_template.content)
      end
    end

    context 'when template belongs to another account' do
      let!(:other_template) { create(:email_template, user: other_user, account: other_user.account) }

      it 'returns not found' do
        get "/v1/users/email_templates/#{other_template.id}", headers: authentication_headers
        expect(response).to have_http_status(:not_found)
      end
    end

    context 'when not authenticated' do
      it 'returns unauthorized' do
        get "/v1/users/email_templates/#{email_template.id}", headers: no_authentication_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'POST /v1/users/email_templates' do
    let(:valid_attributes) do
      {
        email_template: {
          name: 'Novo Template',
          subject: 'Assunto do Email',
          content: 'Conteúdo do email com {{candidato_nome}}',
          category_id: 1
        }
      }
    end

    let(:invalid_attributes) do
      {
        email_template: {
          name: '',
          subject: '',
          content: '',
          category_id: nil
        }
      }
    end

    context 'when authenticated with valid attributes' do
      it 'creates a new email template' do
        post '/v1/users/email_templates', params: valid_attributes.to_json, headers: authentication_headers

        expect(response).to have_http_status(:created)
        json = JSON.parse(response.body)

        expect(json['data']['attributes']['name']).to eq('Novo Template')
        expect(json['data']['attributes']['subject']).to eq('Assunto do Email')
        expect(json['data']['attributes']['user_id']).to eq(user.id)
        expect(json['data']['attributes']['account_id']).to eq(user.account.id)
      end

      it 'increases email template count by 1' do
        expect {
          post '/v1/users/email_templates', params: valid_attributes.to_json, headers: authentication_headers
        }.to change(EmailTemplate, :count).by(1)
      end

      it 'sets the correct user and account' do
        post '/v1/users/email_templates', params: valid_attributes.to_json, headers: authentication_headers

        template = EmailTemplate.last
        expect(template.user_id).to eq(user.id)
        expect(template.account_id).to eq(user.account.id)
      end
    end

    context 'when authenticated with invalid attributes' do
      it 'returns unprocessable entity' do
        post '/v1/users/email_templates', params: invalid_attributes.to_json, headers: authentication_headers

        expect(response).to have_http_status(:unprocessable_entity)
      end
    end

    context 'when not authenticated' do
      it 'returns unauthorized' do
        post '/v1/users/email_templates', params: valid_attributes.to_json, headers: no_authentication_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'PUT /v1/users/email_templates/:id' do
    let!(:email_template) { create(:email_template, user: user, account: user.account, name: 'Template Original') }

    let(:update_attributes) do
      {
        email_template: {
          name: 'Template Atualizado',
          subject: 'Novo Assunto',
          content: 'Novo conteúdo'
        }
      }
    end

    context 'when authenticated' do
      it 'updates the email template' do
        put "/v1/users/email_templates/#{email_template.id}", params: update_attributes.to_json, headers: authentication_headers

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)

        expect(json['data']['attributes']['name']).to eq('Template Atualizado')
        expect(json['data']['attributes']['subject']).to eq('Novo Assunto')
        expect(json['data']['attributes']['content']).to eq('Novo conteúdo')
      end

      it 'persists the changes' do
        put "/v1/users/email_templates/#{email_template.id}", params: update_attributes.to_json, headers: authentication_headers

        email_template.reload
        expect(email_template.name).to eq('Template Atualizado')
        expect(email_template.subject).to eq('Novo Assunto')
      end
    end

    context 'when template belongs to another account' do
      let!(:other_template) { create(:email_template, user: other_user, account: other_user.account) }

      it 'returns not found' do
        put "/v1/users/email_templates/#{other_template.id}", params: update_attributes.to_json, headers: authentication_headers
        expect(response).to have_http_status(:not_found)
      end
    end

    context 'when not authenticated' do
      it 'returns unauthorized' do
        put "/v1/users/email_templates/#{email_template.id}", params: update_attributes.to_json, headers: no_authentication_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'DELETE /v1/users/email_templates/:id' do
    let!(:email_template) { create(:email_template, user: user, account: user.account) }

    context 'when authenticated' do
      it 'soft deletes the email template' do
        delete "/v1/users/email_templates/#{email_template.id}", headers: authentication_headers

        expect(response).to have_http_status(:ok)
        email_template.reload
        expect(email_template.is_deleted).to be true
      end

      it 'does not actually delete the record' do
        expect {
          delete "/v1/users/email_templates/#{email_template.id}", headers: authentication_headers
        }.not_to change(EmailTemplate, :count)
      end
    end

    context 'when template belongs to another account' do
      let!(:other_template) { create(:email_template, user: other_user, account: other_user.account) }

      it 'returns not found' do
        delete "/v1/users/email_templates/#{other_template.id}", headers: authentication_headers
        expect(response).to have_http_status(:not_found)
      end
    end

    context 'when not authenticated' do
      it 'returns unauthorized' do
        delete "/v1/users/email_templates/#{email_template.id}", headers: no_authentication_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'GET /v1/users/email_templates/categories' do
    context 'when authenticated' do
      it 'returns all categories' do
        get '/v1/users/email_templates/categories', headers: authentication_headers

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)

        expect(json['categories']).to be_an(Array)
        expect(json['categories'].size).to eq(5)
        expect(json['categories'].first).to have_key('id')
        expect(json['categories'].first).to have_key('name')
        expect(json['categories'].first).to have_key('color')
      end
    end

    context 'when not authenticated' do
      it 'returns unauthorized' do
        get '/v1/users/email_templates/categories', headers: no_authentication_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'POST /v1/users/email_templates/generate_suggestion' do
    let(:suggestion_response) do
      {
        name: 'Template Sugerido',
        subject: 'Assunto Sugerido',
        content: 'Conteúdo sugerido com {{candidato_nome}}',
        category_id: 1
      }
    end

    context 'when creating suggestion from scratch' do
      let(:params) do
        {
          text: 'Crie um email de aprovação formal para candidatos'
        }
      end

      before do
        allow(EmailTemplates::SuggestionService).to receive(:call).and_return(suggestion_response)
      end

      it 'generates a suggestion' do
        post '/v1/users/email_templates/generate_suggestion', params: params.to_json, headers: authentication_headers

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)

        expect(json['data']['name']).to eq('Template Sugerido')
        expect(json['data']['subject']).to eq('Assunto Sugerido')
        expect(json['data']['content']).to eq('Conteúdo sugerido com {{candidato_nome}}')
        expect(json['data']['category_id']).to eq(1)
      end

      it 'calls the service with nil template' do
        post '/v1/users/email_templates/generate_suggestion', params: params.to_json, headers: authentication_headers

        expect(EmailTemplates::SuggestionService).to have_received(:call).with(nil, 'Crie um email de aprovação formal para candidatos', {})
      end
    end

    context 'when creating suggestion based on existing template' do
      let!(:email_template) { create(:email_template, user: user, account: user.account) }
      let(:params) do
        {
          email_template_id: email_template.id,
          text: 'Torne o email mais formal'
        }
      end

      before do
        allow(EmailTemplates::SuggestionService).to receive(:call).and_return(suggestion_response)
      end

      it 'generates a suggestion based on template' do
        post '/v1/users/email_templates/generate_suggestion', params: params.to_json, headers: authentication_headers

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)

        expect(json['data']['name']).to eq('Template Sugerido')
        expect(json['data']['category_id']).to eq(1)
      end

      it 'calls the service with the template' do
        post '/v1/users/email_templates/generate_suggestion', params: params.to_json, headers: authentication_headers

        expect(EmailTemplates::SuggestionService).to have_received(:call).with(email_template, 'Torne o email mais formal', {})
      end
    end

    context 'when text is blank' do
      let(:params) { { text: '' } }

      it 'returns unprocessable entity' do
        post '/v1/users/email_templates/generate_suggestion', params: params.to_json, headers: authentication_headers

        expect(response).to have_http_status(:unprocessable_entity)
        json = JSON.parse(response.body)
        expect(json['errors']).to be_present
      end
    end

    context 'when template does not exist' do
      let(:params) do
        {
          email_template_id: 99999,
          text: 'Modifique o template'
        }
      end

      it 'returns not found' do
        post '/v1/users/email_templates/generate_suggestion', params: params.to_json, headers: authentication_headers

        expect(response).to have_http_status(:not_found)
      end
    end

    context 'when template belongs to another account' do
      let!(:other_template) { create(:email_template, user: other_user, account: other_user.account) }
      let(:params) do
        {
          email_template_id: other_template.id,
          text: 'Modifique o template'
        }
      end

      it 'returns not found' do
        post '/v1/users/email_templates/generate_suggestion', params: params.to_json, headers: authentication_headers

        expect(response).to have_http_status(:not_found)
      end
    end

    context 'when service returns nil' do
      let(:params) { { text: 'Crie um template' } }

      before do
        allow(EmailTemplates::SuggestionService).to receive(:call).and_return(nil)
      end

      it 'returns internal server error' do
        post '/v1/users/email_templates/generate_suggestion', params: params.to_json, headers: authentication_headers

        expect(response).to have_http_status(:internal_server_error)
        json = JSON.parse(response.body)
        expect(json['errors']).to be_present
      end
    end

    context 'when using modification_text parameter' do
      let(:params) do
        {
          modification_text: 'Crie um email de aprovação'
        }
      end

      before do
        allow(EmailTemplates::SuggestionService).to receive(:call).and_return(suggestion_response)
      end

      it 'accepts modification_text as parameter' do
        post '/v1/users/email_templates/generate_suggestion', params: params.to_json, headers: authentication_headers

        expect(response).to have_http_status(:ok)
        expect(EmailTemplates::SuggestionService).to have_received(:call).with(nil, 'Crie um email de aprovação', {})
      end
    end

    context 'when using id parameter instead of email_template_id' do
      let!(:email_template) { create(:email_template, user: user, account: user.account) }
      let(:params) do
        {
          id: email_template.id,
          text: 'Modifique o template'
        }
      end

      before do
        allow(EmailTemplates::SuggestionService).to receive(:call).and_return(suggestion_response)
      end

      it 'accepts id as parameter' do
        post '/v1/users/email_templates/generate_suggestion', params: params.to_json, headers: authentication_headers

        expect(response).to have_http_status(:ok)
        expect(EmailTemplates::SuggestionService).to have_received(:call).with(email_template, 'Modifique o template', {})
      end
    end

    context 'when not authenticated' do
      let(:params) { { text: 'Crie um template' } }

      it 'returns unauthorized' do
        post '/v1/users/email_templates/generate_suggestion', params: params.to_json, headers: no_authentication_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'POST /v1/users/email_templates/:id/duplicate' do
    let!(:email_template) do
      create(:email_template,
        user: user,
        account: user.account,
        name: 'Template Original',
        subject: 'Assunto Original',
        content: 'Conteúdo original com {{candidato_nome}}',
        category_id: 1
      )
    end

    context 'when authenticated' do
      it 'creates a duplicate of the email template' do
        expect {
          post "/v1/users/email_templates/#{email_template.id}/duplicate", headers: authentication_headers
        }.to change(EmailTemplate, :count).by(1)

        expect(response).to have_http_status(:created)
        json = JSON.parse(response.body)

        expect(json['data']['attributes']['name']).to eq('Template Original (cópia)')
        expect(json['data']['attributes']['subject']).to eq('Assunto Original')
        expect(json['data']['attributes']['content']).to eq('Conteúdo original com {{candidato_nome}}')
        expect(json['data']['attributes']['category_id']).to eq(1)
      end

      it 'sets the duplicate to the current user' do
        post "/v1/users/email_templates/#{email_template.id}/duplicate", headers: authentication_headers

        duplicated = EmailTemplate.last
        expect(duplicated.user_id).to eq(user.id)
        expect(duplicated.account_id).to eq(user.account.id)
      end

      it 'ensures is_deleted is false on duplicate' do
        deleted_template = create(:email_template, :deleted, user: user, account: user.account)

        post "/v1/users/email_templates/#{deleted_template.id}/duplicate", headers: authentication_headers

        duplicated = EmailTemplate.last
        expect(duplicated.is_deleted).to be false
      end

      it 'preserves all template attributes except name, user_id, and is_deleted' do
        post "/v1/users/email_templates/#{email_template.id}/duplicate", headers: authentication_headers

        duplicated = EmailTemplate.last
        expect(duplicated.subject).to eq(email_template.subject)
        expect(duplicated.content).to eq(email_template.content)
        expect(duplicated.category_id).to eq(email_template.category_id)
        expect(duplicated.name).not_to eq(email_template.name)
        expect(duplicated.name).to eq("#{email_template.name} (cópia)")
      end
    end

    context 'when template belongs to another account' do
      let!(:other_template) { create(:email_template, user: other_user, account: other_user.account) }

      it 'returns not found' do
        post "/v1/users/email_templates/#{other_template.id}/duplicate", headers: authentication_headers
        expect(response).to have_http_status(:not_found)
      end

      it 'does not create a duplicate' do
        expect {
          post "/v1/users/email_templates/#{other_template.id}/duplicate", headers: authentication_headers
        }.not_to change(EmailTemplate, :count)
      end
    end

    context 'when not authenticated' do
      it 'returns unauthorized' do
        post "/v1/users/email_templates/#{email_template.id}/duplicate", headers: no_authentication_headers
        expect(response).to have_http_status(:unauthorized)
      end

      it 'does not create a duplicate' do
        expect {
          post "/v1/users/email_templates/#{email_template.id}/duplicate", headers: no_authentication_headers
        }.not_to change(EmailTemplate, :count)
      end
    end
  end

  describe 'GET /v1/users/email_templates/tags' do
    context 'when authenticated' do
      it 'returns all available tags' do
        get '/v1/users/email_templates/tags', headers: authentication_headers

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json['data']).to be_an(Array)
        expect(json['data']).not_to be_empty
        expect(json['data'].first['attributes']).to include('text', 'tag', 'field')
      end

      it 'filters tags by reference_type' do
        get '/v1/users/email_templates/tags', params: { reference_type: 'Candidate' }, headers: authentication_headers

        json = JSON.parse(response.body)
        tags = json['data'].map { |t| t['attributes']['tag'] }
        expect(tags).to include('{{candidate_name}}', '{{candidate_email}}')
        expect(tags).not_to include('{{job_title}}')
      end

      it 'filters tags by multiple reference_types' do
        get '/v1/users/email_templates/tags', params: { reference_types: [ 'Candidate', 'Job' ] }, headers: authentication_headers

        json = JSON.parse(response.body)
        tags = json['data'].map { |t| t['attributes']['tag'] }
        expect(tags).to include('{{candidate_name}}', '{{job_title}}')
      end
    end

    context 'when not authenticated' do
      it 'returns unauthorized' do
        get '/v1/users/email_templates/tags', headers: no_authentication_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'POST /v1/users/email_templates/render' do
    let!(:candidate) { create(:candidate, account_id: account.id, name: 'João Silva', email: 'joao@test.com') }

    context 'when authenticated with inline content' do
      it 'renders candidate variables' do
        post '/v1/users/email_templates/render',
          params: {
            content: 'Olá {{candidate_name}}, seu email é {{candidate_email}}',
            context: { candidate_id: candidate.id }
          }.to_json,
          headers: authentication_headers

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json['rendered_text']).to eq('Olá João Silva, seu email é joao@test.com')
        expect(json['missing_variables']).to be_empty
      end

      it 'returns dash for missing entity' do
        post '/v1/users/email_templates/render',
          params: { content: 'Vaga: {{job_title}}', context: {} }.to_json,
          headers: authentication_headers

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json['rendered_text']).to eq('Vaga: -')
        expect(json['missing_variables']).to be_empty
      end

      it 'reports unknown variables in missing_variables' do
        post '/v1/users/email_templates/render',
          params: { content: 'Olá {{variavel_desconhecida}}', context: {} }.to_json,
          headers: authentication_headers

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json['missing_variables']).to include('{{variavel_desconhecida}}')
      end

      it 'renders user variables from current user' do
        post '/v1/users/email_templates/render',
          params: { content: 'Recrutador: {{user_name}}', context: {} }.to_json,
          headers: authentication_headers

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json['rendered_text']).to eq("Recrutador: #{user.name}")
      end
    end

    context 'when using template_id' do
      let!(:email_template) do
        create(:email_template, user: user, account: account, content: 'Olá {{candidate_name}}!')
      end

      it 'renders from template_id' do
        post '/v1/users/email_templates/render',
          params: {
            template_id: email_template.id,
            context: { candidate_id: candidate.id }
          }.to_json,
          headers: authentication_headers

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json['rendered_text']).to eq('Olá João Silva!')
      end

      it 'allows content to override template content' do
        post '/v1/users/email_templates/render',
          params: {
            template_id: email_template.id,
            content: 'Override: {{candidate_name}}',
            context: { candidate_id: candidate.id }
          }.to_json,
          headers: authentication_headers

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json['rendered_text']).to eq('Override: João Silva')
      end

      it 'returns not found for another account template' do
        other_template = create(:email_template, user: other_user, account: other_user.account)

        post '/v1/users/email_templates/render',
          params: { template_id: other_template.id }.to_json,
          headers: authentication_headers

        expect(response).to have_http_status(:not_found)
      end
    end

    context 'when content is blank' do
      it 'returns unprocessable entity' do
        post '/v1/users/email_templates/render',
          params: { content: '' }.to_json,
          headers: authentication_headers

        expect(response).to have_http_status(:unprocessable_entity)
      end
    end

    context 'when not authenticated' do
      it 'returns unauthorized' do
        post '/v1/users/email_templates/render',
          params: { content: 'Hello' }.to_json,
          headers: no_authentication_headers

        expect(response).to have_http_status(:unauthorized)
      end
    end
  end
end
