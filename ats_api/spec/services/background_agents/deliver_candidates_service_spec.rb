# frozen_string_literal: true

require 'rails_helper'

RSpec.describe BackgroundAgents::DeliverCandidatesService do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:job) { create(:job, user: user, account: account) }
  let(:agent) { create(:background_agent, user: user, account: account, job: job) }
  let(:sourcing) { create(:sourcing, user: user, account: account) }

  before { Apartment::Tenant.switch!(account.tenant) }

  describe '#call' do
    subject(:result) do
      described_class.new(
        background_agent: agent, sourcing: sourcing, candidates_data: candidates_data
      ).call
    end

    context 'when candidates_data is blank' do
      let(:candidates_data) { [] }

      it 'returns zero counts' do
        expect(result).to eq({ created: 0, skipped: 0 })
      end
    end

    context 'when sourcing is nil' do
      let(:candidates_data) { [{ candidate_id: 1 }] }

      it 'returns zero counts' do
        result = described_class.new(
          background_agent: agent, sourcing: nil, candidates_data: candidates_data
        ).call
        expect(result).to eq({ created: 0, skipped: 0 })
      end
    end

    context 'with local candidates' do
      let(:candidate) { create(:candidate, account_id: account.id) }
      let(:candidates_data) do
        [{
          candidate_id: candidate.id,
          source_provider: 'local',
          score: 85.0,
          category: 'strong',
          justification: 'Great match',
          strengths: ['Ruby expert'],
          concerns: [],
          requirement_coverage: 0.9
        }]
      end

      let(:sourced_profile) { create(:sourced_profile, account: account, candidate: candidate) }

      before do
        allow_any_instance_of(BackgroundAgents::LocalProfileCreator)
          .to receive(:call).and_return(sourced_profile)
        sps = create(:sourced_profile_sourcing,
          sourced_profile: sourced_profile, sourcing: sourcing, account: account, user: user)
        allow(sourced_profile).to receive(:ensure_sourced_profile_sourcing).and_return(sps)
      end

      it 'returns created count' do
        expect(result[:created]).to eq(1)
        expect(result[:skipped]).to eq(0)
      end
    end

    context 'with external candidates' do
      let(:candidates_data) do
        [{
          external_id: 'ext_123',
          source_provider: 'pearch',
          name: 'External Candidate',
          score: 90.0,
          category: 'strong'
        }]
      end

      let(:sourced_profile) { create(:sourced_profile, account: account) }

      before do
        allow_any_instance_of(BackgroundAgents::ExternalProfileCreator)
          .to receive(:call).and_return(sourced_profile)
        sps = create(:sourced_profile_sourcing,
          sourced_profile: sourced_profile, sourcing: sourcing, account: account, user: user)
        allow(sourced_profile).to receive(:ensure_sourced_profile_sourcing).and_return(sps)
      end

      it 'returns created count' do
        expect(result[:created]).to eq(1)
        expect(result[:skipped]).to eq(0)
      end
    end

    context 'when profile creation returns nil' do
      let(:candidates_data) { [{ candidate_id: 999, source_provider: 'local' }] }

      before do
        allow_any_instance_of(BackgroundAgents::LocalProfileCreator)
          .to receive(:call).and_return(nil)
      end

      it 'increments skipped' do
        expect(result[:created]).to eq(0)
        expect(result[:skipped]).to eq(1)
      end
    end

    context 'when ensure_sourced_profile_sourcing returns nil' do
      let(:candidate) { create(:candidate, account_id: account.id) }
      let(:candidates_data) { [{ candidate_id: candidate.id, source_provider: 'local' }] }
      let(:sourced_profile) { create(:sourced_profile, account: account, candidate: candidate) }

      before do
        allow_any_instance_of(BackgroundAgents::LocalProfileCreator)
          .to receive(:call).and_return(sourced_profile)
        allow(sourced_profile).to receive(:ensure_sourced_profile_sourcing).and_return(nil)
      end

      it 'increments skipped' do
        expect(result[:created]).to eq(0)
        expect(result[:skipped]).to eq(1)
      end
    end

    context 'when an exception occurs for a candidate' do
      let(:candidates_data) do
        [
          { candidate_id: 999, source_provider: 'local' },
          { candidate_id: 888, source_provider: 'local' }
        ]
      end

      before do
        allow_any_instance_of(BackgroundAgents::LocalProfileCreator)
          .to receive(:call).and_raise(StandardError, 'DB error')
      end

      it 'skips errored candidates and continues' do
        expect(result[:created]).to eq(0)
        expect(result[:skipped]).to eq(2)
      end
    end
  end
end

RSpec.describe BackgroundAgents::ProfileDeduplicator do
  describe '.extract_linkedin_slug' do
    it 'extracts slug from standard URL' do
      expect(described_class.extract_linkedin_slug('https://www.linkedin.com/in/john-doe'))
        .to eq('john-doe')
    end

    it 'extracts slug from URL with query params' do
      expect(described_class.extract_linkedin_slug('https://linkedin.com/in/john-doe?locale=en'))
        .to eq('john-doe')
    end

    it 'returns nil for blank URL' do
      expect(described_class.extract_linkedin_slug(nil)).to be_nil
      expect(described_class.extract_linkedin_slug('')).to be_nil
    end

    it 'returns nil for non-profile URL' do
      expect(described_class.extract_linkedin_slug('https://linkedin.com/company/test')).to be_nil
    end
  end

  describe '.find_existing_external' do
    let(:account) { create(:account) }

    before { Apartment::Tenant.switch!(account.tenant) }

    context 'when profile exists by external_id' do
      let!(:profile) { create(:sourced_profile, account: account, external_id: 'ext_abc') }

      it 'finds by external_id' do
        result = described_class.find_existing_external(
          account_id: account.id, external_id: 'ext_abc', data: {}
        )
        expect(result).to eq(profile)
      end
    end

    context 'when no matching profile exists' do
      it 'returns nil' do
        result = described_class.find_existing_external(
          account_id: account.id, external_id: 'ext_none', data: {}
        )
        expect(result).to be_nil
      end
    end
  end
end

RSpec.describe BackgroundAgents::CurriculumTextBuilder do
  describe '.call' do
    it 'builds text from data' do
      result = described_class.call(
        data: { title: 'Senior Dev', location: 'SP', summary: 'Experienced' },
        experiences: [],
        skills: %w[Ruby Rails],
        certifications: [],
        languages: []
      )

      expect(result).to include('Senior Dev')
      expect(result).to include('SP')
      expect(result).to include('Ruby, Rails')
    end

    it 'includes experience details' do
      experiences = [{
        'company_info' => { 'name' => 'Acme Corp' },
        'company_roles' => [{ 'title' => 'Developer', 'start_date' => '2020-01' }]
      }]

      result = described_class.call(
        data: { title: 'Dev' },
        experiences: experiences,
        skills: [],
        certifications: [],
        languages: []
      )

      expect(result).to include('Acme Corp')
      expect(result).to include('Developer')
    end

    it 'includes certifications' do
      result = described_class.call(
        data: {},
        experiences: [],
        skills: [],
        certifications: [{ 'title' => 'AWS Solutions Architect' }],
        languages: []
      )

      expect(result).to include('AWS Solutions Architect')
    end

    it 'includes languages' do
      result = described_class.call(
        data: {},
        experiences: [],
        skills: [],
        certifications: [],
        languages: [{ 'language' => 'English', 'proficiency' => 'Fluent' }]
      )

      expect(result).to include('English - Fluent')
    end

    it 'returns empty string for blank data' do
      result = described_class.call(
        data: {},
        experiences: [],
        skills: [],
        certifications: [],
        languages: []
      )

      expect(result).to eq('')
    end
  end
end
