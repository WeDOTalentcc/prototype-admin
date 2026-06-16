# frozen_string_literal: true

require 'rails_helper'

RSpec.describe EntityColumnService::Structure, type: :service do
  describe '.supported_entity?' do
    it 'returns true for supported entities' do
      expect(described_class.supported_entity?('candidate')).to be true
      expect(described_class.supported_entity?('job')).to be true
      expect(described_class.supported_entity?('apply')).to be true
    end

    it 'returns false for unsupported entities' do
      expect(described_class.supported_entity?('unsupported')).to be false
      expect(described_class.supported_entity?('')).to be false
      expect(described_class.supported_entity?(nil)).to be false
    end

    it 'handles pluralized entity names' do
      expect(described_class.supported_entity?('candidates')).to be true
      expect(described_class.supported_entity?('jobs')).to be true
    end
  end

  describe '.entity_columns' do
    context 'with supported entity' do
      it 'returns structure for basic request' do
        result = described_class.entity_columns('candidate')

        expect(result).to be_an(Array)
        expect(result).not_to be_empty
        expect(result.first).to have_key(:value)
        expect(result.first).to have_key(:text)
      end

      it 'returns requester-specific columns when available' do
        result = described_class.entity_columns('candidate', 'shortlists')

        expect(result).to be_an(Array)
        expect(result).not_to be_empty
      end

      it 'returns only active columns when only_active is true' do
        result = described_class.entity_columns('candidate', 'shortlists', only_active: true)

        expect(result).to be_an(Array)
      end
    end

    context 'with unsupported entity' do
      it 'returns empty array' do
        result = described_class.entity_columns('unsupported')

        expect(result).to eq([])
      end
    end

    context 'with shortlist requester' do
      let(:account) { create(:account) }
      let!(:report) do
        create(:report,
               name: 'Test Report',
               is_deleted: false,
               account: account
              )
      end

      before do
        allow(Report).to receive(:where).and_return([ report ])
      end

      it 'adds report columns for shortlist requesters' do
        result = described_class.entity_columns('candidate', 'shortlists')

        report_column = result.find { |col| col[:type] == 'ShortlistText' }
        expect(report_column).to be_present
        expect(report_column[:text]).to eq('Test report')
        expect(report_column[:value]).to eq('testreport')
      end
    end

    context 'with job requester and entity_id' do
      let(:job_id) { 123 }
      let(:evaluation_id) { 456 }
      let!(:evaluation) { double('Evaluation', id: evaluation_id) }
      let!(:question) { double('Question', title: 'Test Question', response_type: 1) }

      before do
        allow(Evaluation).to receive(:where).with(job_id: job_id).and_return(double(pluck: [ evaluation_id ]))
        allow(Question).to receive(:where).with(evaluation_id: [ evaluation_id ])
                      .and_return(double(group: double(pluck: [ [ 'Test Question', 1 ] ])))
      end

      it 'adds evaluation question columns' do
        result = described_class.entity_columns('apply', 'job', entity_id: job_id)

        question_column = result.find { |col| col[:type] == 'AnswersCache' }
        expect(question_column).to be_present
        expect(question_column[:text]).to eq('Test Question')
        expect(question_column[:value]).to eq('answers_cache')
        expect(question_column[:entity_id]).to eq(job_id)
      end
    end
  end

  describe '.column_filter_type' do
    it 'returns correct filter types for response types' do
      expect(described_class.column_filter_type(0)).to eq('Text')
      expect(described_class.column_filter_type(1)).to eq('AnswersAgg')
      expect(described_class.column_filter_type(4)).to eq('Money')
      expect(described_class.column_filter_type(7)).to eq('Text')
    end

    it 'returns Text for unknown response types' do
      expect(described_class.column_filter_type(999)).to eq('Text')
      expect(described_class.column_filter_type(nil)).to eq('Text')
    end

    it 'handles string input' do
      expect(described_class.column_filter_type('4')).to eq('Money')
    end
  end

  describe 'private methods' do
    describe '.merge_requester_columns' do
      let(:entity_class) { EntityColumnService::Entities::Candidate }
      let(:requester) { 'default' }

      it 'merges base structure with requester columns' do
        base_structure = [
          { value: 'name', text: 'Name', type: 'text' },
          { value: 'email', text: 'Email', type: 'text' }
        ]
        requester_columns = [
          { value: 'name', text: 'Full Name', type: 'dynamic_text' }
        ]

        allow(entity_class).to receive(:structure).and_return(base_structure)
        allow(entity_class).to receive(:default).and_return(requester_columns)

        result = described_class.send(:merge_requester_columns, entity_class, 'default', nil)

        name_column = result.find { |col| col[:value] == 'name' }
        email_column = result.find { |col| col[:value] == 'email' }

        expect(name_column[:text]).to eq('Full Name')
        expect(name_column[:type]).to eq('dynamic_text')
        expect(email_column[:text]).to eq('Email')
      end
    end

    describe '.build_report_column' do
      let(:report) { double('Report', name: 'Performance Report') }

      it 'builds report column correctly' do
        result = described_class.send(:build_report_column, report)

        expect(result).to eq({
          value: 'performancereport',
          text: 'Performance report',
          sortable: true,
          type: 'ShortlistText',
          filter: 'text'
        })
      end
    end

    describe '.build_question_column' do
      it 'builds question column correctly' do
        result = described_class.send(:build_question_column, 'Test Question', 4, 123)

        expect(result).to eq({
          value: 'answers_cache',
          text: 'Test Question',
          sortable: true,
          type: 'AnswersCache',
          filter: 'Money',
          field_sub_filter: 4,
          entity_id: 123
        })
      end
    end
  end
end
